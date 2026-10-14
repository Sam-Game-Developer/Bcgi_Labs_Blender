import bpy,sys,json
from pathlib import Path
root=Path(__file__).resolve().parent; sys.path.insert(0,str(root))
import bcgi_labs
bcgi_labs.register(); p=bpy.context.scene.bcgi_labs
assert len(bcgi_labs.shelf.EFFECTS)==8 and not any(x.startswith('WRITE') for x in bcgi_labs.shelf.EFFECTS)
assert set(x.identifier for x in p.bl_rna.properties['shelf_tab'].enum_items)=={'EFFECTS','CAMERA'}
for kind in bcgi_labs.shelf.EFFECTS:
    image=bpy.data.images.load(str(root/'bcgi_labs/assets/glass'/(kind+'.png')))
    assert image.channels==4 and image.pixels[3]==0
    assert any(image.pixels[i]>.1 for i in range(3,len(image.pixels),4)),kind
p.glass_tint=(.15,.05,.2); p.card_radius=25; bpy.ops.bcgi.reset_appearance()
assert p.card_radius==14 and abs(p.glass_opacity-.86)<1e-6
bpy.ops.wm.save_as_mainfile(filepath=str(root/'glass_ui_test.blend'))
bpy.ops.wm.open_mainfile(filepath=str(root/'glass_ui_test.blend'))
assert bpy.context.scene.bcgi_labs.card_radius==14
result={'version':'0.6.0','effects_camera_only':'PASS','eight_transparent_previews':'PASS','appearance_reset':'PASS','appearance_save_reopen':'PASS','native_sidebar':'Blender theme','actual_scene_blur':'Not implemented'}
(root/'glass_ui_verification.json').write_text(json.dumps(result,indent=2)); print('GLASS_UI_TEST_PASS',json.dumps(result))
