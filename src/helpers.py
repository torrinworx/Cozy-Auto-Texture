import bpy

import os
import sys
import shutil
import pathlib
import platform
import importlib
import subprocess
from collections import namedtuple


# ======== Variables ======== #
sd_version = "stable-diffusion-v1-4"
sd_url = f"https://cozy-auto-texture-sd-repo.s3.us-east-2.amazonaws.com/{sd_version}.zip"

# Paths:
current_drive = os.path.join(pathlib.Path.home().drive, os.sep)

environment_path = os.path.join(current_drive, "Cozy-Auto-Texture-Files")
venv_path = os.path.join(environment_path, "venv")
sd_path = os.path.join(environment_path, sd_version)

# Dependencies

# Declare all modules that this add-on depends on, that may need to be installed. The package and (global) name can be
# set to None, if they are equal to the module name. See import_module and ensure_and_import_module for the explanation
# of the arguments. DO NOT use this to import other parts of this Python add-on, see "Local modules" above for examples.

dependence_dict = {
        "fire": [],
        "numpy": [],
        "diffusers": [],
        "transformers": [],
        "torch==1.12.1+cu116": ["-f", "https://download.pytorch.org/whl/torch_stable.html"],
}

# Current size of final Environment folder including weights and dependencies:
# TODO: Make this number dynamic based on the total "Cozy-Auto-Texture-Files" folder size.
env_size = 7e+9  # 7GB
buffer = 1e+9  # 1GB


# ======== Helper functions ======== #

# Dependency handling:

def are_dependencies_installed():
    global dependencies_installed
    return dependencies_installed


def set_dependencies_installed(are_installed):
    global dependencies_installed
    dependencies_installed = are_installed


def import_module(module_name, global_name=None):
    """
    Import a module.
    :param module_name: Module to import.
    :param global_name: (Optional) Name under which the module is imported. If None the module_name will be used.
       This allows to import under a different name with the same effect as e.g. "import numpy as np" where "np" is
       the global_name under which the module can be accessed.
    :raises: ImportError and ModuleNotFoundError
    """
    if global_name is None:
        global_name = module_name

    if global_name in globals():
        importlib.reload(globals()[global_name])
    else:
        # Attempt to import the module and assign it to globals dictionary. This allow to access the module under
        # the given name, just like the regular import would.
        globals()[global_name] = importlib.import_module(module_name)


def install_pip():
    """
    Installs pip if not already present. Please note that ensurepip.bootstrap() also calls pip, which adds the
    environment variable PIP_REQ_TRACKER. After ensurepip.bootstrap() finishes execution, the directory doesn't exist
    anymore. However, when subprocess is used to call pip, in order to install a package, the environment variables
    still contain PIP_REQ_TRACKER with the now nonexistent path. This is a problem since pip checks if PIP_REQ_TRACKER
    is set and if it is, attempts to use it as temp directory. This would result in an error because the
    directory can't be found. Therefore, PIP_REQ_TRACKER needs to be removed from environment variables.
    :return:
    """

    try:
        # Check if pip is already installed
        subprocess.run([sys.executable, "-m", "pip", "--version"], check=True)
    except subprocess.CalledProcessError:
        import ensurepip

        ensurepip.bootstrap()
        os.environ.pop("PIP_REQ_TRACKER", None)


