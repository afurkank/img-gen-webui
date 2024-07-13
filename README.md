![UI](UI.png)

# How to Run
Clone the repo:

`git clone https://github.com/afurkank/img-gen-webui.git`

and run:

```
docker compose --profile download up --build
# wait until its done, then:
docker compose --profile [ui] up --build
# where [ui] is one of: auto | auto-cpu | comfy | comfy-cpu
```

### Note

Do not select *sd3_medium_incl_clips_t5xxlfp16*. It breaks everything at the moment 🥲

# How to add custom models

Right now adding custom models and Loras is a bit messy since I simply download model weights from wherever their weights are, upload them to my HuggingFace repo, and get the download links from there. So you kind of need to ask me to add models for the time being until I find a better way or until I document this process in more detail so you can do it yourself.

# Image Generation Model Settings

Every model has its own settings that it works well with. You can look up their recommended settings from model cards on HuggingFace or somewhere else.

## Juggernaut X Settings

### Recommended Settings Normal Version (VAE is baked in):

Res: 832*1216 (For Portrait, but any SDXL Res will work fine)

Sampler: DPM++ 2M Karras

Steps: 30-40

CFG: 3-7 (less is a bit more realistic)

HiRes: 4xNMKD-Siax_200k with 15 Steps and 0.3 Denoise + 1.5 Upscale

### Recommended Setting Hyper Version (VAE is baked in):

Res: 832*1216 (Any SDXL Res will work fine)

Sampler: DPM++ SDE Karras

Steps: 4-6

CFG: 1-2 (recommend 2 for a bit negative prompt affection)
Negative: Only working slightly on CFG 2

HiRes: 4xNMKD-Siax_200k with 3 Steps and 0.35 Denoise + 1.5 Upscale

# ToDo

- Customize UI of Automatic1111's **stable-diffusion-webui**
- Add packages for prompt generation and Jotform API calls

# Disclaimer
This repo was based on [AbdBarho's sd webui docker repo](https://github.com/AbdBarho/stable-diffusion-webui-docker). I just customized it and will continue to customize.
The license specified in the [original repo's license](https://github.com/AbdBarho/stable-diffusion-webui-docker/blob/master/LICENSE) (and any other license specified in the original repo) applies here as well.