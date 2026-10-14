# BCGI LABS docking and effects design

Status: design proposal only. Add-on remains v0.5.1; no live UI or effect changes in this checkpoint.

## Current issue

The upper preset library calls WindowManager.invoke_popup(width=850). It is a temporary popup, with no persistent placement or docking implementation. Native Blender popups cannot be treated as dockable library windows.

## Proposed interface

- A persistent viewport shelf with explicit Top, Bottom, Right and Float placement, Pin, Collapse, Close and Reset Position controls.
- Top is the initial placement. Floating position is clamped to the viewport, including after resize; placement is stored with the add-on preferences.
- Float: drag using the title-bar handle. Highlight available edges during drag, then snap on release. Pin locks placement. Escape cancels a drag without closing the shelf; clicks outside do not dismiss it.
- Top/bottom/right shelf docking means attachment to the viewport edge, not creation of a new Blender editor type.
- Keep Blender's native right sidebar for full controls, data pickers, numeric input and keyframing. Provide a native Asset Browser library for Blender-managed editor placement.
- Effects, Studio, Writing and Camera tabs replace the long undivided list. Search and category filtering should scale as the library grows. Target-type labels explain mesh/curve/skeletal requirements.
- Glass direction: rounded corners, restrained highlights, cyan accents and readable text. Custom viewport drawing is needed for this appearance. Native sidebar styling follows Blender's theme. True Apple-style background refraction/blur is not promised; readability and viewport performance come first.
- No change to the global Blender theme. No external web UI runtime is required.

## Reference cross-check

| Requested effect | Current source | Decision |
| --- | --- | --- |
| Chalk / pen writing | writing.py, WRITE_CHALK / WRITE_PEN | Reuse; no duplicate. Curve reveal exists, automatic hand animation does not. |
| Wave | presets.py, WAVE | Reuse existing sinusoidal displacement. Propagating/radial wave mode may need extension after reference verification. |
| Wind Flow | Absent | Add directional animated streamline/ribbon effect with direction, speed, density, length, width and color. |
| Topology View | Absent | Add renderable wireframe overlay, with width/color/opacity and original surface preserved. |
| Electric Shock Wave | Absent | Add animated emissive branching arcs/pulse overlay. Existing GLOW and SCAN are not substitutes. |
| Mud Sim | Absent | Add procedural mud sinking/deformation visual preset with depth, progress and surface controls. Clearly label it as a procedural effect unless a real simulation/cache is implemented. |
| Bone Fracture | Absent | Add fracture visual on a selected bone mesh with break position, gap, fragments and progress. Preserve original mesh; do not destructively alter an armature. Skeletal-bone fracture needs visible bone geometry, which current XRAY does not generate. |

Screenshots identify the requested visual categories; their static pixels do not establish exact motion or physics behavior. Current XRAY is a transparent silhouette material, not an anatomical skeleton generator.

## Acceptance for implementation

1. Shelf survives ordinary clicking, playback and viewport navigation; closes only by an explicit action.
2. Dock/undock/drag/resize/reset work in multiple viewport sizes; placement cannot become inaccessible.
3. Disable/re-enable removes draw handlers and modal handlers cleanly; keyboard/mouse interaction outside the shelf stays available.
4. Existing mesh and curve presets remain intact; new presets have distinct IDs and target-type checks.
5. New effects expose useful animatable controls, preserve source geometry/materials where applicable, and are validated in a fresh file and save/reopen.
6. Publish implementation source, versioned ZIP and honest validation evidence to GitHub after completion.