def install_and_import_module():
    """
    Installs the package through pip and will attempt to import modules into the Venv, or if make_global = True import
    them globally.
    :param make_global: Makes imported modules global if True, will not install imports to Venv. If false, modules will
    only be installed to the Venv to be used with the Stable Diffusion libraries.
    :raises: subprocess.CalledProcessError and ImportError

    Deprecated:
    module_name: Module to import.
    package_name: (Optional) Name of the package that needs to be installed. If None it is assumed to be equal
       to the module_name.
    global_name: (Optional) Name under which the module is imported. If None the module_name will be used.
       This allows to import under a different name with the same effect as e.g. "import numpy as np" where "np" is
       the global_name under which the module can be accessed.
    """

    # TODO: create method for importing Venv specific modules for Stable Diffusion, and method for importing modules
    #  for other Cozy Auto Textures features. This install_and_import_module() function needs to be cleaned up.

    Dependency = namedtuple("Dependency", ["module", "name", "extra_params"])
    dependencies = [Dependency(module=i, name=None, extra_params=j) for i, j in dependence_dict.items()]

    print(f"Installing dependencies: {''.join([i.module for i in dependencies])}")

    for dependency in dependencies:
        module_name = dependency.module_name
        global_name = dependency.global_name
        extra_params = dependency.extra_params
        make_global = False

        if "make_global" in extra_params:
            extra_params.remove("make_global")
            make_global = True

        if global_name is None:
            global_name = module_name

        # Blender disables the loading of user site-packages by default. However, pip will still check them to determine
        # if a dependency is already installed. This can cause problems if the packages is installed in the user
        # site-packages and pip deems the requirement satisfied, but Blender cannot import the package from the user
        # site-packages. Hence, the environment variable PYTHONNOUSERSITE is set to disallow pip from checking the user
        # site-packages. If the package is not already installed for Blender's Python interpreter, it will then try to.
        # The paths used by pip can be checked with the following:
        # `subprocess.run([bpy.app.binary_path_python, "-m", "site"], check=True)`

        # Create a copy of the environment variables and modify them for the subprocess call

        environ_copy = dict(os.environ)
        environ_copy["PYTHONNOUSERSITE"] = "1"

        # TODO: Make this section compatible with Darwin and Linux, "Scripts" should be replaced with "bin"

        install_commands_list = [
                os.path.join(venv_path, "Scripts", "python"),
                "-m",
                "pip",
                "install",
                module_name
        ]

        if extra_params:
            install_commands_list.extend(extra_params)

        subprocess.run(
                install_commands_list,
                check=True,
        )
        subprocess.run(
                [os.path.join(venv_path, "Scripts", "python"), "-m", "pip", "install", "--upgrade", module_name],
                check=True,
                env=environ_copy
        )

        # The installation succeeded, attempt to import the module again
        # import_module(module_name, global_name)


# Venv execution handler:

def execution_handler(venv_path: str, operation_function: str, user_input: dict):
    """
    In order for the Venv to work inside Blender, we must run the script as the Venv is activated
    inside the actual 'activate.bat' file that Venv generates. This means that for each interaction with Stable Diffusion
    we must input the commands into the activate.bat file, then run the file with Subprocess.

    This file controls the interactions with the activate.bat file, it opens, modifies, and runs the files depending on
    what functions are needed by Cozy Auto Texture. Each main function, when called, will activate Stable Diffusion with the
    appropriate input variables.
    """

    activate_bat_path = os.path.join(venv_path, 'Scripts', 'activate.bat')
    python_exe_path = os.path.join(venv_path, 'Scripts', 'python.exe')
    drive = pathlib.Path(activate_bat_path).drive

    sd_interface_path = os.path.join(
            bpy.utils.resource_path("LOCAL"),
            "scripts",
            "addons",
            "Cozy-Auto-Texture",
            "src",
            "sd_interface.py"
    )

    # Get args from user_input:
    args_string = " "
    for arg_name, arg_value in user_input.items():  # user_input: {param_name: param_value}
        args_string += f"""--{arg_name} "{arg_value}" """

    commands = [
            f"""{drive}""",  # Triple quotes so we can include double quotes in commands.
            f"""
            "{python_exe_path}" "{sd_interface_path}" {operation_function}{args_string} 
            """,  # NOTE: "operation_function" is the name of the function in sd_interface.py given to the command line.
    ]

    # Send commands to activate.bat
    with open(activate_bat_path, "rt") as bat_in:
        with open(activate_bat_path, "wt") as bat_out:
            for line in bat_in:
                bat_out.write(line)

            for line in commands:
                bat_out.write(f"\n{line}")

    # Run activate.bat, activate Venv:
    if platform.system() == "Windows":
        subprocess.run(activate_bat_path)
    elif platform.system() in ["Darwin", "Linux"]:
        subprocess.run(args=["source", os.path.join(venv_path, "bin", "activate")], check=True)
    else:
        raise OSError(
                "OS not supported. Cozy Auto Texture only support Darwin, Linux, and Windows operating systems."
        )


# Other:

def check_drive_space(path: str = os.getcwd()):
    """
    Checks current drive if it has enough available space to store the Environment and Stable Diffusion weights.

    returns True if enough space exists in drive, and False if installs will go over drive space.
    """

    total, used, free = shutil.disk_usage(path)

    if free > (env_size + buffer):
        return True
    else:
        return False


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