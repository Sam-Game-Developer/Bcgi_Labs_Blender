import bpy,bcgi_labs,json
from pathlib import Path
from types import SimpleNamespace
module=bcgi_labs.shelf; module.stop_all()
area=max((a for a in bpy.context.screen.areas if a.type=='VIEW_3D'),key=lambda a:a.width*a.height)
region=next(r for r in area.regions if r.type=='WINDOW')
with bpy.context.temp_override(area=area,region=region):
    assert bpy.ops.bcgi.shelf('INVOKE_DEFAULT')=={'RUNNING_MODAL'}
    s=module._instances[0]
    checks={}
    for action in ('TOP','BOTTOM','RIGHT','FLOAT','RESET'):
        s.action(action,bpy.context); x,y,w,h=s.bounds()
        assert 0<=x and 0<=y and x+w<=region.width and y+h<=region.height
        checks[action+'_bounds']=True
    s.action('MIN',bpy.context); assert s.minimized and s.bounds()[3]==42
    s.action('MIN',bpy.context); assert not s.minimized
    checks['minimize_restore']=True
    x,y,w,h=s.bounds()
    def event(kind,value,mx,my): return SimpleNamespace(type=kind,value=value,mouse_x=mx+region.x,mouse_y=my+region.y)
    s.action('MOVE',bpy.context)
    assert s.modal(bpy.context,event('LEFTMOUSE','PRESS',x+55,y+h-20))=={'RUNNING_MODAL'}
    s.modal(bpy.context,event('MOUSEMOVE','NOTHING',x+95,y+h-75))
    s.modal(bpy.context,event('LEFTMOUSE','RELEASE',x+95,y+h-75))
    assert s.dock=='FLOAT' and not s.drag
    checks['simulated_move_events']=True
    assert s.modal(bpy.context,event('LEFTMOUSE','PRESS',-10,-10))=={'PASS_THROUGH'}
    assert s in module._instances
    checks['outside_click_keeps_open']=True
    s.fx=10000; s.fy=-10000; x,y,w,h=s.bounds()
    assert x+w<=region.width and y>=0
    checks['offscreen_clamp']=True
    s.action('RESET',bpy.context)
    assert bpy.ops.bcgi.shelf('INVOKE_DEFAULT')=={'FINISHED'} and len(module._instances)==1
    checks['repeat_open_no_duplicate']=True
    s.finish(); assert not module._instances and not s.handle and not s.timer
    checks['close_cleanup']=True
    assert bpy.ops.bcgi.shelf('INVOKE_DEFAULT')=={'RUNNING_MODAL'}
    checks['reopen']=True
    bpy.context.area.tag_redraw()
Path(r'C:\Users\Samsul Alam Niom\Documents\ChatGPT\Blender\shelf_live_verification.json').write_text(json.dumps(checks,indent=2))
print(json.dumps(checks))
