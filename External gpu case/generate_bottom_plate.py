"""Generate the Rev A dual-K10 riser bottom plate and fit gauge.

Coordinates:
  X: card length / front-to-back direction
  Y: enclosure width
  Z: up from the bottom of the plate

The connector/service end is X=0.  All dimensions are millimetres.
"""

from pathlib import Path

import numpy as np
import trimesh


OUT = Path(__file__).resolve().parent

# Confirmed/measured riser dimensions.
PCB_LENGTH = 127.0
PCB_WIDTH = 42.0
HOLE_GRID_X = 95.0
HOLE_GRID_Y = 35.0
BOARD_HOLE_DIAMETER = 4.0
POCKET_DEPTH = 5.0

# FDM allowances and standard case alignment.
POCKET_CLEARANCE_PER_SIDE = 0.4
PRINTED_HOLE_DIAMETER = 4.5
PCI_SLOT_PITCH = 20.32
RISER_CENTER_SPACING = 3 * PCI_SLOT_PITCH  # one empty slot between dual-slot cards

# Full bottom plate.
PLATE_LENGTH = 320.0
PLATE_WIDTH = 180.0
PLATE_THICKNESS = 12.0
RISER_X = 20.0
REV_D_PLATE_THICKNESS = 10.0
REV_D_RISER_X = 30.0
WIDE_RECESS_WIDTH = 48.0
RECESS_LEAD_IN_STEP = 0.8
AIRFLOW_BAY_WIDTH = 120.0
BAFFLE_GROOVE_WIDTH = 3.4
BAFFLE_GROOVE_DEPTH = 4.0
BAFFLE_GROOVE_END_MARGIN = 15.0
BAFFLE_THICKNESS = 3.0
BAFFLE_TOTAL_HEIGHT = 165.0
SHORT_BAFFLE_TOTAL_HEIGHT = 135.0
BAFFLE_END_CLEARANCE = 0.4


def box(size, center):
    mesh = trimesh.creation.box(extents=size)
    mesh.apply_translation(center)
    return mesh


def z_cylinder(diameter, height, center):
    mesh = trimesh.creation.cylinder(radius=diameter / 2, height=height, sections=48)
    mesh.apply_translation(center)
    return mesh


def subtract(base, cutters):
    result = trimesh.boolean.difference([base, *cutters], engine="manifold")
    if result is None:
        raise RuntimeError("Boolean subtraction failed")
    return result


def riser_centers(width):
    return (
        width / 2 - RISER_CENTER_SPACING / 2,
        width / 2 + RISER_CENTER_SPACING / 2,
    )


def add_riser_cuts(
    cutters,
    plate_height,
    board_x,
    center_y,
    include_service_channels,
    connectors_inside=False,
    wide_tapered_recess=False,
):
    pocket_length = PCB_LENGTH + 2 * POCKET_CLEARANCE_PER_SIDE
    pocket_width = (
        WIDE_RECESS_WIDTH
        if wide_tapered_recess
        else PCB_WIDTH + 2 * POCKET_CLEARANCE_PER_SIDE
    )
    pocket_x = board_x - POCKET_CLEARANCE_PER_SIDE

    # The PCB sits on a floor exactly 5 mm below the top surface.
    cutters.append(
        box(
            (pocket_length, pocket_width, POCKET_DEPTH + 0.2),
            (
                pocket_x + pocket_length / 2,
                center_y,
                plate_height - POCKET_DEPTH / 2 + 0.1,
            ),
        )
    )

    if wide_tapered_recess:
        # Two shallow, progressively wider steps form an easy-entry lead-in
        # instead of a single abrupt vertical pocket edge.
        for step_depth, expansion in (
            (2 * RECESS_LEAD_IN_STEP, 0.6),
            (RECESS_LEAD_IN_STEP, 1.2),
        ):
            cutters.append(
                box(
                    (
                        pocket_length + 2 * expansion,
                        pocket_width + 2 * expansion,
                        step_depth + 0.2,
                    ),
                    (
                        pocket_x + pocket_length / 2,
                        center_y,
                        plate_height - step_depth / 2 + 0.1,
                    ),
                )
            )

    # Hole grid is centered on the PCB outline.
    hole_x0 = board_x + (PCB_LENGTH - HOLE_GRID_X) / 2
    for hx in (hole_x0, hole_x0 + HOLE_GRID_X):
        for hy in (center_y - HOLE_GRID_Y / 2, center_y + HOLE_GRID_Y / 2):
            cutters.append(
                z_cylinder(PRINTED_HOLE_DIAMETER, plate_height + 2, (hx, hy, plate_height / 2))
            )

    if include_service_channels:
        # Connector envelope is wider than the bare 42 mm PCB.  This relief and
        # its two open channels preserve room for the 4-pin Molex and USB plug.
        connector_relief_width = 48.0
        if connectors_inside:
            connector_end_x = board_x + PCB_LENGTH
            relief_start_x = connector_end_x - 18.0
            relief_length = 36.0
            channel_start_x = connector_end_x
            channel_length = 40.0
        else:
            relief_start_x = 0.0
            relief_length = board_x + 18.0
            channel_start_x = 0.0
            channel_length = board_x
        cutters.append(
            box(
                (relief_length + 0.2, connector_relief_width, POCKET_DEPTH + 0.2),
                (
                    relief_start_x + relief_length / 2,
                    center_y,
                    plate_height - POCKET_DEPTH / 2 + 0.1,
                ),
            )
        )

        # Open-top cable channels; dimensions remain parametric for final cable-fit tuning.
        channel_depth = min(7.0, plate_height - 3.0)
        # The untouched 5 mm strip between these channels is the extended
        # divider separating the Molex and USB wiring paths.
        for offset_y, channel_width in ((-10.0, 22.0), (13.0, 14.0)):
            cutters.append(
                box(
                    (channel_length + 0.2, channel_width, channel_depth + 0.2),
                    (
                        channel_start_x + channel_length / 2,
                        center_y + offset_y,
                        plate_height - channel_depth / 2 + 0.1,
                    ),
                )
            )


