# BCGI LABS for Blender

**v0.5.2 · Build 20261014 · Tested in Blender 5.2.2 LTS on Windows**

![Infinity studio](docs/BCGI_Infinite_Studio_preview.png)

## Install

Download [the add-on ZIP](dist/BCGI_LABS_v0.5.2_Build20261014.zip).
Open **Edit → Preferences → Add-ons → Install from Disk**, select the ZIP,
enable **BCGI LABS**, then open **3D View → N sidebar → BCGI LABS**.

## Persistent library shelf and stroke materials

Click **BCGI LABS** in a 3D View header or **Open Top Preset Library** in the
sidebar. The library now stays open when clicking elsewhere. It initially docks
below the viewport header. **Dock / Top**, **Bottom**, **Right** and **Float**
choose placement. Drag the title bar, or click **Move** then drag inside the
shelf. The panel stays within the visible viewport and avoids native sidebars.
**− / +** minimizes/restores it; **×** closes it; **Reset** restores the top
position. Arrow buttons or the wheel over the shelf page through the presets.

Placement is stored in the scene; save the blend to retain it. Reopen the shelf
with the header button after loading a file. This is viewport-edge attachment,
not a separate native Blender editor. The custom surface has rounded corners,
soft transparency and highlighted controls; it does not refract/blur the scene.
Full controls remain in the native sidebar and Modifiers tab.

The supplied BCGI LABS robot logo is bundled and shown in the shelf, header and
sidebar. Under **Writing / Drawing Reveal**, **Stroke Material** now selects
and replaces the writing modifier's material. **Use Built-in Chalk / Pen Material**
restores the procedural stroke material. The Stroke Color control updates BCGI
stroke materials; user-supplied shaders remain untouched and are edited through
Blender's Material Properties / Shader Editor.

Fresh-file material selection, custom shader preservation, style switching and
save/reopen passed. Live shelf drawing was inspected; placement, minimize,
reset, close/reopen and simulated drag/click event paths passed. Literal manual
mouse dragging, cold restart and other-PC testing remain unverified. The five
new effect categories in the design document remain planned, not shipped in
this UI/material update.

## Camera overlay

The user's BCGI portrait overlay PNG is bundled in the ZIP. Under **Camera
Overlay**, click **Add / Update Camera Overlay** to add it to the scene camera.
Choose another camera in the Camera field if needed. **Choose Custom PNG / Image**
replaces the guide; **Use Built-in Overlay** restores the bundled PNG.

Controls include visibility, opacity, scale, position, rotation and Fit/Crop/Stretch.
Images are packed into the saved blend, so their original disk path is not needed
on another PC. Repeated application reuses the BCGI slot and preserves unrelated
camera background images. The existing legacy BCGI overlay slot is adopted.

This uses Blender's native foreground camera background image: it is a
**camera-view guide only, excluded from final renders**. Use camera view and
enable viewport overlays to see it. Camera motion retains the guide in camera
space. The bundled layout is designed for portrait 1080 x 1920 framing.

Fresh-camera creation, PNG replacement/reset, control read-back, duplicate
prevention and save/reopen passed in Blender 5.2.2 LTS. Another physical PC has
not been tested.

## Infinity studio

**Add / Update Infinite Studio** creates a continuous disk floor, 360-degree
curved enclosure, matching sky, procedural gradient and linked background lights.
Reusing this button updates the current studio without duplicating it.

- **Infinity Studio** switches the studio on/off and restores the previous world
  when off. It does not delete the studio.
- **Follow Camera** follows the active scene camera's horizontal world movement
  and yaw, including through a parent rig. Ground height stays fixed. It rebinds
  automatically when the active camera changes.
- Color, glow position/spread, size, brightness and shadow controls update live.
  Floor, backdrop and sky use the same camera-space gradient. Their base color
  stays continuous regardless of surface orientation. Contact AO supplies local
  grounding shadows without diffuse lighting producing a visible floor/wall boundary.
  Background Light Power scales the shared gradient brightness.
- **Background Light Power** controls lights linked to studio geometry.
- Select the character mesh or armature, then **Add Lights for Selected Character**.
  **Character Light Power** controls that separate rig, linked to those meshes.

