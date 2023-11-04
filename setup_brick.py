import bpy
import random as r
import sys
import os
import time

from math import radians, sin, cos

ROOT = os.path.expandvars("$LEGO_PATH")
PWD = os.path.join(ROOT, "image_gen")
COMMON_BRICKS_PATH = os.path.join(PWD, "2000bricks.txt")

LDRAW_DIR = os.path.join(ROOT, "ldraw/parts")
OUTPUT_DIR = os.path.join(PWD, "output/v2")
BACKGROUNDS_DIR = os.path.join(PWD, "backgrounds")

PART_COUNT = 10
IMG_PER_BRICK = 200
image_resolution = (600, 600)

def get_time_ms():
    return time.time() * 1000

def get_time_s():
    return time.time()

# Reads top 2000 lego bricks set
# filters models without correspoding .dat model
# returns top 1000 or arg passed
def get_parts(num=1000):
    print("Using ", PART_COUNT, "bricks from", COMMON_BRICKS_PATH)
    with open(COMMON_BRICKS_PATH, 'r') as f:
        lines = f.readlines()
    lines = [line.strip() for line in lines]

    ldraw_files = os.listdir(LDRAW_DIR)
    file_names = [os.path.splitext(file)[0] for file in ldraw_files]

    valid_parts = [line for idx,line in enumerate(lines) if line in file_names]
    valid_parts = valid_parts[:num]

    print("Total top bricks:", klen(lines))
    print("Total ldraw:", len(ldraw_files))
    print("Total after cross check:", len(valid_parts))
    return valid_parts

# Reads top 2000 lego bricks set
# returns list of bricks without .dat models
def get_missing():
    # Open the text file and read all the lines into a list
    with open(COMMON_BRICKS_PATH, 'r') as f:
        lines = f.readlines()

    # Strip newline characters from each line in the list
    lines = [line.strip() for line in lines]

    # Create a new list with the extension removed from each file name
    file_names = [os.path.splitext(file)[0] for file in os.listdir(LDRAW_DIR)]

    # Create new list with elements in lines that are not in file_names
    missing_parts = [(idx, line) for idx,line in enumerate(lines) if line not in file_names]

    print("Total missing:", len(missing_parts))
    return missing_parts

# convert angles
def deg_to_rad(angle):
    return angle / 180 * 3.14159

# BROKEN
def setup_background():
    BACKGROUNDS_DIR = os.listdir(BACKGROUNDS_DIR)
    bg_image_file = r.choice(BACKGROUNDS_DIR)
    bg_image = bpy.data.images.load(BACKGROUNDS_DIR + "/" + bg_image_file)
    print(bg_image_file)

    bpy.context.scene.camera.data.show_background_images = True
    bg = bpy.context.scene.camera.data.background_images.new()
    bg.image = bg_image

# Initialise 
def setup_eevee():
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    bpy.context.scene.rener.resolution_x = image_resolution[0]
    bpy.context.scene.render.resolution_y = image_resolution[1]

# Initialise environment to use cycles correctly and quickly
def setup_cycles():
    # configure render settings
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.render.resolution_x = image_resolution[0]
    bpy.context.scene.render.resolution_y = image_resolution[1]
    bpy.context.scene.render.use_motion_blur = False

    # configure cycles
    bpy.context.scene.cycles.samples = 256
    bpy.context.scene.cycles.device = "GPU"
    bpy.context.scene.cycles.max_bounces = 3
    bpy.context.scene.cycles.adaptive_threshold = 0.05

# Render call image to filepath 
def render(filepath):
    bpy.context.scene.render.filepath = filepath
    bpy.ops.render.render(write_still=True)

# creates plane object at specified transform
def create_plane(pos, rot, scl):
    bpy.ops.mesh.primitive_plane_add(size=1)
    # Get a reference to the newly created plane object
    plane = bpy.context.active_object
    # Set the position, rotation, and scale of the plane
    plane.location = pos
    plane.rotation_euler = rot
    plane.scale = scl
    return plane

def create_point_light(pos, strength):
    bpy.ops.object.light_add(type="POINT", location=pos)
    light = bpy.context.object
    light.data.energy = strength            # default: 1000
    # light.data.color = (1.0, 1.0, 1.0)    # default: (1.0, 1.0, 1.0)
    # light.data.radius = 0.1               # default: 0.1
    return light


def set_position_polar_coords(obj, radius, angle_h, angle_v):
    x = radius * sin(angle_v) * cos(angle_h)
    y = radius * sin(angle_v) * sin(angle_h)
    z = radius * cos(angle_v)
    set_position(obj, x, y, z)
    # light_position = (4, 1, 5.9)
    return (x, y, z)

# import .dat model by part id, simple look up
# MORE HANDLING NEEDED
def import_lego_part(part_id):
    part_file = LDRAW_DIR + "/" + str(part_id) + ".dat"
    bpy.ops.import_scene.importldraw(   filepath=part_file,
                                        filter_glob="*.dat", 
                                        useLogoStuds=True,
                                        instanceStuds=False,
                                        importCameras=False,
                                        cameraBorderPercentage=20.0,
                                        addEnvironment=False,
                                        numberNodes=False,
                                        flatten=False,
                                        bevelEdges=True,
                                        smoothParts=True,
                                        curvedWalls=True)
    return bpy.context.selected_objects[0]

# create new dffuse material of specified r,g,b and set as object material
def set_material(obj, mat):
    if obj.data == None:
        for child in obj.children:
            set_material(child, mat)
    else:
        obj.data.materials[0] = mat

