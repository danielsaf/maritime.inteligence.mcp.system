import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta
from src.core.anomalies import AnomalyDetector

"""
Unit testing module for the Maritime Anomaly Detection engine.

This module validates the core security logic, including Dead Reckoning 
calculations and spatial anomaly clustering (GPS Jamming detection), 
using mocked repository dependencies to isolate the business logic.
"""


@pytest.mark.asyncio
async def test_calculate_predicted_pos():
    """
    Test the Dead Reckoning (position prediction) mathematical logic.

    Verifies that the detector correctly estimates a vessel's position
    based on speed, course, and elapsed time since the last signal.

    Scenario:
        - Vessel heading North (0°) at 20 knots.
        - Time elapsed: 1 hour.
        - Expected result: Latitude increases by ~0.333 degrees (20 nautical miles).
    """
    # Setup: Repository is not needed for pure math, so we provide a MagicMock
    detector = AnomalyDetector(repo=MagicMock())

    # Mock Data: Vessel moving North (0°) at 20 knots
    lat, lon = 60.0, 10.0
    speed = 20.0
    course = 0.0
    # Last seen exactly 1 hour ago
    last_seen = datetime.now(timezone.utc) - timedelta(hours=1)

    # Execution
    predicted = detector.calculate_predicted_pos(lat, lon, speed, course, last_seen)

    # Assertion: 20 nautical miles North = 20 minutes of latitude (20/60 = 0.333 degrees)
    assert predicted["lat"] > 60.3
    assert predicted["lon"] == 10.0  # Longitude should remain unchanged at 0° course
    print(f"✅ Dead Reckoning test passed: Predicted Lat {predicted['lat']}")


@pytest.mark.asyncio
async def test_get_enhanced_anomalies_jamming_detection():
    """
    Test the spatial clustering algorithm for potential GPS jamming detection.

    Verifies that the system identifies groups of vessels that stop
    transmitting signals in the same geographical vicinity.

    Scenario:
        - Mock repository returns 3 inactive vessels clustered within 0.1 degrees.
        - Expected result: Anomaly report contains 3 alerts and 1 jamming cluster.
    """
    # Setup: Create an AsyncMock for the repository to simulate database return values
    mock_repo = AsyncMock()
    mock_repo.get_inactive_vessels.return_value = [
        {"mmsi": "1", "name": "S1", "lat": 50.0, "lon": 10.0, "speed": 10.0, "last_seen": datetime.now(timezone.utc)},
        {"mmsi": "2", "name": "S2", "lat": 50.01, "lon": 10.01, "speed": 10.0, "last_seen": datetime.now(timezone.utc)},
        {"mmsi": "3", "name": "S3", "lat": 50.02, "lon": 10.02, "speed": 10.0, "last_seen": datetime.now(timezone.utc)},
    ]

    detector = AnomalyDetector(repo=mock_repo)

    # Execution: Trigger the anomaly aggregation logic
    result = await detector.get_enhanced_anomalies(threshold_min=15)

    # Assertion: Verify that alerts are mapped and clusters are identified
    assert len(result["alerts"]) == 3
    assert len(result["clusters"]) > 0
    assert result["clusters"][0]["type"] == "POTENTIAL_JAMMING_ZONE"
    assert "1" in result["clusters"][0]["affected_mmsi"]
    print(f"✅ Jamming cluster detection test passed! Found: {len(result['clusters'])} clusters.")