The world color is visible to camera rays without acting as ambient character
lighting. The camera-facing gradient is isolated from indirect emission. Use
Cycles for the verified light-linking result. Legacy Studio Lights adds general
unrestricted lights.

The enclosure is large finite geometry, not mathematically infinite. Normal
shots from inside it show no edges. Extreme positions, vertical travel or very
small studio sizes may require increasing Studio Size. The preview uses a
simple test object and Standard color management. Lighting and color management
affect the final appearance. Existing cameras and source rigs are preserved.

## Floor grid and branding

![Floor grid](docs/BCGI_Infinite_Studio_grid_preview.png)

**Floor Grid:** color, spacing, line width and opacity. This is a renderable
material grid, separate from the global viewport grid. Distances use scene units.

**Floor Branding:**

- **Text:** installed Windows-font dropdown, Segoe UI default, custom TTF/OTF
  loading, text, color, size, position and rotation.
- **PNG Logo:** transparent PNG loading, tint, width, position and rotation.
  Image proportions are preserved.

Loaded images/fonts are packed into the local saved scene. Windows fonts and
user reference screenshots are not distributed here. Use material preview or
rendered shading; enable Scene World and Scene Lights in material preview to
evaluate the studio's actual sky and lighting. Solid shading hides materials.

## Grid, shape and scene controls in v0.5.2

- **Studio Floor** can be disabled independently. The procedural sky/cove stay
  active, while BCGI floor, grid and floor branding hide. Add your own road or
  mesh normally; its geometry/materials are not modified.
- **Glow Shape:** Circle, Oval, Square and Rounded Square. Spread controls the
  outer size; **Glow Feather** controls smooth blending. Aspect Ratio stretches
  the non-circular shapes; Corner Roundness adjusts Rounded Square. Floor,
  backdrop and sky use the same shape field. Circle accounts for render aspect.
- The floor grid uses **world X/Y coordinates**, anchored at world origin. It
  stays aligned with Blender's axes when the camera/studio moves or rotates.
  Grid Box Size, Line Width, Color, Opacity and Glow Strength are adjustable.
- **Hide Viewport Grid** temporarily hides Blender's floor/ortho grid and X/Y
  axes while the BCGI grid is active. Turning it off restores the previous
  viewport settings, including after save/reopen.
- Grid Glow adds emission and enables a Fog Glow compositor for final-render
  halos. High enough brightness is required to cross the glare threshold.
- **Center Whole Scene** recenters visible non-BCGI mesh bounds in X/Y and
  aligns their lowest point with Z=0. With no content mesh it centers the camera
  horizontally. Camera rigs, visible lights and content move together under a
  control Empty; existing child rig hierarchy stays intact. The active studio
  follows the move without double-translating. Undo restores the operation.

![Glowing world grid](docs/BCGI_World_Grid_Glow_preview.png)
![Rounded feather](docs/BCGI_Rounded_Feather_preview.png)

## Writing, ring highlights and upper library

Click **BCGI LABS** at the left of a 3D View header to open the persistent horizontal
thumbnail shelf. A thumbnail button applies the preset to the active object.
Mesh effects require a mesh; writing effects require a curve. The sidebar retains
full controls and also has **Open Top Preset Library**.

### Chalk / pen write-on

Select an editable Curve in Object Mode, choose Chalk or Pen under
**Writing / Drawing Reveal**, and apply. Or click **Create Editable Writing
Sample** to create the editable dollar-symbol paths. Set width, roughness,
color, start frame and duration, then click **Animate Writing**. It inserts
Progress=0 at Start Frame and Progress=1 at Start Frame + Duration.

Each spline is revealed in data order with equal time per spline. Progress is
also an animatable Geometry Nodes modifier input. Curve control points remain
editable. Applying again updates the writing modifier rather than stacking
curve-to-mesh conversions. Chalk uses granular transparency and width variation;
Pen uses a solid ink stroke. Width is measured in curve-local units and acts as
profile radius, so object scaling affects the result.

