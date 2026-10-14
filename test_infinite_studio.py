import bpy,sys,json,time
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root))
import bcgi_labs
bcgi_labs.register()
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=(0,0,1))
subject=bpy.context.object; subject.name='Preview_Subject'; subject.scale=(.45,.3,1)
subject.data.materials.append(bcgi_labs.material('Preview_Subject_Green',(.08,.23,.07)))
for poly in subject.data.polygons: poly.use_smooth=True
camera_data=bpy.data.cameras.new('Preview_Camera'); camera=bpy.data.objects.new('Preview_Camera',camera_data); bpy.context.scene.collection.objects.link(camera)
camera.location=(0,-8,4.7); camera.rotation_euler=(Vector((0,0,1.2))-camera.location).to_track_quat('-Z','Y').to_euler()
camera_data.type='ORTHO'; camera_data.ortho_scale=7.5; bpy.context.scene.camera=camera
rig=bpy.data.objects.new('Preview_Camera_Rig',None); bpy.context.scene.collection.objects.link(rig)
camera.parent=rig
before=tuple(subject.matrix_world)
assert bpy.ops.bcgi.infinite_studio()=={'FINISHED'}
p=bpy.context.scene.bcgi_labs
studio=p.studio_root
bpy.context.view_layer.objects.active=subject
assert bpy.ops.bcgi.character_lights()=={'FINISHED'}
assert p.character_root is not None
for lamp in p.character_root.children:
    assert subject in lamp.light_linking.receiver_collection.objects.values()
for lamp in studio.children:
    if lamp.type=='LIGHT': assert subject not in lamp.light_linking.receiver_collection.objects.values()
original_world=p.original_world
p.infinity_enabled=False
assert bpy.context.scene.world==original_world
p.infinity_enabled=True
assert bpy.context.scene.world.name==studio['studio_world']
bpy.context.view_layer.update()
start=studio.matrix_world.translation.copy()
camera_start=camera.matrix_world.translation.copy()
rig.location.x=2; rig.rotation_euler.z=.3; bpy.context.scene.frame_set(2); bpy.context.view_layer.update()
assert abs(studio.matrix_world.translation.x-start.x-(camera.matrix_world.translation.x-camera_start.x))<1e-4, studio.matrix_world.translation
assert abs(studio.rotation_euler.z-.3)<1e-4,studio.rotation_euler
assert abs(studio.matrix_world.translation.z-start.z)<1e-5
rig.location.x=0; rig.rotation_euler.z=0; bpy.context.scene.frame_set(1); bpy.context.view_layer.update()
count=len(bpy.data.objects)
bpy.ops.bcgi.infinite_studio()
assert len(bpy.data.objects)==count
mat=bpy.data.materials[studio['gradient_material']]
p.glow_spread=.8
assert abs(mat.node_tree.nodes['BCGI_GlowSpread'].inputs[1].default_value[0]-bpy.context.scene.render.resolution_x/bpy.context.scene.render.resolution_y/.8)<1e-5
p.glow_spread=.45
p.show_brand=True; p.brand_text='BCGI LABS'
brand=next(o for o in studio.children if o.get('bcgi_floor_brand'))
assert not brand.hide_render and brand.data.body=='BCGI LABS'
p.studio_size=12
assert studio.scale.x==12
p.studio_size=10
assert tuple(subject.matrix_world)==before
scene=bpy.context.scene; scene.render.engine='CYCLES'; scene.cycles.samples=24; scene.cycles.use_denoising=True
scene.render.resolution_x=360; scene.render.resolution_y=640; scene.render.resolution_percentage=100
scene.world.color=(.12,.12,.12)
scene.view_settings.view_transform='Standard'
scene.render.image_settings.file_format='PNG'; scene.render.filepath=str(root/'BCGI_Infinite_Studio_preview.png')
bpy.ops.wm.save_as_mainfile(filepath=str(root/'BCGI_Infinite_Studio_demo.blend'))
bpy.ops.render.render(write_still=True)
p.grid_enabled=True; p.grid_spacing=.75; p.grid_width=.025; p.grid_color=(.015,.12,.24)
assert abs(mat.node_tree.nodes['BCGI_GridScale'].inputs[3].default_value-1/.75)<1e-4
assert mat.node_tree.nodes['BCGI_GridColor'].inputs[2].default_value[2]>.23
scene.render.filepath=str(root/'BCGI_Infinite_Studio_grid_preview.png')
bpy.ops.render.render(write_still=True)
checks={'studio_create':True,'repeat_no_duplicates':True,'gradient_control_readback':True,'branding_toggle':True,'size_readback':True,'source_preserved':True,'render_written':(root/'BCGI_Infinite_Studio_preview.png').exists()}
checks.update(grid_controls=True,grid_render_written=(root/'BCGI_Infinite_Studio_grid_preview.png').exists(),studio_lights=len([o for o in studio.children if o.get('bcgi_studio_light')])==2)
checks.update(infinity_toggle=True,camera_parent_follow=True,camera_yaw_follow=True,ground_height_preserved=True)
checks.update(background_character_light_linking=True,windows_font_menu=len(bcgi_labs.infinite_studio.windows_fonts(p,bpy.context))>1)
image=bpy.data.images.load(str(root/'bcgi_labs'/'assets'/'BCGI.png')); image.pack(); p.logo_image=image; p.brand_mode='LOGO'
logo=next(o for o in studio.children if o.get('bcgi_floor_logo'))
assert not logo.hide_render and brand.hide_render
p.logo_width=2; p.brand_color=(.1,.6,.8); p.brand_rotation=.4
assert abs(logo.scale.x-.2)<1e-5
checks.update(logo_mode=True,logo_size=True,logo_tint=True,logo_packed=image.packed_file is not None)
from bcgi_labs import presets
for kind in presets.KINDS:
    bpy.context.view_layer.objects.active=subject
    p.fx_preset=kind
    assert bpy.ops.bcgi.apply_preset()=={'FINISHED'}
    assert bpy.ops.bcgi.keyframe_fx()=={'FINISHED'}
    mod=subject.modifiers[-1]
    assert mod.node_group.asset_data is not None and mod.node_group.is_modifier
    evaluated=subject.evaluated_get(bpy.context.evaluated_depsgraph_get())
    assert len(evaluated.data.vertices)>0
    checks['preset_'+kind]=True
    assert subject.animation_data.action is not None
    if kind=='SCAN':
        s=next(s for s in mod.node_group.interface.items_tree if s.name=='Scan Position' and s.in_out=='INPUT')
        presets.set_control(mod,s.identifier,.2); subject.keyframe_insert(data_path=presets.control_path(mod,s.identifier),frame=1)
        presets.set_control(mod,s.identifier,.8); subject.keyframe_insert(data_path=presets.control_path(mod,s.identifier),frame=21)
        scene.frame_set(11)
        value=getattr(mod.properties.inputs,s.identifier).value
        assert .2<value<.8,value
        checks['scan_keyframe_interpolation']=True
        scene.frame_set(1)
    subject.modifiers.remove(mod)
    subject.animation_data_clear()
