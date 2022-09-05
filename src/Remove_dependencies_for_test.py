import os
import sys
import subprocess

# NOTE: Removing dependencies, restarting the add-on with CTRL+R results in errors. Restart Blender after running this
# to get a clean user install experience.


def remove_dependencies(module_name_list):
    """
    Installs the package through pip and attempts to import the installed module.
    :param: module_name_list: Module to import.
    :raises: subprocess.CalledProcessError and ImportError
    """
    for module_name in module_name_list:
        # if package_name is None:
        #     package_name = module_name
        #
        # if global_name is None:
        #     global_name = module_name

        # Blender disables the loading of user site-packages by default. However, pip will still check them to determine
        # if a dependency is already installed. This can cause problems if the packages is installed in the user
        # site-packages and pip deems the requirement satisfied, but Blender cannot import the package from the user
        # site-packages. Hence, the environment variable PYTHONNOUSERSITE is set to disallow pip from checking the user
        # site-packages. If the package is not already installed for Blender's Python interpreter, it will then try to.
        # The paths used by pip can be checked with:
        # `subprocess.run([bpy.app.binary_path_python, "-m", "site"], check=True)`

        # Create a copy of the environment variables and modify them for the subprocess call
        environ_copy = dict(os.environ)
        environ_copy["PYTHONNOUSERSITE"] = "1"

        print(f"PACKAGE TO UNINSTALL: {module_name}")
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", module_name], check=True, env=environ_copy)


remove_dependencies(
    [
        "diffusers",
        "gdown",
        "torch"
    ]
)
