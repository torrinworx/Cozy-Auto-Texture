# Cozy-Auto-Texture
Create textures inside Blender just using text prompts!

The Cozy Auto Texture Blender add-on can automatically generate textures withing Blender for whatever project you are working on. All dependencies are automatically downloaded, including the Stable Diffusion weights! And the best part: you don't need to run Blender with admin privileges.

Stable Diffusion and the weights that are used (`stable-diffusion-v1-4`) are to large to store on GitHub effectively. They are downloaded from an AWS S3 bucket in a .zip file, then unzipped onto your system when you install the dependencies in the add-on settings. The Stable Diffusion weights are around 5GB in size, so the download takes a while. It's recommended that you open the Blender System Console in `Window > Toggle System Console` to display the download progress. 

Cozy Auto Texture will automatically download the wieghts and Python dependencies when you install the dependencies in `Edit > Preferences > Add-ons` by accepting the license agreements checkbox and then clicking on the `Install dependencies` button.

You can also set the path that the dependencies should be installed to. It's recommended to have at least 10GB of drive space avialable.
