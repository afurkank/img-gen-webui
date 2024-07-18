from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload

import pandas as pd
import io

# Define constants
FOLDER_ID = "1oHyGGix-jLUVO_mbiOLXfCY7k4i2jIPO"
SHEET_NAME = "Sheet1"
SHEET_ID = "1zndzuJQ8Uon6I9QO8zM-J2UF4fK1iGyai0STlwTUNVQ"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = '/home/af-karacik/img-gen-webui/jotform-img-gen/sd-logs-429806-2c7f160953be.json'

# Use service account credentials
creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=SCOPES
)

def upload_image_bytes_to_drive(drive_service, image_bytes, image_name, folder_id, mime_type='image/png'):
    file_metadata = {'name': image_name}
    if folder_id:
        file_metadata['parents'] = [folder_id]
    media = MediaIoBaseUpload(io.BytesIO(image_bytes), mimetype=mime_type, resumable=True)
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')

def append_image_to_sheet(sheets_service, drive_service, sheet_id, sheet_name, image_bytes, image_name):
    try:
        # Get the current data in the sheet
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f'{sheet_name}'
        ).execute()
        current_data = result.get('values', [])
        
        # Find or create the 'Image' column
        headers = current_data[0] if current_data else []
        if 'Image' not in headers:
            image_column = len(headers)
            headers.append('Image')
            # Update headers if 'Image' column was added
            sheets_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=f'{sheet_name}!A1',
                valueInputOption='RAW',
                body={'values': [headers]}
            ).execute()
        else:
            image_column = headers.index('Image')

        # Find the next available row
        next_row = len(current_data) + 1

        # Upload image to Drive
        image_id = upload_image_bytes_to_drive(drive_service, image_bytes, image_name, folder_id=FOLDER_ID)
        
        # Create IMAGE formula
        image_formula = f"""=IMAGE("https://drive.google.com/uc?export=view&id={image_id}", 4, 512, 512)"""
        
        # Prepare the row data
        row_data = [''] * len(headers)
        row_data[image_column] = image_formula

        # Append the image formula to the sheet
        body = {
            'values': [row_data]
        }
        result = sheets_service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=f'{sheet_name}!A{next_row}',
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        
        print(f"Image appended to row {next_row}, column {chr(65 + image_column)}. {result.get('updates').get('updatedCells')} cell updated.")
    except HttpError as err:
        print(f"An error occurred: {err}")

try:
    # Create Google Sheets and Drive service
    sheets_service = build('sheets', 'v4', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    image_bytes = None
    with open('kitten.png', 'rb') as f:
        image_bytes = f.read()
    image_name = "generated_image.png"

    # Append the image to the sheet
    append_image_to_sheet(sheets_service, drive_service, SHEET_ID, SHEET_NAME, image_bytes, image_name)

except HttpError as err:
    print(f"An error occurred: {err}")