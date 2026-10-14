import bpy, sys, json, math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import bcgi_labs
bcgi_labs.register()
bpy.ops.mesh.primitive_grid_add(x_subdivisions=12,y_subdivisions=12,size=2)
source=bpy.context.object
original=source.data.copy()
checks={}
for preset in ('SOFT','DRAMA','NEON'):
    bpy.context.scene.bcgi_labs.lighting=preset
    checks['lights_'+preset]=bpy.ops.bcgi.lights()=={'FINISHED'}
checks['backdrop']=bpy.ops.bcgi.backdrop()=={'FINISHED'}
for effect in ('SCATTER','WAVE'):
    bpy.context.view_layer.objects.active=source
    checks[effect]=bpy.ops.bcgi.effect(kind=effect)=={'FINISHED'}
    o=bpy.context.object
    bpy.context.scene.frame_set(1)
    dg=bpy.context.evaluated_depsgraph_get()
    ev=o.evaluated_get(dg)
    if effect=='SCATTER':
        checks['scatter_instances']=sum(1 for inst in dg.object_instances if inst.is_instance)==150
    else:
        a=[v.co.z for v in ev.data.vertices]
        bpy.context.scene.frame_set(24)
        b=[v.co.z for v in o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices]
        checks['wave_animates']=any(abs(x-y)>1e-5 for x,y in zip(a,b))
checks['source_preserved']=all((v.co-original.vertices[i].co).length==0 for i,v in enumerate(source.data.vertices))
checks['panel_registered']=hasattr(bpy.types,'BCGI_PT_panel')
checks['brand_loaded']='brand' in bcgi_labs._previews
bcgi_labs.unregister()
checks['unregister']=not hasattr(bpy.types.Scene,'bcgi_labs')
bcgi_labs.register()
checks['reregister']=hasattr(bpy.types.Scene,'bcgi_labs')
Path(__file__).with_name('verification.json').write_text(json.dumps(checks,indent=2))
print('BCGI_TEST',json.dumps(checks))
assert all(checks.values()), checks
