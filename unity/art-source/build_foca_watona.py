"""Reproducible original Foca Watona model, inspired by the supplied seal plush.

Run with Blender: --background --factory-startup --python build_foca_watona.py
Blender Z up / front -Y; FBX Y up, axis conversion retained on imported root.
Only geometry, procedural UV color, and Blender built-ins; no downloaded assets.
"""
from pathlib import Path
import math
import sys
import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / 'Arcadia/Assets/Arcadia/Art'
OUT.mkdir(parents=True, exist_ok=True)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)


def material(name, color, rough=.4, metallic=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metallic
    return mat


def empty(name, loc=(0,0,0), parent=None):
    ob = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(ob)
    ob.location = loc
    # Blender defers empty transform evaluation; evaluate before preserving world space.
    bpy.context.view_layer.update()
    if parent:
        world = ob.matrix_world.copy()
        ob.parent = parent
        ob.matrix_world = world
        bpy.context.view_layer.update()
    return ob


def finish(ob, name, mat, parent=None):
    ob.name = name
    ob.data.materials.append(mat)
    for poly in ob.data.polygons:
        poly.use_smooth = True
    if parent:
        world = ob.matrix_world.copy()
        ob.parent = parent
        ob.matrix_world = world
    return ob


def sphere(name, loc, scale, mat, parent=None, segments=40, rings=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=loc)
    ob = bpy.context.object
    ob.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(ob, name, mat, parent)


def curve(name, points, radius, mat, parent):
    data = bpy.data.curves.new(name, 'CURVE')
    data.dimensions = '3D'
    data.resolution_u = 12
    data.bevel_depth = radius
    data.bevel_resolution = 2
    spline = data.splines.new('BEZIER')
    spline.bezier_points.add(len(points)-1)
    for point, pos in zip(spline.bezier_points, points):
        point.co = pos
        point.handle_left_type = point.handle_right_type = 'AUTO'
    ob = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.convert(target='MESH')
    return finish(bpy.context.object, name, mat, parent)


# Seamless 3D mottling sampled on spherical UVs. The belly fades to warm white.
# The continuous sphere coordinates keep the longitude seam visually invisible.
w, h = 1024, 512
u, v = np.meshgrid((np.arange(w)+.5)/w, (np.arange(h)+.5)/h)
theta = u * math.tau
phi = v * math.pi
xyz = np.stack([np.sin(phi)*np.cos(theta), np.sin(phi)*np.sin(theta), -np.cos(phi)], axis=-1)
rng = np.random.default_rng(18425)
field = np.zeros((h,w))
fine = np.zeros((h,w))
for i in range(20):
    direction = rng.normal(size=3)
    direction = direction / np.linalg.norm(direction)
    phase = rng.uniform(0, math.tau)
    frequency = rng.uniform(40, 82)
    field += np.sin(np.einsum('ijk,k->ij', xyz, direction) * frequency + phase) / math.sqrt(20)
for i in range(8):
    direction = rng.normal(size=3)
    fine += np.sin(np.einsum('ijk,k->ij', xyz, direction)*115+rng.uniform(0,math.tau)) / 8
spots = np.clip((field+fine*.3-.20)*1.4,0,1)
spots = spots*spots*(3-2*spots)
top = np.clip((xyz[:,:,2]+.35)/.9,0,1)
top = top*top*(3-2*top)
base = np.array([.81,.835,.825])[None,None,:] * (1-top[:,:,None]*.15)
ink = np.array([.29,.335,.34])[None,None,:]
amount = spots * (.18+.46*top)
colors = base*(1-amount[:,:,None])+ink*amount[:,:,None]
colors += fine[:,:,None]*.017
rgba = np.ones((h,w,4), dtype=np.float32)
rgba[:,:,:3] = np.clip(colors,0,1)
texture = bpy.data.images.new('FocaWatona_Albedo', width=w, height=h, alpha=True)
texture.pixels.foreach_set(rgba.ravel())
texture.filepath_raw = str(OUT/'FocaWatona_Albedo.png')
texture.file_format = 'PNG'
texture.save()

skin = material('FocaWatona_Skin',(.68,.72,.71),.78)
image_node = skin.node_tree.nodes.new('ShaderNodeTexImage')
image_node.image = texture
skin.node_tree.links.new(image_node.outputs['Color'],skin.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
cream = material('FocaWatona_Cream',(.82,.85,.80),.82)
eyes = material('FocaWatona_Eyes',(.008,.015,.017),.12)
nose = material('FocaWatona_Nose',(.06,.075,.073),.4)
whiskers = material('FocaWatona_Whiskers',(.54,.59,.57),.65)
lid = material('FocaWatona_Eyelids',(.18,.23,.23),.85)

root = empty('FocaWatona')
body_pivot = empty('SealBodyPivot',(0,0,.30),root)
body = sphere('PlumpSealBody',(0,0,.32),(.405,.50,.315),skin,body_pivot,64,40)
# A gently broader face, round shoulders, slightly narrower rear and soft flat belly.
for vertex in body.data.vertices:
    p = vertex.co
    p.x *= 1-.08*(p.y/.5)
    if p.z < -.26:
        p.z = -.26+(p.z+.26)*.32

# Low-relief cheeks merge into the round head. Facial features remain deliberately small.
for side in (-1,1):
    cheek = sphere('MuzzleLeft' if side<0 else 'MuzzleRight',(side*.059,-.485,.281),(.080,.040,.054),cream,body_pivot)
    eye = sphere('SleepyEyeLeft' if side<0 else 'SleepyEyeRight',(side*.145,-.449,.378),(.040,.020,.024),eyes,body_pivot)
    eye.rotation_euler.z = side*math.radians(-21)
    curve('UpperEyelidLeft' if side<0 else 'UpperEyelidRight',[
        (side*.107,-.454,.383),(side*.141,-.469,.396),(side*.177,-.451,.390)],.0036,lid,body_pivot)
    # Subtle lower crease and three whisker follicles on each soft muzzle lobe.
    curve('CheekCrease',[(side*.020,-.516,.256),(side*.059,-.524,.248),(side*.107,-.511,.268)],.0018,whiskers,body_pivot)
    for j in range(3):
        sphere('WhiskerFollicle',(side*(.072+j*.012),-.519+j*.002,.286-j*.012),(.0026,.0017,.0024),whiskers,body_pivot,12,8)
        curve('Whisker',[(side*(.075+j*.012),-.526,.282-j*.011),
                        (side*(.160+j*.010),-.530,.291-j*.019),
                        (side*(.235+j*.009),-.497,.303-j*.029)],.0012,whiskers,body_pivot)

# Rounded triangular nose, nostrils and a quiet W-shaped mouth.
nose_ob = sphere('VelvetNose',(0,-.525,.318),(.032,.020,.021),nose,body_pivot)
for vert in nose_ob.data.vertices:
    vert.co.x *= .65+.35*(vert.co.z/.021+1)/2
for side in (-1,1):
    sphere('Nostril',(side*.010,-.541,.319),(.004,.002,.0028),eyes,body_pivot,16,8)
curve('MouthPhiltrum',[(0,-.541,.308),(0,-.530,.287),(0,-.528,.274)],.0025,nose,body_pivot)
curve('QuietSmile',[(-.027,-.524,.268),(-.013,-.530,.263),(0,-.529,.274),(.013,-.530,.263),(.027,-.524,.268)],.0022,nose,body_pivot)


def flipper(name, start, end, width, thickness, parent, tail=False):
    start,end = Vector(start),Vector(end)
    direction = (end-start).normalized()
    cross = Vector((-direction.y,direction.x,0)).normalized()
    normal = direction.cross(cross).normalized()
    verts,uvs,faces = [],[],[]
    rings,sides=18,24
    for i in range(rings+1):
        t=i/rings
        center=start.lerp(end,t)
        # Rounded fan with a narrower attachment and gently lobed terminal edge.
        radius=(math.sin(math.pi*t)**.60)*width*(.65+.55*t)
        depth=math.sin(math.pi*t)**.55*thickness
        for j in range(sides):
            a=j*math.tau/sides
            verts.append(center+cross*(math.cos(a)*radius)+normal*(math.sin(a)*depth))
            uvs.append((j/sides,t))
    for i in range(rings):
        for j in range(sides):
            a=i*sides+j;b=i*sides+(j+1)%sides;c=(i+1)*sides+(j+1)%sides;d=(i+1)*sides+j
            faces.append((a,b,c,d))
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(verts,[],faces);mesh.update()
    layer=mesh.uv_layers.new(name='UVMap')
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            layer.data[li].uv=uvs[mesh.loops[li].vertex_index]
    ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob)
    finish(ob,name,skin,parent)
    for digit in (-1,0,1):
        points=[]
        for t in (.53,.67,.80,.91):
            center=start.lerp(end,t)
            offset=digit*width*.28*math.sin(math.pi*t)
            points.append(center+cross*offset+normal*(math.sin(math.pi*t)**.55*thickness+.001))
        curve(name+'SoftFold',points,.0014,whiskers,parent)
    return ob


for side,label in [(-1,'Left'),(1,'Right')]:
    pivot=empty(label+'FlipperPivot',(side*.31,-.08,.13),body_pivot)
    flipper(label+'Flipper',(side*.30,-.075,.145),(side*.60,-.24,.045),.075,.025,pivot)
tail_pivot=empty('TailPivot',(0,.40,.16),body_pivot)
sphere('TailPeduncle',(0,.46,.15),(.11,.16,.075),skin,tail_pivot)
for side,label in [(-1,'Left'),(1,'Right')]:
    flipper(label+'TailLobe',(side*.025,.48,.145),(side*.15,.76,.12),.080,.027,tail_pivot,True)


def children(ob):
    result=[ob]
    for child in ob.children:result.extend(children(child))
    return result


bpy.ops.object.select_all(action='DESELECT')
for ob in children(root):ob.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.fbx(filepath=str(OUT/'FocaWatona.fbx'),use_selection=True,
    object_types={'EMPTY','MESH'},axis_forward='-Z',axis_up='Y',
    apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',
    bake_space_transform=False,add_leaf_bones=False,bake_anim=False,
    mesh_smooth_type='FACE',path_mode='RELATIVE')

# A softly lit studio portrait. These staging objects do not enter the exported FBX.
floor = material('FocaWatona_Studio',(.065,.11,.11),.85)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,.001))
finish(bpy.context.object,'StudioFloor',floor)
world=bpy.context.scene.world
world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.24,.30,.32,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.45
def light(name,loc,power,color,size):
    bpy.ops.object.light_add(type='AREA',location=loc)
    ob=bpy.context.object;ob.name=name;ob.data.energy=power;ob.data.color=color;ob.data.shape='DISK';ob.data.size=size
    ob.rotation_euler=(Vector((0,0,.3))-ob.location).to_track_quat('-Z','Y').to_euler()
light('Warm softbox',(-2,-3,4),230,(1,.92,.82),3)
light('Sky softbox',(3,-1,2),160,(.71,.85,1),3)
light('Rim',(0,3,3),260,(.8,1,.95),2)
bpy.ops.object.camera_add(location=(1.45,-2.35,1.50))
camera=bpy.context.object
camera.rotation_euler=(Vector((0,.08,.29))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO';camera.data.ortho_scale=1.6
scene=bpy.context.scene;scene.camera=camera
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True
scene.render.resolution_x=1200;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(ROOT/'FocaWatona-preview.png')
# Pack a copy for a portable, independently editable Blender source file.
texture.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'FocaWatona.blend'))
if '--skip-render' not in sys.argv:bpy.ops.render.render(write_still=True)
print('FOCA_WATONA_READY',str(OUT/'FocaWatona.fbx'))
print('PIVOTS SealBodyPivot LeftFlipperPivot RightFlipperPivot TailPivot')
