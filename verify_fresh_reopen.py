import bpy,addon_utils,json
from pathlib import Path
root=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(root/'BCGI_Fresh_File_Verified.blend'))
addon_utils.enable('bcgi_labs',default_set=False)
import bcgi_labs
p=bpy.context.scene.bcgi_labs
assert p.studio_root is not None
assert p.grid_enabled and abs(p.grid_spacing-.75)<1e-5
assert p.show_brand and p.brand_text=='FRESH FILE TEST'
assert p.brand_font is not None and p.brand_font.packed_file is not None
studio=p.studio_root; bpy.context.view_layer.update()
start=studio.matrix_world.translation.x
bpy.context.scene.camera.location.x+=1
bpy.context.scene.frame_set(3); bpy.context.view_layer.update()
assert abs(studio.matrix_world.translation.x-start-1)<1e-4
assert all(d.driver.is_valid for d in studio.animation_data.drivers)
result={'saved_file_reopen':True,'grid_settings_preserved':True,'branding_and_packed_font_preserved':True,'camera_follow_after_reopen':True}
(root/'fresh_file_reopen_verification.json').write_text(json.dumps(result,indent=2))
print('REOPEN_VERIFIED',json.dumps(result))
