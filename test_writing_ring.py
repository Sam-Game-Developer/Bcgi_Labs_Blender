import bpy,sys,json
from mathutils import Vector
from pathlib import Path
root=Path(__file__).resolve().parent; sys.path.insert(0,str(root))
import bcgi_labs
from bcgi_labs import writing,presets
bcgi_labs.register()
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene; p=scene.bcgi_labs
camera=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera')); scene.collection.objects.link(camera); camera.location=(0,0,7); camera.data.type='ORTHO'; camera.data.ortho_scale=3.4; scene.camera=camera
scene.world.use_nodes=True
next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND').inputs['Strength'].default_value=.15
light=bpy.data.objects.new('Key',bpy.data.lights.new('Key','AREA')); scene.collection.objects.link(light); light.location=(0,-1,5); light.data.energy=500; light.data.size=4
bpy.ops.mesh.primitive_plane_add(size=3.3)
board=bpy.context.object; board.name='Demo_Board'
material=bcgi_labs.material('Board',(.035,.16,.095)); board.data.materials.append(material)
scene.render.engine='CYCLES'; scene.cycles.samples=24; scene.cycles.use_denoising=True
scene.render.resolution_x=320; scene.render.resolution_y=320; scene.render.resolution_percentage=100
scene.view_settings.view_transform='Standard'; scene.render.image_settings.file_format='PNG'
checks={}
for style in ('CHALK','PEN'):
    p.writing_style=style; p.writing_color=(.95,.95,.95) if style=='CHALK' else (.008,.008,.008)
    p.writing_roughness=.7 if style=='CHALK' else .05; p.writing_width=.026 if style=='CHALK' else .012
    next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Base Color'].default_value=(.035,.16,.095,1) if style=='CHALK' else (.85,.82,.72,1)
    bpy.ops.bcgi.sample_writing(); stroke=bpy.context.object; stroke.location.z=.02
    source=stroke.data; count_splines=len(source.splines)
    p.writing_start=1; p.writing_duration=48; bpy.ops.bcgi.animate_writing()
    totals=[]
    for frame in (1,25,49):
        scene.frame_set(frame); scene.view_layers[0].update()
        evaluated=stroke.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh=evaluated.to_mesh()
        totals.append(len(mesh.vertices) if mesh else 0)
        evaluated.to_mesh_clear()
        if frame in (25,49):
            scene.render.filepath=str(root/('BCGI_Writing_'+style+'_'+str(frame)+'.png')); bpy.ops.render.render(write_still=True)
    print('WRITING_VERTEX_COUNTS',style,totals)
    assert totals[0]==0 and 0<totals[1]<totals[2],totals
    assert stroke.data==source and len(source.splines)==count_splines
    assert writing.latest(stroke).node_group.asset_data
    checks[style+'_write_on_animation']=True; checks[style+'_source_paths_preserved']=True
    stroke.hide_render=True
board.hide_render=True
bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=.18,depth=2.4)
pen=bpy.context.object; pen.rotation_euler=(.2,.5,0)
gold=bcgi_labs.material('Gold',(.42,.24,.04)); pen.data.materials.append(gold)
source_mesh=pen.data; original_materials=list(source_mesh.materials)
camera.location=(3,-5,2.5); camera.rotation_euler=(-camera.location).to_track_quat('-Z','Y').to_euler()
bpy.context.view_layer.update()
bpy.ops.bcgi.infinite_studio()
p.fx_preset='GLOW_RING'; bpy.ops.bcgi.apply_preset()
mod=pen.modifiers[-1]; assert source_mesh==pen.data and list(pen.data.materials)==original_materials
assert mod.node_group.asset_data
bpy.ops.bcgi.keyframe_fx()
scene.frame_set(24)
scene.render.filepath=str(root/'BCGI_Glow_Ring_preview.png'); bpy.ops.render.render(write_still=True)
checks['glow_ring_source_materials_preserved']=True; checks['glow_ring_render']=True; checks['glow_ring_keyframes']=pen.animation_data.action is not None
assert len(bcgi_labs.top_library.choices(p,bpy.context))==10
checks['top_library_ten_presets']=True
icons={x.identifier for x in bpy.types.UILayout.bl_rna.functions['label'].parameters['icon'].enum_items}
assert {'ASSET_MANAGER','CURVE_BEZCURVE'}.issubset(icons)
checks['panel_header_icons']=True
bcgi_labs.unregister(); bcgi_labs.register(); checks['registration_lifecycle']=True
(root/'writing_ring_verification.json').write_text(json.dumps(checks,indent=2)); print('PASS',json.dumps(checks))
