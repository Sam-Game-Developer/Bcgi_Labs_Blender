bl_info = {'name': 'BCGI LABS', 'author': 'BCGI LABS', 'version': (0, 5, 3),
           'blender': (4, 2, 0), 'location': '3D View > Sidebar > BCGI LABS',
           'description': 'Studio lighting, backgrounds and procedural effects', 'category': '3D View'}

import bpy
import bpy.utils.previews
import math
import os
from mathutils import Vector
from bpy.props import EnumProperty, FloatProperty, IntProperty, PointerProperty, FloatVectorProperty, BoolProperty, StringProperty
from . import infinite_studio
from . import presets
from . import writing, top_library, camera_overlay, shelf
from bpy.types import Operator, Panel, PropertyGroup

_previews = None

def collection(label):
    c = bpy.data.collections.new('BCGI_' + label)
    c['bcgi_labs'] = True
    bpy.context.scene.collection.children.link(c)
    return c

def object_in(c, name, data):
    o = bpy.data.objects.new(name, data)
    c.objects.link(o)
    return o

def focus(context):
    o = context.active_object
    if o and o.type == 'MESH':
        corners = [o.matrix_world @ Vector(v) for v in o.bound_box]
        center = sum(corners, Vector()) / 8
        size = max((max(v[i] for v in corners) - min(v[i] for v in corners)) for i in range(3))
        return center, max(size, 0.1)
    return context.scene.cursor.location.copy(), 2.0

def material(name, color, emission=False):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    n.inputs['Base Color'].default_value = (*color, 1)
    n.inputs['Roughness'].default_value = .6
    if emission:
        n.inputs['Emission Color'].default_value = (*color, 1)
        n.inputs['Emission Strength'].default_value = 3
    return m

