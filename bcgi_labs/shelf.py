"""Persistent viewport preset shelf with bounded floating and edge placement."""
import math, os
import bpy, gpu, blf
from gpu_extras.batch import batch_for_shader

_instances=[]

def stop_all():
    for shelf in list(_instances): shelf.finish()

def rect(x,y,w,h,color,r=0):
    if w<=0 or h<=0: return
    r=min(r,w/2,h/2)
    verts=[]
    for cx,cy,start in ((x+w-r,y+h-r,0),(x+r,y+h-r,90),(x+r,y+r,180),(x+w-r,y+r,270)):
        for step in range(7):
            a=math.radians(start+step*15)
            verts.append((cx+r*math.cos(a),cy+r*math.sin(a)))
    shader=gpu.shader.from_builtin('UNIFORM_COLOR')
    shader.bind(); shader.uniform_float('color',color)
    batch_for_shader(shader,'TRI_FAN',{'pos':verts}).draw(shader)

def text(value,x,y,size=12,color=(.88,.94,1,1)):
    blf.size(0,size); blf.position(0,x,y,0); blf.color(0,*color); blf.draw(0,value)

def image_texture(texture,x,y,w,h):
    shader=gpu.shader.from_builtin('IMAGE')
    shader.bind(); shader.uniform_sampler('image',texture)
    batch_for_shader(shader,'TRI_FAN',{'pos':[(x,y),(x+w,y),(x+w,y+h),(x,y+h)],'texCoord':[(0,0),(1,0),(1,1),(0,1)]}).draw(shader)

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
        self.minimized=False; self.drag=None; self.moving=False; self.closed=False; self.page=0
        self.buttons=[]; self.status='Select an object, then click a preset'; self.textures={}
        from .top_library import IDS
        for name in ('brand',)+IDS:
            path=os.path.join(os.path.dirname(__file__),'assets','BCGI.png' if name=='brand' else 'presets/'+name+'.png')
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
        width=max(60,min(1020,available-24))
        if self.dock=='RIGHT': width=min(370,width)
        height=42 if self.minimized else (320 if self.dock=='RIGHT' or width<420 else 180)
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
            x,y,w,h=self.bounds(); self.buttons=[]
            rect(x+2,y-4,w,h,(.01,.03,.06,.28),16)
            rect(x,y,w,h,(.055,.105,.16,.95),16)
            rect(x+1,y+h-40,w-2,39,(.18,.29,.39,.78),15)
            if 'brand' in self.textures: image_texture(self.textures['brand'],x+12,y+h-33,26,26)
            text('BCGI LABS',x+46,y+h-26,13)
            def button(label,bx,by,bw,bh,action,selected=False):
                rect(bx,by,bw,bh,(.14,.43,.53,.9) if selected else (.14,.21,.29,.95),7)
                text(label,bx+7,by+9,11)
                self.buttons.append((bx,by,bw,bh,action))
            # All actions remain accessible at small widths through a second row.
            labels=[('Dock','TOP',43),('Float','FLOAT',45),('Move','MOVE',45),('−' if not self.minimized else '+','MIN',25),('×','CLOSE',25)]
            if w>=420:
                bx=x+w-sum(a[2]+4 for a in labels)-8
                for label,action,bw in labels:
                    button(label,bx,y+h-34,bw,28,action,self.dock==action); bx+=bw+4
            else:
                button('−' if not self.minimized else '+',x+w-66,y+h-34,25,28,'MIN')
                button('×',x+w-35,y+h-34,25,28,'CLOSE')
            if self.minimized: return
            by=y+h-72
            actions=[('Top','TOP'),('Bottom','BOTTOM'),('Right','RIGHT'),('Reset','RESET')]
            if w<420: actions += [('Float','FLOAT'),('Move','MOVE')]
            action_cols=max(2,min(len(actions),int((w-24)/55)))
            for i,(label,action) in enumerate(actions):
                button(label,x+12+(i%action_cols)*((w-24)/action_cols),by-(i//action_cols)*28,(w-24)/action_cols-4,24,action,self.dock==action)
            by-=((len(actions)-1)//action_cols)*28
            from .top_library import IDS
            cols=max(1,int((w-24)/92)); rows=2 if self.dock=='RIGHT' or w<420 else 1
            count=cols*rows; max_page=max(0,(len(IDS)-1)//count); self.page=min(self.page,max_page)
            for index,kind in enumerate(IDS[self.page*count:(self.page+1)*count]):
                col=index%cols; row=index//cols; bw=(w-24)/cols-5
                cx=x+12+col*(bw+5); cy=by-80-row*82
                button('',cx,cy,bw,74,'FX:'+kind,self.window.scene.bcgi_labs.top_preset==kind)
                if kind in self.textures: image_texture(self.textures[kind],cx+(bw-44)/2,cy+25,44,44)
                label=kind.replace('WRITE_','').replace('_',' ').title()
                text(label[:14],cx+5,cy+9,10)
            button('<',x+w-64,y+7,24,23,'PREV')
            button('>',x+w-35,y+7,24,23,'NEXT')
            text(self.status[:max(12,int((w-90)/6))],x+12,y+14,10,(.69,.82,.91,1))
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
        elif action=='MOVE': self.moving=True; self.status='Drag the title bar to move; Esc cancels'
        elif action in ('TOP','BOTTOM','RIGHT','FLOAT'): self.dock=action
        elif action=='RESET': self.dock='TOP'; self.fx=24; self.fy=80; self.minimized=False
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
        x,y,w,h=self.bounds(); inside=x<=mx<=x+w and y<=my<=y+h
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
        if inside and event.type in ('WHEELUPMOUSE','WHEELDOWNMOUSE'):
            self.page=max(0,self.page+(-1 if event.type=='WHEELUPMOUSE' else 1)); self.area.tag_redraw(); return {'RUNNING_MODAL'}
        return {'PASS_THROUGH'}

classes=(BCGI_OT_shelf,)