# found on http://wiki.blender.org/index.php/Dev:2.5/Py/Scripts/Cookbook/Code_snippets/Materials_and_textures
def create_material(name, diffuse, metallic, specular, roughness):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = diffuse
    mat.metallic = metallic
    mat.specular_intensity = specular
    mat.roughness = roughness
    return mat

# set object's position
def set_position(obj, x, y, z):
    obj.location = (x, y, z)
# set object's rotation
def set_rotation(obj, x, y, z):
    obj.rotation_euler = (x, y, z)
# set object's scale
def set_scale(obj, x, y, z):
    obj.scale = (x, y, z)

# remove all objects of type from scene
# (MESH, LIGHT, CAMERA)
def clear_by_type(type="MESH"):
    objects = bpy.context.scene.objects
    for obj in objects:
        if obj.type == type:
            bpy.data.objects.remove(obj, do_unlink=True)
            
def clear_lights():
    print(bpy.data.lights)

# # create new BSDF material
# def create_material():
#     # Set up a new material
#     material = bpy.data.materials.new(name="MyMaterial")time_ms
#     material.use_nodes = True

#     # Get the material's node tree
#     tree = material.node_tree

#     # Clear out the default nodes
#     for node in tree.nodes:
#         tree.nodes.remove(node)

#     # Add a new Principled BSDF node
#     bsdf_node = tree.nodes.new(type='ShaderNodeBsdfPrincipled')
#     bsdf_node.location = (0, 0)

#     # Set the color of the material
#     bsdf_node.inputs['Base Color'].default_value = (1, 0, 0, 1)

#     # Add an output node
#     output_node = tree.nodes.new(type='ShaderNodeOutputMaterial')
#     output_node.location = (400, 0)

#     # Connect the nodes
#     tree.links.new(bsdf_node.outputs['BSDF'], output_node.inputs['Surface'])

#     # Assign the material to the active object
#     bpy.context.object.active_material = material

def object_test(obj):
    print(obj.type)
    for child in obj.children:
        object_test(child)

def run(bricks_file=COMMON_BRICKS_PATH, part_count=10, output_dir=OUTPUT_DIR, img_per_brick=20):
    global OUTPUT_DIR, COMMON_BRICKS_PATH, PART_COUNT, IMAGES_PER_BRICK
    OUTPUT_DIR = output_dir
    COMMON_BRICKS_PATH = bricks_file
    IMG_PER_BRICK = img_per_brick
    PART_COUNT = part_count
    time_start = get_time_s()

    # create planes for ambient light reflection
    NUM_PLANES = 2
    positions = [(7.5, 0, 0), (0, -7.5, 0)]
    rotations = [(0, deg_to_rad(90), 0), (deg_to_rad(90), 0, 0)]
    scales = [(15, 15, 1), (15, 15, 1)]

    for i in range(NUM_PLANES):
       create_plane(positions[i], rotations[i], scales[i])
    
    parts_ids = get_parts(part_count)
    
    MAX_LIGHTS = 3 
    MIN_STRENGTH = 500
    MAX_STRENGTH = 2000
    MIN_RADIUS = 3
    MAX_RADIUS = 10
    
    time_prev = get_time_s()
    print("setup finished @ ", time_prev - time_start)
    for part_id in parts_ids:
        
        clear_by_type("MESH")
        print("import part:", part_id)
        part = import_lego_part(part_id)
        # set renderer
        setup_eevee()
        
        for material in bpy.data.materials:
            material.user_clear()
            bpy.data.materials.remove(material)
        
        for light in bpy.data.lights:
            light.user_clear()
            bpy.data.lights.remove(light)

        
        for i in range(IMG_PER_BRICK):
            
            # lighting
            clear_by_type("LIGHT")
            clear_lights()
            for l in range(r.randint(1, MAX_LIGHTS)):
                strength = r.randint(MIN_STRENGTH, MAX_STRENGTH)
                light = create_point_light((0, 0, 0), strength)
                radius = r.randint(MIN_RADIUS, MAX_RADIUS)
                angle_h = radians(360 * r.random())
                angle_v = radians(90 * r.random())
                set_position_polar_coords(light, radius, angle_h, angle_v)

            # Randomize the rotation of the part
            x = r.uniform(0, 2*3.14159)
            y = r.uniform(0, 2*3.14159)
            z = r.uniform(0, 2*3.14159)
            set_rotation(part, x, y, z)
            
            part.select_set(state=True)
            bpy.context.view_layer.objects.active = part
            bpy.ops.view3d.camera_to_view_selected()

            # Randomize the material color of the part
            diff = (r.uniform(0.0, 1.0), r.uniform(0.0, 1.0), r.uniform(0.0, 1.0), 1.0)
            metallic = r.uniform(0.0, 1.0)
            specular = r.uniform(0.0, 1.0)
            roughness = r.uniform(0.0, 1.0)
            mat = create_material("auto_mat", diff, metallic, specular, roughness)
            set_material(part, mat)

            output_path = OUTPUT_DIR + "/" + part_id + "_" + str(i) + ".png"
            print("Render ", str(part_id) + ".dat (", i, "):", output_path)
            render(output_path)
            time_tmp = get_time_s()
            print("finished render @ ", time_tmp - time_prev)
            time_prev = time_tmp
    
    print("All ", len(parts_ids) * IMG_PER_BRICK, " images rendered @ ", get_time_s() - time_start)

if __name__ == "__main__":
#    print("delete test")
#    obj = bpy.context.selected_objects[0]
#    object_test(obj)
#    
#if __name__ == "wah":
    run()
    get_parts(2000)