class BCGISettings(PropertyGroup):
    shelf_dock: EnumProperty(name='Library Placement',items=[('TOP','Top',''),('BOTTOM','Bottom',''),('RIGHT','Right',''),('FLOAT','Floating','')],default='TOP')
    shelf_x: FloatProperty(default=24)
    shelf_y: FloatProperty(default=80)
    overlay_camera: PointerProperty(name='Camera',type=bpy.types.Object,poll=camera_overlay.camera_poll)
    overlay_image: PointerProperty(name='Custom Image',type=bpy.types.Image)
    overlay_enabled: BoolProperty(name='Show Overlay',default=True,update=camera_overlay.update)
    overlay_opacity: FloatProperty(name='Opacity',default=1,min=0,max=1,update=camera_overlay.update)
    overlay_scale: FloatProperty(name='Scale',default=1,min=.01,max=20,update=camera_overlay.update)
    overlay_offset: FloatVectorProperty(name='Position',size=2,default=(0,0),update=camera_overlay.update)
    overlay_rotation: FloatProperty(name='Rotation',subtype='ANGLE',default=0,update=camera_overlay.update)
    overlay_fit: EnumProperty(name='Fit',items=[('FIT','Fit',''),('CROP','Crop',''),('STRETCH','Stretch','')],default='FIT',update=camera_overlay.update)
    top_preset: EnumProperty(name='Preset Library',items=top_library.choices)
    writing_style: EnumProperty(name='Writing Style',items=[('CHALK','Chalk',''),('PEN','Pen / Ink','')],update=writing.style_changed)
    writing_target: PointerProperty(type=bpy.types.Object,update=writing.target_changed)
    writing_material: PointerProperty(name='Stroke Material',type=bpy.types.Material,update=writing.material_changed)
    writing_width: FloatProperty(name='Stroke Width',default=.015,min=.001,max=1,update=writing.controls)
    writing_roughness: FloatProperty(name='Stroke Roughness',default=.4,min=0,max=1,update=writing.controls)
    writing_color: FloatVectorProperty(name='Stroke Color',subtype='COLOR',size=3,min=0,max=1,default=(.95,.95,.95),update=writing.controls)
    writing_start: IntProperty(name='Start Frame',default=1,min=0)
    writing_duration: IntProperty(name='Draw Duration (Frames)',default=72,min=1,max=10000)
    writing_speed: FloatProperty(name='Speed Multiplier',default=1,min=.05,max=20)
    writing_pause: IntProperty(name='Pause Between Strokes',default=0,min=0,max=1000)
    writing_timing: EnumProperty(name='Stroke Timing',items=[('EQUAL','Equal Time','Each curve spline gets equal draw time'),('LENGTH','By Stroke Length','Longer splines get more time')],default='EQUAL')
    writing_progress: FloatProperty(name='Progress',default=1,min=0,max=1,subtype='FACTOR',update=writing.progress_changed)
    writing_text: StringProperty(name='Text',default='BCGI LABS')
    writing_text_size: FloatProperty(name='Text Size',default=1,min=.01,max=100)
    writing_source: PointerProperty(name='Editable Text Source',type=bpy.types.Object)
    writing_font: PointerProperty(name='Writing Font',type=bpy.types.VectorFont)
    writing_windows_font: EnumProperty(name='Windows Font',items=writing.writing_fonts,update=writing.font_changed)
    floor_enabled: BoolProperty(name='Studio Floor',default=True,update=infinite_studio.update)
    glow_shape: EnumProperty(name='Glow Shape',items=[('CIRCLE','Circle',''),('OVAL','Oval',''),('SQUARE','Square',''),('ROUNDED','Rounded Square','')],update=infinite_studio.update)
    glow_feather: FloatProperty(name='Glow Feather',default=1,min=.01,max=1,update=infinite_studio.update)
    glow_aspect: FloatProperty(name='Glow Aspect Ratio',default=1.5,min=.1,max=10,update=infinite_studio.update)
    glow_roundness: FloatProperty(name='Corner Roundness',default=.5,min=0,max=1,update=infinite_studio.update)
    grid_glow: FloatProperty(name='Grid Glow Strength',default=0,min=0,max=20,update=infinite_studio.update)
    hide_default_grid: BoolProperty(name='Hide Viewport Grid',default=True,update=infinite_studio.update)
    background_power: FloatProperty(name='Background Light Power',default=1,min=0,max=20,update=infinite_studio.update)
    character_power: FloatProperty(name='Character Light Power',default=1,min=0,max=20,update=infinite_studio.update)
    character_root: PointerProperty(type=bpy.types.Object)
    windows_font: EnumProperty(name='Windows Font',items=infinite_studio.windows_fonts,update=infinite_studio.choose_windows_font)
    infinity_enabled: BoolProperty(name='Infinity Studio',default=True,update=infinite_studio.update)
    follow_camera: BoolProperty(name='Follow Camera',default=True,update=infinite_studio.update)
    original_world: PointerProperty(type=bpy.types.World)
    studio_root: PointerProperty(type=bpy.types.Object)
    studio_size: FloatProperty(name='Studio Size',default=10,min=1,max=1000,update=infinite_studio.update)
    studio_color: FloatVectorProperty(name='Blue / Outer Color',subtype='COLOR',size=3,min=0,max=1,default=(.045,.32,.50),update=infinite_studio.update)
    glow_color: FloatVectorProperty(name='Glow Color',subtype='COLOR',size=3,min=0,max=1,default=(.48,.68,.78),update=infinite_studio.update)
    glow_x: FloatProperty(name='Glow Left / Right',default=0,min=-4,max=4,update=infinite_studio.update)
    glow_height: FloatProperty(name='Glow Height',default=.2,min=0,max=3,update=infinite_studio.update)
    glow_spread: FloatProperty(name='Glow Spread',default=.45,min=.05,max=4,update=infinite_studio.update)
    studio_brightness: FloatProperty(name='Gradient Brightness',default=1,min=.01,max=5,update=infinite_studio.update)
    shadow_strength: FloatProperty(name='Shadow Strength',default=.35,min=0,max=1,update=infinite_studio.update)
    show_brand: BoolProperty(name='Floor Branding',default=False,update=infinite_studio.update)
    brand_text: StringProperty(name='Brand Text',default='BCGI LABS',update=infinite_studio.update)
    brand_mode: EnumProperty(name='Type',items=[('TEXT','Text',''),('LOGO','PNG Logo','')],update=infinite_studio.update)
    brand_color: FloatVectorProperty(name='Text Color / Logo Tint',subtype='COLOR',size=3,min=0,max=1,default=(1,1,1),update=infinite_studio.update)
    brand_size: FloatProperty(name='Text Size',default=.5,min=.01,max=20,update=infinite_studio.update)
    logo_width: FloatProperty(name='Logo Width',default=3,min=.01,max=100,update=infinite_studio.update)
    brand_x: FloatProperty(name='Left / Right',default=0,min=-100,max=100,update=infinite_studio.update)
    brand_y: FloatProperty(name='Front / Back',default=-3.2,min=-100,max=100,update=infinite_studio.update)
    brand_rotation: FloatProperty(name='Rotation',subtype='ANGLE',default=0,update=infinite_studio.update)
    brand_font: PointerProperty(type=bpy.types.VectorFont,update=infinite_studio.update)
    logo_image: PointerProperty(type=bpy.types.Image,update=infinite_studio.update)
    fx_preset: EnumProperty(name='Preset',items=[(x,x.replace('_',' ').title(),'') for x in ('WAVE','SCATTER','TWIST','PULSE','SCAN','GLOW','XRAY','GLOW_RING')])
    grid_enabled: BoolProperty(name='Floor Grid',default=False,update=infinite_studio.update)
    grid_color: FloatVectorProperty(name='Grid Color',subtype='COLOR',size=3,min=0,max=1,default=(.025,.10,.16),update=infinite_studio.update)
    grid_spacing: FloatProperty(name='Grid Box Size',default=1,min=.01,max=100,subtype='DISTANCE',update=infinite_studio.update)
    grid_width: FloatProperty(name='Line Width',default=.015,min=.001,max=1,subtype='DISTANCE',update=infinite_studio.update)
    grid_opacity: FloatProperty(name='Grid Opacity',default=.65,min=0,max=1,update=infinite_studio.update)
    lighting: EnumProperty(name='Preset', items=[('SOFT','Soft Studio',''),('DRAMA','Dramatic',''),('NEON','Neon Cyan / Pink','')])
    power: FloatProperty(name='Light Power', default=1, min=.01, max=20)
    backdrop: EnumProperty(name='Color', items=[('GRAY','Neutral Gray',''),('WHITE','White',''),('DARK','Dark','')])
    count: IntProperty(name='Count', default=150, min=1, max=10000)
    seed: IntProperty(name='Seed', default=7, min=0)
    scale: FloatProperty(name='Particle Size', default=.06, min=.001, max=1)
    wave: FloatProperty(name='Wave Height', default=.15, min=0, max=5)

