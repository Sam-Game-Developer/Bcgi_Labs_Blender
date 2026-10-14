"""Persistent viewport preset shelf with bounded floating and edge placement."""
import math, os
import bpy, gpu, blf
from gpu_extras.batch import batch_for_shader

_instances=[]
EFFECTS=('WAVE','SCATTER','TWIST','PULSE','SCAN','GLOW','XRAY','GLOW_RING')

def redraw(self,context):
    if context:
        for area in context.screen.areas if context.screen else []:
            if area.type=='VIEW_3D': area.tag_redraw()

def stop_all():
    for shelf in list(_instances): shelf.finish()

def corners(x,y,w,h,r):
    r=min(r,w/2,h/2)
    return [(cx+r*math.cos(math.radians(start+step*15)),cy+r*math.sin(math.radians(start+step*15)))
            for cx,cy,start in ((x+w-r,y+h-r,0),(x+r,y+h-r,90),(x+r,y+r,180),(x+w-r,y+r,270)) for step in range(7)]

def rect(x,y,w,h,color,r=0,top=None):
    if w<=0 or h<=0: return
    gpu.state.blend_set('ALPHA')
    verts=corners(x,y,w,h,r)
    if top:
        shader=gpu.shader.from_builtin('SMOOTH_COLOR'); shader.bind()
        colors=[tuple(color[i]+(top[i]-color[i])*(vy-y)/h for i in range(4)) for vx,vy in verts]
        batch_for_shader(shader,'TRI_FAN',{'pos':verts,'color':colors}).draw(shader)
    else:
        shader=gpu.shader.from_builtin('UNIFORM_COLOR'); shader.bind(); shader.uniform_float('color',color)
        batch_for_shader(shader,'TRI_FAN',{'pos':verts}).draw(shader)

def lines(points,color):
    shader=gpu.shader.from_builtin('UNIFORM_COLOR'); shader.bind(); shader.uniform_float('color',color)
    batch_for_shader(shader,'LINES',{'pos':points}).draw(shader)

def window_icon(action,x,y,color):
    def frame(a,b):
        return [(a,b),(a+12,b),(a+12,b),(a+12,b+11),(a+12,b+11),(a,b+11),(a,b+11),(a,b)]
    if action=='CLOSE': points=[(x,y),(x+11,y+11),(x+11,y),(x,y+11)]
    elif action=='MIN': points=[(x,y+5),(x+12,y+5)]
    elif action=='MAX': points=frame(x,y)
    elif action=='FLOAT': points=frame(x,y)+frame(x+4,y+4)
    else: points=frame(x,y)+[(x,y+8),(x+12,y+8)]
    lines(points,color)

def text(value,x,y,size=12,color=(.88,.94,1,1)):
    blf.size(0,size); blf.position(0,x,y,0); blf.color(0,*color); blf.draw(0,value)

def image_texture(texture,x,y,w,h,r=0):
    gpu.state.blend_set('ALPHA_PREMULT')
    shader=gpu.shader.from_builtin('IMAGE')
    shader.bind(); shader.uniform_sampler('image',texture)
    verts=corners(x,y,w,h,r)
    batch_for_shader(shader,'TRI_FAN',{'pos':verts,'texCoord':[((vx-x)/w,(vy-y)/h) for vx,vy in verts]}).draw(shader)
    gpu.state.blend_set('ALPHA')

def appearance(layout,p):
    for prop in ('glass_opacity','glass_tint','glass_accent','glass_glow','card_top','card_bottom','card_radius'):
        layout.prop(p,prop)
    layout.operator('bcgi.reset_appearance')

class BCGI_OT_appearance(bpy.types.Operator):
    bl_idname='bcgi.appearance'; bl_label='BCGI LABS Appearance'
    def invoke(self,context,event): return context.window_manager.invoke_popup(self,width=300)
    def execute(self,context): return {'FINISHED'}
    def draw(self,context): appearance(self.layout,context.scene.bcgi_labs)

class BCGI_OT_reset_appearance(bpy.types.Operator):
    bl_idname='bcgi.reset_appearance'; bl_label='Reset Appearance'; bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        p=context.scene.bcgi_labs
        for key,value in {'glass_opacity':.86,'glass_tint':(.025,.07,.12),'glass_accent':(.02,.72,1),'glass_glow':.6,'card_top':(.05,.6,.95),'card_bottom':(.015,.20,.62),'card_radius':14}.items(): setattr(p,key,value)
        return {'FINISHED'}

