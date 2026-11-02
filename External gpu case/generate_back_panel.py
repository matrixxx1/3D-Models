"""Generate the vent-clear, GPU-locating dual-K10 enclosure back panel.

Rev G preserves the physically confirmed Rev B base and shell interfaces,
exposes both GPU exhausts, provides future shroud mounting holes, and adds
inward open-bottom locating lips for both cards. All dimensions are millimetres.
"""

from pathlib import Path

import trimesh

from generate_front_panel import (
    BASE_PLATE_THICKNESS,
    FACE_THICKNESS,
    FASTENER_DIAMETER,
    FLANGE_HOLE_X,
    PANEL_HEIGHT,
    PANEL_WIDTH,
    RETURN_DEPTH,
    RETURN_THICKNESS,
    axis_cylinder,
    box,
    lay_front_face_on_bed,
    validate_and_export,
)


BASE_HOLE_CENTERS_Y = (30.0, 90.0, 150.0)
BOTTOM_TAB_WIDTH = 18.0
# The baffle grooves begin 15.4 mm inward from the plate edge. A face plus an
# 11 mm tab ends at X=15 mm, preserving a small assembly clearance.
BOTTOM_TAB_DEPTH = 11.0

GPU_CENTERS_Y = (50.0, 110.0)
VENT_WIDTH = 48.0
VENT_BOTTOM_Z = 13.0
VENT_TOP_Z = 129.0
VENT_HEIGHT = VENT_TOP_Z - VENT_BOTTOM_Z

SHROUD_HOLE_DIAMETER = 4.5
SHROUD_HOLE_POSITIONS = (
    (18.0, 25.0),
    (18.0, 85.0),
    (18.0, 145.0),
    (162.0, 25.0),
    (162.0, 85.0),
    (162.0, 145.0),
)

LOCATING_LIP_WALL = 3.0
LOCATING_LIP_PROJECTION = 10.0


