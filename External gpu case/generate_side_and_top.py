"""Generate universal side walls and the matching top for the dual-K10 case.

Print two identical side walls. Rotate the second copy 180 degrees end-for-end
for the opposite side; no mirrored STL is required. Coordinates use the full
assembled outer envelope, including the 4 mm front/rear and side faces.
All dimensions are millimetres.
"""

from math import pi
from pathlib import Path

import trimesh

from generate_front_panel import (
    BASE_PLATE_THICKNESS,
    FACE_THICKNESS,
    FASTENER_DIAMETER,
    PANEL_HEIGHT,
    PANEL_WIDTH,
    RETURN_DEPTH,
    RETURN_THICKNESS,
    axis_cylinder,
    box,
    validate_and_export,
)


OUT = Path(__file__).resolve().parent
BASE_LENGTH = 320.0
BASE_WIDTH = 180.0

# The front and rear faces sit outside the 320 mm base. The two side faces sit
# outside its 180 mm width, producing the complete shell envelope below.
SHELL_LENGTH = BASE_LENGTH + 2 * FACE_THICKNESS
SHELL_WIDTH = BASE_WIDTH + 2 * FACE_THICKNESS

RETURN_TOTAL_DEPTH = FACE_THICKNESS + RETURN_DEPTH
FLANGE_START_X = RETURN_TOTAL_DEPTH
FLANGE_END_X = SHELL_LENGTH - RETURN_TOTAL_DEPTH
FLANGE_LENGTH = FLANGE_END_X - FLANGE_START_X
FLANGE_HOLE_INSET = FACE_THICKNESS + 7.5

# Base hole locations translated by the 4 mm outer front face.
SIDE_FLANGE_HOLES_X = (64.0, 164.0, 264.0)
END_WALL_HOLES_X = (FLANGE_HOLE_INSET, SHELL_LENGTH - FLANGE_HOLE_INSET)
END_WALL_HOLES_Z = (35.0, 75.0, 115.0)

# Top holes matching the front/rear top returns and the two universal sides.
TOP_FRONT_REAR_HOLES_X = END_WALL_HOLES_X
TOP_FRONT_REAR_HOLES_Y = (34.0, 94.0, 154.0)
TOP_SIDE_HOLES_X = SIDE_FLANGE_HOLES_X
TOP_SIDE_HOLES_Y = (FLANGE_HOLE_INSET, SHELL_WIDTH - FLANGE_HOLE_INSET)


def make_universal_side_installed():
    """Build one side; the same part rotates end-for-end for the other side."""
    solids = [
        box(
            (SHELL_LENGTH, FACE_THICKNESS, PANEL_HEIGHT),
            (SHELL_LENGTH / 2, FACE_THICKNESS / 2, PANEL_HEIGHT / 2),
        ),
        # End notches prevent these flanges overlapping front/rear returns.
        box(
            (FLANGE_LENGTH, RETURN_DEPTH, RETURN_THICKNESS),
            (
                SHELL_LENGTH / 2,
                FACE_THICKNESS + RETURN_DEPTH / 2,
                BASE_PLATE_THICKNESS + RETURN_THICKNESS / 2,
            ),
        ),
        box(
            (FLANGE_LENGTH, RETURN_DEPTH, RETURN_THICKNESS),
            (
                SHELL_LENGTH / 2,
                FACE_THICKNESS + RETURN_DEPTH / 2,
                PANEL_HEIGHT - RETURN_THICKNESS / 2,
            ),
        ),
    ]
    body = trimesh.boolean.union(solids, engine="manifold")
    if body is None:
        raise RuntimeError("Universal-side union failed")

    cutters = []

    # Base and top holes use the same X pattern, making the part end-for-end
    # symmetric and therefore usable on either side.
    for x in SIDE_FLANGE_HOLES_X:
        cutters.append(
            axis_cylinder(
                "z",
                FASTENER_DIAMETER,
                RETURN_THICKNESS + 2,
                (x, FLANGE_HOLE_INSET, BASE_PLATE_THICKNESS + RETURN_THICKNESS / 2),
            )
        )
        cutters.append(
            axis_cylinder(
                "z",
                FASTENER_DIAMETER,
                RETURN_THICKNESS + 2,
                (x, FLANGE_HOLE_INSET, PANEL_HEIGHT - RETURN_THICKNESS / 2),
            )
        )

    # These holes match the front and rear wall side-return holes.
    for x in END_WALL_HOLES_X:
        for z in END_WALL_HOLES_Z:
            cutters.append(
                axis_cylinder(
                    "y",
                    FASTENER_DIAMETER,
                    FACE_THICKNESS + 2,
                    (x, FACE_THICKNESS / 2, z),
                )
            )

    side = trimesh.boolean.difference([body, *cutters], engine="manifold")
    if side is None:
        raise RuntimeError("Universal-side subtraction failed")
    return side


def lay_side_face_on_bed(mesh):
    flat = mesh.copy()
    flat.apply_transform(trimesh.transformations.rotation_matrix(pi / 2, [1, 0, 0]))
    flat.apply_translation(-flat.bounds[0])
    return flat


def make_top_installed():
    top = box(
        (SHELL_LENGTH, SHELL_WIDTH, RETURN_THICKNESS),
        (SHELL_LENGTH / 2, SHELL_WIDTH / 2, PANEL_HEIGHT + RETURN_THICKNESS / 2),
    )
    cutters = []

    for x in TOP_FRONT_REAR_HOLES_X:
        for y in TOP_FRONT_REAR_HOLES_Y:
            cutters.append(
                axis_cylinder(
                    "z",
                    FASTENER_DIAMETER,
                    RETURN_THICKNESS + 2,
                    (x, y, PANEL_HEIGHT + RETURN_THICKNESS / 2),
                )
            )

    for y in TOP_SIDE_HOLES_Y:
        for x in TOP_SIDE_HOLES_X:
            cutters.append(
                axis_cylinder(
                    "z",
                    FASTENER_DIAMETER,
                    RETURN_THICKNESS + 2,
                    (x, y, PANEL_HEIGHT + RETURN_THICKNESS / 2),
                )
            )

    top = trimesh.boolean.difference([top, *cutters], engine="manifold")
    if top is None:
        raise RuntimeError("Top-panel subtraction failed")
    return top


