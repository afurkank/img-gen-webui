from Pylette import extract_colors
from Pylette.src.palette import Palette

import requests
from collections import Counter
import re
import logging

from utils.jotform_api import get_logo_url
from utils.llm_inferences import openai_inference
from utils.prompt_reader import read_prompts_from_file

logging.basicConfig(level=logging.INFO)

### FOR JPG, PNG, etc.

def get_palette_from_png_jpg(
        image_path: str | None = None,
        image_url: str | None = None,
        image_bytes: bytes | None = None
    ) -> Palette:
    """
    :param image_path: path to Image file
    :param image_url: url to the image-file
    :param image_bytes: bytes representing the image data
    :return: a list of the extracted colors

    This will return a palette object that supports indexing and iteration.
    The colors are sorted from highest to lowest frequency by default.

    ```
    most_common_color = palette[0]
    least_common_color = palette[-1]
    three_most_common_colors = palette[:3]
    ```
    
    The Palette object contains a list of Color objects, which contains a 
    representation of the color in various color modes, with RGB being the 
    default. Accessing the color attributes is easy:

    ```
    color = palette[0]

    print(color.rgb)
    print(color.hls)
    print(color.hsv)
    ```
    
    Here are some other usages:
    To display the color palette:
    `palette.display(save_to_file=False)`
    
    To dump the palette to a CSV file:
    `palette.to_csv(filename='color_palette.csv', frequency=True)`

    In order to pick colors from the palette at random, use the 
    random_color-method which supports both drawing uniformly, and 
    from the original color distribution, given by the frequencies 
    of the extracted colors:
    ```
    random_color = palette.random_color(N=1, mode='uniform')
    random_colors = palette.random_color(N=100, mode='frequency')
    ```
    """
    if image_path:
        return extract_colors(image=image_path, palette_size=10, resize=True)
    elif image_bytes:
        return extract_colors(image_bytes=image_bytes, palette_size=10, resize=True)

    return extract_colors(image_url=image_url, palette_size=10, resize=True)

### FOR SVG

def get_palette_from_svg(svg_url):
    """
    Extracts the most frequent colors from an SVG file at the given URL and 
    returns them as a list of RGB tuples.

    Args:
        svg_url (str): The URL of the SVG file.

    Returns:
        list: A list of RGB tuples representing the most frequent colors in the SVG file.

    Example:
    ```
    palette = get_palette_from_svg('https://example.com/image.svg')
    # Output: [(255, 87, 51), (34, 34, 34), ...]
    ```
    """

    def _hex_to_rgb(hex_color):
        """
        Converts a hexadecimal color code to an RGB tuple.

        Args:
            hex_color (str): The hexadecimal color code (e.g., '#ff5733' or 'ff5733').

        Returns:
            tuple: A tuple representing the RGB color (e.g., (255, 87, 51)).

        Example:
        ```
        rgb = hex_to_rgb('#ff5733')
        # Output: (255, 87, 51)
        ```
        """
        # Remove the '#' if present
        hex_color = hex_color.lstrip('#')
        
        # Convert 3-digit hex to 6-digit
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        
        # Convert to RGB
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    # Fetch the SVG content from the URL
    response = requests.get(svg_url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch SVG from URL. Status code: {response.status_code}")
    
    svg_content = response.text

    # Use regex to find all hexadecimal color codes
    color_pattern = r'#[0-9A-Fa-f]{6}|#[0-9A-Fa-f]{3}'
    colors = re.findall(color_pattern, svg_content)

    # Convert all colors to lowercase for consistency
    colors = [color.lower() for color in colors]

    # Convert HEX to RGB
    rgb_colors = [_hex_to_rgb(color) for color in colors]

    # Count the frequency of each color
    color_counts = Counter(rgb_colors)

    # Sort colors by frequency, most frequent first
    sorted_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)

    return [color for color, _ in sorted_colors]

def get_logo_color_palette(logo_url: str):
    """
    Extracts the most frequent colors from the logo of a JotForm form.

    Args:
        logo_url (str): The URL of the logo.

    Returns:
        list: A list of the most frequent colors in (r, g, b) format extracted 
              from the logo. The list contains up to three colors.

    Raises:
        ValueError: If the logo URL is not valid or the color extraction fails.

    Example:
    ```
    colors = get_logo_color_palette(form_id=1234567890)
    ```
    """
    if '.svg' in logo_url:
        # returns list of colors in (r, g, b) format
        colors = get_palette_from_svg(svg_url=logo_url)
    else:
        # returns Palette object
        palette: Palette = get_palette_from_png_jpg(image_url=logo_url)

        colors = [list(color.rgb) for color in palette]

    # get the most frequent 3 colors
    num_colors_to_pick = min(len(colors), 3) # make sure we are not out of bounds
    colors = colors[:num_colors_to_pick]

    logging.info(f"Colors extracted from the logo: {colors}")

    return colors

def get_structured_color_descriptions(form_id: int, prompt_file_path: str) -> str:
    """
    Retrieves structured color descriptions for the logo of a JotForm form using a 
    specified prompt file and an LLM.

    Args:
        form_id (int): The ID of the JotForm form.
        prompt_file_path (str): The path to the prompt file used for generating the 
                                structured color descriptions.

    Returns:
        str: The response containing structured color descriptions.
        str: "Timeout" if the request times out.

    Raises:
        TimeoutError: If the request times out.

    Example:
    ```
    descriptions = get_structured_color_descriptions(form_id=1234567890, prompt_file_path="prompts/color_palette_prompt.txt")
    # output: "{"1": "Dark Blue", "2": "Orange", "3": "Light Blue"}"
    ```
    """
    logo_url = get_logo_url(form_id=form_id)
    if not logo_url:
        return None
    frequent_colors = get_logo_color_palette(logo_url=logo_url)

    system_prompt, user_prompt = read_prompts_from_file(prompt_file_path, frequent_colors=frequent_colors, len=len)
    try:
        response = openai_inference(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model="gpt-3.5-turbo",
            max_tokens=50,
            temperature=0,
            timeout_seconds=30
        )

        return response
    except TimeoutError:
        return "Timeout"