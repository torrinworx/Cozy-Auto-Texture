bl_info = {
        "name": "Cozy Auto Texture",
        "author": "Torrin Leonard, This Cozy Studio Inc.",
        "version": (0, 0, 2),
        "blender": (3, 2, 2),
        "location": "View3D > Sidebar > Cozy Auto Texture",
        "description": "A free and opensource Blender add-on that enables you to create automatic textures from simple "
                       "text prompts.",
        "support": "COMMUNITY",
        "warning": "Requires installation of dependencies",
        "doc_url": "https://github.com/torrinworx/Cozy-Auto-Texture",
        "tracker_url": "https://github.com/torrinworx/Cozy-Auto-Texture/issues",
        "category": "Development",
}

CAT_version = "v0.0.2"
LAST_UPDATED = "07:10PM, Sept 3rd, 2022"

# Blender modules:
import bpy
from bpy.props import (IntProperty, BoolProperty, CollectionProperty)


# Python modules:
import os
import sys
import shutil
import tempfile
import importlib
import subprocess
from collections import namedtuple


# Local modules:
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

# from .src import
#
# # Refresh Locals for development:
# if "bpy" in locals():
#     modules = {
#         "example": example,
#     }
#
#     for i in modules:
#         if i in locals():
#             importlib.reload(modules[i])


# ======== Helper functions ======== #

# Declare all modules that this add-on depends on, that may need to be installed. The package and (global) name can be
# set to None, if they are equal to the module name. See import_module and ensure_and_import_module for the explanation
# of the arguments. DO NOT use this to import other parts of this Python add-on, import them as usual with an
# "import" statement.
Dependency = namedtuple("Dependency", ["module", "package", "name"])
dependencies = (
    Dependency(module="torch", package=None, name=None),
    Dependency(module="diffusers", package=None, name=None),
    Dependency(module="transformers", package=None, name=None),
    Dependency(module="gdown", package=None, name=None),
)

dependencies_installed = False


def import_stable_diffusion():
    """
    Imports Stable Diffusion from the following link:
    https://drive.google.com/drive/folders/1e77rFcVUlEH7G5RhQDwtGwdUOiG0EdJc

    Currently, the weights for SD are stored on This Cozy Studio Inc.'s Google Drive, and thus the module 'gdown' is
    needed to download the large file.
    :return:
    """
    import gdown

    sd_url = "https://drive.google.com/drive/folders/1e77rFcVUlEH7G5RhQDwtGwdUOiG0EdJc"
    sd_path = os.path.join(
            bpy.utils.resource_path("LOCAL"),
            "scripts",
            "addons",
            "Cozy-Auto-Texture",
            "stable-diffusion-v1-4"
    )

    print(f"Saving to =========== {sd_path}")

    if os.path.exists(sd_path):
        shutil.rmtree(sd_path)

    gdown.download_folder(
            sd_url,
            quiet=False,
            output=sd_path,
            use_cookies=False
    )


def import_module(module_name, global_name=None, reload=True):
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


def install_and_import_module(module_name, package_name=None, global_name=None):
    """
    Installs the package through pip and attempts to import the installed module.
    :param module_name: Module to import.
    :param package_name: (Optional) Name of the package that needs to be installed. If None it is assumed to be equal
       to the module_name.
    :param global_name: (Optional) Name under which the module is imported. If None the module_name will be used.
       This allows to import under a different name with the same effect as e.g. "import numpy as np" where "np" is
       the global_name under which the module can be accessed.
    :raises: subprocess.CalledProcessError and ImportError
    """
    if package_name is None:
        package_name = module_name

    if global_name is None:
        global_name = module_name

    # Blender disables the loading of user site-packages by default. However, pip will still check them to determine
    # if a dependency is already installed. This can cause problems if the packages is installed in the user
    # site-packages and pip deems the requirement satisfied, but Blender cannot import the package from the user
    # site-packages. Hence, the environment variable PYTHONNOUSERSITE is set to disallow pip from checking the user
    # site-packages. If the package is not already installed for Blender's Python interpreter, it will then try to.
    # The paths used by pip can be checked with `subprocess.run([bpy.app.binary_path_python, "-m", "site"], check=True)`

    # Create a copy of the environment variables and modify them for the subprocess call
    environ_copy = dict(os.environ)
    environ_copy["PYTHONNOUSERSITE"] = "1"

    subprocess.run([sys.executable, "-m", "pip", "install", package_name], check=True, env=environ_copy)

    # The installation succeeded, attempt to import the module again
    import_module(module_name, global_name)


# ======== User input Property Group ======== #
class CAT_PGT_Input_Properties(bpy.types.PropertyGroup):
    # Create NFT Data Panel:

    texture_name: bpy.props.StringProperty(name="Texture Name")

    texture_prompt: bpy.props.StringProperty(name="Texture Prompt")

    texture_format: bpy.props.EnumProperty(
        name="Texture Format",
        description="Select texture file format",
        items=[
            ('.png', '.png', 'Export texture as .png'),
            ('.jpg', '.jpg', 'Export texture as .jpg'),
        ]
    )

    save_path: bpy.props.StringProperty(
        name="Save Path",
        description="Save path for NFT files",
        default="/tmp\\",
        maxlen=1024,
        subtype="DIR_PATH"
    )


