"""Portable camera-view PNG guides; never replaces unrelated background slots."""
import os
import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

LEGACY_NAME = 'BCGI_AF_InAppOverlay_Crosshair__SAM_V1_20261006.png'
TAG = 'bcgi_camera_overlay'

def camera(p, context):
    return p.overlay_camera or context.scene.camera

def camera_poll(self, obj):
    return obj.type == 'CAMERA'

def managed_slot(cam):
    if not cam or cam.type != 'CAMERA':
        return None
    return next((slot for slot in cam.data.background_images
                 if slot.image and (slot.image.get(TAG) or slot.image.name == LEGACY_NAME)), None)

def builtin():
    path = os.path.join(os.path.dirname(__file__), 'assets', 'BCGI_Camera_Overlay.png')
    image = bpy.data.images.load(path, check_existing=True)
    image[TAG] = True
    if not image.packed_file:
        image.pack()
    return image

def update(p, context):
    if context is None:
        return
    cam = camera(p, context)
    slot = managed_slot(cam)
    if slot is None:
        return
    slot.show_background_image = p.overlay_enabled
    if p.overlay_enabled:
        cam.data.show_background_images = True
    slot.alpha = p.overlay_opacity
    slot.scale = p.overlay_scale
    slot.offset = p.overlay_offset
    slot.rotation = p.overlay_rotation
    slot.display_depth = 'FRONT'
    slot.frame_method = p.overlay_fit

def apply(p, context):
    cam = camera(p, context)
    if cam is None:
        raise ValueError('Choose a camera or set the scene camera first')
    image = p.overlay_image or builtin()
    if image.source != 'FILE':
        raise ValueError('Choose a PNG or another file-based image')
    if not image.packed_file:
        image.pack()
    image[TAG] = True
    slot = managed_slot(cam)
    if slot is None:
        slot = cam.data.background_images.new()
    slot.source = 'IMAGE'
    slot.image = image
    slot.use_flip_x = False
    slot.use_flip_y = False
    update(p, context)
    return slot

class BCGI_OT_camera_overlay(Operator):
    bl_idname = 'bcgi.camera_overlay'
    bl_label = 'Add / Update Camera Overlay'
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        try:
            apply(context.scene.bcgi_labs, context)
        except (ValueError, RuntimeError, OSError) as error:
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        return {'FINISHED'}

class BCGI_OT_load_overlay(Operator, ImportHelper):
    bl_idname = 'bcgi.load_overlay'
    bl_label = 'Choose Custom PNG / Image'
    bl_options = {'REGISTER', 'UNDO'}
    filter_glob: StringProperty(default='*.png;*.jpg;*.jpeg;*.webp;*.tif;*.tiff', options={'HIDDEN'})
    def execute(self, context):
        p = context.scene.bcgi_labs
        if camera(p, context) is None:
            self.report({'ERROR'}, 'Choose a camera or set the scene camera first')
            return {'CANCELLED'}
        previous = p.overlay_image
        try:
            image = bpy.data.images.load(self.filepath, check_existing=True)
            image.pack()
            p.overlay_image = image
            apply(p, context)
        except (ValueError, RuntimeError, OSError) as error:
            p.overlay_image = previous
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        return {'FINISHED'}

class BCGI_OT_builtin_overlay(Operator):
    bl_idname = 'bcgi.builtin_overlay'
    bl_label = 'Use Built-in Overlay'
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        p = context.scene.bcgi_labs
        previous = p.overlay_image
        p.overlay_image = None
        try:
            apply(p, context)
        except (ValueError, RuntimeError, OSError) as error:
            p.overlay_image = previous
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        return {'FINISHED'}

def draw(layout, p):
    box = layout.box()
    box.label(text='Camera Overlay', icon='CAMERA_DATA')
    box.prop(p, 'overlay_camera')
    box.label(text='Empty camera = active scene camera')
    box.operator('bcgi.camera_overlay')
    box.prop(p, 'overlay_enabled')
    box.prop(p, 'overlay_image')
    box.operator('bcgi.load_overlay')
    box.operator('bcgi.builtin_overlay')
    for prop in ('overlay_opacity', 'overlay_scale', 'overlay_offset', 'overlay_rotation', 'overlay_fit'):
        box.prop(p, prop)
    box.label(text='Camera-view guide; excluded from renders')

classes = (BCGI_OT_camera_overlay, BCGI_OT_load_overlay, BCGI_OT_builtin_overlay)
