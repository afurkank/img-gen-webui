import logging
import base64
import requests

logging.basicConfig(level=logging.INFO)

def generate_img(
        img_model: str,
        prompt: str,
        negative_prompt: str,
        **kwargs
    ) -> bytes:
    
    """ Take image Stable Diffusion parameters and make API call to sd-auto Docker endpoint"""

    url = "http://0.0.0.0:7860"

    # Check for Lora
    use_detailed_hands_lora = kwargs.get('use_detailed_hands_lora', False)
    use_white_bg_lora = kwargs.get('use_white_bg_lora', False)

    if use_detailed_hands_lora:
        prompt += " <lora:detailed_hands:1>" # you can change 1, it needs to be between 0-1
        logging.info("Using 'Detailed Hands Lora'")
    if use_white_bg_lora:
        prompt += " <lora:white_1_0:1>" # you can change 1, it needs to be between 0-1
        logging.info("Using 'White Background Lora'")

    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "seed": kwargs.get('seed'),
        "sampler_name": kwargs.get('sampling_method'),
        "scheduler": kwargs.get('schedule_type'),
        "batch_size": kwargs.get('batch_size'),
        "n_iter": kwargs.get('batch_count'), # ToDo: This may not be related to batch count
        "steps": kwargs.get('sampling_steps'),
        "cfg_scale": kwargs.get('cfg_scale'),
        "width": kwargs.get('width'),
        "height": kwargs.get('height'),
        "override_settings": {
            "sd_model_checkpoint": img_model
        },
    }
    logging.info(f"Payload: {payload}")

    response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=payload)
    # print(response)
    r = response.json()
    # print(r)
    response.raise_for_status()

    image = r['images'][0]
    
    image_bytes = base64.b64decode(image)

    return image_bytes