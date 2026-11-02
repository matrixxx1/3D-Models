"""Generate the modular dual-K10 enclosure front panel.

The installed-coordinate model uses:
  X: enclosure depth, positive toward the cards
  Y: enclosure width, left-to-right
  Z: height from the bottom of the base plate

The exported print-flat STL is rotated onto its broad front face.
All dimensions are millimetres.
"""

from math import atan2, pi
from pathlib import Path

import numpy as np
import trimesh


OUT = Path(__file__).resolve().parent

PANEL_WIDTH = 180.0
PANEL_HEIGHT = 150.0
FACE_THICKNESS = 4.0
RETURN_DEPTH = 15.0
RETURN_THICKNESS = 4.0
BASE_PLATE_THICKNESS = 10.0

FAN_CENTER_Y = PANEL_WIDTH / 2
FAN_CENTER_Z = 87.5
FAN_OPENING_DIAMETER = 116.0
FAN_MOUNT_SPACING = 105.0
FAN_FASTENER_DIAMETER = 5.0

WIRE_PASSAGE_WIDTH = 30.0
WIRE_PASSAGE_HEIGHT = 20.0
WIRE_PASSAGE_CENTERS_Y = (50.0, 130.0)
SIDE_WIRE_PASSAGE_WIDTH = 20.0
SIDE_WIRE_PASSAGE_HEIGHT = 30.0
SIDE_WIRE_PASSAGE_CENTERS_Y = (16.0, 164.0)
SIDE_WIRE_PASSAGE_CENTER_Z = 90.0

FASTENER_DIAMETER = 4.5
FLANGE_HOLE_X = FACE_THICKNESS + 7.5


def box(size, center):
    mesh = trimesh.creation.box(extents=size)
    mesh.apply_translation(center)
    return mesh


def axis_cylinder(axis, diameter, length, center):
    mesh = trimesh.creation.cylinder(
        radius=diameter / 2,
        height=length,
        sections=48,
    )
    if axis == "x":
        mesh.apply_transform(trimesh.transformations.rotation_matrix(pi / 2, [0, 1, 0]))
    elif axis == "y":
        mesh.apply_transform(trimesh.transformations.rotation_matrix(pi / 2, [1, 0, 0]))
    elif axis != "z":
        raise ValueError(axis)
    mesh.apply_translation(center)
    return mesh


def diagonal_slot_cutters(y0, z0, y1, z1, depth):
    """Return three overlapping solids forming a capsule slot along Y/Z."""
    x_center = FACE_THICKNESS / 2
    cutters = [
        axis_cylinder("x", FAN_FASTENER_DIAMETER, depth, (x_center, y0, z0)),
        axis_cylinder("x", FAN_FASTENER_DIAMETER, depth, (x_center, y1, z1)),
    ]
    dy = y1 - y0
    dz = z1 - z0
    length = (dy * dy + dz * dz) ** 0.5
    bridge = box((depth, length, FAN_FASTENER_DIAMETER), (x_center, 0, 0))
    bridge.apply_transform(
        trimesh.transformations.rotation_matrix(atan2(dz, dy), [1, 0, 0])
    )
    bridge.apply_translation((0, (y0 + y1) / 2, (z0 + z1) / 2))
    cutters.append(bridge)
    return cutters


