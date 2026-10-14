"""Verify the installed add-on in an isolated factory-startup Blender process."""
import bpy,addon_utils,json,sys
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parent
addon_utils.enable('bcgi_labs',default_set=False)
import bcgi_labs
assert '/scripts/addons/bcgi_labs/' in bcgi_labs.__file__.replace('\\','/'),bcgi_labs.__file__
assert bcgi_labs.bl_info['version']==(0,5,0)
scene=bpy.context.scene
assert scene.bcgi_labs.studio_root is None
original={o.name:o.matrix_world.copy() for o in scene.objects}
camera=scene.camera
camera.location=(0,-8,3)
camera.rotation_euler=(Vector((0,0,1))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO'; camera.data.ortho_scale=8
bpy.context.view_layer.update()
before={o.name:o.matrix_world.copy() for o in scene.objects}
assert bpy.ops.bcgi.infinite_studio()=={'FINISHED'}
p=scene.bcgi_labs; studio=p.studio_root
for name,m in before.items(): assert bpy.data.objects[name].matrix_world==m,name
mat=bpy.data.materials[studio['gradient_material']]
assert any(l.from_socket.name=='Window' and l.to_node.name=='BCGI_GlowCenter' for l in mat.node_tree.links)
assert bpy.data.worlds[studio['studio_world']].node_tree.nodes.get('BCGI_SkyGradient')
p.grid_enabled=True; p.grid_spacing=.75
assert abs(mat.node_tree.nodes['BCGI_GridScale'].inputs[3].default_value-1/.75)<1e-4
p.show_brand=True; p.brand_text='FRESH FILE TEST'
brand=next(o for o in studio.children if o.get('bcgi_floor_brand'))
assert brand.data.body=='FRESH FILE TEST' and not brand.hide_render
bpy.context.view_layer.update()
start=studio.matrix_world.translation.copy()
camera.location.x+=3; scene.frame_set(2); bpy.context.view_layer.update()
assert abs(studio.matrix_world.translation.x-start.x-3)<1e-4
world=p.original_world; p.infinity_enabled=False; assert scene.world==world
p.infinity_enabled=True
count=len(scene.objects); bpy.ops.bcgi.infinite_studio(); assert len(scene.objects)==count
scene.render.engine='CYCLES'; scene.cycles.samples=16; scene.cycles.use_denoising=True
scene.render.resolution_x=320; scene.render.resolution_y=240; scene.render.resolution_percentage=100
scene.view_settings.view_transform='Standard'; scene.render.image_settings.file_format='PNG'
scene.render.filepath=str(root/'BCGI_Fresh_File_Verified.png')
bpy.ops.render.render(write_still=True)
path=root/'BCGI_Fresh_File_Verified.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(path))
result={'installed_addon_version':list(bcgi_labs.bl_info['version']),'factory_startup_scene':True,
        'installed_addon_path':bcgi_labs.__file__,
        'fresh_studio_creation':True,'existing_objects_preserved':True,'camera_gradient_and_sky':True,
        'grid_controls':True,'text_branding':True,'camera_follow':True,'infinity_toggle':True,
        'repeat_no_duplicates':True,'render_written':(root/'BCGI_Fresh_File_Verified.png').exists(),
        'saved_fresh_file':path.exists()}
(root/'fresh_file_verification.json').write_text(json.dumps(result,indent=2))
print('FRESH_FILE_VERIFIED',json.dumps(result))
