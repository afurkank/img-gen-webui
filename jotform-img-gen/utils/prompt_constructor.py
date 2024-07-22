import json
import logging
from typing import Literal
from dotenv import load_dotenv

from utils.get_color_palette import get_structured_color_descriptions
from utils.llm_inferences import groq_inference, openai_inference
from utils.prompt_reader import read_prompts_from_file
from utils.jotform_api import get_title

# Load the .env file
load_dotenv()
logging.basicConfig(level=logging.INFO)

def get_prompt_for_image_gen(
        prompt_file_path: str,
        form_id: int, 
        model: Literal['llama3-8b', 'llama3-70b', 'mixtral-8x7b', 'gpt-3.5-turbo'] = 'llama3-8b'
    ):
    """
    Generates a prompt for image generation using structured color descriptions and 
    form details from a JotForm form.

    Args:
        form_id (int): The ID of the JotForm form.
        model (Literal['llama3-8b', 'llama3-70b', 'mixtral-8x7b']): The model to be used 
              for generating the prompt. Defaults to 'llama3-8b'.

    Returns:
        str: The generated prompt for image generation.
        str: "Timeout" if the request times out.

    Raises:
        TimeoutError: If the request times out.

    Example:
    ```
    prompt = get_prompt_for_image_gen(form_id=1234567890, model='llama3-70b')
    ```
    """
    # some parameters
    temperature = 0.8
    max_tokens = 200
    timeout_seconds = 30

    # Get title of the form
    heading = get_title(form_id=form_id)

    # Get colors of the logo
    colors = get_structured_color_descriptions(form_id=form_id, prompt_file_path="prompts/color_palette_prompt.txt")
    if colors:
        colors_json = json.loads(colors)
        colors_string = ", ".join(colors_json.values())

        logging.info(f"Color descriptions of logo: {colors_string}")

        # Read pre-defined prompt
        # either 'avatar image' or 'background image' prompt file can be used here
        system_prompt, user_prompt = read_prompts_from_file(file_path=prompt_file_path, heading=heading, colors_string=colors_string, len=len)
    else:
        # logo form doesn't exist, so we cannot extract colors
        # we read the prompt that doesn't require colors as input
        prompt_file_name = prompt_file_path.split('.')[0]
        new_file_path = prompt_file_name + '_wo_color' + '.txt'
        system_prompt, user_prompt = read_prompts_from_file(file_path=new_file_path, heading=heading, len=len)

    # Get prompt via LLM for image generation
    try:
        generated_prompt = groq_inference(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout_seconds=timeout_seconds
        ) if model != 'gpt-3.5-turbo' else openai_inference(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout_seconds=timeout_seconds
        )

        return generated_prompt
    except TimeoutError:
        return "Timeout"