from typing import List, Optional
from pydantic import BaseModel, Field

class TerrainFeatures(BaseModel):
    """
    Standard input schema for a single terrain plot observation.
    Accepts the raw continuous cartographic features and categorical area/soil IDs.
    """
    Elevation: float = Field(..., description="Elevation in meters (1800 - 4000)", example=2596.0)
    Aspect: float = Field(..., description="Aspect in degrees azimuth (0 - 360)", example=51.0)
    Slope: float = Field(..., description="Slope in degrees (0 - 66)", example=3.0)
    Horizontal_Distance_To_Hydrology: float = Field(..., description="Distance to nearest water (m)", example=258.0)
    Vertical_Distance_To_Hydrology: float = Field(..., description="Vertical distance to water (m)", example=0.0)
    Horizontal_Distance_To_Roadways: float = Field(..., description="Distance to nearest road (m)", example=510.0)
    Horizontal_Distance_To_Fire_Points: float = Field(..., description="Distance to fire ignition points (m)", example=6279.0)
    Hillshade_9am: float = Field(..., description="Hillshade index at 9am (0 - 255)", example=221.0)
    Hillshade_Noon: float = Field(..., description="Hillshade index at Noon (0 - 255)", example=232.0)
    Hillshade_3pm: float = Field(..., description="Hillshade index at 3pm (0 - 255)", example=148.0)
    Wilderness_Area: int = Field(1, description="Wilderness area index (1 to 4)", ge=1, le=4, example=1)
    Soil_Type: int = Field(29, description="Soil type index (1 to 40)", ge=1, le=40, example=29)

class PredictionResponse(BaseModel):
    """
    Output schema for a single prediction response.
    """
    cover_type_id: int = Field(..., description="Predicted Cover Type Code (1 - 7)")
    tree_species: str = Field(..., description="Common Forest Species Name")
    confidence: float = Field(..., description="Model confidence probability (0.0 - 1.0)")
    latency_ms: float = Field(..., description="Inference latency in milliseconds")

class BatchPredictionRequest(BaseModel):
    """
    Batch prediction request payload.
    """
    items: List[TerrainFeatures]

class BatchPredictionResponse(BaseModel):
    """
    Batch prediction output payload.
    """
    total_samples: int
    predictions: List[PredictionResponse]
