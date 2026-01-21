"""
Pydantic schemas for validating Ephemeral Object List JSON.

Based on AICI Challenge architectural drawing data.
Handles LINE and POLYLINE objects with high-precision float coordinates.
"""

from typing import List, Literal, Union

from pydantic import BaseModel, Field, field_validator


class Point(BaseModel):
    """
    A 2D coordinate point with high-precision float values.
    Represents [x, y] coordinates in the drawing.
    """
    x: float = Field(..., description="X coordinate (high-precision float)")
    y: float = Field(..., description="Y coordinate (high-precision float)")
    
    @classmethod
    def from_list(cls, coords: List[float]) -> "Point":
        """Create a Point from a [x, y] list."""
        if len(coords) != 2:
            raise ValueError(f"Point must have exactly 2 coordinates, got {len(coords)}")
        return cls(x=coords[0], y=coords[1])
    
    def to_list(self) -> List[float]:
        """Convert Point to [x, y] list."""
        return [self.x, self.y]
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {"x": -24702.60593810492, "y": 19584.95903660336}
            ]
        }
    }


class LineObject(BaseModel):
    """
    A LINE object in the drawing.
    Contains a start point and an end point.
    """
    type: Literal["LINE"] = Field(..., description="Object type (must be 'LINE')")
    layer: str = Field(..., description="Layer name (e.g., 'Highway', 'Walls')")
    start: List[float] = Field(..., min_length=2, max_length=2, description="Start point [x, y]")
    end: List[float] = Field(..., min_length=2, max_length=2, description="End point [x, y]")
    
    @field_validator('start', 'end')
    @classmethod
    def validate_point(cls, v: List[float]) -> List[float]:
        """Validate that points have exactly 2 coordinates."""
        if len(v) != 2:
            raise ValueError(f"Point must have exactly 2 coordinates, got {len(v)}")
        if not all(isinstance(coord, (int, float)) for coord in v):
            raise ValueError("All coordinates must be numeric")
        return v
    
    def get_start_point(self) -> Point:
        """Get start point as Point object."""
        return Point.from_list(self.start)
    
    def get_end_point(self) -> Point:
        """Get end point as Point object."""
        return Point.from_list(self.end)
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "type": "LINE",
                    "layer": "Highway",
                    "start": [-24702.60593810492, 19584.95903660336],
                    "end": [28381.4248793173, 19584.95903660336]
                }
            ]
        }
    }


class PolylineObject(BaseModel):
    """
    A POLYLINE object in the drawing.
    Contains multiple points and can be closed or open.
    """
    type: Literal["POLYLINE"] = Field(..., description="Object type (must be 'POLYLINE')")
    layer: str = Field(..., description="Layer name (e.g., 'Walls', 'Doors', 'Windows', 'Plot Boundary')")
    points: List[List[float]] = Field(..., min_length=2, description="List of points [[x, y], [x, y], ...]")
    closed: bool = Field(..., description="Whether the polyline is closed (forms a polygon)")
    
    @field_validator('points')
    @classmethod
    def validate_points(cls, v: List[List[float]]) -> List[List[float]]:
        """Validate that all points have exactly 2 coordinates."""
        if len(v) < 2:
            raise ValueError("Polyline must have at least 2 points")
        
        for i, point in enumerate(v):
            if len(point) != 2:
                raise ValueError(f"Point {i} must have exactly 2 coordinates, got {len(point)}")
            if not all(isinstance(coord, (int, float)) for coord in point):
                raise ValueError(f"Point {i} must have numeric coordinates")
        
        return v
    
    def get_points(self) -> List[Point]:
        """Get all points as Point objects."""
        return [Point.from_list(p) for p in self.points]
    
    def is_polygon(self) -> bool:
        """Check if this is a closed polygon."""
        return self.closed
    
    def point_count(self) -> int:
        """Get the number of points in the polyline."""
        return len(self.points)
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "type": "POLYLINE",
                    "layer": "Walls",
                    "points": [
                        [-9660.590529393809, 29584.95903660337],
                        [-10660.59052939381, 29584.95903660337],
                        [-10660.59052939381, 22084.95903660337]
                    ],
                    "closed": True
                }
            ]
        }
    }


class EphemeralDrawing(BaseModel):
    """
    Complete ephemeral drawing data containing a list of objects.
    This is the top-level schema for validating architectural drawing JSON.
    
    This data is session-specific and NOT stored in the Vector DB.
    """
    objects: List[Union[LineObject, PolylineObject]] = Field(
        ...,
        description="List of drawing objects (LINE or POLYLINE)"
    )
    
    @field_validator('objects')
    @classmethod
    def validate_objects(cls, v: List[Union[LineObject, PolylineObject]]) -> List[Union[LineObject, PolylineObject]]:
        """Validate that there is at least one object."""
        if len(v) == 0:
            raise ValueError("Drawing must contain at least one object")
        return v
    
    def get_layers(self) -> List[str]:
        """Get list of unique layer names."""
        return list(set(obj.layer for obj in self.objects))
    
    def get_objects_by_layer(self, layer_name: str) -> List[Union[LineObject, PolylineObject]]:
        """Get all objects on a specific layer."""
        return [obj for obj in self.objects if obj.layer == layer_name]
    
    def get_objects_by_type(self, object_type: str) -> List[Union[LineObject, PolylineObject]]:
        """Get all objects of a specific type (LINE or POLYLINE)."""
        return [obj for obj in self.objects if obj.type == object_type]
    
    def count_by_layer(self) -> dict:
        """Get count of objects per layer."""
        counts = {}
        for obj in self.objects:
            counts[obj.layer] = counts.get(obj.layer, 0) + 1
        return counts
    
    def count_by_type(self) -> dict:
        """Get count of objects per type."""
        counts = {}
        for obj in self.objects:
            counts[obj.type] = counts.get(obj.type, 0) + 1
        return counts
    
    def total_objects(self) -> int:
        """Get total number of objects in the drawing."""
        return len(self.objects)
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "objects": [
                        {
                            "type": "LINE",
                            "layer": "Highway",
                            "start": [-24702.60593810492, 19584.95903660336],
                            "end": [28381.4248793173, 19584.95903660336]
                        },
                        {
                            "type": "POLYLINE",
                            "layer": "Walls",
                            "points": [
                                [-9660.590529393809, 29584.95903660337],
                                [-10660.59052939381, 29584.95903660337]
                            ],
                            "closed": True
                        }
                    ]
                }
            ]
        }
    }


# Helper function to validate raw JSON
def validate_drawing_json(json_data: List[dict]) -> EphemeralDrawing:
    """
    Validate and parse raw JSON drawing data.
    
    Args:
        json_data: List of drawing object dictionaries
        
    Returns:
        Validated EphemeralDrawing object
        
    Raises:
        ValidationError: If the JSON doesn't match the schema
    """
    return EphemeralDrawing(objects=json_data)


# Helper function to validate and extract metadata
def get_drawing_metadata(json_data: List[dict]) -> dict:
    """
    Extract metadata from drawing JSON without full validation.
    Useful for quick analysis.
    
    Args:
        json_data: List of drawing object dictionaries
        
    Returns:
        Dictionary with drawing metadata
    """
    drawing = validate_drawing_json(json_data)
    
    return {
        "total_objects": drawing.total_objects(),
        "layers": drawing.get_layers(),
        "objects_by_layer": drawing.count_by_layer(),
        "objects_by_type": drawing.count_by_type(),
        "has_lines": "LINE" in drawing.count_by_type(),
        "has_polylines": "POLYLINE" in drawing.count_by_type(),
    }
