import numpy as np
import pandas as pd

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies production feature engineering transformations to raw cartographic inputs.
    
    Generates:
    1. Euclidean_Distance_To_Hydrology: 3D straight-line distance to water.
    2. Elevation_Minus_VDist_Hydrology: True elevation of local water table.
    3. Aspect_Sin & Aspect_Cos: Smooth cyclical azimuth representation (0 to 360 deg).
    4. Mean_Distance_To_Amenities: Average proximity to water, roadways, and fire points.
    5. Hillshade_Range: Diurnal solar exposure variance (Noon minus 9am).
    """
    df_out = df.copy()

    # 1. 3D Euclidean distance to water
    df_out["Euclidean_Distance_To_Hydrology"] = np.sqrt(
        df_out["Horizontal_Distance_To_Hydrology"]**2 + 
        df_out["Vertical_Distance_To_Hydrology"]**2
    )

    # 2. Water elevation
    df_out["Elevation_Minus_VDist_Hydrology"] = (
        df_out["Elevation"] - df_out["Vertical_Distance_To_Hydrology"]
    )

    # 3. Cyclical Aspect encodings
    df_out["Aspect_Sin"] = np.sin(df_out["Aspect"] * np.pi / 180.0)
    df_out["Aspect_Cos"] = np.cos(df_out["Aspect"] * np.pi / 180.0)

    # 4. Mean distance to amenities
    df_out["Mean_Distance_To_Amenities"] = (
        df_out["Horizontal_Distance_To_Hydrology"] + 
        df_out["Horizontal_Distance_To_Roadways"] + 
        df_out["Horizontal_Distance_To_Fire_Points"]
    ) / 3.0

    # 5. Hillshade diurnal range
    df_out["Hillshade_Range"] = df_out["Hillshade_Noon"] - df_out["Hillshade_9am"]

    return df_out