class CAT_PGT_Input_Properties_Pre(bpy.types.PropertyGroup):
    # Install Dependencies panel:
    venv_path: bpy.props.StringProperty(
            name="Environment Path",
            description="The save path for the needed modules and the Stable Diffusion weights. If you have already "
                        "installed Cozy Auto Texture, or you are using a different version of Blender, you can use your"
                        " old Environment Path. Regardless of the method, always initiate your Environment.",
            default="/tmp\\",
            maxlen=1024,
            subtype="DIR_PATH"
    )

    agree_to_license: bpy.props.BoolProperty(
            name="I agree",
            description="I agree to the Cozy Auto Texture License and the Hugging Face Stable Diffusion License."
    )


# ======== Operators ======== #
class CreateTextures(bpy.types.Operator):
    bl_idname = 'cat.create_textures'
    bl_label = 'Create Textures'
    bl_description = 'Creates textures with Stable Diffusion by using the Texture Description as text input.'
    bl_options = {"REGISTER", "UNDO"}

    reverse_order: BoolProperty(
        default=False,
        name="Reverse Order")

    def execute(self, context):

        class UserInput:
            texture_name = bpy.context.scene.input_tool.texture_name
            texture_prompt = bpy.context.scene.input_tool.texture_prompt
            texture_format = bpy.context.scene.input_tool.texture_format

            save_path = bpy.path.abspath(bpy.context.scene.input_tool.save_path)

        if not UserInput.save_path:
            UserInput.save_path = tempfile.gettempdir()
        if UserInput.save_path == "/tmp\\":
            UserInput.save_path = tempfile.gettempdir()

        from src.main import text2img  # Imported here to account for pre-dependency.

        text2img(UserInput)

        self.report({'INFO'}, f"Texture(s) Created!")
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


# ======== UI Panels ======== #
class CAT_PT_Main(bpy.types.Panel):
    bl_label = "Cozy Auto Texture"
    bl_idname = "CAT_PT_Main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Cozy Auto Texture'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        input_tool = scene.input_tool

        """
        The Main panel for Cozy Auto Texture.
        """

        row = layout.row()
        row.prop(input_tool, "texture_name")

        row = layout.row()
        row.prop(input_tool, "texture_prompt")

        row = layout.row()
        row.label(text="*Input text for Stable Diffusion model.")

        row = layout.row()
        row.prop(input_tool, "texture_format")

        layout.separator()

        row = layout.row()
        row.prop(input_tool, "save_path")

        layout.separator()

        layout.operator("cat.create_textures", icon='DISCLOSURE_TRI_RIGHT', text="Create Textures")

        layout.separator()


class CAT_PT_Help(bpy.types.Panel):
    bl_label = "Help"
    bl_idname = "CAT_PT_Help"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Cozy Auto Texture'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        input_tool = scene.input_tool

        row = layout.row()
        row.label(text=f"Looking for help?")

        row = layout.row()
        row.operator("wm.url_open", text="Cozy Auto Texture Documentation",
                icon='URL').url = "https://github.com/torrinworx/Cozy-Auto-Texture"

        row = layout.row()
        row.operator(
                "wm.url_open",
                text="YouTube Tutorials",
                icon='URL'
        ).url = "https://www.youtube.com/c/ThisCozyStudio"

        row = layout.row()
        row.operator("wm.url_open", text="Join Our Discord Community!",
                icon='URL').url = "https://discord.gg/UpZt5Un57t"

        row = layout.row()
        layout.label(text=f"{CAT_version}, {LAST_UPDATED}")

        layout.label(text="Installed Dependencies:")
        for dependency in dependencies:
            if dependency.name is None and hasattr(globals()[dependency.module], "__version__"):
                layout.label(text=f"{dependency.module} {globals()[dependency.module].__version__}")
            elif hasattr(globals()[dependency.name], "__version__"):
                layout.label(text=f"{dependency.module} {globals()[dependency.name].__version__}")
            else:
                layout.label(text=f"{dependency.module}")
            if os.path.exists(os.path.relpath("stable-diffusion-v1-4")):
                layout.label(text="stable-diffusion-v1-4")


