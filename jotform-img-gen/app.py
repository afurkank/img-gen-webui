import json
import logging
import PIL.Image
import gradio as gr

from utils.prompt_constructor import get_prompt_for_image_gen
from utils.local_img_generation import generate_img
from utils.remove_bg import get_bg_removed_img
from utils.log_image import log_image
from io import BytesIO

def generate_prompt(image_type, form_id, prompt, llm_model):
    if prompt:
        return prompt, None
    elif form_id:
        try:
            form_id = int(form_id)
            if form_id <= 0:
                raise ValueError("Form ID must be a positive integer.")
            prompt_file_path = f"prompts/{image_type}_img_prompt.txt"
            return get_prompt_for_image_gen(prompt_file_path, form_id, llm_model), None
        except ValueError as ve:
            return None, f"Invalid Form ID for {image_type}: {str(ve)}"
    else:
        return None, "Either prompt or Form ID must be provided."

def generate_image(image_type, img_model, prompt, negative_prompt, rmv_bg: bool, **kwargs):
    """
    Takes in image type (Background or Avatar) and model parameters.

    Returns PIL image(used for displaying the image), generation info, and image bytes.
    """
    try:
        image_bytes, info = generate_img(img_model, prompt, negative_prompt, **kwargs)
        if image_type == 'avatar' and rmv_bg:
            image_bytes = get_bg_removed_img(image_bytes=image_bytes)

        img = PIL.Image.open(BytesIO(image_bytes))
        return img, info, image_bytes
    except Exception as e:
        return None, f"Error generating image: {str(e)}", None