class BCGI_OT_lights(Operator):
    bl_idname = 'bcgi.lights'
    bl_label = 'Add Studio Lights'
    bl_options = {'REGISTER','UNDO'}
    def execute(self, context):
        p=context.scene.bcgi_labs
        center,size=focus(context)
        c=collection('Studio_'+p.lighting)
        colors={'SOFT':[(1,.91,.8),(.75,.85,1),(1,1,1)],
                'DRAMA':[(1,.7,.4),(.2,.35,1),(1,.9,.8)],
                'NEON':[(.1,1,1),(1,.08,.5),(.4,.4,1)]}[p.lighting]
        for i,(pos,power) in enumerate([((-1,-1,1.4),600),((1,-.6,.6),250),((.3,1,1.2),800)]):
            d=bpy.data.lights.new('BCGI_'+['Key','Fill','Rim'][i], 'AREA')
            d.energy=power*p.power*size*size
            d.color=colors[i]
            d.shape='DISK'
            d.size=size*.8
            o=object_in(c,d.name,d)
            o.location=center+Vector(pos)*size
            o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
        self.report({'INFO'}, 'Added studio lights around selection or cursor')
        return {'FINISHED'}

class BCGI_OT_backdrop(Operator):
    bl_idname='bcgi.backdrop'
    bl_label='Add Cyclorama Background'
    bl_options={'REGISTER','UNDO'}
    def execute(self, context):
        center,size=focus(context)
        floor=center.z-size/2
        if context.active_object and context.active_object.type=='MESH':
            floor=min((context.active_object.matrix_world@Vector(v)).z for v in context.active_object.bound_box)
        radius=size
        profile=[(-size*3,0),(size,0)]
        for i in range(1,25):
            a=(math.pi/2)*i/24
            profile.append((size+radius*math.sin(a),radius*(1-math.cos(a))))
        profile.append((size+radius,size*4))
        verts=[(x,y,z) for y,z in profile for x in (-size*3,size*3)]
        faces=[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(profile)-1)]
        mesh=bpy.data.meshes.new('BCGI_Cyclorama')
        mesh.from_pydata(verts,[],faces)
        mesh.update()
        o=object_in(collection('Background'),'BCGI_Cyclorama',mesh)
        o.location=(center.x,center.y,floor)
        for f in mesh.polygons: f.use_smooth=True
        color={'GRAY':(.18,.18,.18),'WHITE':(.8,.8,.8),'DARK':(.025,.025,.035)}[context.scene.bcgi_labs.backdrop]
        mesh.materials.append(material('BCGI_Background',color))
        return {'FINISHED'}

