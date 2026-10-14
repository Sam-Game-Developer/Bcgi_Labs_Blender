"""Editable curve strokes with sequential chalk/ink write-on animation."""
import bpy,math
from mathutils import Vector
from .presets import set_control,control_path

def stroke_material(style,color):
    m=bpy.data.materials.new('BCGI_'+style+'_Stroke'); m.use_nodes=True
    tree=m.node_tree; tree.nodes.clear()
    shader=tree.nodes.new('ShaderNodeBsdfPrincipled'); shader.name='BCGI_StrokeColor'
    shader.inputs['Base Color'].default_value=(*color,1); shader.inputs['Roughness'].default_value=.95 if style=='CHALK' else .4
    out=tree.nodes.new('ShaderNodeOutputMaterial')
    if style=='CHALK':
        noise=tree.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=140
        noise.inputs['Detail'].default_value=2
        tex=tree.nodes.new('ShaderNodeTexCoord'); tree.links.new(tex.outputs['Object'],noise.inputs['Vector'])
        ramp=tree.nodes.new('ShaderNodeMapRange'); ramp.inputs['From Min'].default_value=.3; ramp.inputs['From Max'].default_value=.6; ramp.clamp=True
        tree.links.new(noise.outputs['Fac'],ramp.inputs['Value'])
        transparent=tree.nodes.new('ShaderNodeBsdfTransparent'); mix=tree.nodes.new('ShaderNodeMixShader')
        for a,b in [(ramp.outputs[0],mix.inputs[0]),(transparent.outputs[0],mix.inputs[1]),(shader.outputs[0],mix.inputs[2]),(mix.outputs[0],out.inputs['Surface'])]: tree.links.new(a,b)
    else: tree.links.new(shader.outputs[0],out.inputs['Surface'])
    return m

