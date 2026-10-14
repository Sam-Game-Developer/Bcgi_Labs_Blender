"""Render new transparent preview assets from native 3D geometry, in isolation."""
import bpy,sys,math
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parent; sys.path.insert(0,str(root))
import bcgi_labs
from bcgi_labs import presets
bcgi_labs.register()
scene=bpy.context.scene
scene.render.engine='CYCLES'; scene.cycles.samples=16; scene.cycles.use_denoising=True
scene.render.resolution_x=192; scene.render.resolution_y=192; scene.render.resolution_percentage=100
scene.render.film_transparent=True; scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_mode='RGBA'
scene.view_settings.view_transform='AgX'
dest=root/'bcgi_labs/assets/glass'; dest.mkdir(parents=True,exist_ok=True)
for kind in bcgi_labs.shelf.EFFECTS:
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    if kind=='WAVE':
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=36,y_subdivisions=36,size=2)
    elif kind=='TWIST':
        bpy.ops.mesh.primitive_cube_add(size=1.3); o=bpy.context.object; o.scale=(.5,.5,1.4); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        mod=o.modifiers.new('Preview Subdivision','SUBSURF'); mod.subdivision_type='SIMPLE'; mod.levels=4
    else: bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=24,radius=.75)
    o=bpy.context.object
    for face in o.data.polygons: face.use_smooth=True
    mat=bcgi_labs.material('Preview Cyan',(.12,.65,.9)); o.data.materials.append(mat)
    scene.bcgi_labs.fx_preset=kind; bpy.ops.bcgi.apply_preset()
    if kind=='SCATTER':
        mod=o.modifiers[-1]
        for socket in mod.node_group.interface.items_tree:
            if socket.name=='Count': presets.set_control(mod,socket.identifier,65)
            if socket.name=='Size': presets.set_control(mod,socket.identifier,.055)
    if kind=='GLOW_RING':
        o.hide_render=True
        bpy.ops.mesh.primitive_torus_add(major_radius=.63,minor_radius=.035,major_segments=64,minor_segments=12)
        ring=bpy.context.object; ring.rotation_euler=(math.pi/2,.3,0)
        ring.data.materials.append(bcgi_labs.material('Preview Ring',(.2,.85,1),True)); o=ring
    camera=bpy.data.objects.new('Preview Camera',bpy.data.cameras.new('Preview Camera')); scene.collection.objects.link(camera)
    camera.location=(3,-5,3); camera.rotation_euler=(-camera.location).to_track_quat('-Z','Y').to_euler(); camera.data.type='ORTHO'; camera.data.ortho_scale=2.9; scene.camera=camera
    if kind=='TWIST': camera.data.ortho_scale=2.7
    for location,energy in [((1,-3,4),500),((-3,-1,2),350)]:
        light=bpy.data.objects.new('Preview Light',bpy.data.lights.new('Preview Light','AREA')); scene.collection.objects.link(light)
        light.location=location; light.rotation_euler=(-light.location).to_track_quat('-Z','Y').to_euler(); light.data.energy=energy; light.data.size=3
    scene.frame_set(12); scene.compositing_node_group=None
    scene.render.filepath=str(dest/(kind+'.png')); bpy.ops.render.render(write_still=True)
print('GLASS_PREVIEWS_PASS')
