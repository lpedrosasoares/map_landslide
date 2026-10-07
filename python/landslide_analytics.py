import math
import warnings

import geopandas as gpd
import numpy as np

from shapely.geometry import Point, Polygon
from shapely.affinity import rotate, translate


# ============================================================
# 1. LOAD DATA
# ============================================================

def load_data(path, epsg=None):
    """
    Load vector data, remove missing/empty geometries,
    and optionally reproject.
    """

    gdf = gpd.read_file(path)

    total = len(gdf)

    # --------------------------------------------------------
    # Remove missing geometries
    # --------------------------------------------------------

    missing = gdf.geometry.isna().sum()

    gdf = gdf[
        ~gdf.geometry.isna()
    ].copy()

    # --------------------------------------------------------
    # Remove empty geometries
    # --------------------------------------------------------

    empty = gdf.geometry.is_empty.sum()

    gdf = gdf[
        ~gdf.geometry.is_empty
    ].copy()

    # --------------------------------------------------------
    # Reproject
    # --------------------------------------------------------

    if epsg is not None:
        gdf = gdf.to_crs(epsg=epsg)

    gdf = gdf.reset_index(drop=True)

    removed = total - len(gdf)

    # --------------------------------------------------------
    # Print information
    # --------------------------------------------------------

    print(f"Loaded: {total:,} features")
    print(f"Missing geometries removed: {missing:,}")
    print(f"Empty geometries removed: {empty:,}")
    print(f"Total removed: {removed:,}")
    print(f"Valid geometries: {len(gdf):,}")

    if epsg is not None:
        print(f"CRS: EPSG:{epsg}")

    return gdf


# ============================================================
# 2. BASIC METRICS
# ============================================================

def calculate_basic_metrics(gdf):

    gdf = gdf.copy()

    centroid = gdf.geometry.centroid

    gdf["xCentroid"] = centroid.x
    gdf["yCentroid"] = centroid.y

    gdf["LSArea"] = gdf.geometry.area
    gdf["LSPerim"] = gdf.geometry.length

    gdf["convex_hull"] = gdf.geometry.convex_hull

    gdf["CH_Area"] = gdf["convex_hull"].area
    gdf["CH_Perim"] = gdf["convex_hull"].length

    return gdf


# ============================================================
# 3. LWR
# ============================================================

def calc_lwr(area, perimeter):

    discriminant = (
        perimeter**4
        - 16 * np.pi**2 * area**2
    )

    if discriminant <= 0:
        return np.nan

    denominator = (
        perimeter**2
        - np.sqrt(discriminant)
    )

    if denominator <= 0:
        return np.nan

    return (
        4 * np.pi * area
    ) / denominator


def calculate_lwr(gdf):

    gdf = gdf.copy()

    gdf["LWR"] = [
        calc_lwr(area, perimeter)
        for area, perimeter
        in zip(gdf["LSArea"], gdf["LSPerim"])
    ]

    return gdf


# ============================================================
# 4. LENGTH / WIDTH
# ============================================================

def calculate_length_width(gdf):

    gdf = gdf.copy()

    # Dimensions derived from convex hull
    gdf["L"] = 2 * np.sqrt(
        (
            gdf["CH_Area"]
            * gdf["LWR"]
        ) / np.pi
    )

    gdf["W"] = 2 * np.sqrt(
        gdf["CH_Area"]
        / (np.pi * gdf["LWR"])
    )

    # Scale dimensions to original landslide area
    scale_factor = np.sqrt(
        gdf["LSArea"]
        / gdf["CH_Area"]
    )

    gdf["L_sc"] = gdf["L"] * scale_factor
    gdf["W_sc"] = gdf["W"] * scale_factor

    return gdf


# ============================================================
# 5. MINIMUM ROTATED RECTANGLE
# ============================================================

def calculate_minimum_rectangle(gdf):

    gdf = gdf.copy()

    # GeoPandas version where this is a method
    gdf["mrr"] = (
        gdf.geometry
        .minimum_rotated_rectangle()
    )

    return gdf


# ============================================================
# 6. MRR DIMENSIONS
# ============================================================

def calculate_mrr_dimensions(gdf):

    gdf = gdf.copy()

    lengths = []
    widths = []

    for geom in gdf.geometry:

        if geom is None or geom.is_empty:
            lengths.append(np.nan)
            widths.append(np.nan)
            continue

        # Shapely geometry:
        # minimum_rotated_rectangle is a property
        rect = geom.minimum_rotated_rectangle

        coords = list(rect.exterior.coords)[:-1]

        if len(coords) != 4:
            lengths.append(np.nan)
            widths.append(np.nan)
            continue

        sides = []

        for i in range(4):

            x1, y1 = coords[i]
            x2, y2 = coords[(i + 1) % 4]

            length = math.hypot(
                x2 - x1,
                y2 - y1
            )

            sides.append(length)

        sides = sorted(sides)

        width = np.mean(
            sides[:2]
        )

        length = np.mean(
            sides[2:]
        )

        lengths.append(length)
        widths.append(width)

    gdf["mrr_length"] = lengths
    gdf["mrr_width"] = widths

    return gdf


