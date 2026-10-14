import bpy,sys,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parent; sys.path.insert(0,str(root))
import bcgi_labs
bcgi_labs.register()
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera')); scene.collection.objects.link(cam)
cam.location=(0,-8,4); cam.rotation_euler=(Vector((0,0,1))-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.type='ORTHO'; cam.data.ortho_scale=8; scene.camera=cam
scene.render.resolution_x=320; scene.render.resolution_y=240; scene.render.resolution_percentage=100
bpy.ops.bcgi.infinite_studio(); p=scene.bcgi_labs; studio=p.studio_root
mat=bpy.data.materials[studio['gradient_material']]; nodes=mat.node_tree.nodes
p.grid_enabled=True; p.grid_spacing=2; p.grid_width=.05; p.grid_opacity=.6; p.grid_glow=4
assert abs(nodes['BCGI_GridScale'].inputs[3].default_value-.5)<1e-5
assert nodes['BCGI_GridScale'].inputs[0].links[0].from_node.type=='NEW_GEOMETRY'
assert nodes['BCGI_GridGlowStrength'].inputs[1].default_value==4
for shape in ('CIRCLE','OVAL','SQUARE','ROUNDED'):
    p.glow_shape=shape
    assert nodes['BCGI_Gradient'].inputs[0].links[0].from_node.name=='BCGI_ShapeFeather'
    assert bpy.data.worlds[studio['studio_world']].node_tree.nodes['BCGI_SkyGradient'].inputs[0].links[0].from_node.name=='BCGI_SkyShapeFeather'
p.glow_feather=.8
assert abs(nodes['BCGI_ShapeFeather'].inputs['From Min'].default_value-.2)<1e-5
p.glow_x=2; p.glow_height=2; bpy.ops.bcgi.center_glow(); assert p.glow_x==0 and abs(p.glow_height-.2)<1e-5
bpy.context.view_layer.objects.active=None; bpy.ops.bcgi.center_studio()
assert (studio.matrix_world.translation.xy-cam.matrix_world.translation.xy).length<1e-4
floor=bpy.data.objects[studio['floor_object']]
p.floor_enabled=False
assert floor.hide_render and not studio.users_collection[0].hide_render
assert scene.world.name==studio['studio_world']
road_mesh=bpy.data.meshes.new('Custom_Road'); road_mesh.from_pydata([(-4,-4,0),(4,-4,0),(4,4,0),(-4,4,0)],[],[(0,1,2,3)])
road=bpy.data.objects.new('Custom_Road',road_mesh); scene.collection.objects.link(road)
before=road.matrix_world.copy(); p.floor_enabled=True; p.floor_enabled=False
assert road.matrix_world==before and not road.hide_render
p.floor_enabled=True
scene.render.engine='CYCLES'; scene.cycles.samples=16; scene.cycles.use_denoising=True
scene.render.image_settings.file_format='PNG'; scene.view_settings.view_transform='Standard'
road.hide_render=True
from bcgi_labs.presets import enable_glow
enable_glow(scene)
scene.render.filepath=str(root/'BCGI_World_Grid_Glow_preview.png'); bpy.ops.render.render(write_still=True)
p.grid_enabled=False; p.glow_shape='ROUNDED'; p.glow_roundness=.6
scene.render.filepath=str(root/'BCGI_Rounded_Feather_preview.png'); bpy.ops.render.render(write_still=True)
result={'world_aligned_grid':True,'grid_box_size':True,'grid_glow':True,'four_shapes':True,'feather':True,'center_glow':True,'center_studio':True,'independent_floor_toggle':True,'sky_stays_on':True,'custom_road_preserved':True,'rendered_previews':True}
(root/'grid_shapes_verification.json').write_text(json.dumps(result,indent=2)); print('PASS',json.dumps(result))