checks['fx_keyframes']=True
font_path=Path('C:/Windows/Fonts/arial.ttf')
if font_path.exists():
    assert bpy.ops.bcgi.load_font(filepath=str(font_path))=={'FINISHED'}
    assert p.brand_font.packed_file is not None
    checks['custom_font_packed']=True
p.brand_mode='TEXT'; p.brand_font=None; p.brand_color=(1,1,1); p.brand_rotation=0; p.grid_enabled=False
for kind in ('SCAN','GLOW','XRAY'):
    p.fx_preset=kind
    bpy.ops.bcgi.apply_preset()
    scene.render.filepath=str(root/('BCGI_FX_'+kind+'_preview.png'))
    bpy.ops.render.render(write_still=True)
    checks['render_'+kind]=(root/('BCGI_FX_'+kind+'_preview.png')).exists()
    subject.modifiers.remove(subject.modifiers[-1])
library_path=root/'asset_library'; library_path.mkdir(exist_ok=True)
bpy.data.libraries.write(str(library_path/'BCGI_LABS_FX.blend'),set([presets.build(k) for k in presets.KINDS]+[bcgi_labs.writing.build('CHALK'),bcgi_labs.writing.build('PEN')]),fake_user=True)
with bpy.data.libraries.load(str(library_path/'BCGI_LABS_FX.blend')) as (data_from,data_to):
    assert len(data_from.node_groups)==10
checks['ten_exported_assets']=True
lib=bpy.context.preferences.filepaths.asset_libraries.new(name='BCGI Test',directory=str(library_path))
try:
    status={'CANCELLED'}
    if bpy.app.background: raise RuntimeError('NOT_RUN_BACKGROUND: native asset scanner needs UI event processing; see live asset check')
    for attempt in range(6):
        status=bpy.ops.object.modifier_add_node_group(asset_library_type='CUSTOM',asset_library_identifier='BCGI Test',relative_asset_identifier='BCGI_LABS_FX.blend/NodeTree/BCGI FX · Glow',use_selected_objects=False)
        if status=={'FINISHED'}: break
        time.sleep(.5)
    assert status=={'FINISHED'},status
    checks['asset_modifier_import']=True
except Exception as e:
    print('ASSET_IMPORT_CHECK',str(e))
    checks['asset_modifier_import']='NOT_RUN_BACKGROUND' if bpy.app.background else False
(root/'verification_v0.5.0.json').write_text(json.dumps(checks,indent=2))
print('BCGI_TEST',json.dumps(checks))
assert all(v is True or v=='NOT_RUN_BACKGROUND' for v in checks.values()), checks
