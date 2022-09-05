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
    Dependency(module="diffusers", package=None, name=None),
    Dependency(module="gdown", package=None, name=None),
    Dependency(module="torch", package=None, name=None),
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
    sd_path = os.path.realpath(os.path.join("..", "stable-diffusion-v1-4"))

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

    texture_description: bpy.props.StringProperty(name="Texture Description")

    number_o_textures: bpy.props.IntProperty(
            name="Number of Textures to Generate",
            default=1,
            min=1
    )

    save_path: bpy.props.StringProperty(
        name="Save Path",
        description="Save path for NFT files",
        default="",
        maxlen=1024,
        subtype="DIR_PATH"
    )

    test_bool: bpy.props.BoolProperty(
            name="Enable something"
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
            texture_description = bpy.context.scene.input_tool.texture_description
            number_o_textures = bpy.context.scene.input_tool.number_o_textures

            save_path = bpy.path.abspath(bpy.context.scene.input_tool.save_path)
            sd_repo_path = bpy.path.abspath(bpy.context.scene.input_tool.sd_repo_path)

            test_bool = bpy.context.scene.input_tool.text_bool

        if not UserInput.save_path:
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
        row.prop(input_tool, "texture_description")

        row = layout.row()
        row.label(text="*Input text for Stable Diffusion model.")

        row = layout.row()
        row.prop(input_tool, "number_o_textures")

        layout.separator()

        row = layout.row()
        row.prop(input_tool, "save_path")

        layout.separator()

        self.layout.operator("cat.create_textures", icon='DISCLOSURE_TRI_RIGHT', text="Create Textures")

        layout.separator()

        row = layout.row()
        row.label(text=f"Looking for help?")

        row = layout.row()
        row.operator("wm.url_open", text="Cozy Auto Texture Documentation",
                icon='URL').url = "https://github.com/torrinworx/Blend_My_NFTs"

        row = layout.row()
        row.operator(
                "wm.url_open",
                text="YouTube Tutorials",
                icon='URL'
        ).url = "https://www.youtube.com/watch?v=ygKJYz4BjRs&list=PLuVvzaanutXcYtWmPVKu2bx83EYNxLRsX"

        row = layout.row()
        row.operator("wm.url_open", text="Join Our Discord Community!",
                icon='URL').url = "https://discord.gg/UpZt5Un57t"

        row = layout.row()
        layout.label(text=f"{CAT_version}, {LAST_UPDATED}")

        for dependency in dependencies:
            if dependency.name is None and hasattr(globals()[dependency.module], "__version__"):
                layout.label(text=f"{dependency.module} {globals()[dependency.module].__version__}")
            elif hasattr(globals()[dependency.name], "__version__"):
                layout.label(text=f"{dependency.module} {globals()[dependency.name].__version__}")
            else:
                layout.label(text=f"{dependency.module}")


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

        # # Importing Stable Diffusion
        # try:
        #     import_stable_diffusion()
        # except Exception as err:
        #     self.report({"ERROR"}, str(err))
        #     return {"CANCELLED"}

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
                 f"   re-open Blender with Administrator privileges.",
                 f"",
                 f"   If you're attempting to run the add-on from the text editor, ",
                 f"   you won't see the options described above. Please install the ",
                 f"   add-on properly through the preferences.",
                 f"",
                 f"1. Open the add-on preferences (Edit > Preferences > Add-ons).",
                 f"2. Press the \"Install\" button.",
                 f"3. Search for the add-on file.",
                 f"4. Confirm the selection by pressing the \"Install Add-on\" button in the file browser."]

        for line in lines:
            layout.label(text=line)


class CATPRE_preferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    def draw(self, context):
        layout = self.layout
        layout.operator(CATPRE_OT_install_dependencies.bl_idname, icon="CONSOLE")


# ======== Blender add-on register/unregister handling ======== #
classes = (
        # Property Group Classes:
        CAT_PGT_Input_Properties,

        # Operator Classes:
        CreateTextures,

        # Panel Classes:
        CAT_PT_Main,
)

pre_dependency_classes = (
        CATPRE_PT_warning_panel,
        CATPRE_OT_install_dependencies,
        CATPRE_preferences
)


def register():
    global dependencies_installed
    dependencies_installed = False

    for cls in pre_dependency_classes:
        bpy.utils.register_class(cls)

    try:
        for dependency in dependencies:
            import_module(module_name=dependency.module, global_name=dependency.name)
        dependencies_installed = True

    except ModuleNotFoundError:
        # Don't register other panels, operators etc.
        return

    for cls in classes:
        bpy.utils.register_class(cls)

    if dependencies_installed:
        bpy.types.Scene.input_tool = bpy.props.PointerProperty(type=CAT_PGT_Input_Properties)


def unregister():
    for cls in pre_dependency_classes:
        bpy.utils.unregister_class(cls)

    if dependencies_installed:
        for cls in reversed(classes):
            bpy.utils.unregister_class(cls)

    del bpy.types.Scene.input_tool


if __name__ == '__main__':
    register()