![Chalk halfway](docs/BCGI_Writing_CHALK_25.png)
![Chalk complete](docs/BCGI_Writing_CHALK_49.png)
![Pen complete](docs/BCGI_Writing_PEN_49.png)

This is stroke reveal, not an automatic hand/pen-character animation. Place or
draw the curves on your board/paper surface. It does not infer handwritten
centerlines from a raster logo or typed font; converted text/SVG paths reveal
their contours. Hand movement can be animated separately.

### Glow Ring Highlight

Select a mesh and apply **Glow Ring**. The preset adds emissive rings/arcs while
retaining the object's original mesh and material slots. Initial radius and
orientation are fitted to its local bounds; adjust for irregular objects.
Controls include Radius, Width, Arc Coverage, Ring Count, Spacing, Position,
Rotation, Rotation Speed, Glow Strength and Glow Color. Numeric/vector controls
can be keyframed. A Fog Glow compositor supplies the final-render halo.

![Glow ring](docs/BCGI_Glow_Ring_preview.png)

The library now includes ten assets: eight mesh effects and two writing effects.
Write-on tests verified empty, partial and full geometry at start/middle/end;
render previews, source preservation, material preservation, header thumbnails,
registration lifecycle, fresh-file creation and save/reopen passed in Blender
5.2.2. Literal mouse drag/drop of the new curve assets remains untested.

## Preset library

Eight mesh Geometry Nodes assets: **Wave, Scatter, Twist, Pulse, Scan, Glow,
X-ray, Glow Ring** plus two **Chalk/Pen writing** curve assets. Select a mesh and click **Apply Preset to Selected Mesh**. The modifier
is editable and preserves the underlying mesh.

Click **Install / Refresh Asset Library**. In an Asset Browser choose **BCGI LABS**,
then drag a preset onto the mesh in a 3D View. Native asset-based modifier import
was verified in live Blender. Assets are also supplied in `asset_library/`.

Adjust modifier inputs. Hover a value and press **I**, or click **Keyframe Latest
FX Controls**. Change the frame/value and insert another keyframe. Scan Position
runs from 0 to 1 along the object's generated height. Wave, Twist and Pulse also
expose Scene Time speed controls.

![Scan](docs/BCGI_FX_SCAN_preview.png)
![Glow](docs/BCGI_FX_GLOW_preview.png)
![X-ray](docs/BCGI_FX_XRAY_preview.png)

Glow applies an emissive material and adds a Fog Glow compositor node around
the existing image output in Blender 5.2. The halo appears in final composited
renders; material preview shows emission. X-ray is a transparent stylized edge
effect. Evaluated materials change through the modifier; source material slots
are retained. Remove the modifier to undo. Wave needs sufficient subdivisions.
Scatter adds instances inside the mesh bounds.

Legacy effect-copy buttons and gray/white/dark cycloramas remain available.
Motion retargeting, character creation and fire/smoke simulation are not included.

## Verification

Checks cover original tools, infinity toggling, parented-camera movement/yaw,
linked lighting, Windows fonts, PNG size/tint, keyframes, mesh/writing presets and asset
export. Actual Cycles renders were inspected for the studio, grid, Scan, Glow
and X-ray. Live installation and native asset import passed.

The native scanner needs UI events, so import is `NOT_RUN_BACKGROUND` in the
offline test and verified separately in live Blender. Literal mouse drag/drop,
another PC and other Blender releases have not been tested. A factory-startup
fresh file and its save/reopen in a separate Blender process were verified using
the installed v0.5.2 add-on, including camera follow, grid and packed font settings.
No restart was required in the verified session.

```text
blender --background --factory-startup --python test_bcgi.py
blender --background --factory-startup --python test_infinite_studio.py
blender --background --factory-startup --python test_gradient_seam.py
blender --background --factory-startup --python verify_fresh_file.py
blender --background --factory-startup --python verify_fresh_reopen.py
blender --background --factory-startup --python test_grid_shapes.py
blender --background --factory-startup --python test_scene_center.py
blender --background --factory-startup --python test_writing_ring.py
```

Tests create disposable scenes and render outputs. Source: `bcgi_labs/`.
Reports: `validation/`. BCGI logo supplied by BCGI LABS.