# ============================================================
# 7. ORIENTATION
# ============================================================

def calculate_orientation(gdf):

    gdf = gdf.copy()

    def get_angle(rectangle):

        if rectangle is None:
            return np.nan

        if rectangle.is_empty:
            return np.nan

        coords = list(
            rectangle.exterior.coords
        )

        if len(coords) < 2:
            return np.nan

        x1, y1 = coords[0]
        x2, y2 = coords[1]

        dx = x2 - x1
        dy = y2 - y1

        angle = np.degrees(
            np.arctan2(dy, dx)
        )

        # 0–180 degrees
        angle = angle % 180

        return angle

    # GeoSeries method
    gdf["mrr"] = (
        gdf.geometry
        .minimum_rotated_rectangle()
    )

    gdf["angle"] = (
        gdf["mrr"]
        .apply(get_angle)
    )

    gdf["MBG_Orientation"] = gdf["angle"]

    return gdf


# ============================================================
# 8. CREATE ELLIPSE
# ============================================================

def make_ellipse(
    xc,
    yc,
    length,
    width,
    angle_deg,
    n_points=200
):
    """
    Create an ellipse polygon.
    """

    if (
        pd_isna(xc)
        or pd_isna(yc)
        or pd_isna(length)
        or pd_isna(width)
        or pd_isna(angle_deg)
    ):
        return None

    if length <= 0 or width <= 0:
        return None

    a = length / 2
    b = width / 2

    theta = np.linspace(
        0,
        2 * np.pi,
        n_points
    )

    x = a * np.cos(theta)
    y = b * np.sin(theta)

    ellipse = Polygon(
        zip(x, y)
    )

    ellipse = rotate(
        ellipse,
        angle_deg,
        origin=(0, 0),
        use_radians=False
    )

    ellipse = translate(
        ellipse,
        xc,
        yc
    )

    return ellipse


def pd_isna(value):

    return value is None or (
        isinstance(value, (float, np.floating))
        and np.isnan(value)
    )


# ============================================================
# 9. ELLIPSE
# ============================================================

def calculate_ellipse(gdf):

    gdf = gdf.copy()

    ellipses = []

    for (
        xc,
        yc,
        length,
        width,
        angle
    ) in zip(
        gdf["xCentroid"],
        gdf["yCentroid"],
        gdf["L_sc"],
        gdf["W_sc"],
        gdf["angle"]
    ):

        ellipse = make_ellipse(
            xc,
            yc,
            length,
            width,
            angle
        )

        ellipses.append(ellipse)

    gdf["ellipse"] = ellipses

    return gdf


# ============================================================
# 10. ELLIPTICAL METRICS
# ============================================================

def calculate_elliptical_metrics(gdf):

    gdf = gdf.copy()

    # --------------------------------------------------------
    # Ellipse dimensions
    # --------------------------------------------------------

    gdf["ellipse_L"] = gdf["L_sc"]
    gdf["ellipse_W"] = gdf["W_sc"]

    # --------------------------------------------------------
    # Area
    # --------------------------------------------------------

    gdf["ellipse_area"] = (
        np.pi
        * (gdf["ellipse_L"] / 2)
        * (gdf["ellipse_W"] / 2)
    )

    # --------------------------------------------------------
    # Length / width ratio
    # --------------------------------------------------------

    gdf["ellipse_LWR"] = (
        gdf["ellipse_L"]
        / gdf["ellipse_W"]
    )

    # --------------------------------------------------------
    # Axis ratio
    # --------------------------------------------------------

    gdf["ellipse_axis_ratio"] = (
        gdf["ellipse_W"]
        / gdf["ellipse_L"]
    )

    # --------------------------------------------------------
    # Eccentricity
    # --------------------------------------------------------

    a = gdf["ellipse_L"] / 2
    b = gdf["ellipse_W"] / 2

    ratio = (
        b / a
    ).clip(
        lower=0,
        upper=1
    )

    gdf["ellipse_eccentricity"] = np.sqrt(
        1 - ratio**2
    )

    # --------------------------------------------------------
    # Ellipse perimeter
    # Ramanujan approximation
    # --------------------------------------------------------

    h = (
        (a - b)**2
        / (a + b)**2
    )

    gdf["ellipse_perimeter"] = (
        np.pi
        * (a + b)
        * (
            1
            + (3 * h)
            / (
                10
                + np.sqrt(4 - 3 * h)
            )
        )
    )

    # --------------------------------------------------------
    # Landslide / ellipse area ratio
    # --------------------------------------------------------

    gdf["ellipse_area_ratio"] = (
        gdf["LSArea"]
        / gdf["ellipse_area"]
    )

    # --------------------------------------------------------
    # Ellipse circularity
    # --------------------------------------------------------

    gdf["ellipse_circularity"] = (
        4 * np.pi
        * gdf["ellipse_area"]
        / gdf["ellipse_perimeter"]**2
    )

    # --------------------------------------------------------
    # Intersection
    # --------------------------------------------------------

    intersection_area = []

    for geom, ellipse in zip(
        gdf.geometry,
        gdf["ellipse"]
    ):

        if (
            geom is None
            or ellipse is None
            or geom.is_empty
            or ellipse.is_empty
        ):
            intersection_area.append(
                np.nan
            )

        else:
            intersection_area.append(
                geom.intersection(
                    ellipse
                ).area
            )

    gdf["A_Intersection"] = (
        intersection_area
    )

    # --------------------------------------------------------
    # Intersection / landslide
    # --------------------------------------------------------

    gdf["intersection_ratio"] = (
        gdf["A_Intersection"]
        / gdf["LSArea"]
    )

    # --------------------------------------------------------
    # Intersection / ellipse
    # --------------------------------------------------------

    gdf["ellipse_overlap_ratio"] = (
        gdf["A_Intersection"]
        / gdf["ellipse_area"]
    )

    # --------------------------------------------------------
    # Ellipticity / shape similarity
    #
    # +1 = complete overlap
    #  0 = 50% overlap
    # -1 = no overlap
    # --------------------------------------------------------

    gdf["E"] = (
        1
        - 2
        * (
            (
                gdf["LSArea"]
                - gdf["A_Intersection"]
            )
            / gdf["LSArea"]
        )
    )

    return gdf