def make_back_panel_installed():
    lip_depth = LOCATING_LIP_PROJECTION + 0.4
    lip_x = FACE_THICKNESS - 0.2 + lip_depth / 2
    lip_outer_width = VENT_WIDTH + 2 * LOCATING_LIP_WALL
    solids = [
        box(
            (FACE_THICKNESS, PANEL_WIDTH, PANEL_HEIGHT),
            (FACE_THICKNESS / 2, PANEL_WIDTH / 2, PANEL_HEIGHT / 2),
        ),
        # Three isolated base tabs leave the GPU bracket bays unobstructed.
        *[
            box(
                (BOTTOM_TAB_DEPTH, BOTTOM_TAB_WIDTH, RETURN_THICKNESS),
                (
                    FACE_THICKNESS + BOTTOM_TAB_DEPTH / 2,
                    y,
                    BASE_PLATE_THICKNESS + RETURN_THICKNESS / 2,
                ),
            )
            for y in BASE_HOLE_CENTERS_Y
        ],
        # Side and top returns retain the shell attachment interface.
        box(
            (RETURN_DEPTH, RETURN_THICKNESS, PANEL_HEIGHT - BASE_PLATE_THICKNESS),
            (
                FACE_THICKNESS + RETURN_DEPTH / 2,
                RETURN_THICKNESS / 2,
                BASE_PLATE_THICKNESS + (PANEL_HEIGHT - BASE_PLATE_THICKNESS) / 2,
            ),
        ),
        box(
            (RETURN_DEPTH, RETURN_THICKNESS, PANEL_HEIGHT - BASE_PLATE_THICKNESS),
            (
                FACE_THICKNESS + RETURN_DEPTH / 2,
                PANEL_WIDTH - RETURN_THICKNESS / 2,
                BASE_PLATE_THICKNESS + (PANEL_HEIGHT - BASE_PLATE_THICKNESS) / 2,
            ),
        ),
        box(
            (RETURN_DEPTH, PANEL_WIDTH, RETURN_THICKNESS),
            (
                FACE_THICKNESS + RETURN_DEPTH / 2,
                PANEL_WIDTH / 2,
                PANEL_HEIGHT - RETURN_THICKNESS / 2,
            ),
        ),
        # Open-bottom U-shaped lips locate the sides and tops of both cards.
        # Their inner edges are flush with the openings, while the missing
        # lower rail lets the card bottoms pass through unobstructed.
        *[
            part
            for y in GPU_CENTERS_Y
            for part in (
                box(
                    (lip_depth, LOCATING_LIP_WALL, VENT_HEIGHT),
                    (lip_x, y - VENT_WIDTH / 2 - LOCATING_LIP_WALL / 2, VENT_BOTTOM_Z + VENT_HEIGHT / 2),
                ),
                box(
                    (lip_depth, LOCATING_LIP_WALL, VENT_HEIGHT),
                    (lip_x, y + VENT_WIDTH / 2 + LOCATING_LIP_WALL / 2, VENT_BOTTOM_Z + VENT_HEIGHT / 2),
                ),
                box(
                    (lip_depth, lip_outer_width, LOCATING_LIP_WALL),
                    (lip_x, y, VENT_TOP_Z + LOCATING_LIP_WALL / 2),
                ),
            )
        ],
    ]
    body = trimesh.boolean.union(solids, engine="manifold")
    if body is None:
        raise RuntimeError("Back-panel union failed")

    # Rectangular openings provide margin around the measured K10 exhausts and
    # remove the circular fan opening that partially covered both vents.
    cutters = [
        box(
            (FACE_THICKNESS + 4, VENT_WIDTH, VENT_HEIGHT),
            (FACE_THICKNESS / 2, y, VENT_BOTTOM_Z + VENT_HEIGHT / 2),
        )
        for y in GPU_CENTERS_Y
    ]

    # Six M4-clearance holes reserve a symmetric interface for a future shroud.
    for y, z in SHROUD_HOLE_POSITIONS:
        cutters.append(
            axis_cylinder(
                "x",
                SHROUD_HOLE_DIAMETER,
                FACE_THICKNESS + 4,
                (FACE_THICKNESS / 2, y, z),
            )
        )

    for y in BASE_HOLE_CENTERS_Y:
        cutters.append(
            axis_cylinder(
                "z",
                FASTENER_DIAMETER,
                RETURN_THICKNESS + 2,
                (FLANGE_HOLE_X, y, BASE_PLATE_THICKNESS + RETURN_THICKNESS / 2),
            )
        )

    for y in (RETURN_THICKNESS / 2, PANEL_WIDTH - RETURN_THICKNESS / 2):
        for z in (35.0, 75.0, 115.0):
            cutters.append(
                axis_cylinder(
                    "y",
                    FASTENER_DIAMETER,
                    RETURN_THICKNESS + 2,
                    (FLANGE_HOLE_X, y, z),
                )
            )

    for y in BASE_HOLE_CENTERS_Y:
        cutters.append(
            axis_cylinder(
                "z",
                FASTENER_DIAMETER,
                RETURN_THICKNESS + 2,
                (FLANGE_HOLE_X, y, PANEL_HEIGHT - RETURN_THICKNESS / 2),
            )
        )

    panel = trimesh.boolean.difference([body, *cutters], engine="manifold")
    if panel is None:
        raise RuntimeError("Back-panel subtraction failed")
    return panel


