import os
import sys
import fire
import zipfile
import requests
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
    def import_stable_diffusion(self, sd_path, sd_url, venv_path):
        """
        Imports Stable Diffusion from the 'sd_url' as a zip file, then unzips SD.
        """

        # Download zip file
        zip_path = sd_path + ".zip"

        with open(zip_path, 'wb+') as file:
            r = requests.get(sd_url, stream=True)
            total_length = r.headers.get('content-length')

            if total_length is None:  # no content length header
                file.write(r.content)
            else:
                dl = 0
                total_length = int(total_length)
                for data in r.iter_content(chunk_size=4096):
                    dl += len(data)
                    file.write(data)
                    done = int(50 * dl / total_length)
                    sys.stdout.write("\r[%s%s]" % ('=' * done, ' ' * (50 - done)))
                    sys.stdout.flush()

        # Unzip file
        unzipped_path = os.path.join(venv_path, zipfile.ZipFile(zip_path).namelist()[0])

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(venv_path)

        os.remove(zip_path)

        print(f"Stable Diffusion downloaded, unzipped, and installed at:\n{unzipped_path}")

        return unzipped_path

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