def lay_top_on_bed(mesh):
    flat = mesh.copy()
    flat.apply_translation(-flat.bounds[0])
    return flat


def render_side_diagram(filename):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Rectangle

    fig, ax = plt.subplots(figsize=(12, 5.5), dpi=180)
    ax.add_patch(
        Rectangle(
            (0, 0),
            SHELL_LENGTH,
            PANEL_HEIGHT,
            facecolor="#dcecf6",
            edgecolor="#16384d",
            linewidth=2,
        )
    )
    for x in END_WALL_HOLES_X:
        for z in END_WALL_HOLES_Z:
            ax.add_patch(Circle((x, z), FASTENER_DIAMETER / 2, color="#8b2f2f"))
    for x in SIDE_FLANGE_HOLES_X:
        ax.add_patch(Circle((x, 12.0), FASTENER_DIAMETER / 2, color="#315f9b"))
        ax.add_patch(Circle((x, 148.0), FASTENER_DIAMETER / 2, color="#2d7a3f"))
    ax.axvline(FLANGE_START_X, color="#6b3f91", linestyle="--", linewidth=1)
    ax.axvline(FLANGE_END_X, color="#6b3f91", linestyle="--", linewidth=1)
    ax.text(SHELL_LENGTH / 2, 75, "same STL for left and right\nrotate second copy end-for-end", ha="center", va="center")
    ax.text(SHELL_LENGTH / 2, 143, "top flange: 3 holes", ha="center", color="#2d7a3f")
    ax.text(SHELL_LENGTH / 2, 17, "base flange: 3 holes", ha="center", color="#315f9b")
    ax.set_xlim(-5, SHELL_LENGTH + 5)
    ax.set_ylim(-5, PANEL_HEIGHT + 5)
    ax.set_aspect("equal")
    ax.set_xlabel("assembled shell length (mm)")
    ax.set_ylabel("height from base bottom (mm)")
    ax.set_title("Universal side panel Rev A - print two identical copies")
    ax.grid(True, linewidth=0.25, alpha=0.35)
    fig.tight_layout()
    fig.savefig(OUT / filename, bbox_inches="tight")
    plt.close(fig)


def render_top_diagram(filename):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Rectangle

    fig, ax = plt.subplots(figsize=(12, 7), dpi=180)
    ax.add_patch(
        Rectangle(
            (0, 0),
            SHELL_LENGTH,
            SHELL_WIDTH,
            facecolor="#dcecf6",
            edgecolor="#16384d",
            linewidth=2,
        )
    )
    for x in TOP_FRONT_REAR_HOLES_X:
        for y in TOP_FRONT_REAR_HOLES_Y:
            ax.add_patch(Circle((x, y), FASTENER_DIAMETER / 2, color="#8b2f2f"))
    for y in TOP_SIDE_HOLES_Y:
        for x in TOP_SIDE_HOLES_X:
            ax.add_patch(Circle((x, y), FASTENER_DIAMETER / 2, color="#2d7a3f"))
    ax.text(SHELL_LENGTH / 2, SHELL_WIDTH / 2, "328 x 188 x 4 mm top", ha="center", va="center", fontsize=11)
    ax.text(22, SHELL_WIDTH / 2, "front/rear holes", ha="center", va="center", rotation=90, color="#8b2f2f")
    ax.text(SHELL_LENGTH / 2, 20, "side holes", ha="center", color="#2d7a3f")
    ax.set_xlim(-5, SHELL_LENGTH + 5)
    ax.set_ylim(-5, SHELL_WIDTH + 5)
    ax.set_aspect("equal")
    ax.set_xlabel("shell length (mm)")
    ax.set_ylabel("shell width (mm)")
    ax.set_title("Top panel Rev A")
    ax.grid(True, linewidth=0.25, alpha=0.35)
    fig.tight_layout()
    fig.savefig(OUT / filename, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    side_installed = make_universal_side_installed()
    side_flat = lay_side_face_on_bed(side_installed)
    lower_gauge_region = box(
        (SHELL_LENGTH, 40.0, 45.0),
        (SHELL_LENGTH / 2, 10.0, 22.5),
    )
    lower_gauge = trimesh.boolean.intersection(
        [side_installed, lower_gauge_region], engine="manifold"
    )
    if lower_gauge is None:
        raise RuntimeError("Universal-side lower fit-gauge intersection failed")
    lower_gauge_flat = lay_side_face_on_bed(lower_gauge)
    top_installed = make_top_installed()
    top_flat = lay_top_on_bed(top_installed)

    validate_and_export(side_installed, "side_panel_universal_rev_a_installed_orientation.stl")
    validate_and_export(side_flat, "side_panel_universal_rev_a_print_flat_print_two.stl")
    validate_and_export(lower_gauge_flat, "side_panel_universal_rev_a_lower_fit_gauge.stl")
    validate_and_export(top_installed, "top_panel_rev_a_installed_orientation.stl")
    validate_and_export(top_flat, "top_panel_rev_a_print_flat.stl")
    render_side_diagram("side_panel_universal_rev_a.png")
    render_top_diagram("top_panel_rev_a.png")
