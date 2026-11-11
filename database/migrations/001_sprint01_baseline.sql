-- SpotMap Sprint 01 baseline — disposable / test DB only.
-- Subset of SpotMap_Postgres_Schema_v1.sql + staging table.
-- Do NOT apply to production without review, RLS and backup.
BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS countries (
  code char(2) PRIMARY KEY,
  name text NOT NULL
);
INSERT INTO countries(code, name) VALUES ('RU', 'Россия')
ON CONFLICT (code) DO NOTHING;

CREATE TABLE IF NOT EXISTS regions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  country_code char(2) NOT NULL REFERENCES countries(code),
  name text NOT NULL,
  UNIQUE (country_code, name)
);

CREATE TABLE IF NOT EXISTS disciplines (
  slug text PRIMARY KEY,
  display_name_ru text NOT NULL,
  propulsion text NOT NULL CHECK (propulsion IN ('boat', 'cable', 'other')),
  parent_slug text,
  priority text NOT NULL DEFAULT 'P1' CHECK (priority IN ('P0', 'P1', 'P2'))
);
INSERT INTO disciplines(slug, display_name_ru, propulsion, parent_slug, priority) VALUES
  ('wakesurf', 'Вейксёрфинг', 'boat', 'wake', 'P0'),
  ('wakeskim', 'Вейкским', 'boat', 'wake', 'P0'),
  ('wakeboard_cable', 'Вейкборд — электротяга', 'cable', 'wakeboard', 'P0'),
  ('wakeboard_boat', 'Вейкборд — катер', 'boat', 'wakeboard', 'P0'),
  ('wakeskate_cable', 'Вейкскейт — электротяга', 'cable', 'wakeskate', 'P1'),
  ('waterski_boat', 'Водные лыжи — катер', 'boat', 'waterski', 'P1'),
  ('waterski_cable', 'Водные лыжи — электротяга', 'cable', 'waterski', 'P1')
ON CONFLICT (slug) DO NOTHING;

CREATE TABLE IF NOT EXISTS sources (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  code text NOT NULL UNIQUE,
  title text NOT NULL,
  source_type text NOT NULL DEFAULT 'internal_export'
    CHECK (source_type IN ('internal_export', 'osint', 'owner', 'ugc', 'other')),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS source_records (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id uuid NOT NULL REFERENCES sources(id),
  external_key text NOT NULL,
  payload_sha256 text,
  captured_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (source_id, external_key)
);

-- Candidates never appear on the public map automatically.
CREATE TABLE IF NOT EXISTS staging_candidates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  legacy_row_id text,
  fingerprint text NOT NULL,
  raw_name text NOT NULL,
  raw_region text,
  raw_address text,
  raw_segment text,
  raw_category text,
  raw_disciplines text,
  candidate_kind text NOT NULL DEFAULT 'spot_or_club'
    CHECK (candidate_kind IN ('spot_or_club', 'cable_installation', 'other')),
  official_or_public_website text,
  public_telegram_url text,
  source_url text,
  source_snapshot text,
  source_sha256 text,
  geo_status text NOT NULL DEFAULT 'missing'
    CHECK (geo_status IN ('missing', 'approximate', 'verified', 'disputed')),
  operation_status text NOT NULL DEFAULT 'unknown'
    CHECK (operation_status IN (
      'open', 'seasonal_closed', 'temporarily_closed',
      'permanently_closed', 'planned', 'unknown'
    )),
  publication_status text NOT NULL DEFAULT 'draft'
    CHECK (publication_status IN ('draft', 'pending', 'published', 'hidden', 'merged')),
  source_record_id uuid REFERENCES source_records(id),
  imported_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (fingerprint)
);
CREATE INDEX IF NOT EXISTS ix_staging_legacy ON staging_candidates(legacy_row_id);
CREATE INDEX IF NOT EXISTS ix_staging_kind ON staging_candidates(candidate_kind, geo_status);

CREATE TABLE IF NOT EXISTS spots (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  region_id uuid REFERENCES regions(id),
  country_code char(2) NOT NULL REFERENCES countries(code) DEFAULT 'RU',
  display_name text NOT NULL,
  slug text,
  kind text NOT NULL DEFAULT 'waterbody'
    CHECK (kind IN ('waterbody', 'wakepark', 'pool', 'other')),
  locality text,
  address_text text,
  point geography(Point, 4326),
  geo_status text NOT NULL DEFAULT 'missing'
    CHECK (geo_status IN ('missing', 'approximate', 'verified', 'disputed')),
  geo_verified_at timestamptz,
  publication_status text NOT NULL DEFAULT 'draft'
    CHECK (publication_status IN ('draft', 'pending', 'published', 'hidden', 'merged')),
  operation_status text NOT NULL DEFAULT 'unknown'
    CHECK (operation_status IN (
      'open', 'seasonal_closed', 'temporarily_closed',
      'permanently_closed', 'planned', 'unknown'
    )),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT geo_spot_verified CHECK (
    geo_status <> 'verified' OR (point IS NOT NULL AND geo_verified_at IS NOT NULL)
  )
);
CREATE INDEX IF NOT EXISTS ix_spots_point ON spots USING GIST (point);
CREATE INDEX IF NOT EXISTS ix_spots_pub ON spots(publication_status, geo_status);

CREATE TABLE IF NOT EXISTS cable_installations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  spot_id uuid NOT NULL REFERENCES spots(id),
  name text NOT NULL,
  installation_type text NOT NULL DEFAULT 'unknown'
    CHECK (installation_type IN (
      'full_size_circuit', 'two_tower_reversible', 'multi_tower_other',
      'pool_cable', 'portable_other', 'unknown'
    )),
  point geography(Point, 4326),
  geo_status text NOT NULL DEFAULT 'missing'
    CHECK (geo_status IN ('missing', 'approximate', 'verified', 'disputed')),
  geo_verified_at timestamptz,
  publication_status text NOT NULL DEFAULT 'draft'
    CHECK (publication_status IN ('draft', 'pending', 'published', 'hidden', 'merged')),
  operation_status text NOT NULL DEFAULT 'unknown'
    CHECK (operation_status IN (
      'open', 'seasonal_closed', 'temporarily_closed',
      'permanently_closed', 'planned', 'unknown'
    )),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (geo_status <> 'verified' OR (point IS NOT NULL AND geo_verified_at IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS ix_installations_point ON cable_installations USING GIST (point);
CREATE INDEX IF NOT EXISTS ix_installations_spot ON cable_installations(spot_id);

CREATE TABLE IF NOT EXISTS schema_migrations (
  version text PRIMARY KEY,
  applied_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO schema_migrations(version) VALUES ('001_sprint01_baseline')
ON CONFLICT (version) DO NOTHING;

COMMIT;
