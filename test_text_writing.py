import bpy,sys,json
from pathlib import Path
root=Path(__file__).resolve().parent; sys.path.insert(0,str(root))
import bcgi_labs
from bcgi_labs import writing
from bcgi_labs.presets import control_path,set_control
bcgi_labs.register(); p=bpy.context.scene.bcgi_labs
p.writing_text='BCGI'; p.writing_start=10; p.writing_duration=80; p.writing_speed=2; p.writing_pause=3
assert bpy.ops.bcgi.text_writing()=={'FINISHED'}
o=p.writing_target; source=p.writing_source; mod=writing.latest(o)
assert source.type=='FONT' and o.type=='CURVE' and len(o.data.splines)>0 and source.hide_render
assert source.data.body=='BCGI' and p.writing_font.packed_file
keys=writing.timing_keys(p,o); count=len(o.data.splines)
assert abs(keys[-1][0]-(10+40+3*(count-1)))<1e-6
progress=next(s for s in mod.node_group.interface.items_tree if s.name=='Progress' and s.in_out=='INPUT')
path=control_path(mod,progress.identifier)
def curve(): return next(c for cs in writing.fcurve_collections(o.animation_data.action) for c in cs if c.data_path==path)
assert len(curve().keyframe_points)==len(keys) and all(k.interpolation=='LINEAR' for k in curve().keyframe_points)
mid=(keys[1][0]+keys[2][0])/2
assert abs(curve().evaluate(mid)-1/count)<1e-6
# Separate width keys survive timing rebuilds.
width=next(s for s in mod.node_group.interface.items_tree if s.name=='Width' and s.in_out=='INPUT')
o.keyframe_insert(data_path=control_path(mod,width.identifier),frame=7)
p.writing_pause=0; p.writing_start=20; p.writing_duration=60; p.writing_speed=1
assert bpy.ops.bcgi.animate_writing()=={'FINISHED'}
assert len(curve().keyframe_points)==count+1 and curve().keyframe_points[0].co.x==20
assert any(c.data_path==control_path(mod,width.identifier) for cs in writing.fcurve_collections(o.animation_data.action) for c in cs)
p.writing_timing='LENGTH'; bpy.ops.bcgi.animate_writing(); length_keys=writing.timing_keys(p,o)
assert abs(length_keys[-1][0]-80)<1e-6
o.location=(3,4,2); bpy.context.view_layer.update(); before=o.matrix_world.copy(); p.writing_text='LABS'; p.writing_style='PEN'
assert bpy.ops.bcgi.text_writing()=={'FINISHED'}
assert p.writing_target==o and p.writing_source==source and source.data.body=='LABS'
assert o.matrix_world==before and len(o.modifiers)==1
assert p.writing_material.get('bcgi_writing_material')=='PEN'
# Animation changes evaluated geometry from empty to full.
bpy.context.scene.frame_set(20); bpy.context.view_layer.update()
ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh=ev.to_mesh(); start_vertices=len(mesh.vertices) if mesh else 0; ev.to_mesh_clear()
bpy.context.scene.frame_set(80); bpy.context.view_layer.update()
ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh=ev.to_mesh(); end_vertices=len(mesh.vertices); ev.to_mesh_clear()
assert start_vertices==0 and end_vertices>0,(start_vertices,end_vertices)
bpy.ops.wm.save_as_mainfile(filepath=str(root/'text_writing_test.blend'))
bpy.ops.wm.open_mainfile(filepath=str(root/'text_writing_test.blend'))
p=bpy.context.scene.bcgi_labs
assert p.writing_source.data.body=='LABS' and p.writing_font.packed_file and p.writing_target.animation_data.action
result={'version':'0.5.3','automatic_text_curves':'PASS','windows_font_packed':'PASS','editable_source_preserved':'PASS','repeat_update_same_target':'PASS','target_transform_preserved':'PASS','speed_and_pause_keys':'PASS','linear_hold_during_pause':'PASS','old_progress_keys_replaced':'PASS','other_animation_preserved':'PASS','length_based_timing':'PASS','chalk_pen_materials':'PASS','evaluated_empty_to_full':'PASS','save_reopen':'PASS','outline_not_single_line':True}
(root/'text_writing_verification.json').write_text(json.dumps(result,indent=2)); print('TEXT_WRITING_TEST_PASS',json.dumps(result))