def make_front_panel_installed(include_wire_passages=True):
    # Front face is external at X=0. Returns project inward toward +X.
    solids = [
        box(
            (FACE_THICKNESS, PANEL_WIDTH, PANEL_HEIGHT),
            (FACE_THICKNESS / 2, PANEL_WIDTH / 2, PANEL_HEIGHT / 2),
        ),
        # Bottom foot rests on the 10 mm-thick base plate.
        box(
            (RETURN_DEPTH, PANEL_WIDTH, RETURN_THICKNESS),
            (
                FACE_THICKNESS + RETURN_DEPTH / 2,
                PANEL_WIDTH / 2,
                BASE_PLATE_THICKNESS + RETURN_THICKNESS / 2,
            ),
        ),
        # Left and right returns receive side-panel bolts.
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
        # Top return receives top-panel bolts.
        box(
            (RETURN_DEPTH, PANEL_WIDTH, RETURN_THICKNESS),
            (
                FACE_THICKNESS + RETURN_DEPTH / 2,
                PANEL_WIDTH / 2,
                PANEL_HEIGHT - RETURN_THICKNESS / 2,
            ),
        ),
    ]
    body = trimesh.boolean.union(solids, engine="manifold")
    if body is None:
        raise RuntimeError("Front-panel union failed")

    cutters = []

    # Main fan opening.
    cutters.append(
        axis_cylinder(
            "x",
            FAN_OPENING_DIAMETER,
            FACE_THICKNESS + 4,
            (FACE_THICKNESS / 2, FAN_CENTER_Y, FAN_CENTER_Z),
        )
    )

    # Fixed round holes match the actual 120 mm fan's standard 105 mm pattern.
    for sy in (-1, 1):
        for sz in (-1, 1):
            cutters.append(
                axis_cylinder(
                    "x",
                    FAN_FASTENER_DIAMETER,
                    FACE_THICKNESS + 4,
                    (
                        FACE_THICKNESS / 2,
                        FAN_CENTER_Y + sy * FAN_MOUNT_SPACING / 2,
                        FAN_CENTER_Z + sz * FAN_MOUNT_SPACING / 2,
                    ),
                )
            )

    if include_wire_passages:
        # Two independent bottom wire passages cut through the face and bottom foot.
        for wire_y in WIRE_PASSAGE_CENTERS_Y:
            cutters.append(
                box(
                    (RETURN_DEPTH + FACE_THICKNESS + 2, WIRE_PASSAGE_WIDTH, WIRE_PASSAGE_HEIGHT + 0.2),
                    (
                        (RETURN_DEPTH + FACE_THICKNESS) / 2,
                        wire_y,
                        BASE_PLATE_THICKNESS + WIRE_PASSAGE_HEIGHT / 2,
                    ),
                )
            )

        # Two additional vertical wire passages sit beside the fan frame.
        for wire_y in SIDE_WIRE_PASSAGE_CENTERS_Y:
            cutters.append(
                box(
                    (
                        RETURN_DEPTH + FACE_THICKNESS + 2,
                        SIDE_WIRE_PASSAGE_WIDTH,
                        SIDE_WIRE_PASSAGE_HEIGHT,
                    ),
                    (
                        (RETURN_DEPTH + FACE_THICKNESS) / 2,
                        wire_y,
                        SIDE_WIRE_PASSAGE_CENTER_Z,
                    ),
                )
            )

    # Three base-plate bolts align to the existing Rev D holes. Moving the wire
    # passage left of center restores use of the Y=90 fastener.
    for y in (30.0, 90.0, 150.0):
        cutters.append(
            axis_cylinder(
                "z",
                FASTENER_DIAMETER,
                RETURN_THICKNESS + 2,
                (FLANGE_HOLE_X, y, BASE_PLATE_THICKNESS + RETURN_THICKNESS / 2),
            )
        )

    # Side-panel through holes: three per side.
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

    # Top-panel through holes: three across the width.
    for y in (30.0, 90.0, 150.0):
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
        raise RuntimeError("Front-panel subtraction failed")
    return panel


def lay_front_face_on_bed(mesh):
    flat = mesh.copy()
    flat.apply_transform(trimesh.transformations.rotation_matrix(-pi / 2, [0, 1, 0]))
    flat.apply_translation(-flat.bounds[0])
    return flat


def validate_and_export(mesh, filename):
    if not mesh.is_watertight:
        raise RuntimeError(f"{filename} is not watertight")
    if not mesh.is_winding_consistent:
        raise RuntimeError(f"{filename} has inconsistent winding")
    if len(mesh.split()) != 1:
        raise RuntimeError(f"{filename} is not a single component")
    mesh.export(OUT / filename)
    print(
        f"{filename}: faces={len(mesh.faces)}, volume={mesh.volume:.1f} mm^3, "
        f"bounds={np.round(mesh.bounds, 3).tolist()}"
    )


