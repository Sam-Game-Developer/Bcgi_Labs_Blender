import bpy,bcgi_labs,json
from types import SimpleNamespace
from pathlib import Path
s=bcgi_labs.shelf._instances[0]; area=s.area; region=s.region
def event(kind,value,x,y): return SimpleNamespace(type=kind,value=value,mouse_x=x+region.x,mouse_y=y+region.y)
checks={}
with bpy.context.temp_override(area=area,region=region):
    for mode in ('TOP','BOTTOM','RIGHT','FLOAT'):
        s.action(mode,bpy.context); x,y,w,h=s.bounds()
        assert x>=0 and y>=0 and x+w<=region.width and y+h<=region.height
    checks['dock_bounds']=True
    s.action('RESET',bpy.context)
    old=s.bounds(); s.action('MAX',bpy.context); assert s.bounds()[2]>=old[2]
    s.action('MAX',bpy.context); assert s.bounds()==old
    checks['maximize_restore']=True
    s.action('MIN',bpy.context); assert s.bounds()[3]==42
    s.action('MIN',bpy.context); checks['minimize_restore']=True
    x,y,w,h=s.bounds(); s.mouse=(x+w-8,y+8); s.action('RESIZE',bpy.context)
    s.modal(bpy.context,event('MOUSEMOVE','NOTHING',x+w-170,y-55))
    s.modal(bpy.context,event('LEFTMOUSE','RELEASE',x+w-170,y-55))
    assert s.width<old[2] and s.height>old[3] and not s.resize
    assert bpy.context.scene.bcgi_labs.shelf_width==s.width
    checks['simulated_resize_and_persistence']=True
    s.action('TAB:CAMERA',bpy.context); assert s.tab=='CAMERA'
    s.action('TAB:EFFECTS',bpy.context); assert s.tab=='EFFECTS'
    checks['two_tabs']=True
    assert s.modal(bpy.context,event('LEFTMOUSE','PRESS',-10,-10))=={'PASS_THROUGH'}
    checks['outside_click_pass_through']=True
    s.action('RESET',bpy.context); bpy.context.scene.bcgi_labs.top_preset='GLOW'
    s.finish(); assert not bcgi_labs.shelf._instances and s.handle is None and s.timer is None
    bpy.ops.bcgi.shelf('INVOKE_DEFAULT'); checks['close_reopen_cleanup']=True
    assert 'brand' in bcgi_labs.shelf._instances[0].textures
    checks['live_previews_loaded']=True
Path(r'C:\Users\Samsul Alam Niom\Documents\ChatGPT\Blender\glass_live_verification.json').write_text(json.dumps(checks,indent=2)); print(json.dumps(checks))
