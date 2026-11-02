# Dual K10 modular enclosure — bottom plate Rev A through Rev D

This directory contains the first parametric bottom-plate design for two
PCE164P-N03-style PCIe risers and Tesla K10 cards.

## Confirmed dimensions

- PCB mounting-hole diameter: 4 mm
- Hole pattern: 95 mm × 35 mm, center-to-center
- Riser pocket floor: 5 mm below the plate surface
- Bare PCB working envelope: 127 mm × 42 mm
- Connector-end working envelope: approximately 47 mm wide × 10 mm high

## Rev A layout

- Full plate: 320 mm × 180 mm × 12 mm
- Riser center spacing: 60.96 mm (three standard 20.32 mm expansion-slot pitches)
- Riser pocket clearance: 0.4 mm per side
- Printed mounting holes: 4.5 mm diameter to compensate for typical FDM undersizing
- Two open service channels per riser at the connector end
- Six reserved shell fasteners and six reserved front/rear-panel fasteners

## Rev B airflow compatibility

Rev B retains the 180 mm outer width required by the planned fan face and adds
two 3.4 mm-wide × 4 mm-deep slots for removable 3 mm baffles. The
grooves define a centered 120 mm card-airflow bay. This lets the future inlet
plenum converge from the large fan to a low-bypass passage around the K10s,
without making the fan mounting face narrower.

The grooves stop 15 mm before both ends so they do not dictate the future front
or rear panel joint.

## Rev C corrected orientation and wiring channels

Rev C introduced the corrected orientation. It retains the Rev B baffle slots, places the
PCI bracket/rear end at X=0, and flips the Molex/USB connector reliefs to the
interior ends of the riser pockets. Separate open wiring channels extend 40 mm
farther into the enclosure beyond each connector face.

## Rev D wider recess, lead-in, relocation, and thinner plate

Rev D is the recommended plate revision:

- The complete riser recess is 48 mm wide, matching the connector relief width.
- Two shallow 0.8 mm steps expand the pocket by 0.6 mm and 1.2 mm per side,
  creating a staggered easy-entry lead-in instead of one abrupt edge.
- Both riser recesses and all eight associated bolt holes move 10 mm toward the
  plate center in the X direction, from X=20 mm to X=30 mm.
- The Molex and USB channels continue 40 mm past the connector face with a
  continuous 5 mm divider between them.
- Plate thickness is reduced from 12 mm to 10 mm. The 5 mm board recess retains
  a 5 mm floor, while the deepest cable channels retain at least a 3 mm floor.
- The 3.4 mm-wide × 4 mm-deep removable-baffle slots are retained.

## Separate baffles

`airflow_baffle_flat_rev_a_print_two.stl` is one baffle laid flat for printing;
print two identical copies. Each is 289.2 mm long × 165 mm high × 3 mm thick.
Four millimetres seat in the plate slot, leaving 161 mm above the plate. The
height remains parametric in `generate_bottom_plate.py` so it can be matched to
the shell when that part is designed.

The 150 mm-tall front panel uses the shortened
`airflow_baffle_flat_rev_b_135mm_print_two.stl`. It is 30 mm shorter than Rev A,
preserving the previous 9 mm clearance beneath the enclosure top. Print two.

## Front panel Rev E

The front panel is 180 mm wide × 150 mm high with a 4 mm face and 15 mm-deep
rear attachment returns. It includes:

- 116 mm fan airflow opening for the pictured 120 mm fan
- Four 5 mm round mounting holes on a 105 mm square pattern
- Two 30 mm-wide × 20 mm-tall passages along the bottom at Y=50 and Y=130 mm
- Two vertical 20 mm-wide × 30 mm-tall passages beside the fan at Y=16 and
  Y=164 mm, centered at Z=90 mm
- Bottom foot aligned to all three Rev D base holes at Y=30, 90, and 150 mm
- Three M4 clearance holes on each side return
- Three M4 clearance holes on the top return

The fan is centered at Y=90 mm and Z=87.5 mm. All four wire passages clear the
fan opening, fan fasteners, and three base fasteners.

## Back panel Rev G

Rev G retains the physically confirmed Rev B envelope, three segmented base
tabs, and all base/side/top enclosure fasteners. It replaces the circular fan
opening with two 48 x 116 mm GPU exhaust windows centered at Y=50 and Y=110 mm,
running from Z=13 to Z=129 mm. Relative to Rev E, the openings move down 5 mm
and extend another 25 mm downward so the bottoms of both cards can pass through.
The horizontal 10 mm leftward correction is retained. Six 4.5 mm M4-clearance
holes provide a future shroud interface without committing to its geometry.

