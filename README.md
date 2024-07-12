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

# How to add custom models

Right now adding custom models and Loras is a bit messy since I simply download model weights from wherever their weights are, upload them to my HuggingFace repo, and get the download links from there. So you kind of need to ask me to add models for the time being until I find a better way or until I document this process in more detail so you can do it yourself.

# ToDo

- Customize UI of Automatic1111's **stable-diffusion-webui**
- Add packages for prompt generation and Jotform API calls

# Disclaimer
This repo was based on [AbdBarho's sd webui docker repo](https://github.com/AbdBarho/stable-diffusion-webui-docker). I just customized it and will continue to customize.
The license specified in the [original repo's license](https://github.com/AbdBarho/stable-diffusion-webui-docker/blob/master/LICENSE) (and any other license specified in the original repo) applies here as well.