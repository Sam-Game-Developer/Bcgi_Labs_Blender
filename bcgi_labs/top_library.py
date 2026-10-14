import bpy
from bpy.props import StringProperty
_icons=None
_choices=[]
IDS=('WAVE','SCATTER','TWIST','PULSE','SCAN','GLOW','XRAY','GLOW_RING','WRITE_CHALK','WRITE_PEN')

def choices(self,context):
    global _choices
    if not _choices: _choices=[(name,name.replace('_',' ').title(),'Select then apply',_icons[name].icon_id if _icons and name in _icons else 0,index) for index,name in enumerate(IDS)]
    return _choices

class BCGI_OT_top_apply(bpy.types.Operator):
    bl_idname='bcgi.top_apply'; bl_label='Apply Selected Preset'; bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        p=context.scene.bcgi_labs; kind=p.top_preset
        if kind.startswith('WRITE_'):
            p.writing_style=kind.split('_',1)[1]
            if not bpy.ops.bcgi.apply_writing.poll():
                self.report({'ERROR'},'Select a curve for writing, or create a writing sample.'); return {'CANCELLED'}
            return bpy.ops.bcgi.apply_writing()
        p.fx_preset=kind
        if not bpy.ops.bcgi.apply_preset.poll():
            self.report({'ERROR'},'Select a mesh in Object Mode.'); return {'CANCELLED'}
        return bpy.ops.bcgi.apply_preset()

class BCGI_OT_top_pick(bpy.types.Operator):
    bl_idname='bcgi.top_pick'; bl_label='Select Preset'
    preset: StringProperty()
    def execute(self,context):
        context.scene.bcgi_labs.top_preset=self.preset
        return bpy.ops.bcgi.top_apply()

class BCGI_OT_top_library(bpy.types.Operator):
    bl_idname='bcgi.top_library'; bl_label='BCGI LABS Preset Library'
    def invoke(self,context,event): return context.window_manager.invoke_popup(self,width=850)
    def execute(self,context): return {'FINISHED'}
    def draw(self,context):
        layout=self.layout; p=context.scene.bcgi_labs
        layout.label(text='BCGI LABS · Click a preset to apply it to the active object')
        for start in (0,5):
            row=layout.row()
            for kind in IDS[start:start+5]:
                card=row.column(align=True)
                if _icons and kind in _icons: card.template_icon(icon_value=_icons[kind].icon_id,scale=4)
                else: card.label(text='',icon='GEOMETRY_NODES')
                card.operator('bcgi.top_pick',text=kind.replace('_',' ').title(),depress=p.top_preset==kind).preset=kind
        row=layout.row(); row.operator('bcgi.top_apply'); row.operator('bcgi.sample_writing'); row.operator('bcgi.animate_writing')
        layout.label(text='Mesh FX: select a mesh · Writing: select a curve · Controls: BCGI LABS sidebar / Modifiers')

def header(self,context): self.layout.operator('bcgi.top_library',text='BCGI LABS',icon='ASSET_MANAGER')
