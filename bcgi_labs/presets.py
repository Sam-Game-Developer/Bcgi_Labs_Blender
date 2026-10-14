"""Modifier assets with animatable inputs; exports to a native Blender asset library."""
import bpy, os
import json
KINDS=('WAVE','SCATTER','TWIST','PULSE','SCAN','GLOW','XRAY','GLOW_RING')

def set_control(mod,identifier,value):
    if hasattr(mod,'properties'):
        getattr(mod.properties.inputs,identifier).value=value
    else: mod[identifier]=value

def control_path(mod,identifier):
    if hasattr(mod,'properties'):
        return mod.path_from_id()+'.properties.inputs.'+identifier+'.value'
    return mod.path_from_id()+'['+json.dumps(identifier)+']'

def enable_glow(scene):
    # Blender 5.2 compositor: wrap its existing image output with a glare node.
    if not hasattr(scene,'compositing_node_group'): return False
    tree=scene.compositing_node_group
    if tree is None:
        tree=bpy.data.node_groups.new('BCGI Render Glow','CompositorNodeTree')
        tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
        source=tree.nodes.new('CompositorNodeRLayers'); output=tree.nodes.new('NodeGroupOutput')
        tree.links.new(source.outputs['Image'],output.inputs['Image'])
        scene.compositing_node_group=tree
    if tree.nodes.get('BCGI_GlowHalo'): return True
    output=next((n for n in tree.nodes if n.type=='GROUP_OUTPUT' and n.is_active_output),None)
    if output is None or not output.inputs or not output.inputs[0].links: return False
    source=output.inputs[0].links[0].from_socket
    glare=tree.nodes.new('CompositorNodeGlare'); glare.name='BCGI_GlowHalo'; glare.label='BCGI Glow Halo'
    glare.inputs['Type'].default_value='Fog Glow'
    glare.inputs['Threshold'].default_value=1
    tree.links.new(source,glare.inputs['Image']); tree.links.new(glare.outputs['Image'],output.inputs[0])
    return True

