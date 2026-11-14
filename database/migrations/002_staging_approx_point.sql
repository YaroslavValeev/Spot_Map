-- Staging approximate coordinates from geocoder (never auto-verified / published).
BEGIN;

ALTER TABLE staging_candidates
  ADD COLUMN IF NOT EXISTS approx_point geography(Point, 4326),
  ADD COLUMN IF NOT EXISTS approx_precision text
    CHECK (approx_precision IS NULL OR approx_precision IN ('address', 'region', 'name_region')),
  ADD COLUMN IF NOT EXISTS approx_geocode_query text,
  ADD COLUMN IF NOT EXISTS approx_geocoded_at timestamptz,
  ADD COLUMN IF NOT EXISTS approx_geocode_provider text;

CREATE INDEX IF NOT EXISTS ix_staging_approx_point
  ON staging_candidates USING GIST (approx_point);

INSERT INTO schema_migrations(version) VALUES ('002_staging_approx_point')
ON CONFLICT (version) DO NOTHING;

COMMIT;
