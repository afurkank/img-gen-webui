def read_prompts_from_file(file_path, **kwargs):
    """
    Reads and extracts the system and user prompts from a .txt file and
    dynamically inserts values into the user prompt using f-string formatting.

    Args:
        file_path (str): The path to the .txt file containing the prompts.
        **kwargs: Additional keyword arguments to be used for dynamic content 
                  insertion into the user prompt.

    Returns:
        tuple: A tuple containing the system prompt and the user prompt with 
               dynamic content inserted.

    Raises:
        FileNotFoundError: If the specified file path does not exist.
        ValueError: If the prompts are not properly formatted in the file.

    Example:
    ```
    system_prompt, user_prompt = read_prompts_from_file(
        'prompts.txt', frequent_colors="(27, 56, 23)\n(87, 57, 12)\n(42, 106, 71)", len=len
    )
    ```
    """
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Extract SYSTEM_PROMPT and USER_PROMPT from the file content
    system_prompt_start = content.find('SYSTEM_PROMPT="""') + len('SYSTEM_PROMPT="""')
    system_prompt_end = content.find('"""', system_prompt_start)
    system_prompt = content[system_prompt_start:system_prompt_end]
    
    user_prompt_start = content.find('USER_PROMPT="""') + len('USER_PROMPT="""')
    user_prompt_end = content.find('"""', user_prompt_start)
    user_prompt = content[user_prompt_start:user_prompt_end]
    
    # Use eval to dynamically insert values into the USER_PROMPT
    user_prompt = eval(f"f'''{user_prompt}'''", {}, kwargs)
    
    return system_prompt, user_prompt