"""
In order for the Venv to work inside Blender, we must run the script as the Venv is activated
inside the actual 'activate.bat' file that Venv generates. This means that for each interaction with Stable Diffusion
we must input the commands into the activate.bat file, then run the file with Subprocess.

This file controls the interactions with the activate.bat file, it opens, modifies, and runs the files depending on
what functions are needed by Cozy Auto Texture. Each main function, when called, will activate Stable Diffusion with the
appropriate input variables.
"""
import bpy

import os
import pathlib
import platform
import subprocess


def modify_execute_bat(venv_path: str, operation_function: str, user_input: dict):
    """"""
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
