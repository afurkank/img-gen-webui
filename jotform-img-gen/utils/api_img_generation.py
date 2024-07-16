import os
import logging
import openai
import base64
import requests
from dotenv import load_dotenv
from openai import OpenAI
from typing import Literal

# Load the .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)

# load env variables
try:
    openai_client = OpenAI()
    openai_client.api_key = os.getenv("OPENAI_API_KEY")
except ValueError as e:
    logging.info(str(e))

def generate_img(
        prompt: str,
        model: Literal["dall-e-3", "dall-e-2", "sd3", "sdxl"] = "dall-e-3",
        size: Literal["1024x1024", "1024x1792", "1792x1024"] = "1024x1024",
        quality: Literal["hd", "standard"] = "standard",
        style: Literal["natural", "vivid"] = "vivid"
    ) -> bytes:
    if model.startswith('dall-e'):
        try:
            response = openai_client.images.generate(
            model=model,
            prompt=prompt,
            size=size,
            quality=quality,
            style=style,
            n=1,
            response_format='b64_json' # 'b64_json' or 'url'
            )
        except openai.OpenAIError as e:
            logging.info(e.http_status)
            logging.info(e.error)
            raise

        image_data = response.data[0].b64_json

        # Decode the base64 string to bytes
        image_bytes = base64.b64decode(image_data)

        return image_bytes
    elif model == 'sd3':
        return generate_sd3_image(prompt)
    else:
        return generate_sdxl_image(prompt)

def generate_sd3_image(prompt: str):
    try:
        NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
    except ValueError as e:
        logging.info(str(e))
    
    invoke_url = "https://ai.api.nvidia.com/v1/genai/stabilityai/stable-diffusion-3-medium"

    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Accept": "application/json",
    }

    payload = {
        "prompt": f"{prompt}",
        "cfg_scale": 5,
        "aspect_ratio": "16:9",
        "seed": 0,
        "steps": 30,
        "negative_prompt": "(deformed, distorted, disfigured:1.3), poorly drawn, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, (mutated hands and fingers:1.4), disconnected limbs, mutation, mutated, ugly, disgusting, blurry, amputation"
    }

    response = requests.post(invoke_url, headers=headers, json=payload)

    response.raise_for_status()
    response_body = response.json()

    image_bytes = base64.b64decode(response_body['image'])

    return image_bytes

def generate_sdxl_image(prompt: str):
    try:
        NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
    except ValueError as e:
        logging.info(str(e))
    
    invoke_url = "https://ai.api.nvidia.com/v1/genai/stabilityai/stable-diffusion-xl"

    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Accept": "application/json",
    }

    payload = {
        "text_prompts": [
            {
                "text": f"{prompt}",
                "weight": 1
            },
            {
                "text": "(deformed, distorted, disfigured:1.3), poorly drawn, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, (mutated hands and fingers:1.4), disconnected limbs, mutation, mutated, ugly, disgusting, blurry, amputation",
                "weight": -1
            }
        ],
        "cfg_scale": 5,
        "sampler": "K_DPM_2_ANCESTRAL",
        "seed": 0,
        "steps": 25
    }

    response = requests.post(invoke_url, headers=headers, json=payload)

    response.raise_for_status()
    response_body = response.json()

    image_bytes = base64.b64decode(response_body['artifacts'][0]['base64'])

    return image_bytes

def stability_ai_inference(prompt: str):
    try:
        STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
    except ValueError as e:
        logging.info(str(e))
    
    response = requests.post(
        f"https://api.stability.ai/v2beta/stable-image/generate/sd3-medium",
        headers={
            "authorization": f"Bearer {STABILITY_API_KEY}",
            "accept": "application/json"
        },
        files={"none": ''},
        data={
            "prompt": f"{prompt}",
            "output_format": "png",
        },
    )

    if response.status_code == 200:
        # Decode the base64 string to bytes
        response_body = response.json()

        image_bytes = base64.b64decode(response_body['image'])

        return image_bytes
    else:
        raise Exception(str(response.json()))