def render_base_tab_plan(filename):
    """Render a top view of the corrected rear mounting interface."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Rectangle

    fig, ax = plt.subplots(figsize=(10, 3.5), dpi=180)
    ax.add_patch(
        Rectangle((0, 0), PANEL_WIDTH, FACE_THICKNESS, facecolor="#5b8eaa", edgecolor="#16384d")
    )
    for y in BASE_HOLE_CENTERS_Y:
        ax.add_patch(
            Rectangle(
                (y - BOTTOM_TAB_WIDTH / 2, FACE_THICKNESS),
                BOTTOM_TAB_WIDTH,
                BOTTOM_TAB_DEPTH,
                facecolor="#82bfd8",
                edgecolor="#16384d",
            )
        )
        ax.add_patch(Circle((y, FLANGE_HOLE_X), FASTENER_DIAMETER / 2, color="#8b2f2f"))
    for y in (0, PANEL_WIDTH - RETURN_THICKNESS):
        ax.add_patch(
            Rectangle(
                (y, FACE_THICKNESS),
                RETURN_THICKNESS,
                RETURN_DEPTH,
                facecolor="#82bfd8",
                edgecolor="#16384d",
            )
        )
    ax.axhline(15.4, color="#6b3f91", linestyle="--", linewidth=1.5, label="baffle groove starts")
    ax.text(60, 9.5, "42 mm card-clear bay", ha="center", va="center", fontsize=9)
    ax.text(120, 9.5, "42 mm card-clear bay", ha="center", va="center", fontsize=9)
    ax.set_xlim(-5, PANEL_WIDTH + 5)
    ax.set_ylim(-2, 22)
    ax.set_aspect("equal")
    ax.set_xlabel("panel width (mm)")
    ax.set_ylabel("inward depth (mm)")
    ax.set_title("Back panel Rev G - confirmed segmented base tabs, top view")
    ax.grid(True, linewidth=0.25, alpha=0.35)
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(Path(__file__).resolve().parent / filename, bbox_inches="tight")
    plt.close(fig)


def render_back_elevation(filename):
    """Render the vent, peg, and future-shroud interfaces from the rear."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Rectangle

    fig, ax = plt.subplots(figsize=(9, 7.5), dpi=180)
    ax.add_patch(
        Rectangle(
            (0, 0),
            PANEL_WIDTH,
            PANEL_HEIGHT,
            facecolor="#dcecf6",
            edgecolor="#16384d",
            linewidth=2,
        )
    )
    for y in GPU_CENTERS_Y:
        ax.add_patch(
            Rectangle(
                (y - VENT_WIDTH / 2, VENT_BOTTOM_Z),
                VENT_WIDTH,
                VENT_HEIGHT,
                facecolor="#f7fbfd",
                edgecolor="#0f4f73",
                linewidth=2,
            )
        )
        ax.text(
            y,
            VENT_BOTTOM_Z + VENT_HEIGHT / 2,
            f"GPU exhaust\n{VENT_WIDTH:.0f} x {VENT_HEIGHT:.0f}",
            ha="center",
            va="center",
            fontsize=8,
        )
    for y, z in SHROUD_HOLE_POSITIONS:
        ax.add_patch(
            Circle(
                (y, z),
                SHROUD_HOLE_DIAMETER / 2,
                facecolor="#8b2f2f",
                edgecolor="#5a1717",
            )
        )
    for y in GPU_CENTERS_Y:
        ax.add_patch(
            Rectangle(
                (y - VENT_WIDTH / 2 - LOCATING_LIP_WALL, VENT_BOTTOM_Z),
                LOCATING_LIP_WALL,
                VENT_HEIGHT,
                facecolor="#5ea66f",
                edgecolor="#2d7a3f",
                linewidth=1,
            )
        )
        ax.add_patch(
            Rectangle(
                (y + VENT_WIDTH / 2, VENT_BOTTOM_Z),
                LOCATING_LIP_WALL,
                VENT_HEIGHT,
                facecolor="#5ea66f",
                edgecolor="#2d7a3f",
                linewidth=1,
            )
        )
        ax.add_patch(
            Rectangle(
                (y - VENT_WIDTH / 2 - LOCATING_LIP_WALL, VENT_TOP_Z),
                VENT_WIDTH + 2 * LOCATING_LIP_WALL,
                LOCATING_LIP_WALL,
                facecolor="#5ea66f",
                edgecolor="#2d7a3f",
                linewidth=1,
            )
        )
    ax.text(90, 145, "6 x M4 shroud holes", ha="center", va="center", fontsize=8)
    ax.text(90, 138, "10 mm-deep open-bottom locating lips", ha="center", va="center", fontsize=8)
    ax.axhline(BASE_PLATE_THICKNESS, color="#555", linestyle="--", linewidth=1)
    ax.text(4, BASE_PLATE_THICKNESS + 2, "plate top", fontsize=8, va="bottom")
    ax.set_xlim(-5, PANEL_WIDTH + 5)
    ax.set_ylim(-5, PANEL_HEIGHT + 5)
    ax.set_aspect("equal")
    ax.set_xlabel("panel width (mm)")
    ax.set_ylabel("height from base bottom (mm)")
    ax.set_title("dual K10 back panel Rev G")
    ax.grid(True, linewidth=0.25, alpha=0.35)
    fig.tight_layout()
    fig.savefig(Path(__file__).resolve().parent / filename, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    installed = make_back_panel_installed()
    print_flat = lay_front_face_on_bed(installed)
    # One complete GPU bay is enough to verify the repeated locating-lip
    # geometry while keeping the test print much smaller than the full panel.
    peg_gauge_region = box((40.0, 70.0, 127.0), (10.0, GPU_CENTERS_Y[0], 71.5))
    peg_gauge = trimesh.boolean.intersection([installed, peg_gauge_region], engine="manifold")
    if peg_gauge is None:
        raise RuntimeError("Back-panel vent/lip fit-gauge intersection failed")
    peg_gauge_flat = lay_front_face_on_bed(peg_gauge)
    validate_and_export(installed, "back_panel_rev_g_installed_orientation.stl")
    validate_and_export(print_flat, "back_panel_rev_g_print_flat.stl")
    validate_and_export(peg_gauge_flat, "back_panel_rev_g_single_gpu_vent_lip_fit_gauge.stl")
    render_back_elevation("back_panel_rev_g.png")
    render_base_tab_plan("back_panel_rev_g_base_tabs.png")