def build(style):
    from . import group
    name='BCGI Writing · '+style.title()
    if bpy.data.node_groups.get(name): return bpy.data.node_groups[name]
    g,inp,out=group(name,[('Progress','NodeSocketFloat',1,0,1),('Width','NodeSocketFloat',.015,.001,1),('Roughness','NodeSocketFloat',.4 if style=='CHALK' else 0,0,1)])
    material=stroke_material(style,(.95,.95,.95) if style=='CHALK' else (.015,.015,.015))
    s=g.interface.new_socket(name='Stroke Material',in_out='INPUT',socket_type='NodeSocketMaterial'); s.default_value=material
    g['bcgi_writing']=style; g.is_modifier=True
    def n(typ): return g.nodes.new(typ)
    def link(a,b): g.links.new(a,b)
    def mathop(op,a,b):
        node=n('ShaderNodeMath'); node.operation=op; link(a,node.inputs[0])
        if isinstance(b,(float,int)): node.inputs[1].default_value=b
        else: link(b,node.inputs[1])
        return node.outputs[0]
    size=n('GeometryNodeAttributeDomainSize'); size.component='CURVE'; link(inp.outputs['Geometry'],size.inputs['Geometry'])
    index=n('GeometryNodeInputIndex')
    factor=mathop('SUBTRACT',mathop('MULTIPLY',inp.outputs['Progress'],size.outputs['Spline Count']),index.outputs[0])
    trim=n('GeometryNodeTrimCurve'); trim.mode='FACTOR'; link(inp.outputs['Geometry'],trim.inputs['Curve']); link(factor,trim.inputs['End'])
    delete=n('GeometryNodeDeleteGeometry'); delete.domain='CURVE'; link(trim.outputs['Curve'],delete.inputs['Geometry']); link(mathop('LESS_THAN',factor,.00001),delete.inputs['Selection'])
    sample=n('GeometryNodeResampleCurve'); sample.inputs['Mode'].default_value='Length'; sample.inputs['Length'].default_value=.015; link(delete.outputs[0],sample.inputs['Curve'])
    pos=n('GeometryNodeInputPosition'); noise=n('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=90; link(pos.outputs[0],noise.inputs['Vector'])
    # Width variation is 1 - Roughness + Roughness * noise, positive across range.
    base=n('ShaderNodeMath'); base.operation='SUBTRACT'; base.inputs[0].default_value=1; link(inp.outputs['Roughness'],base.inputs[1])
    variation=mathop('ADD',mathop('MULTIPLY',noise.outputs['Fac'],inp.outputs['Roughness']),base.outputs[0])
    radius=n('GeometryNodeSetCurveRadius'); link(sample.outputs[0],radius.inputs['Curve']); link(variation,radius.inputs['Radius'])
    circle=n('GeometryNodeCurvePrimitiveCircle'); circle.inputs['Resolution'].default_value=12; link(inp.outputs['Width'],circle.inputs['Radius'])
    mesh=n('GeometryNodeCurveToMesh'); mesh.inputs['Fill Caps'].default_value=True
    link(radius.outputs[0],mesh.inputs['Curve']); link(circle.outputs[0],mesh.inputs['Profile Curve'])
    link(variation,mesh.inputs['Scale'])
    setter=n('GeometryNodeSetMaterial'); link(mesh.outputs[0],setter.inputs['Geometry']); link(inp.outputs['Stroke Material'],setter.inputs['Material']); link(setter.outputs[0],out.inputs['Geometry'])
    for i,node in enumerate(g.nodes): node.location=((i%5)*220,-(i//5)*200)
    g.asset_mark(); g.asset_data.author='BCGI LABS'; g.asset_data.description='Apply to a curve; animate Progress 0 to 1 for sequential writing.'
    return g

def latest(o):
    if not o: return None
    return next((m for m in reversed(list(o.modifiers)) if m.type=='NODES' and m.node_group and m.node_group.get('bcgi_writing')),None)

def controls(self,context):
    mod=latest(self.writing_target or context.active_object)
    if not mod: return
    for socket in mod.node_group.interface.items_tree:
        if socket.item_type=='SOCKET' and socket.in_out=='INPUT':
            if socket.name=='Width': set_control(mod,socket.identifier,self.writing_width)
            if socket.name=='Roughness': set_control(mod,socket.identifier,self.writing_roughness)
            if socket.name=='Stroke Material':
                if hasattr(mod,'properties'): mat=getattr(mod.properties.inputs,socket.identifier).value
                else: mat=mod[socket.identifier]
                if mat: mat.node_tree.nodes['BCGI_StrokeColor'].inputs['Base Color'].default_value=(*self.writing_color,1)

def style_changed(self,context):
    self.writing_color=(.95,.95,.95) if self.writing_style=='CHALK' else (.015,.015,.015)
    self.writing_roughness=.4 if self.writing_style=='CHALK' else .03

class BCGI_OT_writing(bpy.types.Operator):
    bl_idname='bcgi.apply_writing'; bl_label='Apply Writing to Curve'; bl_options={'REGISTER','UNDO'}
    @classmethod
    def poll(cls,context): return context.mode=='OBJECT' and context.active_object is not None and context.active_object.type=='CURVE'
    def execute(self,context):
        p=context.scene.bcgi_labs; o=context.active_object
        g=build(p.writing_style); mod=latest(o) or o.modifiers.new(g.name,'NODES'); mod.node_group=g
        for s in g.interface.items_tree:
            if s.item_type=='SOCKET' and s.in_out=='INPUT' and s.socket_type!='NodeSocketGeometry':
                value=s.default_value.copy() if s.name=='Stroke Material' else s.default_value
                set_control(mod,s.identifier,value)
        p.writing_target=o; controls(p,context)
        return {'FINISHED'}

class BCGI_OT_animate_writing(bpy.types.Operator):
    bl_idname='bcgi.animate_writing'; bl_label='Animate Writing'; bl_options={'REGISTER','UNDO'}
    @classmethod
    def poll(cls,context): return latest(context.scene.bcgi_labs.writing_target or context.active_object) is not None
    def execute(self,context):
        p=context.scene.bcgi_labs; o=p.writing_target or context.active_object; mod=latest(o)
        socket=next(s for s in mod.node_group.interface.items_tree if s.name=='Progress' and s.in_out=='INPUT')
        for frame,value in [(p.writing_start,0),(p.writing_start+p.writing_duration,1)]:
            set_control(mod,socket.identifier,value); o.keyframe_insert(data_path=control_path(mod,socket.identifier),frame=frame,group='BCGI Writing')
        context.scene.frame_set(p.writing_start)
        return {'FINISHED'}

class BCGI_OT_sample_writing(bpy.types.Operator):
    bl_idname='bcgi.sample_writing'; bl_label='Create Editable Writing Sample'; bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        data=bpy.data.curves.new('BCGI_Drawing_Paths','CURVE'); data.dimensions='3D'
        paths=[[(.4,1,0),(-.25,1,0),(-.45,.7,0),(-.1,.4,0),(.4,.1,0),(.25,-.5,0),(-.35,-.6,0)],[(0,1.3,0),(0,-.85,0)]]
        for path in paths:
            spline=data.splines.new('BEZIER'); spline.bezier_points.add(len(path)-1)
            for point,co in zip(spline.bezier_points,path): point.co=co; point.handle_left_type='AUTO'; point.handle_right_type='AUTO'
        o=bpy.data.objects.new('BCGI_Writing_Sample',data); context.scene.collection.objects.link(o); o.location=context.scene.cursor.location
        for selected in context.selected_objects: selected.select_set(False)
        o.select_set(True); context.view_layer.objects.active=o
        bpy.ops.bcgi.apply_writing()
        return {'FINISHED'}
