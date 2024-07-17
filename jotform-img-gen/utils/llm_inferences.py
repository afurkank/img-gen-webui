import os
import logging
from dotenv import load_dotenv
from typing import Literal

from groq import Groq
from openai import OpenAI

# Load the .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)

def groq_inference(
        system_prompt: str, 
        user_prompt: str, 
        model: Literal['llama3-8b', 'llama3-70b', "mixtral-8x7b"], 
        max_tokens: int = 200, 
        temperature: float = 0.8, 
        timeout_seconds: int = 30
    ) -> str:

    try:
        groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    except ValueError as e:
        logging.info(str(e))

    model_mapping = {
        'llama3-8b': 'llama3-8b-8192',
        'llama3-70b': 'llama3-70b-8192',
    }

    model = model_mapping.get(model, 'mixtral-8x7b-32768')
    
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]
        
        chat_completion = groq_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout_seconds
        )

        return chat_completion.choices[0].message.content
    except TimeoutError as e:
        logging.info(str(e))
        return "An error occurred during prompt generation."

def openai_inference(system_prompt: str, 
        user_prompt: str, 
        model: Literal['gpt-3.5-turbo', 'gpt-4'], 
        max_tokens: int = 200, 
        temperature: float = 0.8, 
        timeout_seconds: int = 30
    ) -> str:

    try:
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except ValueError as e:
        logging.info(str(e))
    
    messages = [
        {"role": "system", "content": system_prompt},
        {'role': 'user', 'content': user_prompt}
    ]
    
    chat_completion = openai_client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        timeout=timeout_seconds
    )

    return chat_completion.choices[0].message.content