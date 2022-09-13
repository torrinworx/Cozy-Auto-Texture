import os
import fire
from torch import autocast
from diffusers import StableDiffusionPipeline


# ======== Helper functions ======== #

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


# ======== Command Line ======== #
class SDInterfaceCommands(object):

    def text2img(
            self,
            texture_name: str,
            texture_prompt: str,
            save_path: str,
            texture_format: str,
            model_path: str,
            device: str
    ):
        """
        Main function to control Blender/Stable Diffusion text to image bridge.
        :return:
        """

        pipe = StableDiffusionPipeline.from_pretrained(model_path)  # Specify model path
        pipe = pipe.to(device)  # Specify render device

        with autocast(device):
            image = pipe(texture_prompt)["sample"][0]

        image_path = uniquify(os.path.join(save_path, texture_name) + texture_format)
        image.save(image_path)

        return image_path


if __name__ == '__main__':
    fire.Fire(SDInterfaceCommands)
