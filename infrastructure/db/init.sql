-- 1. Enable PostGIS extension for spatial operations
CREATE EXTENSION IF NOT EXISTS postgis;

-- 2. Vessels table - stores real-time tracking data
CREATE TABLE IF NOT EXISTS vessels (
    mmsi INTEGER PRIMARY KEY,
    name VARCHAR(255),
    last_pos GEOGRAPHY(POINT, 4326),
    speed FLOAT,
    course FLOAT,
    type VARCHAR(100),
    last_seen TIMESTAMP WITH TIME ZONE
);

-- 3. Geofences table - stores protected areas and security zones
CREATE TABLE IF NOT EXISTS geofences (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    area GEOGRAPHY(POLYGON, 4326),
    severity VARCHAR(20) DEFAULT 'INFO' -- Critical, High, Medium, Info
);

-- 4. Spatial Indexes - Essential for performance with thousands of vessels
-- Using GiST (Generalized Search Tree) for geography types
CREATE INDEX IF NOT EXISTS idx_vessels_pos ON vessels USING GIST (last_pos);
CREATE INDEX IF NOT EXISTS idx_geofences_area ON geofences USING GIST (area);

-- --- INITIAL DATA SEEDING ---

-- A. Bergen Port Safety Zone (Strategic Harbor Entrance)
INSERT INTO geofences (name, area, severity)
VALUES (
    'Bergen Port Safety Zone',
    'POLYGON((5.25 60.38, 5.35 60.38, 5.35 60.42, 5.25 60.42, 5.25 60.38))'::geography,
    'CRITICAL'
)
ON CONFLICT DO NOTHING;

-- B. Hywind Tampen (World''s Largest Floating Wind Farm)
INSERT INTO geofences (name, area, severity)
VALUES (
    'Hywind Tampen Zone',
    'POLYGON((2.2 61.3, 2.4 61.3, 2.4 61.5, 2.2 61.5, 2.2 61.3))'::geography,
    'HIGH'
)
ON CONFLICT DO NOTHING;

-- C. Troll A Platform Exclusion Zone (Strategic Gas Infrastructure)
-- A small, tight box around the platform coordinates
INSERT INTO geofences (name, area, severity)
VALUES (
    'Troll A Exclusion Zone',
    'POLYGON((3.71 60.63, 3.73 60.63, 3.73 60.65, 3.71 60.65, 3.71 60.63))'::geography,
    'CRITICAL'
)
ON CONFLICT DO NOTHING;

-- D. North Sea Signal Monitoring Area (Large region for Jamming Detection)
INSERT INTO geofences (name, area, severity)
VALUES (
    'North Sea Monitoring Sector',
    'POLYGON((3.0 57.0, 15.0 57.0, 15.0 65.0, 3.0 65.0, 3.0 57.0))'::geography,
    'INFO'
)
ON CONFLICT DO NOTHING;