import os

filename = os.path.expandvars("$LEGO_PATH/image_gen/setup_brick.py")
exec(compile(open(filename).read(), filename, 'exec'))

# Command-line / subprocess
# 
#     You can use subprocess to run blender (like any other application) from python.
#     Use the -b / --background switch to run blender in the backgroud (GUI-less).
#     Use the -P <filename> / --python <filename> switch to load desired python script.
#         Or use --python-console to run python from stdin.
# 
# Example: blender --background --python myscript.py
# 
# See: https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html