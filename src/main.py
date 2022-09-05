import os
from torch import autocast
from diffusers import StableDiffusionPipeline

model_path = os.path.relpath(os.path.join("..", "stable-diffusion-v1-4"))


def uniquify(path):
    """
    Creates unique paths and increments file names to avoid overwriting images. Checks if paths exist, if it does,
    increments file name with a given number to ensure it doesn't get overwritten.
    :param path:
    :return:
    """
    filename, extension = os.path.splitext(path)
    counter = 1

    while os.path.exists(path):
        path = filename + " (" + str(counter) + ")" + extension
        counter += 1

    return path


def text2img(user_input):
    """
    Main function to control Blender/Stable Diffusion text to image bridge.
    :return:
    """
    save_path = user_input.save_path
    prompt = user_input.prompt
    image_format = user_input.image_name

    # TODO: allow user to specify CPU or GPU (cuda) render method for images.
    # device = user_input.device
    device = "cuda"

    pipe = StableDiffusionPipeline.from_pretrained(model_path)  # Specify model path
    pipe = pipe.to(device)  # Specify render device

    with autocast("cuda"):
        image = pipe(prompt)["sample"][0]

    image_path = uniquify(os.path.join(save_path, prompt) + image_format)  # Path to image

    image.save(image_path)
