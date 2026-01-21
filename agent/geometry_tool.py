"""
Custom LangChain tool for analyzing architectural drawing geometry.

This tool enables the LLM to reason about spatial relationships in the drawing
without seeing the visual image, using shapely for geometric calculations.

Key capabilities:
- Calculate polygon areas (for "50% curtilage" rule)
- Calculate distances between walls and plot boundaries (for "2m boundary" rule)
- Analyze spatial relationships and overlaps
"""

import json
from typing import Any, Dict, List, Optional

from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from shapely.geometry import LineString
from shapely.geometry import Point as ShapelyPoint
from shapely.geometry import Polygon
from shapely.ops import nearest_points
from shapely.strtree import STRtree


class GeometryAnalysisInput(BaseModel):
    """Input schema for the AnalyzeGeometry tool."""
    
    question: str = Field(
        ...,
        description="The user's question about the drawing geometry"
    )
    drawing_data: List[Dict[str, Any]] = Field(
        ...,
        description="Raw JSON drawing data (list of LINE and POLYLINE objects)"
    )


class AnalyzeGeometryTool(BaseTool):
    """
    Custom LangChain tool for geometric analysis of architectural drawings.
    
    This tool allows the LLM to "see" and reason about the drawing by:
    1. Parsing LINE and POLYLINE objects into shapely geometries
    2. Calculating areas of polygons (e.g., plot boundary, building footprint)
    3. Calculating distances between objects (e.g., walls to boundary)
    4. Analyzing spatial relationships
    
    Critical for regulatory compliance checks like:
    - 50% curtilage rule (requires area calculations)
    - 2m boundary rule (requires distance calculations)
    """
    
    name: str = "AnalyzeGeometry"
    description: str = """
    Analyzes the geometry of an architectural drawing to answer spatial questions.
    
    Use this tool when you need to:
    - Calculate the area of a polygon (e.g., plot boundary, building footprint)
    - Calculate distances between objects (e.g., wall to boundary)
    - Determine if objects overlap or intersect
    - Check spatial relationships and compliance with rules
    
    Input: A question about the geometry and the raw JSON drawing data.
    Output: Detailed geometric analysis with measurements and calculations.
    """
    args_schema: type[BaseModel] = GeometryAnalysisInput
    
    def _parse_drawing_objects(self, drawing_data: List[Dict[str, Any]]) -> Dict[str, List[Any]]:
        """
        Parse drawing objects into categorized shapely geometries.
        
        Args:
            drawing_data: List of LINE and POLYLINE objects
            
        Returns:
            Dictionary mapping layer names to lists of shapely geometries
        """
        geometries_by_layer = {}
        
        for obj in drawing_data:
            obj_type = obj.get("type")
            layer = obj.get("layer", "Unknown")
            
            if layer not in geometries_by_layer:
                geometries_by_layer[layer] = []
            
            try:
                if obj_type == "LINE":
                    # Create LineString from start and end points
                    start = obj.get("start", [])
                    end = obj.get("end", [])
                    if len(start) == 2 and len(end) == 2:
                        line = LineString([start, end])
                        geometries_by_layer[layer].append({
                            "type": "LineString",
                            "geometry": line,
                            "original": obj
                        })
                
                elif obj_type == "POLYLINE":
                    # Create LineString or Polygon from points
                    points = obj.get("points", [])
                    closed = obj.get("closed", False)
                    
                    if len(points) >= 2:
                        if closed and len(points) >= 3:
                            # PRODUCTION FIX: Add validity check for polygon creation
                            # If polygon is not closed or has invalid geometry, shapely might error
                            try:
                                polygon = Polygon(points)
                                
                                # Validate that the polygon is valid
                                if not polygon.is_valid:
                                    # Attempt to fix invalid polygon using buffer(0)
                                    # This handles self-intersecting polygons (e.g., bow-tie shapes)
                                    try:
                                        fixed_polygon = polygon.buffer(0)
                                        if fixed_polygon.is_valid and not fixed_polygon.is_empty:
                                            print(f"Info: Fixed invalid polygon on layer {layer} using buffer(0).")
                                            polygon = fixed_polygon
                                        else:
                                            print(f"Warning: Invalid polygon on layer {layer} could not be fixed. "
                                                  f"Reason: Polygon geometry is not valid (self-intersecting or not closed properly). "
                                                  f"Skipping this object.")
                                            continue
                                    except Exception as fix_error:
                                        print(f"Warning: Invalid polygon on layer {layer} could not be fixed. "
                                              f"Details: {str(fix_error)}. Skipping this object.")
                                        continue
                                
                                geometries_by_layer[layer].append({
                                    "type": "Polygon",
                                    "geometry": polygon,
                                    "original": obj
                                })
                            except Exception as poly_error:
                                print(f"Error: Could not create polygon on layer {layer}. "
                                      f"The polyline points may not form a closed loop or have invalid coordinates. "
                                      f"Details: {str(poly_error)}")
                                continue
                        else:
                            # Open polyline -> LineString
                            line = LineString(points)
                            geometries_by_layer[layer].append({
                                "type": "LineString",
                                "geometry": line,
                                "original": obj
                            })
            
            except Exception as e:
                # Skip invalid geometries
                print(f"Warning: Could not parse object on layer {layer}: {str(e)}")
                continue
        
        return geometries_by_layer
    
    def _calculate_polygon_area(self, polygon: Polygon) -> float:
        """Calculate the area of a polygon."""
        return polygon.area
    
    def _calculate_distance(self, geom1, geom2) -> float:
        """Calculate the minimum distance between two geometries."""
        return geom1.distance(geom2)
    
    def _get_nearest_points(self, geom1, geom2) -> tuple:
        """Get the nearest points between two geometries."""
        return nearest_points(geom1, geom2)
    
    def _analyze_areas(self, geometries_by_layer: Dict[str, List[Any]]) -> Dict[str, Any]:
        """
        Calculate areas of all polygons, organized by layer.
        
        Critical for "50% curtilage" rule.
        """
        areas = {}
        total_area = 0.0
        
        for layer, geoms in geometries_by_layer.items():
            layer_polygons = [g for g in geoms if g["type"] == "Polygon"]
            
            if layer_polygons:
                layer_area = sum(self._calculate_polygon_area(g["geometry"]) for g in layer_polygons)
                areas[layer] = {
                    "area": layer_area,
                    "count": len(layer_polygons),
                    "unit": "square units"
                }
                total_area += layer_area
        
        areas["total"] = total_area
        return areas
    
    def _analyze_distances(
        self,
        geometries_by_layer: Dict[str, List[Any]],
        layer1: str,
        layer2: str
    ) -> Dict[str, Any]:
        """
        Calculate distances between objects on two layers using spatial indexing.
        
        Uses STRtree spatial index for efficient O(N log N) performance instead of O(N^2).
        Critical for "2m boundary" rule (e.g., Walls to Plot Boundary).
        """
        if layer1 not in geometries_by_layer or layer2 not in geometries_by_layer:
            return {
                "error": f"One or both layers not found: {layer1}, {layer2}",
                "available_layers": list(geometries_by_layer.keys())
            }
        
        geoms1 = geometries_by_layer[layer1]
        geoms2 = geometries_by_layer[layer2]
        
        if not geoms1 or not geoms2:
            return {"error": "One or both layers have no geometries"}
        
        # Build spatial index for layer2 geometries for efficient nearest neighbor queries
        geoms2_geometries = [g["geometry"] for g in geoms2]
        spatial_index = STRtree(geoms2_geometries)
        
        distances = []
        
        # For each geometry in layer1, find its nearest neighbor(s) in layer2 using spatial index
        for g1 in geoms1:
            g1_geom = g1["geometry"]
            
            # Query nearest geometry in layer2 using spatial index
            # nearest() returns the single nearest geometry
            nearest_g2_geom = spatial_index.nearest(g1_geom)
            
            # Calculate distance to nearest neighbor
            dist = self._calculate_distance(g1_geom, nearest_g2_geom)
            
            # Get nearest points
            pt1, pt2 = self._get_nearest_points(g1_geom, nearest_g2_geom)
            
            distances.append({
                "distance": dist,
                "from_layer": layer1,
                "to_layer": layer2,
                "nearest_point_on_layer1": [pt1.x, pt1.y],
                "nearest_point_on_layer2": [pt2.x, pt2.y]
            })
        
        if distances:
            min_distance = min(d["distance"] for d in distances)
            max_distance = max(d["distance"] for d in distances)
            avg_distance = sum(d["distance"] for d in distances) / len(distances)
            
            return {
                "minimum_distance": min_distance,
                "maximum_distance": max_distance,
                "average_distance": avg_distance,
                "all_distances": distances,
                "unit": "coordinate units",
                "count": len(distances)
            }
        
        return {"error": "No distances could be calculated"}
    
    def _analyze_layer(
        self,
        geometries_by_layer: Dict[str, List[Any]],
        layer_name: str
    ) -> Dict[str, Any]:
        """Get detailed information about a specific layer."""
        if layer_name not in geometries_by_layer:
            return {
                "error": f"Layer '{layer_name}' not found",
                "available_layers": list(geometries_by_layer.keys())
            }
        
        geoms = geometries_by_layer[layer_name]
        
        polygons = [g for g in geoms if g["type"] == "Polygon"]
        lines = [g for g in geoms if g["type"] == "LineString"]
        
        info = {
            "layer_name": layer_name,
            "total_objects": len(geoms),
            "polygons": len(polygons),
            "lines": len(lines)
        }
        
        # Calculate total area if there are polygons
        if polygons:
            total_area = sum(self._calculate_polygon_area(p["geometry"]) for p in polygons)
            info["total_area"] = total_area
            info["area_unit"] = "square units"
        
        # Calculate total length if there are lines
        if lines:
            total_length = sum(l["geometry"].length for l in lines)
            info["total_length"] = total_length
            info["length_unit"] = "linear units"
        
        return info
    
    def _get_summary(self, geometries_by_layer: Dict[str, List[Any]]) -> Dict[str, Any]:
        """Get a summary of the entire drawing."""
        layers = list(geometries_by_layer.keys())
        
        total_objects = sum(len(geoms) for geoms in geometries_by_layer.values())
        
        summary = {
            "total_layers": len(layers),
            "layers": layers,
            "total_objects": total_objects,
            "layers_detail": {}
        }
        
        for layer in layers:
            summary["layers_detail"][layer] = self._analyze_layer(geometries_by_layer, layer)
        
        return summary
    
    def _run(self, question: str, drawing_data: List[Dict[str, Any]]) -> str:
        """
        Execute the geometry analysis.
        
        Args:
            question: The user's question
            drawing_data: Raw JSON drawing data
            
        Returns:
            Detailed analysis as a formatted string
        """
        try:
            # Parse the drawing objects
            geometries_by_layer = self._parse_drawing_objects(drawing_data)
            
            if not geometries_by_layer:
                return "Error: Could not parse any valid geometries from the drawing data."
            
            # Analyze based on the question
            question_lower = question.lower()
            
            results = {
                "question": question,
                "drawing_summary": self._get_summary(geometries_by_layer)
            }
            
            # Area-related questions (for curtilage rules)
            if any(keyword in question_lower for keyword in ["area", "size", "curtilage", "footprint", "50%"]):
                results["area_analysis"] = self._analyze_areas(geometries_by_layer)
                
                # Calculate percentages if multiple layers
                areas = results["area_analysis"]
                if len(areas) > 2:  # More than just "total"
                    results["area_percentages"] = {}
                    total = areas.get("total", 1)
                    for layer, data in areas.items():
                        if layer != "total" and isinstance(data, dict):
                            percentage = (data["area"] / total * 100) if total > 0 else 0
                            results["area_percentages"][layer] = f"{percentage:.2f}%"
            
            # Distance-related questions (for boundary rules)
            if any(keyword in question_lower for keyword in ["distance", "boundary", "2m", "meters", "setback"]):
                # Try to identify relevant layers
                if "wall" in question_lower and "boundary" in question_lower:
                    results["distance_analysis"] = self._analyze_distances(
                        geometries_by_layer,
                        "Walls",
                        "Plot Boundary"
                    )
                elif "distance" in question_lower:
                    # Provide distances for all layer combinations
                    layers = list(geometries_by_layer.keys())
                    if len(layers) >= 2:
                        results["distance_analysis"] = self._analyze_distances(
                            geometries_by_layer,
                            layers[0],
                            layers[1]
                        )
            
            # Layer-specific questions
            for layer in geometries_by_layer.keys():
                if layer.lower() in question_lower:
                    results[f"{layer}_analysis"] = self._analyze_layer(geometries_by_layer, layer)
            
            # Format the output as a readable string
            output = self._format_results(results)
            return output
            
        except Exception as e:
            return f"Error analyzing geometry: {str(e)}"
    
    def _format_results(self, results: Dict[str, Any]) -> str:
        """Format the analysis results as a readable string."""
        lines = [
            "=" * 80,
            "GEOMETRY ANALYSIS RESULTS",
            "=" * 80,
            f"\nQuestion: {results.get('question', 'N/A')}",
            "\n" + "-" * 80,
        ]
        
        # Drawing summary
        if "drawing_summary" in results:
            summary = results["drawing_summary"]
            lines.append("\nDRAWING SUMMARY:")
            lines.append(f"  Total Layers: {summary['total_layers']}")
            lines.append(f"  Layers: {', '.join(summary['layers'])}")
            lines.append(f"  Total Objects: {summary['total_objects']}")
        
        # Area analysis
        if "area_analysis" in results:
            lines.append("\n" + "-" * 80)
            lines.append("\nAREA ANALYSIS:")
            areas = results["area_analysis"]
            
            for layer, data in areas.items():
                if layer != "total" and isinstance(data, dict):
                    lines.append(f"  {layer}:")
                    lines.append(f"    Area: {data['area']:.2f} {data['unit']}")
                    lines.append(f"    Polygons: {data['count']}")
            
            if "total" in areas:
                lines.append(f"\n  TOTAL AREA: {areas['total']:.2f} square units")
            
            # Show percentages if available
            if "area_percentages" in results:
                lines.append("\n  AREA PERCENTAGES:")
                for layer, pct in results["area_percentages"].items():
                    lines.append(f"    {layer}: {pct}")
        
        # Distance analysis
        if "distance_analysis" in results:
            lines.append("\n" + "-" * 80)
            lines.append("\nDISTANCE ANALYSIS:")
            dist = results["distance_analysis"]
            
            if "error" in dist:
                lines.append(f"  Error: {dist['error']}")
                if "available_layers" in dist:
                    lines.append(f"  Available layers: {', '.join(dist['available_layers'])}")
            else:
                lines.append(f"  Minimum Distance: {dist['minimum_distance']:.2f} {dist['unit']}")
                lines.append(f"  Maximum Distance: {dist['maximum_distance']:.2f} {dist['unit']}")
                lines.append(f"  Average Distance: {dist['average_distance']:.2f} {dist['unit']}")
                lines.append(f"  Measurements: {dist['count']}")
        
        # Layer-specific analyses
        for key, value in results.items():
            if key.endswith("_analysis") and key not in ["area_analysis", "distance_analysis"]:
                lines.append("\n" + "-" * 80)
                lines.append(f"\n{key.upper().replace('_', ' ')}:")
                if isinstance(value, dict):
                    for k, v in value.items():
                        lines.append(f"  {k}: {v}")
        
        lines.append("\n" + "=" * 80)
        
        return "\n".join(lines)
    
    async def _arun(self, question: str, drawing_data: List[Dict[str, Any]]) -> str:
        """Async version (not implemented, falls back to sync)."""
        return self._run(question, drawing_data)