def make_full_plate(
    include_baffle_guides=False,
    connectors_inside=False,
    plate_thickness=PLATE_THICKNESS,
    riser_x=RISER_X,
    wide_tapered_recess=False,
):
    base = box(
        (PLATE_LENGTH, PLATE_WIDTH, plate_thickness),
        (PLATE_LENGTH / 2, PLATE_WIDTH / 2, plate_thickness / 2),
    )
    cutters = []

    for cy in riser_centers(PLATE_WIDTH):
        add_riser_cuts(
            cutters,
            plate_thickness,
            riser_x,
            cy,
            True,
            connectors_inside=connectors_inside,
            wide_tapered_recess=wide_tapered_recess,
        )

    if include_baffle_guides:
        # Removable 3 mm baffles can locate in these grooves.  They create a
        # centered 120 mm airflow bay while preserving the 180 mm fan face.
        groove_length = PLATE_LENGTH - 2 * BAFFLE_GROOVE_END_MARGIN
        for y in (
            (PLATE_WIDTH - AIRFLOW_BAY_WIDTH) / 2,
            (PLATE_WIDTH + AIRFLOW_BAY_WIDTH) / 2,
        ):
            cutters.append(
                box(
                    (groove_length, BAFFLE_GROOVE_WIDTH, BAFFLE_GROOVE_DEPTH + 0.2),
                    (
                        PLATE_LENGTH / 2,
                        y,
                        plate_thickness - BAFFLE_GROOVE_DEPTH / 2 + 0.1,
                    ),
                )
            )

    # Reserved vertical fasteners for a future slide-over shell.
    for x in (60.0, 160.0, 260.0):
        for y in (7.5, PLATE_WIDTH - 7.5):
            cutters.append(z_cylinder(PRINTED_HOLE_DIAMETER, plate_thickness + 2, (x, y, plate_thickness / 2)))

    # Reserved vertical fasteners for the future front and rear panels.
    for x in (7.5, PLATE_LENGTH - 7.5):
        for y in (30.0, PLATE_WIDTH / 2, PLATE_WIDTH - 30.0):
            cutters.append(z_cylinder(PRINTED_HOLE_DIAMETER, plate_thickness + 2, (x, y, plate_thickness / 2)))

    return subtract(base, cutters)


def make_fit_gauge(connectors_inside=False, wide_tapered_recess=False):
    gauge_length = 190.0 if connectors_inside else 150.0
    gauge_width = 120.0
    gauge_height = 8.0
    board_x = (gauge_length - PCB_LENGTH) / 2
    base = box(
        (gauge_length, gauge_width, gauge_height),
        (gauge_length / 2, gauge_width / 2, gauge_height / 2),
    )
    cutters = []
    for cy in riser_centers(gauge_width):
        add_riser_cuts(
            cutters,
            gauge_height,
            board_x,
            cy,
            True,
            connectors_inside=connectors_inside,
            wide_tapered_recess=wide_tapered_recess,
        )
    return subtract(base, cutters)


