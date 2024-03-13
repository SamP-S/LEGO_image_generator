#"/bin/zsh"
SCRIPT="setup_brick.py"
SCRIPT_DIR="${PWD}/$(dirname ${BASH_SOURCE[0]})"
SCRIPT_PATH="$SCRIPT_DIR/$SCRIPT"

blender --background --addons io_scene_importldraw --python $SCRIPT_PATH
# blender --background --addons io_scene_importldraw --python-console