def group(name, sockets):
    g=bpy.data.node_groups.new(name,'GeometryNodeTree')
    g.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    g.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    for name,typ,val,lo,hi in sockets:
        s=g.interface.new_socket(name=name,in_out='INPUT',socket_type=typ)
        s.default_value=val
        s.min_value=lo
        s.max_value=hi
    inp=g.nodes.new('NodeGroupInput'); inp.location=(-700,0)
    out=g.nodes.new('NodeGroupOutput'); out.location=(700,0)
    return g,inp,out

def node(g,kind,x,y):
    n=g.nodes.new(kind); n.location=(x,y); return n

class BCGI_OT_effect(Operator):
    bl_idname='bcgi.effect'
    bl_label='Add Procedural Effect'
    bl_options={'REGISTER','UNDO'}
    kind: EnumProperty(items=[('SCATTER','Scatter / Spark Field',''),('WAVE','Animated Wave','')])
    @classmethod
    def poll(cls,context):
        return context.mode=='OBJECT' and context.active_object is not None and context.active_object.type=='MESH'
    def execute(self,context):
        source=context.active_object
        p=context.scene.bcgi_labs
        # Effect copy retains source geometry and transform; the original stays untouched.
        o=object_in(collection('FX_'+self.kind),'BCGI_'+self.kind,source.data.copy())
        o.matrix_world=source.matrix_world.copy()
        if self.kind=='SCATTER':
            g,inp,out=group('BCGI_Scatter',[('Count','NodeSocketInt',p.count,1,10000),('Seed','NodeSocketInt',p.seed,0,100000),('Size','NodeSocketFloat',p.scale,.001,1)])
            bounds=node(g,'GeometryNodeBoundBox',-480,180)
            points=node(g,'GeometryNodeMeshLine',-480,-140)
            points.inputs['Offset'].default_value=(0,0,0)
            random=node(g,'FunctionNodeRandomValue',-250,180); random.data_type='FLOAT_VECTOR'
            position=node(g,'GeometryNodeSetPosition',0,0)
            ico=node(g,'GeometryNodeMeshIcoSphere',-250,-260)
            ico.inputs['Subdivisions'].default_value=1
            mat=node(g,'GeometryNodeSetMaterial',0,-240)
            mat.inputs['Material'].default_value=material('BCGI_Sparks',(.1,.6,1),True)
            inst=node(g,'GeometryNodeInstanceOnPoints',260,0)
            links=[(inp.outputs['Geometry'],bounds.inputs['Geometry']),
                   (inp.outputs['Count'],points.inputs['Count']),
                   (bounds.outputs['Min'],random.inputs['Min']),(bounds.outputs['Max'],random.inputs['Max']),
                   (inp.outputs['Seed'],random.inputs['Seed']),
                   (points.outputs['Mesh'],position.inputs['Geometry']),(random.outputs['Value'],position.inputs['Position']),
                   (inp.outputs['Size'],ico.inputs['Radius']),(ico.outputs['Mesh'],mat.inputs['Geometry']),
                   (mat.outputs['Geometry'],inst.inputs['Instance']),(position.outputs['Geometry'],inst.inputs['Points']),
                   (inst.outputs['Instances'],out.inputs['Geometry'])]
        else:
            g,inp,out=group('BCGI_Animated_Wave',[('Height','NodeSocketFloat',p.wave,0,5),('Speed','NodeSocketFloat',1,0,10),('Frequency','NodeSocketFloat',3,.01,30)])
            pos=node(g,'GeometryNodeInputPosition',-650,-180)
            separate=node(g,'ShaderNodeSeparateXYZ',-460,-180)
            freq=node(g,'ShaderNodeMath',-280,-100); freq.operation='MULTIPLY'
            time=node(g,'GeometryNodeInputSceneTime',-650,-380)
            speed=node(g,'ShaderNodeMath',-460,-380); speed.operation='MULTIPLY'
            add=node(g,'ShaderNodeMath',-100,-160); add.operation='ADD'
            sine=node(g,'ShaderNodeMath',80,-160); sine.operation='SINE'
            height=node(g,'ShaderNodeMath',260,-160); height.operation='MULTIPLY'
            vec=node(g,'ShaderNodeCombineXYZ',440,-160)
            setpos=node(g,'GeometryNodeSetPosition',440,100)
            links=[(pos.outputs['Position'],separate.inputs[0]),(separate.outputs['X'],freq.inputs[0]),
                   (inp.outputs['Frequency'],freq.inputs[1]),(time.outputs['Seconds'],speed.inputs[0]),
                   (inp.outputs['Speed'],speed.inputs[1]),(freq.outputs[0],add.inputs[0]),(speed.outputs[0],add.inputs[1]),
                   (add.outputs[0],sine.inputs[0]),(sine.outputs[0],height.inputs[0]),(inp.outputs['Height'],height.inputs[1]),
                   (height.outputs[0],vec.inputs['Z']),(vec.outputs[0],setpos.inputs['Offset']),
                   (inp.outputs['Geometry'],setpos.inputs['Geometry']),(setpos.outputs['Geometry'],out.inputs['Geometry'])]
        for a,b in links: g.links.new(a,b)
        mod=o.modifiers.new('BCGI Controls','NODES'); mod.node_group=g
        for selected in context.selected_objects: selected.select_set(False)
        o.select_set(True); context.view_layer.objects.active=o
        self.report({'INFO'}, 'Effect added on a separate copy; adjust controls in Modifiers')
        return {'FINISHED'}

