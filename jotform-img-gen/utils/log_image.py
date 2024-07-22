from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload

import io
import os
import logging
import json
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

def find_file(filename):
    for root, dirs, files in os.walk('.'):
        if filename in files:
            return os.path.join(os.path.abspath(root), filename)
    return None

def load_env_variables():
    # load env variables
    load_dotenv()

    # assign env variables
    try:
        FOLDER_ID = os.getenv("FOLDER_ID")
        SHEET_NAME = os.getenv("SHEET_NAME")
        SHEET_ID = os.getenv("SHEET_ID")
        SERVICE_ACCOUNT_FILE = find_file(str(os.getenv("SERVICE_ACCOUNT_FILE")))

        return (FOLDER_ID, SHEET_NAME, SHEET_ID, SERVICE_ACCOUNT_FILE)
    except ValueError as e:
        logging.info(str(e))

def upload_image_bytes_to_drive(drive_service, image_bytes, image_name, folder_id, mime_type='image/png'):
    image_name += '.png'

    file_metadata = {'name': image_name}
    if folder_id:
        file_metadata['parents'] = [folder_id]
    media = MediaIoBaseUpload(io.BytesIO(image_bytes), mimetype=mime_type, resumable=True)
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')

def append_image_to_sheet(sheets_service, drive_service, sheet_id, sheet_name, 
                          image_bytes, image_name, rating, info, folder_id,
                          ):
    info = json.loads(info.replace("\n", "\\n"))
    assert type(info) == dict, f"info must be of type dict not {type(info)}"

    try:
        # Get the current data in the sheet
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f'{sheet_name}'
        ).execute()
        
        current_data = result.get('values', [])
        
        # Define all required columns
        required_columns = ['SD Model Name', 'Prompt', 'Negative Prompt', 'Sampling Steps',
                            'Sampler Name', 'Schedule Type', 'Width', 'Height', 'CFG Scale', 
                            'Seed', 'Image', 'Rating', 'Image Link']
        
        # Create or update headers
        headers = current_data[0] if current_data else []
        for col in required_columns:
            if col not in headers:
                headers.append(col)
        
        # Update headers if any new columns were added
        sheets_service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f'{sheet_name}!A1',
            valueInputOption='RAW',
            body={'values': [headers]}
        ).execute()

        # Find the next available row
        next_row = len(current_data) + 1

        # Upload image to Drive
        image_id = upload_image_bytes_to_drive(drive_service, image_bytes, image_name, folder_id=folder_id)
        
        # Drive link
        drive_link = f"https://drive.google.com/uc?export=view&id={image_id}"

        # Create IMAGE formula
        image_formula = f"""=IMAGE("{drive_link}", 4, 300, 300)"""
        
        # Prepare the row data
        row_data = [''] * len(headers)
        row_data[headers.index('Image')] = image_formula
        row_data[headers.index('Rating')] = rating
        row_data[headers.index('Prompt')] = info.get('prompt', '')
        row_data[headers.index('Negative Prompt')] = info.get('negative_prompt', '')
        row_data[headers.index('Seed')] = info.get('seed', '')
        row_data[headers.index('Width')] = info.get('width', '')
        row_data[headers.index('Height')] = info.get('height', '')
        row_data[headers.index('Sampler Name')] = info.get('sampler_name', '')
        row_data[headers.index('CFG Scale')] = info.get('cfg_scale', '')
        row_data[headers.index('Sampling Steps')] = info.get('steps', '')
        row_data[headers.index('SD Model Name')] = info.get('sd_model_name', '')
        row_data[headers.index('Image Link')] = drive_link
        
        extra_params = info.get('extra_generation_params', {})
        row_data[headers.index('Schedule Type')] = extra_params.get('Schedule type', '')

        # Append the data to the sheet
        body = {
            'values': [row_data]
        }
        result = sheets_service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=f'{sheet_name}!A{next_row}',
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        
        # Adjust row height and column width for the image
        adjust_cell_size(sheets_service, sheet_id, sheet_name, next_row, headers.index('Image'))

        logging.info(f"Data appended to row {next_row}. {result.get('updates').get('updatedCells')} cells updated.")
    except HttpError as err:
        logging.info(f"An error occurred: {err}")

def adjust_cell_size(sheets_service, sheet_id, sheet_name, row_index, column_index):
    try:
        # Set row height and column width (adjust the size as needed)
        row_height = 300  # in pixels
        column_width = 300  # in pixels
        
        requests = [
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": get_sheet_id(sheets_service, sheet_id, sheet_name),
                        "dimension": "ROWS",
                        "startIndex": row_index - 1,
                        "endIndex": row_index
                    },
                    "properties": {
                        "pixelSize": row_height
                    },
                    "fields": "pixelSize"
                }
            },
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": get_sheet_id(sheets_service, sheet_id, sheet_name),
                        "dimension": "COLUMNS",
                        "startIndex": column_index,
                        "endIndex": column_index + 1
                    },
                    "properties": {
                        "pixelSize": column_width
                    },
                    "fields": "pixelSize"
                }
            }
        ]

        body = {
            'requests': requests
        }
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body=body
        ).execute()

        logging.info(f"Adjusted cell size for row {row_index} and column {chr(65 + column_index)}.")
    except HttpError as err:
        logging.info(f"An error occurred while adjusting cell size: {err}")

def get_sheet_id(sheets_service, sheet_id, sheet_name):
    try:
        spreadsheet = sheets_service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        for sheet in spreadsheet.get('sheets'):
            if sheet.get("properties").get("title") == sheet_name:
                return sheet.get("properties").get("sheetId")
    except HttpError as err:
        logging.info(f"An error occurred while getting sheet ID: {err}")
        return None

def log_image(
        image_bytes: bytes, 
        image_name: str, 
        rating: float, 
        info: str,
    ):
    folder_id, sheet_name, sheet_id, service_account_file = load_env_variables()

    # Use service account credentials
    creds = Credentials.from_service_account_file(
        service_account_file,
        scopes=SCOPES
    )

    try:
        # Create Google Sheets and Drive service
        sheets_service = build('sheets', 'v4', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)

        # Append the image and data to the sheet
        append_image_to_sheet(sheets_service, drive_service, sheet_id, 
                              sheet_name, image_bytes, image_name, rating, 
                              info, folder_id)

        return "The image and associated data were successfully logged."

    except HttpError as err:
        err_str = f"An error occurred: {err}"
        logging.info(err_str)
        return err_str