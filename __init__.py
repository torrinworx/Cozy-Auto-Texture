bl_info = {
        "name": "Cozy Auto Texture",
        "author": "Torrin Leonard, This Cozy Studio Inc.",
        "version": (0, 0, 4),
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

CAT_version = "v0.0.4"
LAST_UPDATED = "11:40PM, Sept 13rd, 2022"

# Blender modules:
import bpy


# Python modules:
import os
import sys
import asyncio
import tempfile
import importlib
import subprocess


# Local modules:
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from .src import helpers

# Refresh Locals for development:
if "bpy" in locals():
    modules = {
        "helpers": helpers,
    }

    for i in modules:
        if i in locals():
            importlib.reload(modules[i])


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

    device: bpy.props.EnumProperty(
        name="Device Type",
        description="Select render device for Stable Diffusion.",
        items=[
            ('cuda', 'Cuda (GPU)', 'Render with Cuda (GPU)'),
            ('cpu', 'CPU', 'Render with CPU'),
        ]
    )


class CAT_PGT_Input_Properties_Pre(bpy.types.PropertyGroup):
    # Install Dependencies panel:
    venv_path: bpy.props.StringProperty(
            name="Environment Path",
            description="The save path for the needed modules and the Stable Diffusion weights. If you have already "
                        "installed Cozy Auto Texture, or you are using a different version of Blender, you can use your"
                        " old Environment Path. Regardless of the method, always initiate your Environment.",
            default=f"{helpers.current_drive}",
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

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    async def sd_interaction(self, context):
        environment_path = os.path.join(bpy.context.scene.input_tool_pre.venv_path, "Cozy-Auto-Texture-Files")
        venv_path = os.path.join(environment_path, "venv")
        sd_path = os.path.join(environment_path, helpers.sd_version)

        subprocess.run(["pip", "-V"], check=True)

        user_input = {
            "texture_name": bpy.context.scene.input_tool.texture_name,
            "texture_prompt": bpy.context.scene.input_tool.texture_prompt,
            "save_path": os.path.abspath(bpy.path.abspath(bpy.context.scene.input_tool.save_path)),
            "texture_format": bpy.context.scene.input_tool.texture_format,
            "model_path": sd_path,
            "device": bpy.context.scene.input_tool.device,
        }

        if not user_input["save_path"]:
            user_input["save_path"] = tempfile.gettempdir()
        if user_input["save_path"] == "/tmp\\":
            user_input["save_path"] = tempfile.gettempdir()

        # "text2img" - name of function inside sd_interface.py file
        helpers.execution_handler(venv_path=venv_path, operation_function="text2img", user_input=user_input)

        self.report({'INFO'}, f"Texture(s) Created!")

    def execute(self, context):
        async_task = asyncio.ensure_future(self.sd_interaction(context))
        return {"FINISHED"}


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

        row = layout.row()
        row.prop(input_tool, "device")

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
        row.operator(
                "wm.url_open", text="Cozy Auto Texture Documentation",
                icon='URL'
        ).url = "https://github.com/torrinworx/Cozy-Auto-Texture"

        row = layout.row()
        row.operator(
                "wm.url_open",
                text="YouTube Tutorials",
                icon='URL'
        ).url = "https://www.youtube.com/c/ThisCozyStudio"

        row = layout.row()
        row.operator(
                "wm.url_open", text="Join Our Discord Community!",
                icon='URL'
        ).url = "https://discord.gg/UpZt5Un57t"

        row = layout.row()
        layout.label(text=f"{CAT_version}, {LAST_UPDATED}")

        # TODO: find better way to displayed installed dependencies:
        # layout.label(text="Installed Dependencies:")
        # for dependency in dependencies:
        #     if dependency.name is None and hasattr(globals()[dependency.module], "__version__"):
        #         layout.label(text=f"{dependency.module} {globals()[dependency.module].__version__}")
        #     elif hasattr(globals()[dependency.name], "__version__"):
        #         layout.label(text=f"{dependency.module} {globals()[dependency.name].__version__}")
        #     else:
        #         layout.label(text=f"{dependency.module}")
        #     if os.path.exists(os.path.relpath(sd_version)):
        #         layout.label(text=sd_version)


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
    def poll(cls, context):
        environment_path = os.path.exists(
                os.path.join(
                        bpy.context.scene.input_tool_pre.venv_path,
                        "Cozy-Auto-Texture-Files"
                )
        )
        return not environment_path

    def execute(self, context):
        # TODO: make asynchronous so that download progress is viewable from UI.
        # Paths:
        environment_path = os.path.join(bpy.context.scene.input_tool_pre.venv_path, "Cozy-Auto-Texture-Files")
        venv_path = os.path.join(environment_path, "venv")
        sd_path = os.path.join(environment_path, helpers.sd_version)

        helpers.create_path_log(path=environment_path, path_name="environment_path")

        # Install pip:
        helpers.install_pip()

        # Install Venv:
        if not os.path.exists(venv_path):
            subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
        else:
            pass
            # TODO: Upgrade Venv if venv already detected.

        # Importing dependencies
        try:
            helpers.install_and_import_module(venv_path=venv_path)

            print("Python modules installed successfully.")
        except (subprocess.CalledProcessError, ImportError) as err:
            self.report({"ERROR"}, str(err))
            return {"CANCELLED"}

        # Importing Stable Diffusion
        user_input = {
                "sd_path": sd_path,
                "sd_url": helpers.sd_url,
                "environment_path": environment_path,
        }

        try:
            helpers.execution_handler(
                    venv_path=venv_path,
                    operation_function="import_stable_diffusion",
                    user_input=user_input
            )
            print("Stable Diffusion successfully installed.")

        except Exception as err:
            self.report({"ERROR"}, str(err))
            return {"CANCELLED"}

        print("Dependencies installed successfully")

        helpers.set_dependencies_installed(True)

        for cls in classes:
            bpy.utils.register_class(cls)

        bpy.types.Scene.input_tool = bpy.props.PointerProperty(type=CAT_PGT_Input_Properties)

        return {'FINISHED'}


# ======== Pre-Dependency UI Panels ======== #
class CATPRE_PT_warning_panel(bpy.types.Panel):
    bl_label = "Cozy Auto Texture Warning"
    bl_category = "Cozy Auto Texture"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    @classmethod
    def poll(cls, context):
        environment_path = os.path.exists(
            os.path.join(
                bpy.context.scene.input_tool_pre.venv_path,
                "Cozy-Auto-Texture-Files"
            )
        )
        return not environment_path

    def draw(self, context):
        layout = self.layout

        lines = [
                f"Please install the missing dependencies for the \"{bl_info.get('name')}\" add-on.",
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
                f"Please read the two following License Agreements. You must accept the terms ",
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
    # TODO:
    #  1. Detect if dependencies are already installed when restarting add-on
    #  2. Detect if dependencies are installed when fresh installing add-on on different Blender version for example
    #  Possible solution use environ variables: os.environ['variable_name'] = 'variable_value'

    global dependencies_installed
    dependencies_installed = False

    for cls in pre_dependency_classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.input_tool_pre = bpy.props.PointerProperty(type=CAT_PGT_Input_Properties_Pre)

    if helpers.read_path_log(check_exists=True):
        # environment_path = helpers.read_path_log()["environment_path"]

        helpers.set_dependencies_installed(True)

        for cls in classes:
            bpy.utils.register_class(cls)

        bpy.types.Scene.input_tool = bpy.props.PointerProperty(type=CAT_PGT_Input_Properties)

        helpers.set_dependencies_installed(True)
        return

    helpers.set_dependencies_installed(False)
    return


def unregister():
    for cls in pre_dependency_classes:
        bpy.utils.unregister_class(cls)

    if dependencies_installed:
        for cls in reversed(classes):
            bpy.utils.unregister_class(cls)
        del bpy.types.Scene.input_tool

    del bpy.types.Scene.input_tool_pre


if __name__ == '__main__':
    register()