class BCGI_PT_panel(Panel):
    bl_label='BCGI LABS · Studio Toolkit'
    bl_idname='BCGI_PT_panel'
    bl_space_type='VIEW_3D'; bl_region_type='UI'; bl_category='BCGI LABS'
    def draw(self,context):
        layout=self.layout; p=context.scene.bcgi_labs
        if _previews and 'brand' in _previews:
            layout.template_icon(icon_value=_previews['brand'].icon_id,scale=3)
        layout.label(text='Version 0.5.3 · Build 20261014')
        layout.operator('bcgi.top_library',text='Open Top Preset Library')
        camera_overlay.draw(layout,p)
        box=layout.box(); box.label(text='Infinite Gradient Studio',icon='WORLD')
        box.operator('bcgi.infinite_studio')
        box.prop(p,'infinity_enabled'); box.prop(p,'follow_camera')
        box.prop(p,'floor_enabled')
        box.operator('bcgi.center_scene')
        box.prop(p,'background_power')
        for prop in ('studio_size','studio_color','glow_color','glow_x','glow_height','glow_spread','studio_brightness','shadow_strength','show_brand'):
            box.prop(p,prop)
        box.prop(p,'glow_shape'); box.prop(p,'glow_feather')
        if p.glow_shape!='CIRCLE': box.prop(p,'glow_aspect')
        if p.glow_shape=='ROUNDED': box.prop(p,'glow_roundness')
        if p.show_brand:
            box.prop(p,'brand_mode')
            if p.brand_mode=='TEXT':
                box.prop(p,'brand_text'); box.prop(p,'windows_font'); box.operator('bcgi.load_font'); box.prop(p,'brand_size')
            else:
                box.prop(p,'logo_image'); box.operator('bcgi.load_logo'); box.prop(p,'logo_width')
            for prop in ('brand_color','brand_x','brand_y','brand_rotation'): box.prop(p,prop)
        box.prop(p,'grid_enabled')
        if p.grid_enabled:
            for prop in ('grid_color','grid_spacing','grid_width','grid_opacity','grid_glow','hide_default_grid'): box.prop(p,prop)
        box=layout.box(); box.label(text='Studio Lighting',icon='LIGHT_AREA')
        box.prop(p,'character_power'); box.operator('bcgi.character_lights')
        box.prop(p,'lighting'); box.prop(p,'power'); box.operator('bcgi.lights')
        box=layout.box(); box.label(text='Studio Background',icon='IMAGE_BACKGROUND')
        box.prop(p,'backdrop'); box.operator('bcgi.backdrop')
        box=layout.box(); box.label(text='Geometry Nodes / FX',icon='GEOMETRY_NODES')
        box.prop(p,'fx_preset'); box.operator('bcgi.apply_preset'); box.operator('bcgi.keyframe_fx')
        box.operator('bcgi.install_preset_library')
        box.label(text='Drag assets from BCGI LABS library')
        box.label(text='Select a mesh in Object Mode')
        box.prop(p,'count'); box.prop(p,'seed'); box.prop(p,'scale')
        box.operator('bcgi.effect',text='Add Scatter / Spark Field').kind='SCATTER'
        box.prop(p,'wave'); box.operator('bcgi.effect',text='Add Animated Wave').kind='WAVE'
        box=layout.box(); box.label(text='Writing / Drawing Reveal',icon='CURVE_BEZCURVE')
        box.prop(p,'writing_text'); box.prop(p,'writing_text_size')
        box.prop(p,'writing_windows_font'); box.prop(p,'writing_font'); box.operator('bcgi.writing_font')
        box.operator('bcgi.text_writing'); box.prop(p,'writing_source')
        box.label(text='Fonts reveal outlines; drawn curves reveal strokes')
        box.prop(p,'writing_style'); box.operator('bcgi.sample_writing')
        box.operator('bcgi.apply_writing'); box.prop(p,'writing_target')
        box.template_ID(p,'writing_material')
        box.operator('bcgi.default_writing_material')
        for prop in ('writing_color','writing_width','writing_roughness','writing_start','writing_duration'): box.prop(p,prop)
        for prop in ('writing_speed','writing_pause','writing_timing'): box.prop(p,prop)
        box.operator('bcgi.animate_writing',text='Apply / Update Writing Timing')
        box.prop(p,'writing_progress'); box.operator('bcgi.keyframe_writing')
        box.label(text='Animate Progress 0 → 1 in Modifiers')
        layout.label(text='FX controls: Modifiers tab',icon='MODIFIER')
        layout.label(text='Wave needs a subdivided mesh')
        layout.label(text='Tools add separate BCGI collections')

