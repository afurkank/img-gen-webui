import os
import ast
import logging
import requests
from dotenv import load_dotenv

# Load the .env file
load_dotenv()
logging.basicConfig(level=logging.INFO)

# load env variables
try:
    JOTFORM_API_KEY = os.getenv('JOTFORM_API_KEY')
except ValueError as e:
    logging.info(str(e))

def get_logo_url(form_id: int):
    """
    Retrieves the logo URL from the JotForm form properties using the form ID.

    Args:
        form_id (int): The ID of the JotForm form.

    Returns:
        str: The URL of the form's logo image if the request is successful.
        None: If the request fails or the logo URL cannot be retrieved.

    Raises:
        HTTPError: If the request to the JotForm API fails.

    Example:
    ```
    logo_url = get_logo(form_id=1234567890)
    ```
    """
    url = f"https://api.jotform.com/form/{form_id}/properties"
    
    params = {
        "apiKey": JOTFORM_API_KEY
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        # Request was successful
        data = response.json()

        json_str:str = data['content']['styleJSON']

        parsed_dict = ast.literal_eval(json_str.replace('\\', ''))

        try:
            logo_url = parsed_dict['@formCoverImg']
            return logo_url
        except:
            logging.info("Form doesn't have a logo, continuing without color extraction..")
            return None
    else:
        # Request failed
        logging.info(f"Request failed with status code: {response.status_code}")
        logging.info(response.text)
    return

def get_title(form_id: int):
    """
    Retrieves the title of the first question from a JotForm form using the form ID.

    Args:
        form_id (int): The ID of the JotForm form.

    Returns:
        str: The title of the first question in the form.

    Raises:
        HTTPError: If the request to the JotForm API fails.

    Example:
    ```
    title = get_title(form_id=1234567890)
    ```
    """

    url = f"https://api.jotform.com/form/{form_id}/questions"

    params = {
        "apiKey": JOTFORM_API_KEY
    }

    # Make the GET request
    response = requests.get(url, params=params)
    # Check if the request was successful
    if response.status_code == 200:
        # Request was successful
        data = response.json()
        answers:dict = data["content"]
    else:
        # Request failed
        logging.info(f"Request failed with status code: {response.status_code}")
        logging.info(response.text)

    title = next(iter(answers.items()))[1]['text']

    return title