def build(kind):
    if kind=='GLOW_RING': return build_ring()
    from . import group, node
    existing=next((g for g in bpy.data.node_groups if g.get('bcgi_preset')==kind and g.get('bcgi_schema')==1),None)
    if existing: return existing
    controls={
        'WAVE':[('Height','NodeSocketFloat',.15,0,5),('Speed','NodeSocketFloat',1,0,10),('Frequency','NodeSocketFloat',3,.01,30)],
        'SCATTER':[('Count','NodeSocketInt',150,1,10000),('Seed','NodeSocketInt',7,0,100000),('Size','NodeSocketFloat',.06,.001,1)],
        'TWIST':[('Strength','NodeSocketFloat',1,-10,10),('Speed','NodeSocketFloat',0,0,10)],
        'PULSE':[('Amount','NodeSocketFloat',.15,0,.9),('Speed','NodeSocketFloat',2,0,20)],
        'SCAN':[('Scan Position','NodeSocketFloat',.5,0,1),('Band Width','NodeSocketFloat',.04,.001,1)],
        'GLOW':[('Glow Strength','NodeSocketFloat',5,0,100)],
        'XRAY':[('Opacity','NodeSocketFloat',.5,0,1)]}[kind]
    g,inp,out=group('BCGI FX · '+kind.title(),controls)
    g['bcgi_preset']=kind; g['bcgi_schema']=1; g.is_modifier=True
    def n(typ,x=0,y=0): return node(g,typ,x,y)
    def link(a,b): g.links.new(a,b)
    def mathop(op,a,b=None):
        m=n('ShaderNodeMath'); m.operation=op
        link(a,m.inputs[0])
        if b is not None:
            if isinstance(b,(int,float)): m.inputs[1].default_value=b
            else: link(b,m.inputs[1])
        return m.outputs[0]
    time=n('GeometryNodeInputSceneTime') if kind in ('WAVE','TWIST','PULSE') else None
    if kind=='WAVE':
        pos=n('GeometryNodeInputPosition'); xyz=n('ShaderNodeSeparateXYZ'); link(pos.outputs[0],xyz.inputs[0])
        phase=mathop('ADD',mathop('MULTIPLY',xyz.outputs['X'],inp.outputs['Frequency']),mathop('MULTIPLY',time.outputs['Seconds'],inp.outputs['Speed']))
        height=mathop('MULTIPLY',mathop('SINE',phase),inp.outputs['Height'])
        vec=n('ShaderNodeCombineXYZ'); link(height,vec.inputs['Z'])
        setpos=n('GeometryNodeSetPosition'); link(inp.outputs['Geometry'],setpos.inputs['Geometry']); link(vec.outputs[0],setpos.inputs['Offset']); link(setpos.outputs[0],out.inputs[0])
    elif kind=='TWIST':
        pos=n('GeometryNodeInputPosition'); xyz=n('ShaderNodeSeparateXYZ'); link(pos.outputs[0],xyz.inputs[0])
        angle=mathop('ADD',mathop('MULTIPLY',xyz.outputs['Z'],inp.outputs['Strength']),mathop('MULTIPLY',time.outputs['Seconds'],inp.outputs['Speed']))
        rotate=n('ShaderNodeVectorRotate'); rotate.rotation_type='AXIS_ANGLE'; rotate.inputs['Axis'].default_value=(0,0,1)
        link(pos.outputs[0],rotate.inputs['Vector']); link(angle,rotate.inputs['Angle'])
        setpos=n('GeometryNodeSetPosition'); link(inp.outputs[0],setpos.inputs['Geometry']); link(rotate.outputs[0],setpos.inputs['Position']); link(setpos.outputs[0],out.inputs[0])
    elif kind=='PULSE':
        scale=mathop('ADD',mathop('MULTIPLY',mathop('SINE',mathop('MULTIPLY',time.outputs['Seconds'],inp.outputs['Speed'])),inp.outputs['Amount']),1)
        vec=n('ShaderNodeCombineXYZ')
        for socket in vec.inputs: link(scale,socket)
        transform=n('GeometryNodeTransform'); link(inp.outputs[0],transform.inputs['Geometry']); link(vec.outputs[0],transform.inputs['Scale']); link(transform.outputs[0],out.inputs[0])
    elif kind=='SCATTER':
        box=n('GeometryNodeBoundBox'); link(inp.outputs[0],box.inputs[0])
        points=n('GeometryNodeMeshLine'); points.inputs['Offset'].default_value=(0,0,0); link(inp.outputs['Count'],points.inputs['Count'])
        random=n('FunctionNodeRandomValue'); random.data_type='FLOAT_VECTOR'
        link(box.outputs['Min'],random.inputs['Min']); link(box.outputs['Max'],random.inputs['Max']); link(inp.outputs['Seed'],random.inputs['Seed'])
        setpos=n('GeometryNodeSetPosition'); link(points.outputs['Mesh'],setpos.inputs['Geometry']); link(random.outputs['Value'],setpos.inputs['Position'])
        ico=n('GeometryNodeMeshIcoSphere'); ico.inputs['Subdivisions'].default_value=1; link(inp.outputs['Size'],ico.inputs['Radius'])
        instances=n('GeometryNodeInstanceOnPoints'); link(setpos.outputs[0],instances.inputs['Points']); link(ico.outputs['Mesh'],instances.inputs['Instance'])
        join=n('GeometryNodeJoinGeometry'); link(inp.outputs[0],join.inputs[0]); link(instances.outputs[0],join.inputs[0]); link(join.outputs[0],out.inputs[0])
    else:
        mat=bpy.data.materials.new('BCGI FX '+kind); mat.use_nodes=True; mat.node_tree.nodes.clear()
        nt=mat.node_tree; ns=nt.nodes; ls=nt.links
        def shader(typ): return ns.new(typ)
        def attr(name):
            a=shader('ShaderNodeAttribute'); a.attribute_name=name; return a.outputs['Fac']
        def smath(op,a,b):
            m=shader('ShaderNodeMath'); m.operation=op; ls.new(a,m.inputs[0])
            if isinstance(b,(int,float)): m.inputs[1].default_value=b
            else: ls.new(b,m.inputs[1])
            return m.outputs[0]
        emission=shader('ShaderNodeEmission'); emission.inputs['Color'].default_value=(.02,.8,1,1)
        output=shader('ShaderNodeOutputMaterial')
        geo=inp.outputs['Geometry']
        for title,_,value,lo,hi in controls:
            store=n('GeometryNodeStoreNamedAttribute'); store.data_type='FLOAT'; store.domain='POINT'
            store.inputs['Name'].default_value='bcgi_'+title.replace(' ','_').lower()
            link(geo,store.inputs['Geometry']); link(inp.outputs[title],store.inputs['Value']); geo=store.outputs[0]
        if kind=='GLOW':
            ls.new(attr('bcgi_glow_strength'),emission.inputs['Strength']); ls.new(emission.outputs[0],output.inputs['Surface'])
        elif kind=='XRAY':
            facing=shader('ShaderNodeLayerWeight'); mask=smath('MULTIPLY',smath('POWER',facing.outputs['Facing'],2),attr('bcgi_opacity'))
            transparent=shader('ShaderNodeBsdfTransparent'); mix=shader('ShaderNodeMixShader')
            emission.inputs['Strength'].default_value=2
            ls.new(mask,mix.inputs[0]); ls.new(transparent.outputs[0],mix.inputs[1]); ls.new(emission.outputs[0],mix.inputs[2]); ls.new(mix.outputs[0],output.inputs['Surface'])
        else:
            tex=shader('ShaderNodeTexCoord'); xyz=shader('ShaderNodeSeparateXYZ'); ls.new(tex.outputs['Generated'],xyz.inputs[0])
            distance=smath('ABSOLUTE',smath('SUBTRACT',xyz.outputs['Z'],attr('bcgi_scan_position')),0)
            band=smath('LESS_THAN',distance,attr('bcgi_band_width'))
            base=shader('ShaderNodeBsdfPrincipled'); base.inputs['Base Color'].default_value=(.025,.05,.08,1)
            emission.inputs['Strength'].default_value=5
            mix=shader('ShaderNodeMixShader'); ls.new(band,mix.inputs[0]); ls.new(base.outputs[0],mix.inputs[1]); ls.new(emission.outputs[0],mix.inputs[2]); ls.new(mix.outputs[0],output.inputs['Surface'])
        setter=n('GeometryNodeSetMaterial'); setter.inputs['Material'].default_value=mat
        link(geo,setter.inputs['Geometry']); link(setter.outputs[0],out.inputs[0])
    g.asset_mark(); g.asset_data.author='BCGI LABS'; g.asset_data.description='Editable '+kind.lower()+' modifier. Keyframe the exposed modifier controls.'
    # Arrange the graph for inspection rather than leaving all nodes stacked.
    for i,nd in enumerate(g.nodes): nd.location=((i%5)*230,(i//5)*-220)
    return g

def build_ring():
    from . import group
    name='BCGI FX · Glow Ring Highlight'
    existing=bpy.data.node_groups.get(name)
    if existing: return existing
    g,inp,out=group(name,[('Radius','NodeSocketFloat',1,.001,100),('Width','NodeSocketFloat',.025,.001,1),
                         ('Arc Coverage','NodeSocketFloat',.8,.01,1),('Ring Count','NodeSocketInt',2,1,10),
                         ('Spacing','NodeSocketFloat',.12,0,10),('Glow Strength','NodeSocketFloat',8,0,100),
                         ('Rotation Speed','NodeSocketFloat',1,-10,10)])
    for title,typ,default in [('Position','NodeSocketVector',(0,0,0)),('Rotation','NodeSocketVector',(0,0,0)),('Glow Color','NodeSocketColor',(1,1,1,1))]:
        s=g.interface.new_socket(name=title,in_out='INPUT',socket_type=typ); s.default_value=default
    def n(typ): return g.nodes.new(typ)
    def link(a,b): g.links.new(a,b)
    circle=n('GeometryNodeCurvePrimitiveCircle'); circle.inputs['Resolution'].default_value=96; link(inp.outputs['Radius'],circle.inputs['Radius'])
    trim=n('GeometryNodeTrimCurve'); trim.mode='FACTOR'; link(circle.outputs['Curve'],trim.inputs['Curve']); link(inp.outputs['Arc Coverage'],trim.inputs['End'])
    profile=n('GeometryNodeCurvePrimitiveCircle'); profile.inputs['Resolution'].default_value=12; link(inp.outputs['Width'],profile.inputs['Radius'])
    mesh=n('GeometryNodeCurveToMesh'); mesh.inputs['Fill Caps'].default_value=True; link(trim.outputs[0],mesh.inputs['Curve']); link(profile.outputs[0],mesh.inputs['Profile Curve'])
    geo=mesh.outputs[0]
    for title,dtype,attribute in [('Glow Strength','FLOAT','bcgi_ring_strength'),('Glow Color','FLOAT_COLOR','bcgi_ring_color')]:
        store=n('GeometryNodeStoreNamedAttribute'); store.data_type=dtype; store.domain='POINT'; store.inputs['Name'].default_value=attribute
        link(geo,store.inputs['Geometry']); link(inp.outputs[title],store.inputs['Value']); geo=store.outputs[0]
    material=bpy.data.materials.new('BCGI_Ring_Glow'); material.use_nodes=True; material.node_tree.nodes.clear()
    mt=material.node_tree; emit=mt.nodes.new('ShaderNodeEmission'); output=mt.nodes.new('ShaderNodeOutputMaterial')
    for name,socket,attribute in [('Glow Strength','Strength','bcgi_ring_strength'),('Glow Color','Color','bcgi_ring_color')]:
        attr=mt.nodes.new('ShaderNodeAttribute'); attr.attribute_name=attribute
        mt.links.new(attr.outputs['Color' if socket=='Color' else 'Fac'],emit.inputs[socket])
    mt.links.new(emit.outputs[0],output.inputs['Surface'])
    setter=n('GeometryNodeSetMaterial'); setter.inputs['Material'].default_value=material; link(geo,setter.inputs['Geometry'])
    time=n('GeometryNodeInputSceneTime'); speed=n('ShaderNodeMath'); speed.operation='MULTIPLY'; link(time.outputs['Seconds'],speed.inputs[0]); link(inp.outputs['Rotation Speed'],speed.inputs[1])
    spin=n('ShaderNodeCombineXYZ'); link(speed.outputs[0],spin.inputs['Z'])
    rotate=n('GeometryNodeTransform'); link(setter.outputs[0],rotate.inputs['Geometry']); link(spin.outputs[0],rotate.inputs['Rotation'])
    spacing=n('ShaderNodeCombineXYZ'); link(inp.outputs['Spacing'],spacing.inputs['Z'])
    line=n('GeometryNodeMeshLine'); link(inp.outputs['Ring Count'],line.inputs['Count']); link(spacing.outputs[0],line.inputs['Offset'])
    inst=n('GeometryNodeInstanceOnPoints'); link(line.outputs[0],inst.inputs['Points']); link(rotate.outputs[0],inst.inputs['Instance'])
    transformed=n('GeometryNodeTransform'); link(inst.outputs[0],transformed.inputs['Geometry']); link(inp.outputs['Position'],transformed.inputs['Translation']); link(inp.outputs['Rotation'],transformed.inputs['Rotation'])
    join=n('GeometryNodeJoinGeometry'); link(inp.outputs['Geometry'],join.inputs[0]); link(transformed.outputs[0],join.inputs[0]); link(join.outputs[0],out.inputs[0])
    g['bcgi_preset']='GLOW_RING'; g.is_modifier=True; g.asset_mark(); g.asset_data.author='BCGI LABS'; g.asset_data.description='Animated glowing rings/arcs; source object materials stay intact.'
    for i,node in enumerate(g.nodes): node.location=((i%5)*220,-(i//5)*210)
    return g

class BCGI_OT_apply_preset(bpy.types.Operator):
    bl_idname='bcgi.apply_preset'; bl_label='Apply Preset to Selected Mesh'; bl_options={'REGISTER','UNDO'}
    @classmethod
    def poll(cls,context): return context.mode=='OBJECT' and context.active_object is not None and context.active_object.type=='MESH'
    def execute(self,context):
        g=build(context.scene.bcgi_labs.fx_preset)
        mod=context.active_object.modifiers.new(g.name,'NODES'); mod.node_group=g
        for s in g.interface.items_tree:
            if s.item_type=='SOCKET' and s.in_out=='INPUT' and s.socket_type!='NodeSocketGeometry': set_control(mod,s.identifier,s.default_value)
        if context.scene.bcgi_labs.fx_preset=='GLOW_RING':
            o=context.active_object
            bounds=[v for v in o.bound_box]
            dimensions=[max(v[i] for v in bounds)-min(v[i] for v in bounds) for i in range(3)]
            axis=max(range(3),key=lambda i:dimensions[i])
            radius=max(dimensions[i] for i in range(3) if i!=axis)*.6
            rotation=(0,1.57079632679,0) if axis==0 else (1.57079632679,0,0) if axis==1 else (0,0,0)
            position=tuple((max(v[i] for v in bounds)+min(v[i] for v in bounds))/2 for i in range(3))
            for s in g.interface.items_tree:
                if s.item_type=='SOCKET' and s.in_out=='INPUT' and s.name in ('Radius','Position','Rotation','Width'):
                    set_control(mod,s.identifier,{'Radius':max(radius,.01),'Position':position,'Rotation':rotation,'Width':max(radius*.035,.001)}[s.name])
        if context.scene.bcgi_labs.fx_preset in ('GLOW','GLOW_RING'): enable_glow(context.scene)
        self.report({'INFO'},'Preset applied. Controls are in the Modifiers tab; hover a value and press I to keyframe.')
        return {'FINISHED'}

class BCGI_OT_keyframe_fx(bpy.types.Operator):
    bl_idname='bcgi.keyframe_fx'; bl_label='Keyframe Latest FX Controls'; bl_options={'REGISTER','UNDO'}
    @classmethod
    def poll(cls,context):
        return context.active_object is not None and any(m.type=='NODES' and m.node_group and m.node_group.get('bcgi_preset') for m in context.active_object.modifiers)
    def execute(self,context):
        o=context.active_object
        mod=next(m for m in reversed(list(o.modifiers)) if m.type=='NODES' and m.node_group and m.node_group.get('bcgi_preset'))
        for s in mod.node_group.interface.items_tree:
            if s.item_type=='SOCKET' and s.in_out=='INPUT' and s.socket_type!='NodeSocketGeometry':
                o.keyframe_insert(data_path=control_path(mod,s.identifier),frame=context.scene.frame_current,group='BCGI FX')
        return {'FINISHED'}

class BCGI_OT_install_library(bpy.types.Operator):
    bl_idname='bcgi.install_preset_library'; bl_label='Install / Refresh Asset Library'
    def execute(self,context):
        path=bpy.utils.user_resource('DATAFILES',path='bcgi_labs_assets',create=True)
        from .writing import build as writing_build
        bpy.data.libraries.write(os.path.join(path,'BCGI_LABS_FX.blend'),set([build(k) for k in KINDS]+[writing_build('CHALK'),writing_build('PEN')]),fake_user=True)
        libs=context.preferences.filepaths.asset_libraries
        existing=next((lib for lib in libs if lib.name=='BCGI LABS'),None)
        if existing: existing.path=path
        else: libs.new(name='BCGI LABS',directory=path)
        bpy.ops.wm.save_userpref()
        self.report({'INFO'},'Asset Browser: choose BCGI LABS and drag an effect onto a mesh.')
        return {'FINISHED'}