def make_baffle_flat(total_height=BAFFLE_TOTAL_HEIGHT):
    """Create one print-flat baffle; print two identical copies.

    The 165 mm flat width becomes installed height. Four millimetres seat in
    the plate groove, leaving 161 mm above the plate surface.
    """
    installed_length = (
        PLATE_LENGTH - 2 * BAFFLE_GROOVE_END_MARGIN - 2 * BAFFLE_END_CLEARANCE
    )
    return box(
        (installed_length, total_height, BAFFLE_THICKNESS),
        (installed_length / 2, total_height / 2, BAFFLE_THICKNESS / 2),
    )


def validate_and_export(mesh, filename):
    if not mesh.is_watertight:
        raise RuntimeError(f"{filename} is not watertight")
    if mesh.volume <= 0:
        raise RuntimeError(f"{filename} has invalid volume")
    mesh.export(OUT / filename)
    bounds = np.round(mesh.bounds, 3)
    print(f"{filename}: faces={len(mesh.faces)}, volume={mesh.volume:.1f} mm^3, bounds={bounds.tolist()}")


def render_preview(mesh, filename, elevation=42, azimuth=-55):
    """Write a dependency-light shaded inspection render."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    preview = mesh.copy()
    preview.apply_scale((1, 1, 3))  # make shallow recess details legible in the preview only
    fig = plt.figure(figsize=(12, 7), dpi=160)
    ax = fig.add_subplot(111, projection="3d")
    triangles = preview.vertices[preview.faces]
    light = np.array([-0.4, -0.6, 1.0])
    light /= np.linalg.norm(light)
    intensity = np.clip(preview.face_normals @ light, -0.25, 1.0)
    intensity = 0.55 + 0.4 * (intensity + 0.25) / 1.25
    base_color = np.array([0.12, 0.55, 0.82])
    face_colors = np.column_stack((base_color[None, :] * intensity[:, None], np.ones(len(intensity))))
    collection = Poly3DCollection(
        triangles,
        facecolors=face_colors,
        edgecolors="none",
        linewidth=0,
        alpha=1.0,
    )
    ax.add_collection3d(collection)
    low, high = preview.bounds
    center = (low + high) / 2
    extent = high - low
    pad = 0.03
    ax.set_xlim(low[0] - extent[0] * pad, high[0] + extent[0] * pad)
    ax.set_ylim(low[1] - extent[1] * pad, high[1] + extent[1] * pad)
    ax.set_zlim(low[2], high[2] + max(2, extent[2] * 0.1))
    ax.set_box_aspect((extent[0], extent[1], max(extent[2], 25)))
    ax.set_proj_type("ortho")
    ax.view_init(elev=elevation, azim=azimuth)
    ax.set_axis_off()
    ax.set_title(filename.replace("_", " ").replace(".png", ""))
    fig.tight_layout()
    fig.savefig(OUT / filename, bbox_inches="tight")
    plt.close(fig)


def render_layout_diagram(
    filename,
    length,
    width,
    board_x,
    include_shell_holes,
    include_baffle_guides=False,
    connectors_inside=False,
    wide_tapered_recess=False,
):
    """Render an unambiguous top-view manufacturing layout."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Rectangle

    fig, ax = plt.subplots(figsize=(12, 7), dpi=180)
    ax.add_patch(Rectangle((0, 0), length, width, facecolor="#dcecf6", edgecolor="#16384d", linewidth=2))
    pocket_length = PCB_LENGTH + 2 * POCKET_CLEARANCE_PER_SIDE
    pocket_width = (
        WIDE_RECESS_WIDTH
        if wide_tapered_recess
        else PCB_WIDTH + 2 * POCKET_CLEARANCE_PER_SIDE
    )

    for cy in riser_centers(width):
        ax.add_patch(
            Rectangle(
                (board_x - POCKET_CLEARANCE_PER_SIDE, cy - pocket_width / 2),
                pocket_length,
                pocket_width,
                facecolor="#68b6e3",
                edgecolor="#0f4f73",
                linewidth=1.5,
                label="5 mm riser recess",
            )
        )
        if wide_tapered_recess:
            ax.add_patch(
                Rectangle(
                    (
                        board_x - POCKET_CLEARANCE_PER_SIDE - 1.2,
                        cy - pocket_width / 2 - 1.2,
                    ),
                    pocket_length + 2.4,
                    pocket_width + 2.4,
                    fill=False,
                    edgecolor="#0f4f73",
                    linestyle=":",
                    linewidth=1.2,
                )
            )
        if connectors_inside:
            connector_end_x = board_x + PCB_LENGTH
            ax.add_patch(
                Rectangle(
                    (connector_end_x - 18, cy - 24),
                    36,
                    48,
                    facecolor="#9bd1ef",
                    edgecolor="#0f4f73",
                    linewidth=1,
                )
            )
            # Wiring channels continue 40 mm into the enclosure beyond the plugs.
            ax.add_patch(
                Rectangle((connector_end_x, cy - 21), 40, 22, facecolor="#f1c86a", edgecolor="#72520d", linewidth=1)
            )
            ax.add_patch(
                Rectangle((connector_end_x, cy + 6), 40, 14, facecolor="#82d0c1", edgecolor="#19594d", linewidth=1)
            )
        else:
            ax.add_patch(
                Rectangle((0, cy - 24), board_x + 18, 48, facecolor="#9bd1ef", edgecolor="#0f4f73", linewidth=1)
            )
            ax.add_patch(Rectangle((0, cy - 21), board_x, 22, facecolor="#f1c86a", edgecolor="#72520d", linewidth=1))
            ax.add_patch(Rectangle((0, cy + 5), board_x, 14, facecolor="#82d0c1", edgecolor="#19594d", linewidth=1))

        hole_x0 = board_x + (PCB_LENGTH - HOLE_GRID_X) / 2
        for hx in (hole_x0, hole_x0 + HOLE_GRID_X):
            for hy in (cy - HOLE_GRID_Y / 2, cy + HOLE_GRID_Y / 2):
                ax.add_patch(Circle((hx, hy), PRINTED_HOLE_DIAMETER / 2, facecolor="white", edgecolor="#101010"))

        ax.plot([hole_x0, hole_x0 + HOLE_GRID_X], [cy, cy], color="#333", linestyle="--", linewidth=0.6)

    if include_shell_holes:
        for x in (60.0, 160.0, 260.0):
            for y in (7.5, width - 7.5):
                ax.add_patch(Circle((x, y), PRINTED_HOLE_DIAMETER / 2, facecolor="white", edgecolor="#7b2d26"))
        for x in (7.5, length - 7.5):
            for y in (30.0, width / 2, width - 30.0):
                ax.add_patch(Circle((x, y), PRINTED_HOLE_DIAMETER / 2, facecolor="white", edgecolor="#7b2d26"))

    if include_baffle_guides:
        for y in ((width - AIRFLOW_BAY_WIDTH) / 2, (width + AIRFLOW_BAY_WIDTH) / 2):
            ax.add_patch(
                Rectangle(
                    (BAFFLE_GROOVE_END_MARGIN, y - BAFFLE_GROOVE_WIDTH / 2),
                    length - 2 * BAFFLE_GROOVE_END_MARGIN,
                    BAFFLE_GROOVE_WIDTH,
                    facecolor="#8b5fbf",
                    edgecolor="#442465",
                    linewidth=1,
                )
            )
        ax.annotate(
            "",
            (length - 55, (width - AIRFLOW_BAY_WIDTH) / 2),
            (length - 55, (width + AIRFLOW_BAY_WIDTH) / 2),
            arrowprops={"arrowstyle": "<->", "color": "#442465"},
        )
        ax.text(
            length - 52,
            width / 2,
            "120 mm removable-baffle airflow bay",
            rotation=90,
            ha="left",
            va="center",
            fontsize=9,
            color="#442465",
        )
    # Dimension the confirmed riser grid and standard center spacing.
    centers = riser_centers(width)
    ax.annotate("", (board_x + 16, centers[0] - 17.5), (board_x + 111, centers[0] - 17.5), arrowprops={"arrowstyle": "<->"})
    ax.text(board_x + 63.5, centers[0] - 15.5, "95 mm hole centers", ha="center", va="bottom", fontsize=9)
    ax.annotate("", (board_x + 16, centers[0] - 17.5), (board_x + 16, centers[0] + 17.5), arrowprops={"arrowstyle": "<->"})
    ax.text(board_x + 18, centers[0], "35 mm", rotation=90, ha="left", va="center", fontsize=9)
    ax.annotate("", (length - 20, centers[0]), (length - 20, centers[1]), arrowprops={"arrowstyle": "<->"})
    ax.text(length - 18, width / 2, "60.96 mm riser centers", rotation=90, ha="left", va="center", fontsize=9)

    if connectors_inside:
        ax.text(4, width - 5, "PCI bracket / rear end", ha="left", va="top", fontsize=10, weight="bold")
        ax.text(
            board_x + PCB_LENGTH + 3,
            width - 5,
            "Connectors and wiring channels face inside",
            ha="left",
            va="top",
            fontsize=10,
            weight="bold",
        )
    else:
        ax.text(4, width - 5, "Connector/service end", ha="left", va="top", fontsize=10, weight="bold")
    ax.set_xlim(-5, length + 5)
    ax.set_ylim(-5, width + 5)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("X (mm) — card length direction")
    ax.set_ylabel("Y (mm) — enclosure width")
    ax.set_title(filename.replace("_", " ").replace(".png", ""))
    ax.grid(True, linewidth=0.25, alpha=0.35)
    fig.tight_layout()
    fig.savefig(OUT / filename, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    gauge = make_fit_gauge()
    gauge_b = make_fit_gauge(connectors_inside=True)
    gauge_c = make_fit_gauge(connectors_inside=True, wide_tapered_recess=True)
    plate = make_full_plate()
    plate_b = make_full_plate(include_baffle_guides=True)
    plate_c = make_full_plate(include_baffle_guides=True, connectors_inside=True)
    plate_d = make_full_plate(
        include_baffle_guides=True,
        connectors_inside=True,
        plate_thickness=REV_D_PLATE_THICKNESS,
        riser_x=REV_D_RISER_X,
        wide_tapered_recess=True,
    )
    baffle = make_baffle_flat()
    short_baffle = make_baffle_flat(SHORT_BAFFLE_TOTAL_HEIGHT)
    validate_and_export(gauge, "dual_riser_fit_gauge_rev_a.stl")
    validate_and_export(gauge_b, "dual_riser_fit_gauge_rev_b.stl")
    validate_and_export(gauge_c, "dual_riser_fit_gauge_rev_c.stl")
    validate_and_export(plate, "dual_k10_bottom_plate_rev_a.stl")
    validate_and_export(plate_b, "dual_k10_bottom_plate_rev_b.stl")
    validate_and_export(plate_c, "dual_k10_bottom_plate_rev_c.stl")
    validate_and_export(plate_d, "dual_k10_bottom_plate_rev_d.stl")
    validate_and_export(baffle, "airflow_baffle_flat_rev_a_print_two.stl")
    validate_and_export(short_baffle, "airflow_baffle_flat_rev_b_135mm_print_two.stl")
    render_layout_diagram(
        "dual_riser_fit_gauge_rev_a.png", 150.0, 120.0, (150.0 - PCB_LENGTH) / 2, False
    )
    render_layout_diagram(
        "dual_riser_fit_gauge_rev_b.png",
        190.0,
        120.0,
        (190.0 - PCB_LENGTH) / 2,
        False,
        connectors_inside=True,
    )
    render_layout_diagram(
        "dual_riser_fit_gauge_rev_c.png",
        190.0,
        120.0,
        (190.0 - PCB_LENGTH) / 2,
        False,
        connectors_inside=True,
        wide_tapered_recess=True,
    )
    render_layout_diagram("dual_k10_bottom_plate_rev_a.png", PLATE_LENGTH, PLATE_WIDTH, RISER_X, True)
    render_layout_diagram(
        "dual_k10_bottom_plate_rev_b.png",
        PLATE_LENGTH,
        PLATE_WIDTH,
        RISER_X,
        True,
        include_baffle_guides=True,
    )
    render_layout_diagram(
        "dual_k10_bottom_plate_rev_c.png",
        PLATE_LENGTH,
        PLATE_WIDTH,
        RISER_X,
        True,
        include_baffle_guides=True,
        connectors_inside=True,
    )
    render_layout_diagram(
        "dual_k10_bottom_plate_rev_d.png",
        PLATE_LENGTH,
        PLATE_WIDTH,
        REV_D_RISER_X,
        True,
        include_baffle_guides=True,
        connectors_inside=True,
        wide_tapered_recess=True,
    )
