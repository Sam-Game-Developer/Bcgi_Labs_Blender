"""Continuous blue cyclorama with editable procedural gradient and floor text."""
import bpy, math, os
from mathutils import Vector
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty
_windows_fonts=[]

def windows_fonts(self,context):
    global _windows_fonts
    if not _windows_fonts:
        _windows_fonts=[('BUILTIN','Blender Built-in','')]
        try:
            import winreg
            values={}
            for hive in (winreg.HKEY_LOCAL_MACHINE,winreg.HKEY_CURRENT_USER):
                try:
                    with winreg.OpenKey(hive,r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts') as key:
                        for index in range(winreg.QueryInfoKey(key)[1]):
                            name,filename,_=winreg.EnumValue(key,index)
                            path=filename if os.path.isabs(filename) else os.path.join(os.environ.get('WINDIR','C:/Windows'),'Fonts',filename)
                            if os.path.isfile(path) and path.lower().endswith(('.ttf','.otf')): values[path]=name.replace(' (TrueType)','')
                except OSError: pass
            _windows_fonts.extend((path,name,path) for path,name in sorted(values.items(),key=lambda item:item[1].lower()))
        except ImportError: pass
    return _windows_fonts

def choose_windows_font(self,context):
    if self.windows_font=='BUILTIN': self.brand_font=None
    else:
        font=bpy.data.fonts.load(self.windows_font,check_existing=True)
        font.pack(); self.brand_font=font

def camera_changed(scene,depsgraph):
    if not hasattr(scene,'bcgi_labs'): return
    p=scene.bcgi_labs
    if p.studio_root and p.follow_camera and scene.camera and p.studio_root.get('bcgi_follow_camera')!=scene.camera.name:
        follow(p,bpy.context,p.studio_root)

def follow(p,context,root):
    camera=context.scene.camera
    bound=root.get('bcgi_follow_camera','')
    if not p.follow_camera or not camera:
        if bound:
            matrix=root.matrix_world.copy()
            for index in (0,1): root.driver_remove('location',index)
            root.driver_remove('rotation_euler',2)
            root.matrix_world=matrix; root['bcgi_follow_camera']=''
        return
    if bound==camera.name: return
    cam=camera.matrix_world
    for path,index,channel,value in [('location',0,'LOC_X',cam.translation.x),('location',1,'LOC_Y',cam.translation.y),('rotation_euler',2,'ROT_Z',cam.to_euler('XYZ').z)]:
        curve=root.driver_add(path,index); driver=curve.driver; driver.type='SCRIPTED'
        while driver.variables: driver.variables.remove(driver.variables[0])
        var=driver.variables.new(); var.name='camera'; var.type='TRANSFORMS'
        target=var.targets[0]; target.id=camera; target.transform_type=channel; target.transform_space='WORLD_SPACE'
        offset=getattr(root,path)[index]-value
        driver.expression='camera + '+repr(offset)
    root['bcgi_follow_camera']=camera.name

def update(self, context):
    root=self.studio_root
    if not root: return
    root.scale=(self.studio_size,)*3
    follow(self,context,root)
    for c in root.users_collection:
        c.hide_viewport=not self.infinity_enabled; c.hide_render=not self.infinity_enabled
    world=bpy.data.worlds.get(root.get('studio_world',''))
    if world:
        world.node_tree.nodes['BCGI_Sky'].inputs['Color'].default_value=(*self.studio_color,1)
        world.node_tree.nodes['BCGI_Sky'].inputs['Strength'].default_value=self.studio_brightness*self.background_power
        if world.node_tree.nodes.get('BCGI_SkyGradient'):
            wn=world.node_tree.nodes
            wn['BCGI_SkyGradient'].color_ramp.elements[0].color=(*self.glow_color,1)
            wn['BCGI_SkyGradient'].color_ramp.elements[1].color=(*self.studio_color,1)
            wn['BCGI_SkyCenter'].inputs[1].default_value=(.5+self.glow_x,.3+self.glow_height,0)
            wn['BCGI_SkySpread'].inputs[1].default_value=(1/self.glow_spread,1/self.glow_spread,0)
        context.scene.world=world if self.infinity_enabled else self.original_world
    mat=bpy.data.materials.get(root.get('gradient_material',''))
    if mat:
        n=mat.node_tree.nodes
        n['BCGI_Gradient'].color_ramp.elements[0].color=(*self.glow_color,1)
        n['BCGI_Gradient'].color_ramp.elements[1].color=(*self.studio_color,1)
        n['BCGI_GlowCenter'].inputs[1].default_value=(.5+self.glow_x,.3+self.glow_height,0)
        n['BCGI_GlowSpread'].inputs[1].default_value=(1/self.glow_spread,1/self.glow_spread,0)
        n['BCGI_Brightness'].inputs['Strength'].default_value=self.studio_brightness*self.background_power
        n['BCGI_ShadowStrength'].inputs[0].default_value=self.shadow_strength
        if n.get('BCGI_ContactShadowMix'): n['BCGI_ContactShadowMix'].inputs[0].default_value=self.shadow_strength
        n['BCGI_GridScale'].inputs[3].default_value=self.studio_size/self.grid_spacing
        for name in ('BCGI_GridLineX','BCGI_GridLineY'):
            n[name].inputs[1].default_value=min(.45,self.grid_width/(2*self.grid_spacing))
        n['BCGI_GridOpacity'].inputs[1].default_value=self.grid_opacity if self.grid_enabled else 0
        n['BCGI_GridColor'].inputs[2].default_value=(*self.grid_color,1)
    for o in root.children:
        if o.get('bcgi_floor_brand'):
            visible=self.show_brand and self.brand_mode=='TEXT'
            o.hide_render=not visible
            o.hide_viewport=not visible
            o.data.body=self.brand_text
            o.data.size=self.brand_size/self.studio_size
            o.data.font=self.brand_font or bpy.data.fonts.get(o.get('bcgi_default_font','')) or o.data.font
            o.location=(self.brand_x/self.studio_size,self.brand_y/self.studio_size,.0003)
            o.rotation_euler.z=self.brand_rotation
            o.data.materials[0].node_tree.nodes['BCGI_BrandColor'].inputs['Color'].default_value=(*self.brand_color,1)
        if o.get('bcgi_floor_logo'):
            visible=self.show_brand and self.brand_mode=='LOGO' and self.logo_image is not None
            o.hide_render=not visible; o.hide_viewport=not visible
            image=self.logo_image
            ratio=image.size[1]/max(image.size[0],1) if image else 1
            o.scale=(self.logo_width/self.studio_size,self.logo_width*ratio/self.studio_size,1)
            o.location=(self.brand_x/self.studio_size,self.brand_y/self.studio_size,.0004)
            o.rotation_euler.z=self.brand_rotation
            nodes=o.data.materials[0].node_tree.nodes
            nodes['BCGI_LogoImage'].image=image or bpy.data.images.get(root.get('logo_placeholder',''))
            nodes['BCGI_LogoTint'].inputs[2].default_value=(*self.brand_color,1)
        if o.get('bcgi_studio_light'):
            o.data.energy=o['bcgi_studio_light']*(self.studio_size/10)**2*self.background_power
    if self.character_root:
        for o in self.character_root.children:
            if o.type=='LIGHT': o.data.energy=o.get('bcgi_character_power',1000)*self.character_power

def rebuild_gradient(root,mat):
    tree=mat.node_tree; tree.nodes.clear()
    def node(typ,name,x,y):
        n=tree.nodes.new(typ); n.name=name; n.label=name.replace('BCGI_',''); n.location=(x,y); return n
    tex=node('ShaderNodeTexCoord','BCGI_LocalCoordinates',-800,100); tex.object=root
    center=node('ShaderNodeVectorMath','BCGI_GlowCenter',-600,100); center.operation='SUBTRACT'
    spread=node('ShaderNodeVectorMath','BCGI_GlowSpread',-400,100); spread.operation='MULTIPLY'
    length=node('ShaderNodeVectorMath','BCGI_Distance',-200,100); length.operation='LENGTH'
    ramp=node('ShaderNodeValToRGB','BCGI_Gradient',0,100)
    ramp.color_ramp.interpolation='EASE'
    ramp.color_ramp.elements[0].position=0
    ramp.color_ramp.elements[1].position=1
    emission=node('ShaderNodeEmission','BCGI_Brightness',300,150)
    diffuse=node('ShaderNodeBsdfDiffuse','BCGI_GroundShadows',300,-50)
    diffuse.inputs['Roughness'].default_value=1
    mix=node('ShaderNodeMixShader','BCGI_ShadowStrength',550,100)
    output=node('ShaderNodeOutputMaterial','BCGI_Output',800,100)
    scale=node('ShaderNodeVectorMath','BCGI_GridScale',-600,-200); scale.operation='SCALE'
    axes=node('ShaderNodeSeparateXYZ','BCGI_GridAxes',-400,-200)
    local_axes=node('ShaderNodeSeparateXYZ','BCGI_LocalAxes',-600,-650)
    floor=node('ShaderNodeMath','BCGI_FloorOnly',-400,-650); floor.operation='LESS_THAN'; floor.inputs[1].default_value=.0001
    for suffix,axis in [('X','X'),('Y','Y')]:
        wave=node('ShaderNodeMath','BCGI_GridRepeat'+suffix,-200,-200 if axis=='X' else -400)
        wave.operation='PINGPONG'; wave.inputs[1].default_value=.5
        line=node('ShaderNodeMath','BCGI_GridLine'+suffix,0,-200 if axis=='X' else -400); line.operation='LESS_THAN'
        tree.links.new(axes.outputs[axis],wave.inputs[0]); tree.links.new(wave.outputs[0],line.inputs[0])
    maximum=node('ShaderNodeMath','BCGI_GridLines',200,-350); maximum.operation='MAXIMUM'
    floor_mask=node('ShaderNodeMath','BCGI_GridFloor',350,-350); floor_mask.operation='MULTIPLY'
    opacity=node('ShaderNodeMath','BCGI_GridOpacity',500,-350); opacity.operation='MULTIPLY'
    color=node('ShaderNodeMixRGB','BCGI_GridColor',700,-250)
    for a,b in [(tex.outputs['Object'],scale.inputs[0]),(scale.outputs[0],axes.inputs[0]),
                (tex.outputs['Object'],local_axes.inputs[0]),(local_axes.outputs['Z'],floor.inputs[0]),
                (tree.nodes['BCGI_GridLineX'].outputs[0],maximum.inputs[0]),(tree.nodes['BCGI_GridLineY'].outputs[0],maximum.inputs[1]),
                (maximum.outputs[0],floor_mask.inputs[0]),(floor.outputs[0],floor_mask.inputs[1]),
                (floor_mask.outputs[0],opacity.inputs[0]),(opacity.outputs[0],color.inputs[0]),(ramp.outputs['Color'],color.inputs[1])]:
        tree.links.new(a,b)
    for a,b in [(tex.outputs['Window'],center.inputs[0]),(center.outputs[0],spread.inputs[0]),
                (spread.outputs[0],length.inputs[0]),(length.outputs['Value'],ramp.inputs[0]),
                (color.outputs[0],emission.inputs['Color']),(color.outputs[0],diffuse.inputs['Color']),
                (emission.outputs[0],mix.inputs[1]),(diffuse.outputs[0],mix.inputs[2]),(mix.outputs[0],output.inputs['Surface'])]:
        tree.links.new(a,b)
    # One screen-space field for every camera-visible studio surface. Local AO
    # adds contact shading without making floor and wall respond differently to lights.
    ao=node('ShaderNodeAmbientOcclusion','BCGI_ContactAO',850,-400)
    ao.inputs['Distance'].default_value=.5
    shadow=node('ShaderNodeMixRGB','BCGI_ContactShadow',1050,-350); shadow.blend_type='MULTIPLY'; shadow.inputs[0].default_value=1
    shadow_mix=node('ShaderNodeMixRGB','BCGI_ContactShadowMix',1250,-300)
    for a,b in [(color.outputs[0],shadow.inputs[1]),(ao.outputs['AO'],shadow.inputs[2]),
                (color.outputs[0],shadow_mix.inputs[1]),(shadow.outputs[0],shadow_mix.inputs[2]),
                (shadow_mix.outputs[0],emission.inputs['Color'])]: tree.links.new(a,b)
    ray=node('ShaderNodeLightPath','BCGI_BackgroundIsolation',1000,0)
    dark=node('ShaderNodeBsdfDiffuse','BCGI_NoIndirectEmission',1000,-150); dark.inputs['Color'].default_value=(0,0,0,1)
    isolate=node('ShaderNodeMixShader','BCGI_CameraOnlyGradient',1250,0)
    for a,b in [(ray.outputs['Is Camera Ray'],isolate.inputs[0]),(dark.outputs[0],isolate.inputs[1]),(emission.outputs[0],isolate.inputs[2]),(isolate.outputs[0],output.inputs['Surface'])]: tree.links.new(a,b)

def make(context):
    p=context.scene.bcgi_labs
    if p.studio_root and p.studio_root.name in context.scene.objects:
        update(p,context); return p.studio_root
    c=bpy.data.collections.new('BCGI_Infinite_Studio')
    c['bcgi_labs']=True; context.scene.collection.children.link(c)
    root=bpy.data.objects.new('BCGI_Infinite_Studio_Control',None); c.objects.link(root)
    root['bcgi_infinite_studio']=True
    root.location=context.scene.cursor.location
    active=context.active_object
    if active and active.type=='MESH' and not active.name.startswith('BCGI_'):
        bounds=[active.matrix_world@Vector(v) for v in active.bound_box]
        root.location=(active.matrix_world.translation.x,active.matrix_world.translation.y,min(v.z for v in bounds))
    camera=context.scene.camera
    if camera:
        direction=camera.matrix_world.translation-root.location
        if Vector((direction.x,direction.y,0)).length>.001:
            root.rotation_euler.z=math.atan2(direction.x,-direction.y)
    profile=[(-4,0),(.65,0)]
    for i in range(1,65):
        angle=math.pi/2*i/64
        profile.append((.65+.35*math.sin(angle),.35*(1-math.cos(angle))))
    profile.append((1,3))
    # Enclosed 360-degree cove: disk floor, circular curved walls and ceiling.
    rings=[(4,0)]+[(4+math.sin(math.pi/2*i/64),1-math.cos(math.pi/2*i/64)) for i in range(1,65)]+[(5,5)]
    segments=128
    verts=[(0,0,0)]+[(r*math.cos(2*math.pi*j/segments),r*math.sin(2*math.pi*j/segments),z) for r,z in rings for j in range(segments)]
    faces=[(0,1+j,1+(j+1)%segments) for j in range(segments)]
    for i in range(len(rings)-1):
        for j in range(segments):
            a=1+i*segments+j; b=1+i*segments+(j+1)%segments
            faces.append((a,a+segments,b+segments,b))
    ceiling=len(verts); verts.append((0,0,5))
    last=1+(len(rings)-1)*segments
    faces.extend((ceiling,last+(j+1)%segments,last+j) for j in range(segments))
    mesh=bpy.data.meshes.new('BCGI_Continuous_Floor_Backdrop'); mesh.from_pydata(verts,[],faces); mesh.update()
    o=bpy.data.objects.new('BCGI_Gradient_Cyclorama',mesh); c.objects.link(o); o.parent=root
    for poly in mesh.polygons: poly.use_smooth=True
    mat=bpy.data.materials.new('BCGI_Infinite_Gradient'); mat.use_nodes=True
    mesh.materials.append(mat); root['gradient_material']=mat.name
    rebuild_gradient(root,mat)
    text=bpy.data.curves.new('BCGI_Floor_Brand','FONT'); text.align_x='CENTER'; text.size=.05
    brand=bpy.data.objects.new('BCGI_Floor_Brand',text); c.objects.link(brand); brand.parent=root
    brand.location=(0,-.32,.0003)
    white=bpy.data.materials.new('BCGI_Brand_White'); white.use_nodes=True; white.node_tree.nodes.clear()
    bsdf=white.node_tree.nodes.new('ShaderNodeEmission'); bsdf.name='BCGI_BrandColor'
    output=white.node_tree.nodes.new('ShaderNodeOutputMaterial'); white.node_tree.links.new(bsdf.outputs[0],output.inputs['Surface'])
    text.materials.append(white); brand['bcgi_floor_brand']=True; brand['bcgi_default_font']=text.font.name
    logo_mesh=bpy.data.meshes.new('BCGI_Logo_Plane'); logo_mesh.from_pydata([(-.5,-.5,0),(.5,-.5,0),(.5,.5,0),(-.5,.5,0)],[],[(0,1,2,3)])
    uv=logo_mesh.uv_layers.new()
    for loop,co in zip(uv.data,[(0,0),(1,0),(1,1),(0,1)]): loop.uv=co
    logo=bpy.data.objects.new('BCGI_Floor_PNG_Logo',logo_mesh); c.objects.link(logo); logo.parent=root; logo['bcgi_floor_logo']=True
    lm=bpy.data.materials.new('BCGI_Transparent_Logo'); lm.use_nodes=True; lm.node_tree.nodes.clear(); ln=lm.node_tree.nodes; ll=lm.node_tree.links
    placeholder=bpy.data.images.new('BCGI_Transparent_Placeholder',width=1,height=1,alpha=True)
    placeholder.pixels=[1,1,1,0]; placeholder.pack(); root['logo_placeholder']=placeholder.name
    image=ln.new('ShaderNodeTexImage'); image.name='BCGI_LogoImage'; image.image=placeholder
    tint=ln.new('ShaderNodeMixRGB'); tint.name='BCGI_LogoTint'; tint.blend_type='MULTIPLY'; tint.inputs[0].default_value=1
    emit=ln.new('ShaderNodeEmission'); transparent=ln.new('ShaderNodeBsdfTransparent'); mix=ln.new('ShaderNodeMixShader'); out=ln.new('ShaderNodeOutputMaterial')
    for a,b in [(image.outputs['Color'],tint.inputs[1]),(tint.outputs[0],emit.inputs['Color']),(image.outputs['Alpha'],mix.inputs[0]),(transparent.outputs[0],mix.inputs[1]),(emit.outputs[0],mix.inputs[2]),(mix.outputs[0],out.inputs['Surface'])]: ll.new(a,b)
    logo_mesh.materials.append(lm)
    self_world=context.scene.world
    p.original_world=self_world
    world=bpy.data.worlds.new('BCGI_Infinity_Sky'); world.use_nodes=True
    sky=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND'); sky.name='BCGI_Sky'
    tree=world.node_tree
    coords=tree.nodes.new('ShaderNodeTexCoord')
    center=tree.nodes.new('ShaderNodeVectorMath'); center.name='BCGI_SkyCenter'; center.operation='SUBTRACT'
    spread=tree.nodes.new('ShaderNodeVectorMath'); spread.name='BCGI_SkySpread'; spread.operation='MULTIPLY'
    length=tree.nodes.new('ShaderNodeVectorMath'); length.operation='LENGTH'
    ramp=tree.nodes.new('ShaderNodeValToRGB'); ramp.name='BCGI_SkyGradient'; ramp.color_ramp.interpolation='EASE'
    for a,b in [(coords.outputs['Window'],center.inputs[0]),(center.outputs[0],spread.inputs[0]),
                (spread.outputs[0],length.inputs[0]),(length.outputs['Value'],ramp.inputs[0]),(ramp.outputs['Color'],sky.inputs['Color'])]: tree.links.new(a,b)
    path=tree.nodes.new('ShaderNodeLightPath'); dark=tree.nodes.new('ShaderNodeBackground'); dark.inputs['Strength'].default_value=0
    mix=tree.nodes.new('ShaderNodeMixShader'); output=next(n for n in tree.nodes if n.type=='OUTPUT_WORLD')
    for a,b in [(path.outputs['Is Camera Ray'],mix.inputs[0]),(dark.outputs[0],mix.inputs[1]),(sky.outputs[0],mix.inputs[2]),(mix.outputs[0],output.inputs['Surface'])]: tree.links.new(a,b)
    root['studio_world']=world.name
    for name,loc,power,size in [('Key',(-.3,-.4,.6),1000,.3),('Fill',(.3,-.2,.5),300,.5)]:
        light=bpy.data.lights.new('BCGI_Infinite_'+name,'AREA'); light.size=size
        lamp=bpy.data.objects.new(light.name,light); c.objects.link(lamp); lamp.parent=root; lamp.location=loc
        lamp.rotation_euler=(Vector((0,0,.1))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
        lamp['bcgi_studio_light']=power
        lamp.light_linking.receiver_collection=c
    if not p.brand_font:
        font=os.path.join(os.environ.get('WINDIR','C:/Windows'),'Fonts','segoeui.ttf')
        if os.path.isfile(font): p.windows_font=font
    p.studio_root=root; update(p,context)
    return root

class BCGI_OT_infinite_studio(bpy.types.Operator):
    bl_idname='bcgi.infinite_studio'; bl_label='Add / Update Infinite Studio'
    bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        make(context)
        self.report({'INFO'},'Infinite studio ready. Controls update its appearance live.')
        return {'FINISHED'}

class BCGI_OT_load_logo(bpy.types.Operator,ImportHelper):
    bl_idname='bcgi.load_logo'; bl_label='Load PNG Logo'; bl_options={'REGISTER','UNDO'}
    filename_ext='.png'
    filter_glob: StringProperty(default='*.png',options={'HIDDEN'})
    def execute(self,context):
        image=bpy.data.images.load(self.filepath,check_existing=True); image.pack()
        context.scene.bcgi_labs.logo_image=image; context.scene.bcgi_labs.brand_mode='LOGO'
        return {'FINISHED'}

class BCGI_OT_load_font(bpy.types.Operator,ImportHelper):
    bl_idname='bcgi.load_font'; bl_label='Load Font'; bl_options={'REGISTER','UNDO'}
    filename_ext='.ttf'
    filter_glob: StringProperty(default='*.ttf;*.otf',options={'HIDDEN'})
    def execute(self,context):
        font=bpy.data.fonts.load(self.filepath,check_existing=True)
        if hasattr(font,'pack'): font.pack()
        context.scene.bcgi_labs.brand_font=font
        return {'FINISHED'}

class BCGI_OT_character_lights(bpy.types.Operator):
    bl_idname='bcgi.character_lights'; bl_label='Add Lights for Selected Character'; bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        meshes=set()
        for selected in context.selected_objects:
            meshes.update(o for o in [selected]+list(selected.children_recursive) if o.type=='MESH' and not o.name.startswith('BCGI_'))
        if not meshes:
            self.report({'ERROR'},'Select the character mesh or its armature first.'); return {'CANCELLED'}
        bounds=[o.matrix_world@Vector(v) for o in meshes for v in o.bound_box]
        center=sum(bounds,Vector())/len(bounds); size=max(max(v[i] for v in bounds)-min(v[i] for v in bounds) for i in range(3))
        size=max(size,.1)
        collection=bpy.data.collections.new('BCGI_Character_Lighting'); context.scene.collection.children.link(collection)
        receivers=bpy.data.collections.new('BCGI_Character_Light_Receivers')
        for o in meshes: receivers.objects.link(o)
        rig=bpy.data.objects.new('BCGI_Character_Light_Control',None); collection.objects.link(rig); rig.location=center
        for name,offset,power in [('Key',(-1,-1,1.4),600),('Fill',(1,-.6,.6),250),('Rim',(.3,1,1.2),800)]:
            data=bpy.data.lights.new('BCGI_Character_'+name,'AREA'); data.size=size*.8
            o=bpy.data.objects.new(data.name,data); collection.objects.link(o); o.parent=rig; o.location=Vector(offset)*size
            o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
            o['bcgi_character_power']=power*size*size; data.energy=o['bcgi_character_power']*context.scene.bcgi_labs.character_power
            o.light_linking.receiver_collection=receivers
        context.scene.bcgi_labs.character_root=rig
        return {'FINISHED'}
