"""Original Arcadia models. Run: blender --background --python build_arcadia_assets.py.

Blender coordinates: Z up, front -Y. FBX exports use Unity's Y-up convention.
No external assets, textures, or add-ons. All generated geometry is project-owned.
"""
import bpy
import math
import random
import sys
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / 'Arcadia/Assets/Arcadia/Art'
OUT.mkdir(parents=True, exist_ok=True)
random.seed(184)
# Generated sources are reproducible; keep the repository free of .blend1 backups.
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)


def material(name, color, metallic=0, roughness=.4, emission=0):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metallic
    p.inputs['Roughness'].default_value=roughness
    if emission:
        p.inputs['Emission Color'].default_value=(*color,1)
        p.inputs['Emission Strength'].default_value=emission
    return m

ivory=material('Auri_Ceramic',(.78,.83,.76),.16,.31)
brass=material('Auri_Brass',(.55,.30,.105),.74,.31)
dark=material('Auri_Joint',(.033,.073,.075),.48,.38)
cyan=material('Auri_Light',(.07,.82,.70),.15,.2,2.1)
glass=material('Auri_Visor',(.008,.045,.06),.7,.2)
stone=material('Ruin_Limestone',(.55,.59,.46),.05,.88)
stone_light=material('Ruin_Edge',(.69,.69,.52),.05,.78)
moss=material('Ruin_Moss',(.13,.25,.12),0,.95)
leaf=material('Garden_Leaf',(.12,.34,.18),0,.72)
leaf_light=material('Garden_LeafLight',(.25,.49,.22),0,.7)


def empty(name, location=(0,0,0), parent=None):
    o=bpy.data.objects.new(name,None)
    bpy.context.collection.objects.link(o)
    o.location=location
    if parent:
        o.parent=parent
    return o


def finish(o,name,mat,parent=None):
    o.name=name
    o.data.materials.append(mat)
    if parent:
        world=o.matrix_world.copy()
        o.parent=parent
        o.matrix_world=world
    return o


def box(name,loc,scale,mat,bevel=.025,parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object
    o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        m=o.modifiers.new('Soft cast edges','BEVEL'); m.width=bevel; m.segments=3
        bpy.context.view_layer.objects.active=o
        bpy.ops.object.modifier_apply(modifier=m.name)
    for p in o.data.polygons: p.use_smooth=False
    return finish(o,name,mat,parent)


def sphere(name,loc,scale,mat,parent=None,segments=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=12,radius=1,location=loc)
    o=bpy.context.object; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for p in o.data.polygons:p.use_smooth=True
    return finish(o,name,mat,parent)


def cylinder(name,loc,radius,depth,mat,parent=None,rot=(0,0,0),vertices=20):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc,rotation=rot)
    o=bpy.context.object
    m=o.modifiers.new('Rounded rim','BEVEL');m.width=min(.009,radius*.18);m.segments=2
    bpy.ops.object.modifier_apply(modifier=m.name)
    return finish(o,name,mat,parent)


def rod(name,start,end,radius,mat,parent=None):
    a=Vector(start);b=Vector(end);d=b-a
    o=cylinder(name,(a+b)/2,radius,d.length,mat,parent)
    o.rotation_euler=d.to_track_quat('Z','Y').to_euler()
    return o


