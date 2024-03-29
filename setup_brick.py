import bpy
import random as r
import sys
import os
from time import time
import csv
import configparser
from math import radians, sin, cos, pi

renderer = bpy.data.scenes["Scene"].render.engine

# convert angles
def deg_to_rad(angle):
    return angle / 180 * pi

def get_next_version(dir):
    if not os.path.exists(dir):
        os.mkdir(dir)
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
    output_dir = os.path.join(dir, "v" + str(highest_number + 1))
    print(f"Output Directory: {output_dir}")
    return output_dir

def str_to_int_tuple(s):
    return tuple(map(int, s.split(',')))

def str_to_float_tuple(s):
    return tuple(map(float, s.split(',')))


### RENDERER

def setup_renderer():
    if CFG["RENDER"]["renderer"] == "cycles":
        setup_cycles()
    else:
        setup_eevee()
    res = str_to_int_tuple(CFG["RENDER"]["resolution"])
    
    bpy.context.scene.render.resolution_x = res[0]
    bpy.context.scene.render.resolution_y = res[1]
    
    # set black background
    bg = str_to_float_tuple(CFG["RENDER"]["background"])
    bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = bg

def setup_eevee():
    print("Renderer: EEVEE")
    bpy.context.scene.render.engine = "BLENDER_EEVEE"
    
def setup_cycles():
    print("Renderer: CYCLES")
    bpy.context.scene.render.engine = "CYCLES"
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
    global CFG
    MIN_LIGHTS = int(CFG["LIGHTING"]["num_min"])
    MAX_LIGHTS = int(CFG["LIGHTING"]["num_max"])
    MIN_STRENGTH = int(CFG["LIGHTING"]["strength_min"])
    MAX_STRENGTH = int(CFG["LIGHTING"]["strength_max"])
    MIN_RADIUS = int(CFG["LIGHTING"]["radius_min"])
    MAX_RADIUS = int(CFG["LIGHTING"]["radius_max"])

    for l in range(r.randint(MIN_LIGHTS, MAX_LIGHTS)):
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
    arr = [3001]
    try:
        with open(bricks_path) as f:
            arr = [l.strip() for l in f]
    except Exception as e:
        print(f"ERROR: Could not open @ {bricks_path}")
        print(e)
    return arr

# get ldraw supported parts
def get_ldraw_parts(ldraw_dir):
    ldraw_parts_dir = os.path.join(ldraw_dir, "parts")
    ldraw_files = os.listdir(ldraw_parts_dir)
    file_names = [os.path.splitext(file)[0] for file in ldraw_files]
    return file_names 

# import .dat model by part id, simple look up
# MORE HANDLING NEEDED
def import_lego_part(part_id):
    global CFG
    part_file = os.path.join(CFG["PATHS"]["ldraw"], "parts", str(part_id) + ".dat")
    bpy.ops.import_scene.importldraw(  
        filepath=part_file,
        filter_glob="*.dat",
        ldrawPath=CFG["PATHS"]["ldraw"],
        useLogoStuds=True,
        instanceStuds=False,
        importCameras=False,
        cameraBorderPercentage=30.0,
        addEnvironment=False,
        numberNodes=False,
        flatten=False,
        bevelEdges=True,
        smoothParts=True,
        curvedWalls=True
    )
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

# Randomize the rotation of the part
def setup_part_random(part):   
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
    diffuse_min = str_to_float_tuple(CFG["GENERAL"]["diffuse_min"])
    diffuse_max = str_to_float_tuple(CFG["GENERAL"]["diffuse_max"])
    diffuse = (
        r.uniform(diffuse_min[0], diffuse_max[0]),
        r.uniform(diffuse_min[1], diffuse_max[1]),
        r.uniform(diffuse_min[2], diffuse_max[2]),
        1.0
    )
    metallic_min = float(CFG["GENERAL"]["metallic_min"])
    metallic_max = float(CFG["GENERAL"]["metallic_max"])
    metallic = r.uniform(metallic_min, metallic_max)
    specular_min = float(CFG["GENERAL"]["specular_min"])
    specular_max = float(CFG["GENERAL"]["specular_max"])
    specular = r.uniform(specular_min, specular_max)
    roughness_min = float(CFG["GENERAL"]["roughness_min"])
    roughness_max = float(CFG["GENERAL"]["roughness_max"])
    roughness = r.uniform(roughness_min, roughness_max)
    print("material:")
    print(f"\tdiffuse = ({diffuse[0]}, {diffuse[1]}, {diffuse[2]})")
    print(f"\tmetallic = {metallic}")
    print(f"\tspecular = {specular}")
    print(f"\troughness = {roughness}")
    return set_material_properties(mat, diffuse, metallic, specular, roughness)

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
       
