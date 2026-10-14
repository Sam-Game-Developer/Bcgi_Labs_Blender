import bpy,sys,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parent; sys.path.insert(0,str(root))
import bcgi_labs
bcgi_labs.register()
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
data=bpy.data.cameras.new('Seam_Test_Camera'); camera=bpy.data.objects.new(data.name,data); scene.collection.objects.link(camera)
camera.location=(0,-8,3); camera.rotation_euler=(Vector((0,0,1))-camera.location).to_track_quat('-Z','Y').to_euler(); scene.camera=camera
data.type='ORTHO'; data.ortho_scale=8
bpy.ops.bcgi.infinite_studio()
p=scene.bcgi_labs; p.show_brand=False; p.grid_enabled=False
scene.render.engine='CYCLES'; scene.cycles.samples=16; scene.cycles.use_denoising=False
scene.render.resolution_x=320; scene.render.resolution_y=240; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.view_settings.view_transform='Standard'
def render(name):
    path=root/name; scene.render.filepath=str(path); bpy.ops.render.render(write_still=True)
    image=bpy.data.images.load(str(path),check_existing=False)
    pixels=list(image.pixels); bpy.data.images.remove(image); return pixels
surface=next(o for o in p.studio_root.children if o.type=='MESH' and not o.get('bcgi_floor_logo'))
a=render('BCGI_Gradient_surface.png')
surface.hide_render=True
b=render('BCGI_Gradient_sky.png')
difference=max(abs(x-y) for i,(x,y) in enumerate(zip(a,b)) if i%4!=3)
print('SURFACE_SKY_MAX_DIFFERENCE',difference)
assert difference<.01,difference
surface.hide_render=False
camera.location=(4,-8,4); camera.rotation_euler=(Vector((0,0,1))-camera.location).to_track_quat('-Z','Y').to_euler(); scene.frame_set(2)
c=render('BCGI_Gradient_camera_moved.png')
changed=max(abs(x-y) for i,(x,y) in enumerate(zip(a,c)) if i%4!=3)
print('CAMERA_MOVE_MAX_DIFFERENCE',changed)
assert changed<.01,changed
result={'surface_sky_match':True,'camera_movement_gradient_match':True,'surface_sky_max_difference':difference,'camera_move_max_difference':changed}
(root/'gradient_seam_verification.json').write_text(json.dumps(result,indent=2))
