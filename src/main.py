import os
from torch import autocast
from diffusers import StableDiffusionPipeline


def text2img(user_input):
    """
    Main function to control Blender/Stable Diffusion text to image bridge.
    :return:
    """
    model_path = r"D:\Desktop\torri\stable-diffusion-v1-4"
    device = "cuda"

    pipe = StableDiffusionPipeline.from_pretrained(model_path)
    pipe = pipe.to("cuda")

    prompt = "A Canadian flag on the back of a boat."
    with autocast("cuda"):
        image = pipe(prompt)["sample"][0]

    image_path = fr"D:\Desktop\torri\Cavelry Pendents\{prompt}.png"


    def uniquify(path):
        filename, extension = os.path.splitext(path)
        counter = 1

        while os.path.exists(path):
            path = filename + " (" + str(counter) + ")" + extension
            counter += 1

        return path

    image_path = uniquify(image_path)

    image.save(image_path)