def render_brick(brick_id, output_dir):
    brick_dir = os.path.join(output_dir, str(brick_id))
    os.makedirs(brick_dir)
    time_brick_start = time()

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
    setup_renderer()
    setup_planes()
    mat = create_material(f"new_mat")
    
    colours_per_brick = int(CFG["GENERAL"]["colours_per_brick"])
    rotations_per_colour = int(CFG["GENERAL"]["rotations_per_colour"])
    
    # iterate each colour
    for i in range(colours_per_brick):
    
        # lighting
        pop_by_type("LIGHT")
        clear_lights()
        setup_lights()
        
        # material
        set_random_material_properties(mat)
        set_object_material(part, mat)
        
        for j in range(rotations_per_colour):
            time_itr_start = time()
            
            # rotation
            setup_part_random(part)
            
            part.select_set(state=True)
            bpy.context.view_layer.objects.active = part
            
            # camera centering
            bpy.ops.view3d.camera_to_view_selected()

            # render to png
            output_path = os.path.join(brick_dir, brick_id + "_" + str(i) + ".png")
            render(output_path)
            print("Render ", str(brick_id) + ".dat (", i, ") [",  time() - time_itr_start, "]:", output_path)
    print("Finished Brick:", brick_id, "@", time() - time_brick_start, "s")

def get_total_images():
    num_bricks = int(CFG["GENERAL"]["num_bricks"])
    colours_per_brick = int(CFG["GENERAL"]["colours_per_brick"])
    rotations_per_colour = int(CFG["GENERAL"]["rotations_per_colour"])
    return num_bricks * colours_per_brick * rotations_per_colour
    
### MAIN DRIVER CODE

def save_config(path):
    dini = configparser.ConfigParser()
    dini["PATHS"] = {
        "x": "incomplete"
    }
    with open(path, "w") as default_ini:
        dini.write(default_ini)

def load_cwd():
    global PWD
    try:
        PWD = os.path.dirname(bpy.context.space_data.text.filepath)
    except AttributeError as e:
        PWD = os.getcwd()

def load_config(path):
    global CFG
    if not os.path.exists(path):
        print(f"WARNING: Could not find config file @ {path}")
        save_config(path)
    CFG = configparser.ConfigParser()
    CFG.read(path)

def load_brickset():
    global PARTS
    ldraw_dir = CFG["PATHS"]["ldraw"]
    brickset_path = CFG["PATHS"]["brickset"]
    parts = get_parts(brickset_path)
    ldraw_parts = get_ldraw_parts(ldraw_dir)
    valid_parts = [line for idx,line in enumerate(parts) if line in ldraw_parts]
    invalid_parts = [line for idx,line in enumerate(parts) if line not in ldraw_parts]
    # use subset
    PARTS = valid_parts
    if int(CFG["GENERAL"]["use_subset"]):
        num_parts = int(CFG["GENERAL"]["num_bricks"])
        offset_parts = int(CFG["GENERAL"]["offset_bricks"])
        PARTS = valid_parts[offset_parts:num_parts+offset_parts]
    # debug
    print("Brickset File:", brickset_path)
    print("LDraw Dir:", ldraw_dir)
    print("Total parts:", len(parts))
    print("Total ldraw parts:", len(ldraw_parts))
    print("Total valid:", len(valid_parts))
    print("Total invalid:", len(invalid_parts))
    print("Invalid parts:", invalid_parts)

def load_output():
    global OUTPUT_DIR
    OUTPUT_DIR = get_next_version(CFG["PATHS"]["output"])
    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)

def run():
    global PARTS, OUTPUT_DIR
    time_start = time()
    print("setup finished @ ", time() - time_start)
    time_start = time()
    for part_id in PARTS:
        print(f"rendering: {part_id}")
        render_brick(part_id, OUTPUT_DIR)
    print(f"Using: {bpy.data.scenes['Scene'].render.engine}")
    print(f"All {get_total_images()} images rendered @ {time() - time_start}")

    
def main():
    load_cwd()
    load_config(os.path.join(PWD, "config.ini"))
    load_brickset()
    load_output()
    run()
        
if __name__ == "__main__":
    print(f"Blender {bpy.app.version_string}")
    if (3, 6, 9) == bpy.app.version:
        main()
    else:
        print("ERROR: Unsupported Blender Version, use LTS 3.6.9")
    