classes=(BCGISettings,BCGI_OT_lights,BCGI_OT_backdrop,BCGI_OT_effect,infinite_studio.BCGI_OT_infinite_studio,infinite_studio.BCGI_OT_center_glow,infinite_studio.BCGI_OT_center_studio,infinite_studio.BCGI_OT_center_scene,infinite_studio.BCGI_OT_load_logo,infinite_studio.BCGI_OT_load_font,infinite_studio.BCGI_OT_character_lights,presets.BCGI_OT_apply_preset,presets.BCGI_OT_keyframe_fx,presets.BCGI_OT_install_library,BCGI_PT_panel)
classes=classes+(writing.BCGI_OT_writing,writing.BCGI_OT_animate_writing,writing.BCGI_OT_sample_writing,top_library.BCGI_OT_top_library,top_library.BCGI_OT_top_apply,top_library.BCGI_OT_top_pick)
classes=classes+camera_overlay.classes
classes=classes+(writing.BCGI_OT_default_writing_material,)
classes=classes+shelf.classes
classes=classes+(writing.BCGI_OT_writing_font,writing.BCGI_OT_text_writing,writing.BCGI_OT_keyframe_writing)
def register():
    global _previews
    for cls in classes: bpy.utils.register_class(cls)
    bpy.types.Scene.bcgi_labs=PointerProperty(type=BCGISettings)
    _previews=bpy.utils.previews.new()
    path=os.path.join(os.path.dirname(__file__),'assets','BCGI.png')
    if os.path.isfile(path): _previews.load('brand',path,'IMAGE')
    top_library._icons=_previews
    top_library._choices=[]
    for name in top_library.IDS:
        path=os.path.join(os.path.dirname(__file__),'assets','presets',name+'.png')
        if os.path.isfile(path): _previews.load(name,path,'IMAGE')
    bpy.types.VIEW3D_HT_header.prepend(top_library.header)
    if infinite_studio.camera_changed not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(infinite_studio.camera_changed)

def unregister():
    global _previews
    shelf.stop_all()
    bpy.types.VIEW3D_HT_header.remove(top_library.header)
    top_library._icons=None
    infinite_studio.restore_overlays()
    if infinite_studio.camera_changed in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(infinite_studio.camera_changed)
    if _previews:
        bpy.utils.previews.remove(_previews); _previews=None
    del bpy.types.Scene.bcgi_labs
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