# ============================================================
# 11. CIRCULARITY
# ============================================================

def calculate_circularity(gdf):

    gdf = gdf.copy()

    gdf["circularity_index"] = (
        4
        * np.pi
        * gdf["LSArea"]
        / gdf["LSPerim"]**2
    )

    return gdf


# ============================================================
# 12. COMPLEXITY
# ============================================================

def calculate_complexity(gdf):

    gdf = gdf.copy()

    gdf["complexity_index"] = (
        gdf["CH_Area"]
        / gdf["LSArea"]
    )

    return gdf


# ============================================================
# 13. PERIMETER DENSITY
# ============================================================

def calculate_perimeter_density(gdf):

    gdf = gdf.copy()

    gdf["perimeter_density"] = (
        gdf["LSPerim"]**2
        / gdf["LSArea"]
    )

    return gdf


# ============================================================
# 14. MINIMUM BOUNDING CIRCLE
# ============================================================

def calculate_bounding_circle_ratio(gdf):

    gdf = gdf.copy()

    # GeoSeries method
    circles = (
        gdf.geometry
        .minimum_bounding_circle()
    )

    circle_area = circles.area

    gdf["ratio_area_bounding_circle"] = (
        gdf["LSArea"]
        / circle_area
    )

    return gdf


# ============================================================
# 15. RELATIVE ELONGATION
# ============================================================

def calculate_relative_elongation(gdf):

    gdf = gdf.copy()

    gdf["relative_elongation_index"] = (
        gdf["mrr_length"]
        - gdf["mrr_width"]
    ) / (
        gdf["mrr_length"]
        + gdf["mrr_width"]
    )

    return gdf


# ============================================================
# 16. ALL METRICS
# ============================================================

def calculate_all_metrics(gdf):

    print("\nCalculating morphology metrics...")

    # Basic
    gdf = calculate_basic_metrics(gdf)
    print("✓ Basic metrics")

    # LWR
    gdf = calculate_lwr(gdf)
    print("✓ LWR")

    # Length / width
    gdf = calculate_length_width(gdf)
    print("✓ Length / width")

    # Minimum rotated rectangle
    gdf = calculate_minimum_rectangle(gdf)
    print("✓ Minimum rotated rectangle")

    # MRR dimensions
    gdf = calculate_mrr_dimensions(gdf)
    print("✓ MRR dimensions")

    # Orientation
    gdf = calculate_orientation(gdf)
    print("✓ Orientation")

    # Ellipse
    gdf = calculate_ellipse(gdf)
    print("✓ Ellipse")

    # Elliptical metrics
    gdf = calculate_elliptical_metrics(gdf)
    print("✓ Elliptical metrics")

    # Circularity
    gdf = calculate_circularity(gdf)
    print("✓ Circularity")

    # Complexity
    gdf = calculate_complexity(gdf)
    print("✓ Complexity")

    # Perimeter density
    gdf = calculate_perimeter_density(gdf)
    print("✓ Perimeter density")

    # Bounding circle
    gdf = calculate_bounding_circle_ratio(gdf)
    print("✓ Bounding circle ratio")

    # Relative elongation
    gdf = calculate_relative_elongation(gdf)
    print("✓ Relative elongation")

    print(
        f"\nFinished. "
        f"{len(gdf):,} features × "
        f"{len(gdf.columns):,} columns"
    )

    return gdf


# ============================================================
# 17. SAVE RESULTS
# ============================================================

def save_results(gdf, output_path):

    gdf.to_file(
        output_path,
        driver="GPKG"
    )

    print(f"Saved: {output_path}")