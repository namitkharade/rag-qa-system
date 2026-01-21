#!/usr/bin/env python
"""
Test script for the AnalyzeGeometry tool.

Demonstrates how the tool enables the LLM to reason about spatial relationships
without seeing the visual image.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from geometry_tool import analyze_geometry


def load_sample_drawing():
    """Load the 240314_Drawing.json file."""
    drawing_path = Path(__file__).parent.parent / "240314_Drawing.json"
    
    if not drawing_path.exists():
        print(f"Warning: Could not find {drawing_path}")
        print("Using synthetic sample data instead...\n")
        return create_sample_drawing()
    
    with open(drawing_path, 'r') as f:
        return json.load(f)


def create_sample_drawing():
    """Create a sample drawing for testing."""
    return [
        {
            "type": "POLYLINE",
            "layer": "Plot Boundary",
            "points": [
                [-13160.59, 19584.96],
                [-3160.59, 19584.96],
                [-3160.59, 44584.96],
                [-13160.59, 44584.96]
            ],
            "closed": True
        },
        {
            "type": "POLYLINE",
            "layer": "Walls",
            "points": [
                [-9660.59, 29584.96],
                [-10660.59, 29584.96],
                [-10660.59, 22084.96],
                [-8560.59, 22084.96],
                [-8560.59, 29584.96]
            ],
            "closed": True
        },
        {
            "type": "POLYLINE",
            "layer": "Walls",
            "points": [
                [-6660.59, 29584.96],
                [-6660.59, 29234.96],
                [-6010.59, 29234.96],
                [-6010.59, 22434.96],
                [-7760.59, 22434.96],
                [-7760.59, 22084.96],
                [-5660.59, 22084.96],
                [-5660.59, 29584.96]
            ],
            "closed": True
        },
        {
            "type": "LINE",
            "layer": "Highway",
            "start": [-24702.61, 19584.96],
            "end": [28381.42, 19584.96]
        }
    ]


def test_area_calculations():
    """Test area calculation capabilities (for 50% curtilage rule)."""
    print("\n" + "=" * 80)
    print("TEST 1: AREA CALCULATIONS (50% Curtilage Rule)")
    print("=" * 80)
    
    drawing = load_sample_drawing()
    
    question = "What is the total area of the Plot Boundary and what percentage is covered by the Walls?"
    
    result = analyze_geometry(question, drawing)
    print(result)


def test_distance_calculations():
    """Test distance calculation capabilities (for 2m boundary rule)."""
    print("\n" + "=" * 80)
    print("TEST 2: DISTANCE CALCULATIONS (2m Boundary Rule)")
    print("=" * 80)
    
    drawing = load_sample_drawing()
    
    question = "What is the minimum distance between the Walls and the Plot Boundary?"
    
    result = analyze_geometry(question, drawing)
    print(result)


def test_layer_analysis():
    """Test layer-specific analysis."""
    print("\n" + "=" * 80)
    print("TEST 3: LAYER-SPECIFIC ANALYSIS")
    print("=" * 80)
    
    drawing = load_sample_drawing()
    
    question = "Analyze the Walls layer and tell me about its geometry."
    
    result = analyze_geometry(question, drawing)
    print(result)


def test_compliance_check():
    """Test a full compliance check scenario."""
    print("\n" + "=" * 80)
    print("TEST 4: COMPLIANCE CHECK SCENARIO")
    print("=" * 80)
    
    drawing = load_sample_drawing()
    
    question = """Check if this building complies with:
1. The 50% curtilage rule (building cannot exceed 50% of plot area)
2. The 2m boundary rule (walls must be at least 2m from plot boundary)
"""
    
    result = analyze_geometry(question, drawing)
    print(result)


def interactive_mode():
    """Allow user to ask custom questions about the drawing."""
    print("\n" + "=" * 80)
    print("INTERACTIVE MODE")
    print("=" * 80)
    print("Ask questions about the drawing geometry.")
    print("Type 'exit' to quit.\n")
    
    drawing = load_sample_drawing()
    
    while True:
        question = input("\nYour question: ").strip()
        
        if question.lower() in ['exit', 'quit', 'q']:
            print("\nGoodbye!")
            break
        
        if not question:
            continue
        
        result = analyze_geometry(question, drawing)
        print(result)


def main():
    """Run the geometry tool tests."""
    print("\n" + "=" * 80)
    print("GEOMETRY ANALYSIS TOOL - TEST SUITE")
    print("=" * 80)
    print("\nThis tool enables the LLM to reason about architectural drawings")
    print("without seeing the visual image, using shapely for geometric analysis.\n")
    
    # Run automated tests
    test_area_calculations()
    test_distance_calculations()
    test_layer_analysis()
    test_compliance_check()
    
    # Ask if user wants interactive mode
    print("\n" + "=" * 80)
    response = input("\nWould you like to enter interactive mode? (y/n): ").strip().lower()
    
    if response == 'y':
        interactive_mode()
    else:
        print("\nTests completed!")


if __name__ == "__main__":
    main()
