import gradio as gr
from utils.prompt_constructor import get_prompt_for_image_gen
from utils.local_img_generation import generate_img
from utils.remove_bg import get_bg_removed_img
from io import BytesIO
import PIL.Image

def generate_prompt(image_type, form_id, prompt, llm_model):
    if prompt:
        return prompt, None
    elif form_id:
        try:
            form_id = int(form_id)
            if form_id <= 0:
                raise ValueError("Form ID must be a positive integer.")
            prompt_file_path = f"prompts/{image_type}_img_prompt.txt" # services/jotform/
            return get_prompt_for_image_gen(prompt_file_path, form_id, llm_model), None
        except ValueError as ve:
            return None, f"Invalid Form ID for {image_type}: {str(ve)}"
    else:
        return None, "Either prompt or Form ID must be provided."

def generate_image(image_type, img_model, prompt, negative_prompt, **kwargs):
    
    # if img_model.startswith('dall-e'):
    #     generate_params.update({
    #         'size': img_size,
    #         'quality': img_quality,
    #         'style': img_style
    #     })

    try:
        image_data = generate_img(img_model, prompt, negative_prompt, **kwargs)
        if image_type == 'avatar':
            image_data = get_bg_removed_img(image_bytes=image_data)

        img = PIL.Image.open(BytesIO(image_data))
        return img, None
    except Exception as e:
        return None, f"Error generating image: {str(e)}"