# Create a global instance of the tool
analyze_geometry_tool = AnalyzeGeometryTool()


def analyze_geometry(question: str, drawing_data: List[Dict[str, Any]]) -> str:
    """
    Convenience function to use the AnalyzeGeometry tool.
    
    Args:
        question: The user's question about the drawing
        drawing_data: Raw JSON drawing data
        
    Returns:
        Detailed geometric analysis
    """
    return analyze_geometry_tool._run(question, drawing_data)


if __name__ == "__main__":
    """Test the geometry tool with sample data."""
    
    # Sample drawing data
    sample_drawing = [
        {
            "type": "POLYLINE",
            "layer": "Plot Boundary",
            "points": [[0, 0], [100, 0], [100, 100], [0, 100]],
            "closed": True
        },
        {
            "type": "POLYLINE",
            "layer": "Walls",
            "points": [[10, 10], [50, 10], [50, 50], [10, 50]],
            "closed": True
        },
        {
            "type": "LINE",
            "layer": "Highway",
            "start": [-10, 0],
            "end": [110, 0]
        }
    ]
    
    # Test questions
    questions = [
        "What is the area of the Plot Boundary?",
        "What is the distance between the Walls and Plot Boundary?",
        "Calculate the percentage of the plot covered by the building."
    ]
    
    print("\n" + "=" * 80)
    print("TESTING GEOMETRY ANALYSIS TOOL")
    print("=" * 80)
    
    for question in questions:
        print(f"\n\nTesting: {question}")
        result = analyze_geometry(question, sample_drawing)
        print(result)
