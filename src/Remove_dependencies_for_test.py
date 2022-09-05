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
        # Create a copy of the environment variables and modify them for the subprocess call
        environ_copy = dict(os.environ)
        environ_copy["PYTHONNOUSERSITE"] = "1"

        print(f"PACKAGE TO UNINSTALL: {module_name}")
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", module_name], check=True, env=environ_copy)


remove_dependencies(
    [
        "diffusers",
        "transformers",
        "gdown",
        "torch"
    ]
)