class BCGI_OT_camera_controls(bpy.types.Operator):
    bl_idname='bcgi.camera_controls'; bl_label='Camera Overlay Controls'
    def invoke(self,context,event): return context.window_manager.invoke_popup(self,width=330)
    def execute(self,context): return {'FINISHED'}
    def draw(self,context):
        from . import camera_overlay
        camera_overlay.draw(self.layout,context.scene.bcgi_labs)

def poll_view(cls,context): return context.area is not None and context.area.type=='VIEW_3D'

class BCGI_OT_shelf(bpy.types.Operator):
    bl_idname='bcgi.shelf'; bl_label='BCGI LABS Dockable Library'
    @classmethod
    def poll(cls,context): return poll_view(cls,context)

    def invoke(self,context,event):
        for item in _instances:
            if item.area==context.area:
                item.minimized=False; item.dock='TOP'; item.save(); item.area.tag_redraw()
                return {'FINISHED'}
        self.area=context.area; self.window=context.window
        self.region=next(r for r in self.area.regions if r.type=='WINDOW')
        p=context.scene.bcgi_labs
        self.dock=p.shelf_dock; self.fx=p.shelf_x; self.fy=p.shelf_y
        self.width=p.shelf_width; self.height=p.shelf_height; self.right_width=p.shelf_right_width; self.right_height=p.shelf_right_height
        self.tab=p.shelf_tab; self.maximized=False; self.resize=None; self.hover=None
        self.minimized=False; self.drag=None; self.moving=False; self.closed=False; self.page=0
        self.buttons=[]; self.status='Select an object, then click a preset'; self.textures={}
        for name in ('brand',)+EFFECTS:
            path=os.path.join(os.path.dirname(__file__),'assets','BCGI.png' if name=='brand' else 'glass/'+name+'.png')
            if os.path.isfile(path):
                image=bpy.data.images.load(path,check_existing=True)
                self.textures[name]=gpu.texture.from_image(image)
        self.handle=bpy.types.SpaceView3D.draw_handler_add(self.draw_shelf,(),'WINDOW','POST_PIXEL')
        self.timer=context.window_manager.event_timer_add(.2,window=self.window)
        _instances.append(self); context.window_manager.modal_handler_add(self)
        self.area.tag_redraw()
        return {'RUNNING_MODAL'}

    def save(self):
        try:
            p=self.window.scene.bcgi_labs
            p.shelf_dock=self.dock; p.shelf_x=self.fx; p.shelf_y=self.fy
            p.shelf_width=self.width; p.shelf_height=self.height
            p.shelf_right_width=self.right_width; p.shelf_right_height=self.right_height; p.shelf_tab=self.tab
        except (ReferenceError,AttributeError): pass

    def bounds(self):
        left,right=0,self.region.width
        top=self.region.height
        area=getattr(self,'area',None)
        if area:
            for region in area.regions:
                if region.type in {'HEADER','TOOL_HEADER'}:
                    ry=region.y-self.region.y
                    if top/2<ry<top: top=ry
                if region.type in {'UI','TOOLS'} and region.width>1:
                    a=region.x-self.region.x; b=a+region.width
                    if a<=left<b: left=b
                    elif left<a<right: right=a
        available=max(80,right-left)
        width=max(60,min(self.right_width if self.dock=='RIGHT' else self.width,available-24))
        height=42 if self.minimized else max(220,self.right_height if self.dock=='RIGHT' else self.height)
        if width<560 and not self.minimized: height=max(320,height)
        if self.maximized and not self.minimized: width=available-24; height=top-24
        height=min(height,max(42,top-24))
        x=max(left+8,min(self.fx,right-width-8)); y=max(8,min(self.fy,top-height-8))
        if self.dock=='TOP': x=left+(available-width)/2; y=top-height-12
        elif self.dock=='BOTTOM': x=left+(available-width)/2; y=12
        elif self.dock=='RIGHT': x=right-width-12; y=top-height-12
        return x,y,width,height

    def draw_shelf(self):
        if self.closed or bpy.context.area!=self.area: return
        gpu.state.blend_set('ALPHA')
        try:
            x,y,w,h=self.bounds(); self.buttons=[]; p=self.window.scene.bcgi_labs
            tint=tuple(p.glass_tint); accent=tuple(p.glass_accent)
            for spread in (6,3,1): rect(x-spread,y-spread,w+2*spread,h+2*spread,(*accent,.035*p.glass_glow),18+spread)
            rect(x-1,y-1,w+2,h+2,(*accent,.4),18)
            rect(x,y,w,h,(*tint,p.glass_opacity),17,tuple(min(1,c+.07) for c in tint)+(p.glass_opacity,))
            if 'brand' in self.textures: image_texture(self.textures['brand'],x+12,y+h-34,27,27,7)
            text('BCGI LABS' if w>340 else 'BCGI',x+46,y+h-26,13)
            def button(label,bx,by,bw,bh,action,selected=False,icon=False):
                hover=self.hover==action
                if selected or hover:
                    rect(bx-1,by-1,bw+2,bh+2,(*accent,.65 if selected else .3),8)
                if not icon: rect(bx,by,bw,bh,(*tint,.95),7,(*accent,.65) if selected else (.10,.22,.34,.88))
                if icon: window_icon(action,bx+8,by+9,(1,.4,.4,1) if action=='CLOSE' and hover else (.83,.94,1,1))
                elif label: text(label,bx+8,by+9,11)
                self.buttons.append((bx,by,bw,bh,action))
            for i,action in enumerate(('DOCK','FLOAT','MIN','MAX','CLOSE')):
                button('',x+w-158+i*29,y+h-35,27,28,action,False,True)
            if self.minimized: return
            by=y+h-78
            button('Effects',x+12,by,70,28,'TAB:EFFECTS',self.tab=='EFFECTS')
            button('Camera',x+88,by,70,28,'TAB:CAMERA',self.tab=='CAMERA')
            button('Appearance',x+164,by,96,28,'LOOK')
            if self.tab=='EFFECTS':
                cols=max(1,min(len(EFFECTS),int((w-24)/120))); rows=max(1,int((h-112)/105))
                count=cols*rows; self.page=min(self.page,max(0,(len(EFFECTS)-1)//count))
                for index,kind in enumerate(EFFECTS[self.page*count:(self.page+1)*count]):
                    col=index%cols; row=index//cols; bw=(w-24)/cols-8; bh=96
                    cx=x+12+col*(bw+8); cy=by-106-row*105
                    selected=p.top_preset==kind; hover=self.hover=='FX:'+kind; r=p.card_radius
                    if selected or hover:
                        for spread in (4,2): rect(cx-spread,cy-spread,bw+2*spread,bh+2*spread,(*accent,(.14 if selected else .07)*p.glass_glow),r+spread)
                        rect(cx-1,cy-1,bw+2,bh+2,(*accent,.95),r+1)
                    rect(cx,cy,bw,bh,(*p.card_bottom,1),r,(*p.card_top,1))
                    if kind in self.textures: image_texture(self.textures[kind],cx,cy+22,bw,bh-22,r)
                    rect(cx,cy,bw,23,(*tint,.97),min(r,10))
                    label={'XRAY':'X-ray','GLOW_RING':'Glow Ring'}.get(kind,kind.title())
                    text(label,cx+8,cy+8,11)
                    self.buttons.append((cx,cy,bw,bh,'FX:'+kind))
                button('<',x+w-88,y+7,24,23,'PREV'); button('>',x+w-59,y+7,24,23,'NEXT')
            else:
                cam=p.overlay_camera or self.window.scene.camera
                text('Camera Overlay  ·  '+(cam.name if cam else 'Choose a camera'),x+16,by-27,12)
                gap=8; bw=min(145,(w-40)/3)
                for i,(label,action) in enumerate((('Choose PNG','PNG'),('Use Built-in','BUILTIN'),('Apply Overlay','APPLY_CAMERA'))):
                    button(label,x+12+i*(bw+gap),by-70,bw,30,action)
                button('Overlay On' if p.overlay_enabled else 'Overlay Off',x+12,by-109,105,28,'TOGGLE',p.overlay_enabled)
                button('Edit Controls',x+125,by-109,105,28,'CAMERA_CONTROLS')
                if w>520: text('Opacity '+str(round(p.overlay_opacity,2))+'  ·  Scale '+str(round(p.overlay_scale,2))+'  ·  '+p.overlay_fit,x+245,by-100,11)
            # Corner grip controls width and height; it stays visible on both tabs.
            lines([(x+w-18,y+5),(x+w-5,y+18),(x+w-12,y+5),(x+w-5,y+12)],(*accent,.9))
            self.buttons.append((x+w-25,y,25,25,'RESIZE'))
            text(self.status[:max(12,int((w-115)/6))],x+12,y+14,10,(.72,.85,.95,1))
            if self.hover:
                label={'DOCK':'Dock: top / bottom / right','FLOAT':'Float','MIN':'Minimize / restore','MAX':'Maximize / restore','CLOSE':'Close','RESIZE':'Drag to resize','LOOK':'Appearance settings'}.get(self.hover)
                if label:
                    tw=min(w-24,len(label)*6+16); rect(x+w-tw-12,y-27,tw,22,(.025,.05,.08,.97),6); text(label,x+w-tw-4,y-20,10)
        finally:
            gpu.state.blend_set('NONE')

    def finish(self):
        if self.closed: return
        self.closed=True
        if self in _instances: _instances.remove(self)
        if getattr(self,'handle',None):
            bpy.types.SpaceView3D.draw_handler_remove(self.handle,'WINDOW'); self.handle=None
        if getattr(self,'timer',None):
            bpy.context.window_manager.event_timer_remove(self.timer); self.timer=None
        try: self.area.tag_redraw()
        except ReferenceError: pass

    def cancel(self,context): self.finish()

    def action(self,action,context):
        if action=='CLOSE': self.finish(); return
        if action=='MIN': self.minimized=not self.minimized
        elif action=='MAX': self.maximized=not self.maximized
        elif action=='DOCK': self.dock={'TOP':'BOTTOM','BOTTOM':'RIGHT','RIGHT':'TOP','FLOAT':'TOP'}[self.dock]
        elif action.startswith('TAB:'): self.tab=action[4:]; self.page=0
        elif action=='RESIZE':
            self.maximized=False
            x,y,w,h=self.bounds(); mx,my=self.mouse
            self.resize=(mx,my,w,h,self.fx,self.fy,self.width,self.height,self.right_width,self.right_height)
        elif action in ('LOOK','CAMERA_CONTROLS','PNG','BUILTIN','APPLY_CAMERA','TOGGLE'):
            with context.temp_override(window=self.window,area=self.area,region=self.region):
                if action=='LOOK': bpy.ops.bcgi.appearance('INVOKE_DEFAULT')
                elif action=='CAMERA_CONTROLS': bpy.ops.bcgi.camera_controls('INVOKE_DEFAULT')
                elif action=='PNG': bpy.ops.bcgi.load_overlay('INVOKE_DEFAULT')
                elif action=='BUILTIN': bpy.ops.bcgi.builtin_overlay()
                elif action=='APPLY_CAMERA': bpy.ops.bcgi.camera_overlay()
                else: context.scene.bcgi_labs.overlay_enabled=not context.scene.bcgi_labs.overlay_enabled
        elif action=='MOVE': self.moving=True; self.status='Drag the title bar to move; Esc cancels'
        elif action in ('TOP','BOTTOM','RIGHT','FLOAT'): self.dock=action
        elif action=='RESET':
            self.dock='TOP'; self.fx=24; self.fy=80; self.minimized=False; self.maximized=False
            self.width=1120; self.height=230; self.right_width=370; self.right_height=340
        elif action in ('PREV','NEXT'): self.page=max(0,self.page+(-1 if action=='PREV' else 1))
        elif action.startswith('FX:'):
            kind=action[3:]
            with context.temp_override(window=self.window,area=self.area,region=self.region):
                p=context.scene.bcgi_labs; p.top_preset=kind
                try:
                    result=bpy.ops.bcgi.top_apply()
                    self.status=kind.replace('_',' ').title()+(' applied' if result=={'FINISHED'} else ': choose the correct object type')
                except RuntimeError: self.status='Select a mesh for FX or a curve for writing'
        self.save()

    def modal(self,context,event):
        if self.closed: return {'FINISHED'}
        if not any(a==self.area for a in self.window.screen.areas) or self.area.type!='VIEW_3D':
            self.finish(); return {'FINISHED'}
        if event.type=='TIMER': self.area.tag_redraw(); return {'PASS_THROUGH'}
        mx=event.mouse_x-self.region.x; my=event.mouse_y-self.region.y
        self.mouse=(mx,my)
        x,y,w,h=self.bounds(); inside=x<=mx<=x+w and y<=my<=y+h
        if self.resize:
            ox,oy,ow,oh,fx,fy,width,height,rw,rh=self.resize
            if event.type=='ESC' and event.value=='PRESS':
                self.fx,self.fy,self.width,self.height,self.right_width,self.right_height=fx,fy,width,height,rw,rh
                self.resize=None; self.save(); self.area.tag_redraw(); return {'RUNNING_MODAL'}
            if event.type=='MOUSEMOVE':
                nw=max(280,min(4000,ow+mx-ox)); nh=max(220,min(2500,oh-my+oy))
                if self.dock=='RIGHT': self.right_width=nw; self.right_height=nh
                else: self.width=nw; self.height=nh
                if self.dock=='FLOAT': self.fy=fy+oh-nh
                self.area.tag_redraw(); return {'RUNNING_MODAL'}
            if event.type=='LEFTMOUSE' and event.value=='RELEASE':
                self.resize=None; self.save(); self.area.tag_redraw(); return {'RUNNING_MODAL'}
            return {'RUNNING_MODAL'}
        if self.drag:
            if event.type=='ESC' and event.value=='PRESS':
                self.dock,self.fx,self.fy=self.drag[4:]; self.drag=None; self.moving=False; self.save(); self.area.tag_redraw(); return {'RUNNING_MODAL'}
            if event.type=='MOUSEMOVE':
                self.fx=self.drag[2]+mx-self.drag[0]; self.fy=self.drag[3]+my-self.drag[1]
                bx,by,_,_=self.bounds(); self.fx=bx; self.fy=by
                self.area.tag_redraw(); return {'RUNNING_MODAL'}
            if event.type=='LEFTMOUSE' and event.value=='RELEASE':
                if my>=self.region.height-30: self.dock='TOP'
                elif my<=30: self.dock='BOTTOM'
                elif mx>=self.region.width-30: self.dock='RIGHT'
                self.drag=None; self.moving=False; self.save(); self.area.tag_redraw(); return {'RUNNING_MODAL'}
            return {'RUNNING_MODAL'}
        if self.moving and event.type=='ESC' and event.value=='PRESS':
            self.moving=False; self.status='Move canceled'; self.area.tag_redraw(); return {'RUNNING_MODAL'}
        if event.type=='LEFTMOUSE' and event.value=='PRESS' and inside:
            if self.moving:
                self.drag=(mx,my,x,y,self.dock,self.fx,self.fy); self.dock='FLOAT'; self.fx=x; self.fy=y
                return {'RUNNING_MODAL'}
            for bx,by,bw,bh,action in self.buttons:
                if bx<=mx<=bx+bw and by<=my<=by+bh:
                    self.action(action,context); self.area.tag_redraw()
                    return {'FINISHED'} if self.closed else {'RUNNING_MODAL'}
            if my>=y+h-40:
                self.drag=(mx,my,x,y,self.dock,self.fx,self.fy); self.dock='FLOAT'; self.fx=x; self.fy=y
            return {'RUNNING_MODAL'}
        if event.type=='MOUSEMOVE':
            hover=next((a for bx,by,bw,bh,a in self.buttons if bx<=mx<=bx+bw and by<=my<=by+bh),None)
            if hover!=self.hover: self.hover=hover; self.area.tag_redraw()
        if inside and event.type in ('WHEELUPMOUSE','WHEELDOWNMOUSE'):
            self.page=max(0,self.page+(-1 if event.type=='WHEELUPMOUSE' else 1)); self.area.tag_redraw(); return {'RUNNING_MODAL'}
        return {'PASS_THROUGH'}

classes=(BCGI_OT_shelf,BCGI_OT_appearance,BCGI_OT_reset_appearance,BCGI_OT_camera_controls)