def create_image_generation_tab(image_type):
    with gr.Tab(f"{image_type.capitalize()} Generation"):
        with gr.Row():
            with gr.Column(scale=2):
                with gr.Row(equal_height=True):
                    form_id = gr.Number(label="Form ID", value=None, minimum=0, step=1, interactive=True, scale=1)
                    prompt = gr.Textbox(label="Prompt", placeholder="Prompt", scale=2)
                    negative_prompt = gr.Textbox(label="Negative prompt", placeholder="Negative prompt", scale=2)
                with gr.Row(equal_height=True):
                    llm_model = gr.Dropdown(["gpt-3.5-turbo", "llama3-8b", "llama3-70b", "mixtral-8x7b"], value="gpt-3.5-turbo", label="Prompt Model", scale=1)
                    img_model = gr.Dropdown(
                        [
                            "sd_xl_base_1.0",
                            "sd_xl_turbo_1.0_fp16",
                            "Juggernaut_X_RunDiffusion",
                            "Juggernaut_X_RunDiffusion_Hyper",
                            "sd3_medium_incl_clips_t5xxlfp16",
                            "Juggernaut-XL_v9_RunDiffusionPhoto_v2",
                            "sdxl_lightning_4step",
                            "sdxl_lightning_8step",
                            "Juggernaut_RunDiffusionPhoto2_Lightning_4Steps"
                        ],
                        value="sd_xl_turbo_1.0_fp16",
                        label="Image Model",
                        scale=2
                    )
                    update_options_bttn = gr.Button("Update Generation Parameters", size='sm', scale=0)

                with gr.Row():
                    if image_type=='avatar':
                            rmv_bg_checkbox = gr.Checkbox(value=False, label="Remove background", scale=1)
                    else:
                        rmv_bg_checkbox = gr.Checkbox(value=False, label="Remove background", scale=1, visible=False)
                with gr.Row():
                    with gr.Accordion("Generation Parameters", open=False):
                        with gr.Row(equal_height=True):
                            img_width = gr.Slider(minimum=64, step=16, maximum=2048, value="512", label="Image Width", scale=1)
                            img_height = gr.Slider(minimum=64, step=16, maximum=2048, value="512", label="Image Height", scale=1)
                            sampling_method = gr.Dropdown(
                                ["DPM++ 2M", "DPM++ SDE", "DPM++ 2M SDE", "DPM++ 2M SDE Heun", "DPM++ 2S a",
                                "DPM++ 3M SDE", "Euler a", "Euler", "LMS", "Heun", "DPM2", "DPM2 a", "DPM fast",
                                "DPM adaptive", "Restart", "DDIM", "PLMS", "UniPC", "LCM"],
                                value="DPM++ 2M",
                                label="Sampling method", scale=1
                            )
                        with gr.Row(equal_height=True):
                            schedule_type = gr.Dropdown(
                                ["Automatic", "Uniform", "Karras", "Exponential", "Poly Exponential", "SGM Uniform"],
                                value="Karras",
                                label="Schedule type", scale=1
                            )
                            cfg_scale = gr.Slider(minimum=1, maximum=30, value=1, step=0.5, label="CFG Scale", scale=1)
                            sampling_steps = gr.Slider(minimum=1, maximum=150, value=1, step=1, label="Sampling steps")
                        with gr.Row(equal_height=True):
                            batch_count = gr.Slider(minimum=1, maximum=100, value=1, step=1, label="Batch count")
                            batch_size = gr.Slider(minimum=1, maximum=8, value=1, step=1, label="Batch size")
                            seed = gr.Number(value=1337, minimum=0, precision=0, step=1, label="Seed")
                        with gr.Row(equal_height=True):
                            use_detailed_hands_lora = gr.Checkbox(value=False, label="Detailed Hands Lora", scale=1)
                            use_white_bg_lora = gr.Checkbox(value=False, label="White Background Lora", scale=1)
                            use_sdxl_lightning_4step_lora = gr.Checkbox(value=False, label="SDXL-Lightning 4 Step Lora", scale=1)
                            use_sdxl_lightning_8step_lora = gr.Checkbox(value=False, label="SDXL-Lightning 8 Step Lora", scale=1)
                generate_button = gr.Button("Generate Image", size='sm')
                output_prompt = gr.Textbox(label="Generated Prompt", placeholder="Prompt generated by LLM", interactive=False)
                info_output = gr.Textbox(label="Generation Info", visible=False)
                with gr.Row(visible=False) as rating_row:
                    rating = gr.Slider(label="Image Rating (1-10)", minimum=1, maximum=10, step=0.5, value=5, interactive=True)
                with gr.Row(visible=False) as user_row:
                    user = gr.Dropdown(choices=['Burak', 'Çağlar', 'Furkan', 'Esra', 'Melike'], value='Furkan', label='User')
                with gr.Row(visible=False) as log_row:
                    log_button = gr.Button("Log the image and its rating", size='sm')
                with gr.Row(visible=False) as success_row:
                    success_text = gr.Textbox(label="Logging Status", placeholder="", interactive=False)

            with gr.Column(scale=1):
                output_image = gr.Image(label="Generated Image", elem_id=f"output-image-{image_type}", type="pil", width=512, height=600)
                

        image_bytes_state = gr.State(None)

        def _generate_image(image_type:str, img_model:str, prompt:str, negative_prompt:str, width:int, 
                            height:int, sampling_method:str, schedule_type:str, batch_count:int, batch_size:int, 
                            cfg_scale:float, seed:float, sampling_steps:int, rmv_bg_checkbox,
                            hands_lora:bool, white_bg_lora:bool, sdxl_light_4s_lora:bool, sdxl_light_8s_lora:bool):
            parameters = {
                'width': width,
                'height': height,
                'sampling_method': sampling_method,
                'schedule_type': schedule_type,
                'batch_count': batch_count,
                'batch_size': batch_size,
                'cfg_scale': cfg_scale,
                'seed': seed,
                'sampling_steps': sampling_steps,
                'use_detailed_hands_lora': hands_lora,
                'use_white_bg_lora': white_bg_lora,
                'use_4step_lora': sdxl_light_4s_lora,
                'use_8step_lora': sdxl_light_8s_lora,
            }
            pil_image, info, image_bytes = generate_image(image_type, img_model, prompt, negative_prompt, rmv_bg_checkbox, **parameters)

            if pil_image is not None:
                return pil_image, info, image_bytes, gr.update(visible=True), gr.update(visible=True), gr.update(visible=True) # change the 1st gr.update to make info visible
            else:
                return None, info, None, gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

        def _log_image(image_bytes, rating, info, user, form_id):
            """
            Takes in image bytes, rating, and JSON formatted generation info.

            Returns a string indicating whether or not the logging was successful
            Updates the visibility of log_result text box
            """
            if image_bytes is None:
                return gr.update(value="No image to log. Please generate an image first.", visible=True)
            
            image_name = json.loads(info.replace("\n", "\\n")).get('job_timestamp')
            if rating is None:
                return gr.update(value="Please provide a rating.", visible=True)

            try:
                log_result = log_image(image_bytes, image_name, rating, info, user, form_id=form_id)
                return gr.update(value=log_result, visible=True)
            except Exception as e:
                return gr.update(value=f"Error logging image: {str(e)}", visible=True)
        
        def update_options(sd_model_name: str):
            parameter_mapping = {
                'Juggernaut_RunDiffusionPhoto2_Lightning_4Steps': {
                    'width': 1024,'height': 1024,'sampling_method': 'DPM++ SDE',
                    'schedule_type': 'Karras','cfg_scale': 1.5,'sampling_steps': 6,
                },
                'Juggernaut-XL_v9_RunDiffusionPhoto_v2': {
                    'width': 832,'height': 1216,'sampling_method': 'DPM++ 2M',
                    'schedule_type': 'Karras','cfg_scale': 5,'sampling_steps': 30,
                },
                'Juggernaut_X_RunDiffusion': {
                    'width': 832,'height': 1216,'sampling_method': 'DPM++ 2M',
                    'schedule_type': 'Karras','cfg_scale': 5,'sampling_steps': 30,
                },
                'Juggernaut_X_RunDiffusion_Hyper': {
                    'width': 832,'height': 1216,'sampling_method': 'DPM++ SDE',
                    'schedule_type': 'Karras','cfg_scale': 1.5,'sampling_steps': 5,
                },
                'sdxl_lightning_4step': {
                    'width': 1024,'height': 1024,'sampling_method': 'Euler',
                    'schedule_type': 'SGM Uniform','cfg_scale': 1,'sampling_steps': 4,
                },
                'sdxl_lightning_8step': {
                    'width': 1024,'height': 1024,'sampling_method': 'Euler',
                    'schedule_type': 'SGM Uniform','cfg_scale': 1,'sampling_steps': 8,
                }
            }

            if sd_model_name in parameter_mapping:
                return parameter_mapping[sd_model_name]
            else:
                return {
                    'width': 512,'height': 512,'sampling_method': 'DPM++ 2M',
                    'schedule_type': 'Karras','cfg_scale': 1,'sampling_steps': 1
                }
        
        def update_ui_components(sd_model_name):
            new_params = update_options(sd_model_name)
            
            updates = [
                gr.update(value=new_params['width']),  # for img_width
                gr.update(value=new_params['height']),  # for img_height
                gr.update(value=new_params['sampling_method']),  # for sampling_method
                gr.update(value=new_params['schedule_type']),  # for schedule_type
                gr.update(value=new_params['cfg_scale']),  # for cfg_scale
                gr.update(value=new_params['sampling_steps'])   # for sampling_steps
            ]
            logging.info(f"Updated parameters for {sd_model_name}")
            
            return updates

        update_options_bttn.click(
            update_ui_components,
            inputs=[img_model],
            outputs=[img_width, img_height, sampling_method, schedule_type, cfg_scale, sampling_steps]
        )

        generate_button.click(
            generate_prompt,

            inputs=[gr.Textbox(value=image_type, visible=False), form_id, prompt, llm_model],

            outputs=[output_prompt, info_output]
        ).then(
            _generate_image,

            inputs=[gr.Textbox(value=image_type, visible=False), img_model, output_prompt, negative_prompt,
                    img_width, img_height, sampling_method, schedule_type, batch_count, batch_size,
                    cfg_scale, seed, sampling_steps, rmv_bg_checkbox, use_detailed_hands_lora,
                    use_white_bg_lora, use_sdxl_lightning_4step_lora, use_sdxl_lightning_8step_lora],

            outputs=[output_image, info_output, image_bytes_state, rating_row, user_row, log_row]
        )

        log_button.click(
            _log_image,
            inputs=[image_bytes_state, rating, info_output, user, form_id],
            outputs=[success_text]
        ).then(
            lambda: gr.update(visible=True),
            outputs=[success_row]
        )

css = '''
.gradio-container{max-width: 1200px !important}
h1{text-align:center}
.clickable-image img {
    cursor: pointer;
}
'''
js_func = """
function refresh() {
    const url = new URL(window.location);

    if (url.searchParams.get('__theme') !== 'dark') {
        url.searchParams.set('__theme', 'dark');
        window.location.href = url.href;
    }
}
"""
with gr.Blocks(css=css, js=js_func, theme="bethecloud/storj_theme") as demo:
    gr.Markdown("# AI Background and Avatar Generator")
    
    create_image_generation_tab("background")
    create_image_generation_tab("avatar")

if __name__ == "__main__":
    demo.launch(server_port=8080)