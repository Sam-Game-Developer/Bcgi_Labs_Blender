import bpy,sys,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parent; sys.path.insert(0,str(root))
import bcgi_labs
bcgi_labs.register()
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_cube_add(location=(202,38,1)); obj=bpy.context.object
camera=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera')); bpy.context.scene.collection.objects.link(camera); camera.location=(202,30,5); bpy.context.scene.camera=camera
rig=bpy.data.objects.new('Camera Rig',None); bpy.context.scene.collection.objects.link(rig); camera.parent=rig
light=bpy.data.objects.new('Key',bpy.data.lights.new('Key','AREA')); bpy.context.scene.collection.objects.link(light); light.location=(206,32,6)
bpy.context.view_layer.update(); bpy.ops.bcgi.infinite_studio()
studio=bpy.context.scene.bcgi_labs.studio_root
bpy.context.view_layer.update()
relative=camera.matrix_world.translation-obj.matrix_world.translation
light_relative=light.matrix_world.translation-obj.matrix_world.translation
bg_relative=studio.matrix_world.translation-camera.matrix_world.translation
bpy.ops.bcgi.center_scene()
assert obj.matrix_world.translation.xy.length<1e-4
assert (camera.matrix_world.translation-obj.matrix_world.translation-relative).length<1e-4
assert (light.matrix_world.translation-obj.matrix_world.translation-light_relative).length<1e-4
assert (studio.matrix_world.translation-camera.matrix_world.translation-bg_relative).length<1e-4
assert camera.parent==rig
count=len(bpy.context.scene.objects); bpy.ops.bcgi.center_scene(); assert len(bpy.context.scene.objects)==count
result={'whole_scene_center':True,'camera_relative_layout':True,'light_relative_layout':True,'background_relative_layout':True,'camera_rig_preserved':True,'repeat_no_duplicate_roots':True}
(root/'scene_center_verification.json').write_text(json.dumps(result,indent=2)); print('PASS',json.dumps(result))
