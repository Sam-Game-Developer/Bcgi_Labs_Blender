import bpy, sys, json
from pathlib import Path
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root))
import bcgi_labs
bcgi_labs.register()
from bcgi_labs import camera_overlay as overlay
p=bpy.context.scene.bcgi_labs
cam=bpy.context.scene.camera
other=cam.data.background_images.new()
other.image=bpy.data.images.new('Unrelated Guide',width=16,height=16)
other.alpha=.3
assert bpy.ops.bcgi.camera_overlay()=={'FINISHED'}
slot=overlay.managed_slot(cam)
assert slot.image.packed_file and list(slot.image.size)==[1080,1920]
assert slot.display_depth=='FRONT' and slot.frame_method=='FIT'
assert bpy.ops.bcgi.camera_overlay()=={'FINISHED'}
assert len(cam.data.background_images)==2
p.overlay_opacity=.45; p.overlay_scale=.8; p.overlay_offset=(.12,-.05); p.overlay_rotation=.2
assert abs(slot.alpha-.45)<1e-6 and abs(slot.scale-.8)<1e-6
assert abs(slot.offset[0]-.12)<1e-6 and abs(slot.rotation-.2)<1e-6
p.overlay_enabled=False
assert not slot.show_background_image and other.show_background_image
assert abs(other.alpha-.3)<1e-6
p.overlay_enabled=True
assert slot.show_background_image
assert bpy.ops.bcgi.load_overlay(filepath=str(root/'bcgi_labs'/'assets'/'BCGI.png'))=={'FINISHED'}
assert slot.image==p.overlay_image and slot.image.packed_file
assert len(cam.data.background_images)==2
assert bpy.ops.bcgi.builtin_overlay()=={'FINISHED'}
assert p.overlay_image is None and slot.image.name.startswith('BCGI_Camera_Overlay')
assert len(cam.data.background_images)==2
cam.location.x+=7
assert overlay.managed_slot(cam)==slot
output=root/'overlay_fresh_file.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(output))
bpy.ops.wm.open_mainfile(filepath=str(output))
cam=bpy.context.scene.camera; slot=overlay.managed_slot(cam)
assert slot and slot.image.packed_file and list(slot.image.size)==[1080,1920]
assert len(cam.data.background_images)==2 and abs(slot.alpha-.45)<1e-6
result={'version':'0.5.1','fresh_camera':'PASS','bundled_png_packed':'PASS','repeat_apply_no_duplicates':'PASS','custom_png_replace':'PASS','builtin_reset':'PASS','controls_readback':'PASS','unrelated_guide_preserved':'PASS','save_reopen':'PASS','another_pc':'NOT_RUN','camera_overlay_final_render':'Excluded by design: native camera-view guide'}
(root/'camera_overlay_verification.json').write_text(json.dumps(result,indent=2))
print('CAMERA_OVERLAY_TEST_PASS',json.dumps(result))
