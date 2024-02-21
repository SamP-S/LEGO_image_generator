import bpy
import random as r
import sys
import os
import time
import csv

from math import radians, sin, cos

### Environment Variables

PWD = os.path.dirname(bpy.context.space_data.text.filepath)

COMMON_BRICKS_PATH = os.path.join(PWD, "20bricks.txt")

LDRAW_ROOT_DIR = os.path.join(PWD, "ldraw")
LDRAW_PARTS_DIR = os.path.join(LDRAW_ROOT_DIR, "parts")
DATA_DIR = os.path.join(PWD, "data")

image_resolution = (300, 300)

def get_time_ms():
    return time.time() * 1000

def get_time_s():
    return time.time()


# convert angles
def deg_to_rad(angle):
    return angle / 180 * 3.14159

def get_next_version(dir):
    folders = [folder for folder in os.listdir(dir) if os.path.isdir(os.path.join(dir, folder))]
    
    if len(folders) == 0:
        print("WARNING: no previous version found, assuming v1")
        return os.path.join(dir, "v1")
    
    highest_number = 0
    for folder in folders:
        try:
            number = int(folder[1:])  # Convert the remaining characters to an integer
            if number > highest_number:
                highest_number = number
        except ValueError:
            pass
    return os.path.join(dir, "v" + str(highest_number + 1))



### RENDERER

# Initialise 
def setup_eevee():
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    bpy.context.scene.render.resolution_x = image_resolution[0]
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



### LIGHTING

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

def setup_lights():
    MAX_LIGHTS = 3 
    MIN_STRENGTH = 500
    MAX_STRENGTH = 2000
    MIN_RADIUS = 3
    MAX_RADIUS = 10

    for l in range(r.randint(1, MAX_LIGHTS)):
        strength = r.randint(MIN_STRENGTH, MAX_STRENGTH)
        light = create_point_light((0, 0, 0), strength)
        radius = r.randint(MIN_RADIUS, MAX_RADIUS)
        angle_h = radians(360 * r.random())
        angle_v = radians(90 * r.random())
        set_position_polar_coords(light, radius, angle_h, angle_v)    



### OBJ

# open csv of brick ids
def get_parts(bricks_path):
    print("Using Bricks File:", bricks_path)
    arr = []
    with open(bricks_path) as f:
        reader = csv.reader(f)
        for row in reader:
            arr.append(row[1].strip())
    return arr

# get ldraw supported parts
def get_ldraw_parts(ldraw_dir):
    ldraw_files = os.listdir(ldraw_dir)
    file_names = [os.path.splitext(file)[0] for file in ldraw_files]
    return file_names

# compare and prints stats
def get_parts_and_check(bricks_path, ldraw_dir):
    print("Brick File:", bricks_path)
    print("LDraw Dir:", ldraw_dir)
    parts = get_parts(bricks_path)
    ldraw_parts = get_ldraw_parts(ldraw_dir)
    valid_parts = [line for idx,line in enumerate(parts) if line in ldraw_parts]
    invalid_parts = [line for idx,line in enumerate(parts) if line not in ldraw_parts]
    print(parts[:15])
    print(ldraw_parts[:15])
    print("Total parts:", len(parts))
    print("Total ldraw parts:", len(ldraw_parts))
    print("Total valid:", len(valid_parts))
    print("Total invalid:", len(invalid_parts))
    return valid_parts, invalid_parts
    

# import .dat model by part id, simple look up
# MORE HANDLING NEEDED
def import_lego_part(part_id):
    part_file = LDRAW_PARTS_DIR + "/" + str(part_id) + ".dat"
    bpy.ops.import_scene.importldraw(   filepath=part_file,
                                        filter_glob="*.dat",
                                        ldrawPath=LDRAW_ROOT_DIR,
                                        useLogoStuds=True,
                                        instanceStuds=False,
                                        importCameras=False,
                                        cameraBorderPercentage=30.0,
                                        addEnvironment=False,
                                        numberNodes=False,
                                        flatten=False,
                                        bevelEdges=True,
                                        smoothParts=True,
                                        curvedWalls=True)
    return bpy.context.selected_objects[0]

# set object's position
def set_position(obj, x, y, z):
    obj.location = (x, y, z)
# set object's rotation
def set_rotation(obj, x, y, z):
    obj.rotation_euler = (x, y, z)
# set object's scale
def set_scale(obj, x, y, z):
    obj.scale = (x, y, z)

def setup_part(part):
    # Randomize the rotation of the part
    x = r.uniform(0, 2*3.14159)
    y = r.uniform(0, 2*3.14159)
    z = r.uniform(0, 2*3.14159)
    set_rotation(part, x, y, z)



