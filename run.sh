#"/bin/zsch"
SCRIPT="setup_brick.py"
SCRIPT_DIR="${PWD}/$(dirname ${BASH_SOURCE[0]})"
SCRIPT_PATH="$SCRIPT_DIR/$SCRIPT"

blender --background --python $SCRIPT_PATH
# blender --background --python-console