# ======== Pre-Dependency Operators ======== #
class CATPRE_OT_install_dependencies(bpy.types.Operator):
    bl_idname = "cat.install_dependencies"
    bl_label = "Install dependencies"
    bl_description = (
            "Downloads and installs the required python packages for this add-on. "
            "Internet connection is required. Blender may have to be started with "
            "elevated permissions in order to install the package."
    )
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(self, context):
        # Deactivate when dependencies have been installed
        return not dependencies_installed

    def execute(self, context):
        # Importing dependencies
        try:
            install_pip()
            for dependency in dependencies:
                install_and_import_module(module_name=dependency.module,
                                          package_name=dependency.package,
                                          global_name=dependency.name)
        except (subprocess.CalledProcessError, ImportError) as err:
            self.report({"ERROR"}, str(err))
            return {"CANCELLED"}

        # Importing Stable Diffusion
        try:
            import_stable_diffusion()
        except Exception as err:
            self.report({"ERROR"}, str(err))
            return {"CANCELLED"}

        global dependencies_installed
        dependencies_installed = True

        # Register the panels, operators, etc. since dependencies are installed
        for cls in classes:
            bpy.utils.register_class(cls)

        bpy.types.Scene.input_tool = bpy.props.PointerProperty(type=CAT_PGT_Input_Properties)

        return {"FINISHED"}


# ======== Pre-Dependency UI Panels ======== #
class CATPRE_PT_warning_panel(bpy.types.Panel):
    bl_label = "Cozy Auto Texture Warning"
    bl_category = "Cozy Auto Texture"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    @classmethod
    def poll(self, context):
        return not dependencies_installed

    def draw(self, context):
        layout = self.layout

        lines = [f"Please install the missing dependencies for the \"{bl_info.get('name')}\" add-on.",
                 f"1. Open Edit > Preferences > Add-ons.",
                 f"2. Search for the \"{bl_info.get('name')}\" add-on.",
                 f"4. Under \"Preferences\" click on the \"{CATPRE_OT_install_dependencies.bl_label}\"",
                 f"   button. This will download and install the missing Python packages,",
                 f"   if Blender has the required permissions. If you are experiencing issues,",
                 f"   re-open Blender with Administrator privileges."
        ]
        for line in lines:
            layout.label(text=line)


class CATPRE_preferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        input_tool_pre = scene.input_tool_pre

        row = layout.row()
        row.prop(input_tool_pre, "venv_path")

        # Hugging Face and Cozy Auto Texture License agreement:

        # This line represents the character space readable in Blender's UI system:
        #         |=======================================================================|
        lines = [
                f"Please read the two following License Agreement. You must accept the terms ",
                f"of the License Agreement before continuing with the installation.",
        ]

        for line in lines:
            layout.alignment = 'CENTER'
            layout.label(text=line)

        row = layout.row()
        row.operator(
                "wm.url_open", text="Stable Diffusion License",
                icon='HELP'
        ).url = "https://huggingface.co/spaces/CompVis/stable-diffusion-license"

        row = layout.row()
        row.operator(
                "wm.url_open", text="Cozy Auto Texture License",
                icon='HELP'
        ).url = "https://github.com/torrinworx/Cozy-Auto-Texture/blob/main/LICENSE"

        row_agree_to_license = layout.row()
        row_agree_to_license.alignment = 'CENTER'
        row_agree_to_license.prop(input_tool_pre, "agree_to_license")

        layout.separator()

        row_install_dependencies_button = layout.row()
        row_install_dependencies_button.operator(CATPRE_OT_install_dependencies.bl_idname, icon="CONSOLE")

        if not bpy.context.scene.input_tool_pre.agree_to_license:
            row_install_dependencies_button.enabled = False
        else:
            row_install_dependencies_button.enabled = True

        if dependencies_installed and bpy.context.scene.input_tool_pre.agree_to_license:
            row_agree_to_license.enabled = False


# ======== Blender add-on register/unregister handling ======== #
classes = (
        # Property Group Classes:
        CAT_PGT_Input_Properties,

        # Operator Classes:
        CreateTextures,

        # Panel Classes:
        CAT_PT_Main,
        CAT_PT_Help,
)

pre_dependency_classes = (
        # Property Group Classes:
        CAT_PGT_Input_Properties_Pre,

        # Operator Classes:
        CATPRE_OT_install_dependencies,

        # Panel Classes
        CATPRE_preferences,
        CATPRE_PT_warning_panel,
)


def register():
    global dependencies_installed
    dependencies_installed = False

    for cls in pre_dependency_classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.input_tool_pre = bpy.props.PointerProperty(type=CAT_PGT_Input_Properties_Pre)

    try:
        for dependency in dependencies:
            import_module(module_name=dependency.module, global_name=dependency.name)
        dependencies_installed = True
    except ModuleNotFoundError:
        return  # Don't register other panels, operators etc.

    else:  # If modules successfully registered:
        for cls in classes:
            bpy.utils.register_class(cls)

        bpy.types.Scene.input_tool = bpy.props.PointerProperty(type=CAT_PGT_Input_Properties)


def unregister():
    for cls in pre_dependency_classes:
        bpy.utils.unregister_class(cls)

    if dependencies_installed:
        for cls in reversed(classes):
            bpy.utils.unregister_class(cls)

    del bpy.types.Scene.input_tool_pre
    del bpy.types.Scene.input_tool


if __name__ == '__main__':
    register()
