import bpy,sys,json
from pathlib import Path
root=Path(__file__).resolve().parent; sys.path.insert(0,str(root))
import bcgi_labs
from bcgi_labs import writing,shelf
bcgi_labs.register(); p=bpy.context.scene.bcgi_labs
bpy.ops.bcgi.sample_writing(); obj=bpy.context.object; mod=writing.latest(obj)
socket=writing.material_socket(mod)
def current(): return getattr(mod.properties.inputs,socket.identifier).value if hasattr(mod,'properties') else mod[socket.identifier]
assert p.writing_material==current() and current().get('bcgi_writing_material')=='CHALK'
custom=bpy.data.materials.new('User_Custom_Chalk'); custom.use_nodes=True
shader=next(n for n in custom.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
shader.inputs['Base Color'].default_value=(.2,.5,.3,1)
p.writing_material=custom
assert current()==custom
p.writing_color=(.9,.1,.2); p.writing_width=.04
assert current()==custom and abs(shader.inputs['Base Color'].default_value[0]-.2)<1e-6
blank=bpy.data.materials.new('No_Nodes'); p.writing_material=blank; p.writing_color=(.3,.4,.5)
assert current()==blank
p.writing_material=custom; bpy.ops.bcgi.apply_writing()
assert current()==custom and len(obj.modifiers)==1
bpy.ops.bcgi.default_writing_material()
assert current()==p.writing_material and current().get('bcgi_writing_material')=='CHALK'
p.writing_style='PEN'; bpy.ops.bcgi.apply_writing()
assert current().get('bcgi_writing_material')=='PEN'
# Bounds remain accessible when the viewport is resized.
class Region: width=900; height=650
fake=type('ShelfState',(),{})(); fake.region=Region(); fake.minimized=False; fake.fx=10000; fake.fy=-10000
fake.width=1120; fake.height=230; fake.right_width=370; fake.right_height=340; fake.maximized=False
for mode in ('TOP','BOTTOM','RIGHT','FLOAT'):
    fake.dock=mode
    x,y,w,h=shelf.BCGI_OT_shelf.bounds(fake)
    assert x>=0 and y>=0 and x+w<=fake.region.width and y+h<=fake.region.height
p.writing_material=custom
bpy.ops.wm.save_as_mainfile(filepath=str(root/'writing_material_test.blend'))
bpy.ops.wm.open_mainfile(filepath=str(root/'writing_material_test.blend'))
p=bpy.context.scene.bcgi_labs; mod=writing.latest(p.writing_target); socket=writing.material_socket(mod)
assert current().name=='User_Custom_Chalk' and p.writing_material==current()
result={'version':'0.5.2','builtin_material_picker':'PASS','custom_material_replace':'PASS','custom_shader_not_overwritten':'PASS','material_without_nodes':'PASS','repeat_apply_reuses_modifier':'PASS','builtin_reset':'PASS','style_switch':'PASS','save_reopen_material':'PASS','shelf_bounds':'PASS'}
(root/'writing_material_verification.json').write_text(json.dumps(result,indent=2)); print('WRITING_MATERIAL_TEST_PASS',json.dumps(result))
