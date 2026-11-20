-- SpotMapExtreme v5: weather provenance, wind profiles, booking redirects, ratings stubs.
-- Draft migration for local/staging. No invented scores. Rollback: DROP tables below.

CREATE TABLE IF NOT EXISTS wind_profiles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  spot_id uuid NOT NULL REFERENCES spots(id) ON DELETE CASCADE,
  ride_area_id uuid,
  discipline_id text NOT NULL,
  approved boolean NOT NULL DEFAULT false,
  version text NOT NULL DEFAULT 'draft-1',
  north_convention text NOT NULL DEFAULT 'METEOROLOGICAL_FROM_DEGREES',
  sectors jsonb NOT NULL DEFAULT '[]'::jsonb,
  notes text,
  verified_at timestamptz,
  verified_by text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (spot_id, discipline_id, version)
);

CREATE INDEX IF NOT EXISTS ix_wind_profiles_spot
  ON wind_profiles(spot_id) WHERE approved = true;

CREATE TABLE IF NOT EXISTS water_temperature_observations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  spot_id uuid NOT NULL REFERENCES spots(id) ON DELETE CASCADE,
  water_c double precision NOT NULL,
  measured_at timestamptz NOT NULL,
  source text NOT NULL,
  location_note text,
  depth_m double precision,
  measurement_method text,
  confidence text NOT NULL DEFAULT 'unknown'
    CHECK (confidence IN ('high', 'medium', 'low', 'unknown')),
  expires_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_water_temp_spot_measured
  ON water_temperature_observations(spot_id, measured_at DESC);

CREATE TABLE IF NOT EXISTS verified_booking_links (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  spot_id uuid NOT NULL REFERENCES spots(id) ON DELETE CASCADE,
  target_url text NOT NULL,
  label text NOT NULL DEFAULT 'Записаться у клуба',
  https_only boolean NOT NULL DEFAULT true,
  verified_at timestamptz NOT NULL DEFAULT now(),
  verified_by text,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (spot_id, target_url)
);

CREATE INDEX IF NOT EXISTS ix_booking_links_spot_active
  ON verified_booking_links(spot_id) WHERE is_active = true;

CREATE TABLE IF NOT EXISTS outbound_booking_clicks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  booking_link_id uuid NOT NULL REFERENCES verified_booking_links(id) ON DELETE CASCADE,
  spot_id uuid NOT NULL REFERENCES spots(id) ON DELETE CASCADE,
  clicked_at timestamptz NOT NULL DEFAULT now(),
  referrer text,
  user_agent text,
  embed_host text,
  utm_source text,
  utm_medium text,
  utm_campaign text,
  ip_hash text
);

CREATE INDEX IF NOT EXISTS ix_outbound_clicks_link_time
  ON outbound_booking_clicks(booking_link_id, clicked_at DESC);

-- External ratings are labels only; never auto-merge into SpotScore.
CREATE TABLE IF NOT EXISTS external_ratings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  spot_id uuid NOT NULL REFERENCES spots(id) ON DELETE CASCADE,
  provider text NOT NULL,
  score double precision,
  ratings_count integer,
  observed_at timestamptz NOT NULL,
  source_url text,
  license_note text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS club_management_requests (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  spot_id uuid NOT NULL REFERENCES spots(id) ON DELETE CASCADE,
  contact_email text,
  contact_telegram text,
  message text,
  status text NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'approved', 'rejected')),
  created_at timestamptz NOT NULL DEFAULT now(),
  reviewed_at timestamptz,
  reviewed_by text
);