def render_front_diagram(filename, include_wire_passages=True, title="dual K10 front panel Rev E"):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Rectangle

    fig, ax = plt.subplots(figsize=(8, 8), dpi=180)
    ax.add_patch(
        Rectangle((0, 0), PANEL_WIDTH, PANEL_HEIGHT, facecolor="#dcecf6", edgecolor="#16384d", linewidth=2)
    )
    ax.add_patch(
        Circle(
            (FAN_CENTER_Y, FAN_CENTER_Z),
            FAN_OPENING_DIAMETER / 2,
            facecolor="#eef7fb",
            edgecolor="#0f4f73",
            linewidth=2,
        )
    )
    for sy in (-1, 1):
        for sz in (-1, 1):
            ax.add_patch(
                Circle(
                    (
                        FAN_CENTER_Y + sy * FAN_MOUNT_SPACING / 2,
                        FAN_CENTER_Z + sz * FAN_MOUNT_SPACING / 2,
                    ),
                    FAN_FASTENER_DIAMETER / 2,
                    facecolor="#8b2f2f",
                    edgecolor="#5a1717",
                )
            )
    if include_wire_passages:
        for wire_y in WIRE_PASSAGE_CENTERS_Y:
            ax.add_patch(
                Rectangle(
                    (wire_y - WIRE_PASSAGE_WIDTH / 2, BASE_PLATE_THICKNESS),
                    WIRE_PASSAGE_WIDTH,
                    WIRE_PASSAGE_HEIGHT,
                    facecolor="#f1c86a",
                    edgecolor="#72520d",
                    linewidth=1.5,
                )
            )
        for wire_y in SIDE_WIRE_PASSAGE_CENTERS_Y:
            ax.add_patch(
                Rectangle(
                    (
                        wire_y - SIDE_WIRE_PASSAGE_WIDTH / 2,
                        SIDE_WIRE_PASSAGE_CENTER_Z - SIDE_WIRE_PASSAGE_HEIGHT / 2,
                    ),
                    SIDE_WIRE_PASSAGE_WIDTH,
                    SIDE_WIRE_PASSAGE_HEIGHT,
                    facecolor="#f1c86a",
                    edgecolor="#72520d",
                    linewidth=1.5,
                )
            )
    ax.axhline(BASE_PLATE_THICKNESS, color="#555", linestyle="--", linewidth=1)
    ax.text(4, BASE_PLATE_THICKNESS + 2, "plate top", fontsize=8, va="bottom")
    ax.text(
        FAN_CENTER_Y,
        FAN_CENTER_Z,
        "116 mm opening\n105 mm mounting pattern",
        ha="center",
        va="center",
        fontsize=9,
    )
    if include_wire_passages:
        ax.text(
            WIRE_PASSAGE_CENTERS_Y[0],
            BASE_PLATE_THICKNESS + WIRE_PASSAGE_HEIGHT / 2,
            "30 × 20",
            ha="center",
            va="center",
            fontsize=7,
        )
        ax.text(
            WIRE_PASSAGE_CENTERS_Y[1],
            BASE_PLATE_THICKNESS + WIRE_PASSAGE_HEIGHT / 2,
            "30 × 20",
            ha="center",
            va="center",
            fontsize=7,
        )
        for wire_y in SIDE_WIRE_PASSAGE_CENTERS_Y:
            ax.text(
                wire_y,
                SIDE_WIRE_PASSAGE_CENTER_Z,
                "20 × 30",
                ha="center",
                va="center",
                fontsize=7,
                rotation=90,
            )
    ax.set_xlim(-5, PANEL_WIDTH + 5)
    ax.set_ylim(-5, PANEL_HEIGHT + 5)
    ax.set_aspect("equal")
    ax.set_xlabel("panel width (mm)")
    ax.set_ylabel("height from base bottom (mm)")
    ax.set_title(title)
    ax.grid(True, linewidth=0.25, alpha=0.35)
    fig.tight_layout()
    fig.savefig(OUT / filename, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    installed = make_front_panel_installed()
    print_flat = lay_front_face_on_bed(installed)
    validate_and_export(installed, "front_panel_rev_e_installed_orientation.stl")
    validate_and_export(print_flat, "front_panel_rev_e_print_flat.stl")
    render_front_diagram("front_panel_rev_e.png")