def torus(name,loc,major,minor,mat,parent=None,rot=(0,0,0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=24,minor_segments=8,location=loc,rotation=rot)
    return finish(bpy.context.object,name,mat,parent)


def all_children(root):
    result=[root]
    for c in root.children:result.extend(all_children(c))
    return result


def export(root,name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in all_children(root):o.select_set(True)
    bpy.context.view_layer.objects.active=root
    bpy.ops.export_scene.fbx(filepath=str(OUT/name),use_selection=True,
        object_types={'EMPTY','MESH'},axis_forward='-Z',axis_up='Y',
        apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',
        # Keep axis conversion on the root transform. Baking it into meshes while
        # retaining EMPTY articulation pivots distorts this mechanical hierarchy
        # in Unity (upright pivot locations, sideways mesh vertices).
        bake_space_transform=False,add_leaf_bones=False,bake_anim=False,
        mesh_smooth_type='FACE',path_mode='AUTO')


# Auri: a ceramic/brass garden surveyor, with separate mechanical pivots.
auri=empty('Auri')
body=empty('BodyPivot',(0,0,.43),auri)
box('TorsoShell',(0,0,.48),(.27,.205,.27),ivory,.055,body)
box('TorsoLowerBand',(0,0,.38),(.253,.213,.052),brass,.018,body)
box('TorsoCollar',(0,0,.615),(.22,.18,.035),brass,.012,body)
cylinder('ChestHousing',(0,-.108,.505),.067,.025,brass,body,(math.pi/2,0,0))
cylinder('ChestGlass',(0,-.124,.505),.048,.012,dark,body,(math.pi/2,0,0))
cylinder('ChestCore',(0,-.134,.505),.028,.008,cyan,body,(math.pi/2,0,0))
for s in (-1,1):
    sphere('ChestRivet',(s*.092,-.104,.55),(.012,.007,.012),brass,body,12)
    box('ShoulderStripe',(s*.116,-.095,.435),(.019,.016,.065),brass,.005,body)
neck=cylinder('Neck',(0,0,.635),.049,.065,dark,body)
head=empty('HeadPivot',(0,0,.69),auri)
box('HeadShell',(0,-.007,.758),(.32,.225,.23),ivory,.065,head)
box('FaceFrame',(0,-.119,.764),(.282,.045,.144),brass,.038,head)
box('Visor',(0,-.147,.764),(.244,.028,.11),glass,.033,head)
for s in (-1,1):
    box('Eye_Left' if s<0 else 'Eye_Right',(s*.057,-.164,.768),(.039,.009,.047),cyan,.013,head)
    cylinder('EarHousing',(s*.177,0,.76),.052,.036,brass,head,(0,math.pi/2,0))
    cylinder('EarCap',(s*.197,0,.76),.032,.008,dark,head,(0,math.pi/2,0))
box('Brow',(0,-.13,.836),(.24,.035,.018),ivory,.008,head)
rod('AntennaStem',(.093,.045,.86),(.118,.044,.944),.008,brass,head)
sphere('AntennaBeacon',(.118,.044,.946),(.018,.018,.018),cyan,head,12)
box('Backpack',(0,.143,.49),(.19,.11,.21),dark,.035,body)
box('BackpackPlate',(0,.203,.49),(.145,.018,.16),brass,.012,body)
for s in (-1,1):
    cylinder('EnergyCanister',(s*.055,.21,.49),.021,.13,ivory,body)
    torus('CanisterLight',(s*.055,.21,.51),.021,.004,cyan,body)

for side,s in [('Left',-1),('Right',1)]:
    arm=empty(side+'ArmPivot',(s*.175,0,.56),auri)
    sphere(side+'Shoulder',(s*.18,0,.56),(.047,.055,.05),brass,arm)
    box(side+'UpperArm',(s*.208,0,.48),(.072,.09,.14),ivory,.022,arm)
    cylinder(side+'Elbow',(s*.214,0,.406),.034,.09,dark,arm,(math.pi/2,0,0))
    box(side+'Forearm',(s*.219,-.006,.35),(.078,.096,.095),brass,.024,arm)
    box(side+'Hand',(s*.221,-.016,.292),(.066,.075,.055),dark,.018,arm)
    for j in (-1,1):
        box(side+'Finger',(s*.221+j*.023,-.035,.27),(.015,.045,.047),ivory,.006,arm)
    leg=empty(side+'LegPivot',(s*.078,0,.355),auri)
    sphere(side+'Hip',(s*.078,0,.33),(.043,.043,.047),dark,leg)
    box(side+'Thigh',(s*.083,0,.267),(.087,.105,.12),ivory,.022,leg)
    cylinder(side+'Knee',(s*.083,-.02,.205),.034,.09,brass,leg,(math.pi/2,0,0))
    box(side+'Shin',(s*.084,0,.135),(.082,.091,.12),ivory,.022,leg)
    box(side+'ShinBand',(s*.084,-.047,.145),(.045,.009,.055),brass,.006,leg)
    sphere(side+'Ankle',(s*.084,0,.071),(.033,.036,.032),dark,leg)
    box(side+'Foot',(s*.087,-.036,.041),(.12,.19,.082),brass,.025,leg)
    box(side+'ToeCap',(s*.087,-.104,.055),(.113,.07,.052),ivory,.017,leg)
    box(side+'Sole',(s*.087,-.036,.012),(.118,.183,.024),dark,.008,leg)
export(auri,'Auri.fbx')

# Save editable character asset before staging the other modules.
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Auri.blend'))

# A three-part ruined column with inset brass emblem and moss cap.
column=empty('RuinColumn')
box('ColumnPlinth',(0,0,.12),(.72,.72,.24),stone,.045,column)
box('PlinthLip',(0,0,.265),(.63,.63,.07),stone_light,.018,column)
cylinder('ColumnShaft',(0,0,1.02),.245,1.44,stone,column,vertices=10)
for z in (.36,1.73):cylinder('ColumnBand',(0,0,z),.29,.12,stone_light,column,vertices=10)
box('ColumnCapital',(0,0,1.86),(.67,.67,.18),stone,.035,column)
box('MossCap',(0,0,1.96),(.59,.59,.035),moss,.015,column)
for x,y in [(-.25,-.23),(.21,.18)]:sphere('MossLichen',(x,y,.295),(.11,.1,.025),moss,column,12)
export(column,'RuinColumn.fbx')
column.hide_render=True
for o in all_children(column):o.hide_render=True

# Arch: width 3.2, walk opening 2.1, height 2.9. Decorative only unless assigned cells.
arch=empty('RuinArch')
for s in (-1,1):
    box('ArchFoot',(s*1.35,0,.13),(.7,.8,.26),stone,.04,arch)
    for j in range(5):
        box('ArchPier',(s*1.35,0,.45+j*.3),(.48,.52,.28),stone if j%2 else stone_light,.025,arch)
    box('ArchSpring',(s*1.35,0,1.93),(.65,.68,.18),stone_light,.025,arch)
for i in range(11):
    a=(i+.5)*math.pi/11
    o=box('ArchVoussoir',(1.35*math.cos(a),0,1.93+.85*math.sin(a)),(.38,.54,.32),stone_light if i==5 else stone,.02,arch)
    o.rotation_euler[1]=-(a-math.pi/2)
export(arch,'RuinArch.fbx')
for o in all_children(arch):o.hide_render=True

# Rock garden: clustered broken stone, designed as a boundary prop.
rocks=empty('RuinRockCluster')
for i,(x,y,z,s) in enumerate([(-.3,0,.16,.36),(.21,.1,.24,.46),(.12,-.25,.1,.22)]):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(x,y,z))
    o=bpy.context.object;o.scale=(s,s*.73,s*.64);o.rotation_euler=(.1*i,.2*i,.44*i)
    finish(o,'BrokenStone'+str(i),stone,rocks)
export(rocks,'RuinRockCluster.fbx')
for o in all_children(rocks):o.hide_render=True

# Broad-leaf fern, single mesh per frond, no transparent textures or alpha sorting.
fern=empty('GardenFern')
for i in range(9):
    angle=i*math.tau/9
    length=.32+(i%3)*.07
    d=Vector((math.cos(angle),math.sin(angle),0))
    tangent=Vector((-math.sin(angle),math.cos(angle),0))
    vertices=[];faces=[]
    for j in range(7):
        t=j/6
        center=d*(length*t)+Vector((0,0,.03+.26*math.sin(t*1.5)))
        w=.065*math.sin(math.pi*t)
        vertices.extend([center-tangent*w,center+Vector((0,0,.016*math.sin(math.pi*t))),center+tangent*w])
        if j:
            a=(j-1)*3;b=j*3
            faces.extend([(a,b,b+1,a+1),(a+1,b+1,b+2,a+2)])
    mesh=bpy.data.meshes.new('FernFrond');mesh.from_pydata(vertices,[],faces);mesh.update()
    ob=bpy.data.objects.new('FernFrond',mesh);bpy.context.collection.objects.link(ob)
    finish(ob,ob.name,leaf if i%2 else leaf_light,fern)
export(fern,'GardenFern.fbx')
for o in all_children(fern):o.hide_render=True

# Auri beauty render; these staging objects never enter the FBX.
floor=material('StudioFloor',(.06,.105,.105),.05,.9)
box('DisplayBase',(0,0,-.055),(1.12,1.12,.11),stone,.08)
cylinder('DisplayBaseGold',(0,0,-.13),.68,.06,brass,vertices=64)
box('StudioGround',(0,0,-.20),(200,200,.1),floor,0)
world=bpy.context.scene.world
world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.19,.22,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.35

def light(name,loc,power,color,size):
    bpy.ops.object.light_add(type='AREA',location=loc)
    o=bpy.context.object;o.name=name;o.data.energy=power;o.data.color=color;o.data.shape='DISK';o.data.size=size
    o.rotation_euler=(Vector((0,0,.45))-o.location).to_track_quat('-Z','Y').to_euler()
light('Warm key',(-2,-3,4),240,(1,.82,.58),3)
light('Sky fill',(3,-1,2),180,(.5,.82,1),2)
light('Golden rim',(1,2,3),350,(1,.59,.25),2)
bpy.ops.object.camera_add(location=(1.35,-2.4,1.35))
cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,.44))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO';cam.data.ortho_scale=1.65
scene=bpy.context.scene;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=48
scene.cycles.use_denoising=True
scene.render.resolution_x=1200;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
scene.render.image_settings.file_format='PNG'
scene.render.filepath=str(ROOT/'Auri-preview.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Arcadia-assets.blend'))
if '--skip-render' not in sys.argv:
    bpy.ops.render.render(write_still=True)
print('ARCADIA_ASSETS_READY',str(OUT))