Each exhaust window has a 3 mm-thick U-shaped locating lip that projects 10 mm
inward. The side and top rails remain flush with the 48 x 116 mm opening, but
Rev G removes the lower horizontal rail completely so the bottom of each card
can pass through unobstructed. The confirmed Rev B bottom tabs remain 18 mm wide
x 11 mm deep at Y=30, 90, and 150 mm, preserving the two 42 mm card-clear lower
bays and stopping before the baffle grooves.

The PCI bracket/rear end is X=0. The rear exhaust shroud has intentionally not
been modeled yet.

## Universal sides and top Rev A

The side wall is one reversible 328 x 150 mm design. Print two identical copies
and rotate the second copy 180 degrees end-for-end for the opposite side. Each
wall has a 4 mm face, 15 mm inward top and bottom flanges, three base holes,
three top holes, and three front/rear holes at each end. The flange ends are
notched back 19 mm so they meet rather than overlap the front and rear returns.

The top is a single 328 x 188 x 4 mm plate. Six holes attach it to the front and
rear top returns, and six attach it to the two side-wall top flanges. Both parts
fit the Creality K2 Plus 350 x 350 mm build area when printed flat.

## Files

- `generate_bottom_plate.py`: editable parametric source and STL generator
- `dual_riser_fit_gauge_rev_a.stl`: smaller test print for pocket, hole-pattern,
  connector relief, and card-spacing validation
- `dual_k10_bottom_plate_rev_a.stl`: full Rev A bottom plate
- `dual_k10_bottom_plate_rev_b.stl`: earlier plate with removable-baffle guides
- `dual_k10_bottom_plate_rev_c.stl`: corrected plate with inward-facing connectors,
  extended wiring channels, and removable-baffle slots
- `dual_k10_bottom_plate_rev_d.stl`: recommended thinner plate with widened,
  shifted, stepped-entry riser recesses
- `dual_riser_fit_gauge_rev_b.stl`: corrected-orientation fit gauge
- `dual_riser_fit_gauge_rev_c.stl`: widened stepped-entry fit gauge for Rev D
- `airflow_baffle_flat_rev_a_print_two.stl`: print-flat baffle; print quantity two
- `airflow_baffle_flat_rev_b_135mm_print_two.stl`: shortened baffle for the
  150 mm-tall front; print quantity two
- `generate_front_panel.py`: editable front-panel generator
- `front_panel_rev_e_print_flat.stl`: recommended print orientation
- `front_panel_rev_e_installed_orientation.stl`: assembly-reference orientation
- `front_panel_rev_e.png`: front elevation, side wire ports, and fan pattern
- `generate_back_panel.py`: editable matching back-panel generator
- `back_panel_rev_g_print_flat.stl`: recommended open-bottom pass-through back-panel
- `back_panel_rev_g_installed_orientation.stl`: assembly-reference orientation
- `back_panel_rev_g_single_gpu_vent_lip_fit_gauge.stl`: open-bottom one-bay fit test
- `back_panel_rev_g.png`: open-bottom lip and shroud-hole elevation
- `back_panel_rev_g_base_tabs.png`: retained confirmed base-tab interface
- `generate_side_and_top.py`: universal side-wall and top-panel generator
- `side_panel_universal_rev_a_print_flat_print_two.stl`: print two identical sides
- `side_panel_universal_rev_a_installed_orientation.stl`: side assembly reference
- `side_panel_universal_rev_a_lower_fit_gauge.stl`: lower strip for base/end fit
- `side_panel_universal_rev_a.png`: reversible side-wall hole layout
- `top_panel_rev_a_print_flat.stl`: complete printable top
- `top_panel_rev_a_installed_orientation.stl`: top assembly reference
- `top_panel_rev_a.png`: four-wall top-hole layout

## Fit-validation order

1. Print the fit gauge before the full plate.
2. Verify that both PCBs enter the pockets without force.
3. Insert all eight fasteners loosely before tightening any of them.
4. Confirm that the Molex and USB plugs have enough insertion and cable-bend room.
5. Install both unpowered K10s and verify the spacing and bracket alignment.
6. Report any measured correction; update the parameters and regenerate the full plate.

The Rev D cable channels are intentionally generous and open toward the inside.
Their final covers/retainers should be designed together with the shell after a
physical cable-fit check.