### MATERIAL

# found on http://wiki.blender.org/index.php/Dev:2.5/Py/Scripts/Cookbook/Code_snippets/Materials_and_textures
# Create new material 
def create_material(name):
    mat = bpy.data.materials.new(name)
    set_random_material_properties(mat)
    return mat

def clear_materials():
    for material in bpy.data.materials:
        material.user_clear()
        bpy.data.materials.remove(material)

# Set material properties
def set_material_properties(mat, diffuse, metallic, specular, roughness):
    mat.diffuse_color = diffuse
    mat.metallic = metallic
    mat.specular_intensity = specular
    mat.roughness = roughness
    return mat

# Set random colour/settings of material
def set_random_material_properties(mat):
    diff = (r.uniform(0.0, 1.0), r.uniform(0.0, 1.0), r.uniform(0.0, 1.0), 1.0)
    metallic = r.uniform(0.0, 1.0)
    specular = r.uniform(0.0, 1.0)
    roughness = r.uniform(0.0, 1.0)
    return set_material_properties(mat, diff, metallic, specular, roughness)

# create new dffuse material of specified r,g,b and set as object material
def set_object_material(obj, mat):
    if obj.data == None:
        for child in obj.children:
            set_object_material(child, mat)
    else:
        obj.data.materials[0] = mat



# remove all objects of type from scene
# (MESH, LIGHT, CAMERA)
def pop_by_type(type="MESH"):
    objects = bpy.context.scene.objects
    for obj in objects:
        if obj.type == type:
            bpy.data.objects.remove(obj, do_unlink=True)
            

### Cache clean up
# remove held assets
def clear_meshes():
    for mesh in bpy.data.meshes:
        mesh.user_clear()
        bpy.data.meshes.remove(mesh)
            
def clear_lights():
    for light in bpy.data.lights:
        light.user_clear()
        bpy.data.lights.remove(light)


### WALL PLANES

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

def setup_planes():
    # create planes for ambient light reflection
    PLANES = [ ((7.5, 0, 0), (0, deg_to_rad(90), 0), (15, 15, 1)),
                ((0, -7.5, 0), (deg_to_rad(90), 0, 0), (15, 15, 1)) ]
    for p in PLANES:
       create_plane(p[0], p[1], p[2])


### Main Function
       
def render_brick(brick_id, output_dir, img_per_brick):
    brick_dir = os.path.join(output_dir, str(brick_id))
    os.makedirs(brick_dir)
    time_brick_start = time.time()

    # clear objects in the scene
    pop_by_type("EMPTY")
    pop_by_type("MESH")
    pop_by_type("LIGHT")
    
    # clear all data in blender
    clear_meshes()
    clear_materials()
    clear_lights()

    # setup iteration independant scene
    print("import part:", brick_id)
    part = import_lego_part(brick_id)
    setup_planes()
    mat = create_material("new_mat")
    
    # iterate per brick
    for i in range(img_per_brick):
        # timing
        time_itr_start = time.time()

        # setup iteration dependant scene
        pop_by_type("LIGHT")
        clear_lights()
        setup_lights()
        setup_part(part)
        set_random_material_properties(mat)
        set_object_material(part, mat)
        part.select_set(state=True)
        bpy.context.view_layer.objects.active = part
        bpy.ops.view3d.camera_to_view_selected()

        # render to png
        output_path = brick_dir + "/" + brick_id + "_" + str(i) + ".png"
        render(output_path)
        print("Render ", str(brick_id) + ".dat (", i, ") [",  time.time() - time_itr_start, "]:", output_path)

    # time total for brick
    print("Finished Brick:", brick_id, "@", time.time() - time_brick_start, "s")


def run(part_ids, output_dir, img_per_brick):    
    os.makedirs(output_dir)
    time_start = get_time_s()
    
    # set renderer
    setup_eevee()
    
    time_prev = get_time_s()
    print("setup finished @ ", time_prev - time_start)
    for part_id in part_ids:
        render_brick(part_id, output_dir, img_per_brick)
        
    print("All ", len(part_ids) * img_per_brick, " images rendered @ ", get_time_s() - time_start)

if __name__ == "__main__":
    v_dir = get_next_version(DATA_DIR)
    print("Dataset Version Dir:", v_dir)
    
    valid_parts, invalid_parts = get_parts_and_check(COMMON_BRICKS_PATH, LDRAW_PARTS_DIR)
    print("Valid:", valid_parts)
    print("Invalid:", invalid_parts)

    NUM_PARTS = 10
    parts_subset = valid_parts[:NUM_PARTS]

    run(part_ids=parts_subset, output_dir=v_dir, img_per_brick=40)