def create_image_generation_tab(image_type):
    with gr.Tab(f"{image_type.capitalize()} Generation"):
        with gr.Row():
            form_id = gr.Number(value=241773743154055, label="Form ID", precision=0, minimum=1)
            prompt = gr.Textbox(label="Prompt", placeholder="Prompt")
            negative_prompt = gr.Textbox(label="Negative prompt", placeholder="Negative prompt")
        
        with gr.Row():
            llm_model = gr.Dropdown(["gpt-3.5-turbo", "llama3-8b", "llama3-70b", "mixtral-8x7b"], value="gpt-3.5-turbo", label="Prompt Model")
            # img_model = gr.Dropdown(["dall-e-3", "sdxl", "sd3", "dall-e-2"], value="dall-e-3", label="Image Model")
            img_model = gr.Dropdown(
                [
                 "sd_xl_base_1.0",
                 "sd_xl_turbo_1.0_fp16",
                 "Juggernaut_X_RunDiffusion",
                 "Juggernaut_X_RunDiffusion_Hyper",
                 "sd3_medium_incl_clips_t5xxlfp16",
                 "Juggernaut-XL_v9_RunDiffusionPhoto_v2",
                ],
                value="Juggernaut-XL_v9_RunDiffusionPhoto_v2",
                label="Image Model"
            )
        with gr.Row():
            use_detailed_hands_lora = gr.Checkbox(
                value=True,
                # info="Whether to use the Detailed Hands Lora",
                label="Detailed Hands Lora"
            )
            use_white_bg_lora = gr.Checkbox(
                value=False,
                # info="Whether to use the White Background Lora. You can mark this if your prompt isn't enough for making the background white.",
                label="White Background Lora"
            )

        # Below are the settings for dall-e:

        # with gr.Row():
        #     img_size = gr.Dropdown(["1024x1024", "1024x1792", "1792x1024"], value="1024x1024", label="Image Size")
        #     img_quality = gr.Dropdown(["standard", "hd"], value="standard", label="Image Quality")
        #     img_style = gr.Dropdown(["vivid", "natural"], value="vivid", label="Image Style")
        
        # Complete list of Sampling Methods:
        # DPM++ 2M, DPM++ SDE, DPM++ 2M SDE
        # DPM++ 2M SDE Heun, DPM++ 2S a
        # DPM++ 3M SDE
        # Euler a, Euler, LMS, Heun, DPM2
        # DPM2 a, DPM fast, DPM adaptive
        # Restart, DDIM, PLMS, UniPC, LCM

        # Complete list of Schedule Types
        # Automatic, Uniform, Karras, Exponential
        # Poly Exponential, SGM Uniform

        # Prompts are constructed as Textbox objects
        # prompt = str(prompt)
        # negative_prompt = str(prompt)

        # # Lora prompts
        # if use_detailed_hands_lora:
        #     prompt += " <lora:detailed_hands:1>" # you can change 1, it needs to be between 0-1
        # if use_white_bg_lora:
        #     prompt += " <lora:white_1_0:1>" # you can change 1, it needs to be between 0-1

        with gr.Row():
            img_width = gr.Dropdown(["512", "832"], value="832", label="Image Width") # ToDo: can be turned into slider
            img_height = gr.Dropdown(["512", "1216"], value="1216", label="Image Height") # ToDo: can be turned into slides
            sampling_method = gr.Dropdown(
                ["DPM++ 2M", "DPM++ SDE", "DPM++ 2M SDE",
                 "DPM++ 2M SDE Heun", "DPM++ 2S a",
                 "DPM++ 3M SDE", "Euler a", "Euler", "LMS",
                 "Heun", "DPM2", "DPM2 a", "DPM fast",
                 "DPM adaptive", "Restart", "DDIM",
                 "PLMS", "UniPC", "LCM",
                ],
                value="DPM++ 2M",
                label="Sampling method"
            )
            schedule_type = gr.Dropdown(
                ["Automatic",
                 "Uniform",
                 "Karras",
                 "Exponential",
                 "Poly Exponential",
                 "SGM Uniform",
                ],
                value="Karras",
                label="Schedule type"
            )
            batch_count = gr.Slider(minimum=1, maximum=100, value=1, step=1, label="Batch count")
            batch_size = gr.Slider(minimum=1, maximum=8, value=1, step=1, label="Batch size")
            cfg_scale = gr.Slider(minimum=1, maximum=30, value=6, step=0.5, label="CFG Scale")
            seed = gr.Number(value=-1, minimum=-1, label="Seed")
            sampling_steps = gr.Slider(minimum=1, maximum=150, value=25, step=1, label="Sampling steps ")
        
        generate_button = gr.Button("Generate Image", size='sm')
        
        output_prompt = gr.Textbox(label="Generated Prompt", placeholder="Prompt generated by LLM", interactive=False)
        output_gallery = gr.Gallery(label="Generated Images", elem_id=f"output-gallery-{image_type}", columns=[3], rows=[1], object_fit="contain", height="auto")
        error_output = gr.Textbox(label="Error", visible=False)
        
        # Below is for showing advanced options when dall-e is selected
        # Not needed if you are running local models

        # def update_model_options(img_model):
        #     is_dall_e = img_model.startswith("dall-e")
        #     return {
        #         img_size: gr.update(visible=is_dall_e),
        #         img_quality: gr.update(visible=is_dall_e),
        #         img_style: gr.update(visible=is_dall_e)
        #     }

        # img_model.change(update_model_options, inputs=[img_model], outputs=[img_size, img_quality, img_style])
        
        def _generate_prompt(image_type, form_id, prompt, llm_model):
            generated_prompt, error = generate_prompt(image_type, form_id, prompt, llm_model)
            return generated_prompt, error

        def _generate_image(
                image_type: str,
                img_model: str,
                prompt: str,
                negative_prompt: str,
                width: int,
                height: int,
                sampling_method: str,
                schedule_type: str,
                batch_count: int,
                batch_size: int,
                cfg_scale: float,
                seed: int,
                sampling_steps: int
            ):
            parameters = { # kwargs
                'width': width,
                'height': height,
                'sampling_method': sampling_method,
                'schedule_type': schedule_type,
                'batch_count': batch_count,
                'batch_size': batch_size,
                'cfg_scale': cfg_scale,
                'seed': seed,
                'sampling_steps': sampling_steps,
                'use_detailed_hands_lora': use_detailed_hands_lora.value,
                'use_white_bg_lora': use_white_bg_lora.value,
            }
            image, error = generate_image(image_type, img_model, prompt, negative_prompt, **parameters)
            if image:
                return [image], error  # Return a list containing the image
            else:
                return None, error
        
        generate_button.click(
            _generate_prompt,
            inputs=[
                gr.Textbox(value=image_type, visible=False),
                form_id,
                prompt,
                llm_model
            ],
            outputs=[output_prompt, error_output]
        ).then(
            _generate_image,
            inputs=[
                gr.Textbox(value=image_type, visible=False),
                img_model,
                output_prompt,
                negative_prompt,
                img_width,
                img_height,
                sampling_method,
                schedule_type,
                batch_count,
                batch_size,
                cfg_scale,
                seed,
                sampling_steps
            ],
            outputs=[output_gallery, error_output]
        )
css = '''
.gradio-container{max-width: 670px !important}
h1{text-align:center}
'''
with gr.Blocks(css=css, theme="bethecloud/storj_theme") as demo:
    gr.Markdown("# AI Background and Avatar Generator")
    
    create_image_generation_tab("background")
    create_image_generation_tab("avatar")

    demo.load(None, None, None)

if __name__ == "__main__":
    demo.launch(
        server_port=5555, # The default port(7860) is used by "sd-auto" Docker container
        # favicon_path="services/jotform/jotform-logo-transparent.svg" # Doesn't work for some reason
    )