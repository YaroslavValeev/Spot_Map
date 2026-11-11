-- SpotMap P0 baseline PostgreSQL 16+ / PostGIS 3+
-- Migration candidate, review in a disposable DB before production.
-- DDL covers primary entities; RBAC/RLS rules and archival policies are app migrations.
BEGIN;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS countries (
 code char(2) PRIMARY KEY, name text NOT NULL
);
INSERT INTO countries(code,name) VALUES ('RU','Россия') ON CONFLICT (code) DO NOTHING;
CREATE TABLE IF NOT EXISTS regions (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 country_code char(2) NOT NULL REFERENCES countries(code),
 name text NOT NULL, external_region_code text,
 UNIQUE(country_code, name)
);
CREATE TABLE IF NOT EXISTS disciplines (
 slug text PRIMARY KEY, display_name_ru text NOT NULL,
 propulsion text NOT NULL CHECK(propulsion IN ('boat','cable','other')),
 parent_slug text, priority text NOT NULL DEFAULT 'P1'
  CHECK(priority IN ('P0','P1','P2'))
);
INSERT INTO disciplines(slug,display_name_ru,propulsion,parent_slug,priority) VALUES
('wakesurf','Вейксёрфинг','boat','wake','P0'),
('wakeskim','Вейкским','boat','wake','P0'),
('wakeboard_cable','Вейкборд — электротяга','cable','wakeboard','P0'),
('wakeboard_boat','Вейкборд — катер','boat','wakeboard','P0'),
('wakeskate_cable','Вейкскейт — электротяга','cable','wakeskate','P1'),
('waterski_boat','Водные лыжи — катер','boat','waterski','P1'),
('waterski_cable','Водные лыжи — электротяга','cable','waterski','P1')
ON CONFLICT (slug) DO NOTHING;

CREATE TABLE IF NOT EXISTS accounts (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 display_name text NOT NULL,
 email text UNIQUE, role text NOT NULL DEFAULT 'rider'
  CHECK(role IN ('rider','business','moderator','admin')),
 created_at timestamptz NOT NULL DEFAULT now(),
 deleted_at timestamptz
);
CREATE TABLE IF NOT EXISTS spots (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 region_id uuid REFERENCES regions(id),
 country_code char(2) NOT NULL REFERENCES countries(code),
 display_name text NOT NULL, slug text,
 kind text NOT NULL DEFAULT 'waterbody'
  CHECK(kind IN ('waterbody','wakepark','pool','other')),
 locality text, address_text text, timezone text,
 waterbody_type text DEFAULT 'unknown'
  CHECK(waterbody_type IN ('lake','reservoir','river','bay','artificial','other','unknown')),
 point geography(Point,4326),
 geo_status text NOT NULL DEFAULT 'missing'
  CHECK(geo_status IN ('missing','approximate','verified','disputed')),
 geo_verified_at timestamptz,
 publication_status text NOT NULL DEFAULT 'draft'
  CHECK(publication_status IN ('draft','pending','published','hidden','merged')),
 operation_status text NOT NULL DEFAULT 'unknown'
  CHECK(operation_status IN ('open','seasonal_closed','temporarily_closed','permanently_closed','planned','unknown')),
 season_note text, description text,
 merged_into_id uuid REFERENCES spots(id),
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
 CONSTRAINT geo_spot_verified CHECK(geo_status <> 'verified' OR (point IS NOT NULL AND geo_verified_at IS NOT NULL)),
 CONSTRAINT geo_spot_merged CHECK(merged_into_id IS NULL OR merged_into_id <> id)
);
CREATE INDEX IF NOT EXISTS ix_spots_point ON spots USING GIST(point);
CREATE INDEX IF NOT EXISTS ix_spots_region_status ON spots(region_id, publication_status, operation_status);
CREATE INDEX IF NOT EXISTS ix_spots_name_trgm ON spots USING GIN (display_name gin_trgm_ops);

CREATE TABLE IF NOT EXISTS clubs (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 display_name text NOT NULL, description text,
 website_url text, phone_public text, telegram_url text,
 publication_status text NOT NULL DEFAULT 'draft'
  CHECK(publication_status IN ('draft','pending','published','hidden','merged')),
 operation_status text NOT NULL DEFAULT 'unknown'
  CHECK(operation_status IN ('open','seasonal_closed','temporarily_closed','permanently_closed','planned','unknown')),
 claim_status text NOT NULL DEFAULT 'unclaimed'
  CHECK(claim_status IN ('unclaimed','pending','claimed','disputed')),
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_clubs_name_trgm ON clubs USING GIN(display_name gin_trgm_ops);
CREATE TABLE IF NOT EXISTS club_spots (
 club_id uuid NOT NULL REFERENCES clubs(id), spot_id uuid NOT NULL REFERENCES spots(id),
 role text NOT NULL DEFAULT 'operator' CHECK(role IN ('operator','school','partner','other')),
 confirmed_at timestamptz, PRIMARY KEY(club_id,spot_id)
);
CREATE TABLE IF NOT EXISTS spot_disciplines (
 spot_id uuid NOT NULL REFERENCES spots(id), discipline_slug text NOT NULL REFERENCES disciplines(slug),
 verified_at timestamptz, PRIMARY KEY(spot_id,discipline_slug)
);
CREATE TABLE IF NOT EXISTS club_disciplines (
 club_id uuid NOT NULL REFERENCES clubs(id), discipline_slug text NOT NULL REFERENCES disciplines(slug),
 verified_at timestamptz, PRIMARY KEY(club_id,discipline_slug)
);

-- One physical cable installation per row: never merge three winches into one.
CREATE TABLE IF NOT EXISTS cable_installations (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 spot_id uuid NOT NULL REFERENCES spots(id),
 operator_club_id uuid REFERENCES clubs(id),
 name text NOT NULL, installation_code text,
 installation_type text NOT NULL DEFAULT 'unknown'
  CHECK(installation_type IN ('full_size_circuit','two_tower_reversible','multi_tower_other','pool_cable','portable_other','unknown')),
 manufacturer text, model text, commissioned_year int CHECK(commissioned_year BETWEEN 1950 AND 2100),
 point geography(Point,4326),
 geo_status text NOT NULL DEFAULT 'missing'
  CHECK(geo_status IN ('missing','approximate','verified','disputed')),
 geo_verified_at timestamptz,
 publication_status text NOT NULL DEFAULT 'draft'
  CHECK(publication_status IN ('draft','pending','published','hidden','merged')),
 operation_status text NOT NULL DEFAULT 'unknown'
  CHECK(operation_status IN ('open','seasonal_closed','temporarily_closed','permanently_closed','planned','unknown')),
 public_access_status text NOT NULL DEFAULT 'unknown'
  CHECK(public_access_status IN ('public','members_only','private','unknown')),
 last_operation_confirmed_at timestamptz,
 season_note text, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
 CHECK(geo_status <> 'verified' OR (point IS NOT NULL AND geo_verified_at IS NOT NULL))
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_installation_code_per_spot ON cable_installations(spot_id,installation_code)
 WHERE installation_code IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_installations_point ON cable_installations USING GIST(point);
CREATE INDEX IF NOT EXISTS ix_installations_filter ON cable_installations(installation_type,operation_status,publication_status);
CREATE INDEX IF NOT EXISTS ix_installations_spot ON cable_installations(spot_id);
CREATE TABLE IF NOT EXISTS installation_disciplines (
 installation_id uuid NOT NULL REFERENCES cable_installations(id),
 discipline_slug text NOT NULL REFERENCES disciplines(slug),
 verified_at timestamptz, PRIMARY KEY(installation_id,discipline_slug)
);

CREATE TABLE IF NOT EXISTS cable_specs (
 installation_id uuid PRIMARY KEY REFERENCES cable_installations(id) ON DELETE CASCADE,
 tower_count int CHECK(tower_count > 0),
 track_length_m numeric(10,2) CHECK(track_length_m > 0),
 cable_height_m numeric(7,2) CHECK(cable_height_m > 0),
 max_riders int CHECK(max_riders > 0),
 carrier_count int CHECK(carrier_count > 0),
 direction text NOT NULL DEFAULT 'unknown'
  CHECK(direction IN ('clockwise','counterclockwise','bidirectional','reversible','unknown')),
 speed_min_kmh numeric(6,2) CHECK(speed_min_kmh >= 0),
 speed_max_kmh numeric(6,2) CHECK(speed_max_kmh >= 0),
 start_type text DEFAULT 'unknown'
  CHECK(start_type IN ('dock','ramp','pool','other','unknown')),
 track_line geometry(LineString,4326),
 requires_helmet boolean, requires_lifejacket boolean,
 beginner_mode boolean, night_riding boolean, winter_indoor boolean,
 updated_at timestamptz NOT NULL DEFAULT now(),
 CHECK(speed_min_kmh IS NULL OR speed_max_kmh IS NULL OR speed_min_kmh <= speed_max_kmh)
);
CREATE INDEX IF NOT EXISTS ix_cable_specs_track ON cable_specs USING GIST(track_line);
CREATE TABLE IF NOT EXISTS installation_features (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 installation_id uuid NOT NULL REFERENCES cable_installations(id) ON DELETE CASCADE,
 name text, feature_type text NOT NULL
  CHECK(feature_type IN ('kicker','box','rail','slider','pipe','funbox','other')),
 skill_level text NOT NULL DEFAULT 'unknown'
  CHECK(skill_level IN ('beginner','intermediate','advanced','pro','unknown')),
 direction text NOT NULL DEFAULT 'unknown'
  CHECK(direction IN ('clockwise','counterclockwise','both','unknown')),
 status text NOT NULL DEFAULT 'unknown'
  CHECK(status IN ('active','removed','damaged','unknown')),
 segment_note text, last_verified_at timestamptz,
 created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS boats (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 club_id uuid NOT NULL REFERENCES clubs(id), home_spot_id uuid REFERENCES spots(id),
 manufacturer text, model text, manufacture_year int CHECK(manufacture_year BETWEEN 1950 AND 2100),
 engine_description text, surf_system text, ballast_description text,
 wave_side text NOT NULL DEFAULT 'unknown'
  CHECK(wave_side IN ('regular','goofy','both','unknown')),
 wave_level text NOT NULL DEFAULT 'unknown'
  CHECK(wave_level IN ('beginner','intermediate','advanced','all','unknown')),
 wave_adjustable boolean, max_passengers int CHECK(max_passengers > 0),
 availability_status text NOT NULL DEFAULT 'unknown'
  CHECK(availability_status IN ('available','unavailable','maintenance','unknown')),
 verified_at timestamptz, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS trainers (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 display_name text NOT NULL, bio text,
 experience_years int CHECK(experience_years BETWEEN 0 AND 100),
 qualifications jsonb NOT NULL DEFAULT '[]'::jsonb,
 specializations jsonb NOT NULL DEFAULT '[]'::jsonb,
 child_training boolean, children_min_age int CHECK(children_min_age BETWEEN 0 AND 18),
 public_profile_url text, verified_at timestamptz,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS trainer_clubs (
 trainer_id uuid NOT NULL REFERENCES trainers(id), club_id uuid NOT NULL REFERENCES clubs(id),
 verified_at timestamptz, PRIMARY KEY(trainer_id,club_id)
);
CREATE TABLE IF NOT EXISTS trainer_disciplines (
 trainer_id uuid NOT NULL REFERENCES trainers(id), discipline_slug text NOT NULL REFERENCES disciplines(slug),
 PRIMARY KEY(trainer_id,discipline_slug)
);

CREATE TABLE IF NOT EXISTS offers (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 club_id uuid NOT NULL REFERENCES clubs(id), spot_id uuid REFERENCES spots(id),
 discipline_slug text NOT NULL REFERENCES disciplines(slug),
 boat_id uuid REFERENCES boats(id), installation_id uuid REFERENCES cable_installations(id),
 service_type text NOT NULL CHECK(service_type IN ('ride_set','training','boat_rental','intro','package','other')),
 title text NOT NULL,
 duration_minutes int CHECK(duration_minutes > 0),
 amount_minor bigint CHECK(amount_minor >= 0), currency_code char(3) NOT NULL DEFAULT 'RUB',
 price_status text NOT NULL DEFAULT 'quote_only'
  CHECK(price_status IN ('current_verified','current_unverified','historical','expired','quote_only')),
 valid_from date, valid_to date, inclusions jsonb NOT NULL DEFAULT '[]'::jsonb,
 cancellation_policy text, booking_url text, verified_at timestamptz,
 created_at timestamptz NOT NULL DEFAULT now(),
 CHECK(num_nonnulls(boat_id,installation_id) <= 1),
 CHECK(valid_from IS NULL OR valid_to IS NULL OR valid_to >= valid_from),
 CHECK(price_status NOT IN ('current_verified','current_unverified') OR amount_minor IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS ix_offers_club_discipline_status ON offers(club_id,discipline_slug,price_status);

CREATE TABLE IF NOT EXISTS amenity_catalog (
 slug text PRIMARY KEY, display_name_ru text NOT NULL
);
INSERT INTO amenity_catalog(slug,display_name_ru) VALUES
('parking','Парковка'),('shower','Душ'),('changing_room','Раздевалка'),('toilet','Туалет'),
('cafe','Кафе'),('restaurant','Ресторан'),('beach','Пляж'),('lounge','Зона отдыха'),
('kids_area','Детская зона'),('wifi','Wi-Fi'),('equipment_storage','Хранение экипировки'),
('accommodation_nearby','Проживание рядом'),('wheelchair_access','Доступность')
ON CONFLICT(slug) DO NOTHING;
CREATE TABLE IF NOT EXISTS spot_amenities (
 spot_id uuid NOT NULL REFERENCES spots(id), amenity_slug text NOT NULL REFERENCES amenity_catalog(slug),
 available boolean, verified_at timestamptz, PRIMARY KEY(spot_id,amenity_slug)
);
CREATE TABLE IF NOT EXISTS club_amenities (
 club_id uuid NOT NULL REFERENCES clubs(id), amenity_slug text NOT NULL REFERENCES amenity_catalog(slug),
 available boolean, verified_at timestamptz, PRIMARY KEY(club_id,amenity_slug)
);

CREATE TABLE IF NOT EXISTS sources (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 source_type text NOT NULL CHECK(source_type IN ('official_site','official_social','telegram','vk','owner','ugc','federation','public_registry','other')),
 title text NOT NULL, canonical_url text, license_note text,
 reliability_class text NOT NULL DEFAULT 'unrated'
  CHECK(reliability_class IN ('unrated','low','medium','high')),
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS import_batches (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 source_label text NOT NULL, file_sha256 char(64), source_snapshot_at timestamptz,
 imported_at timestamptz NOT NULL DEFAULT now(),
 status text NOT NULL DEFAULT 'staged' CHECK(status IN ('staged','validated','committed','failed')),
 notes text
);
CREATE TABLE IF NOT EXISTS source_records (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 source_id uuid NOT NULL REFERENCES sources(id),
 import_batch_id uuid REFERENCES import_batches(id),
 external_object_key text, source_url text,
 observed_at timestamptz NOT NULL, content_hash char(64),
 record_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
 access_level text NOT NULL DEFAULT 'internal'
  CHECK(access_level IN ('public','internal','restricted')),
 UNIQUE(source_id,external_object_key,observed_at)
);
CREATE TABLE IF NOT EXISTS staged_places (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 import_batch_id uuid NOT NULL REFERENCES import_batches(id),
 external_row_key text, raw_name text NOT NULL, raw_address text,
 raw_disciplines text, raw_source_url text, raw_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
 candidate_kind text NOT NULL DEFAULT 'unclassified'
  CHECK(candidate_kind IN ('unclassified','spot','club','installation','installation_candidate')),
 geo_status text NOT NULL DEFAULT 'missing'
  CHECK(geo_status IN ('missing','approximate','verified','disputed')),
 stage_status text NOT NULL DEFAULT 'new'
  CHECK(stage_status IN ('new','matched','geo_pending','review','imported','rejected')),
 spot_id uuid REFERENCES spots(id), club_id uuid REFERENCES clubs(id),
 installation_id uuid REFERENCES cable_installations(id),
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(import_batch_id,external_row_key)
);
CREATE TABLE IF NOT EXISTS dedup_candidates (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 left_staged_id uuid NOT NULL REFERENCES staged_places(id),
 right_staged_id uuid NOT NULL REFERENCES staged_places(id),
 relationship text NOT NULL DEFAULT 'possible_alias'
  CHECK(relationship IN ('same_entity','same_brand','same_site','same_operator','possible_alias','unrelated')),
 review_status text NOT NULL DEFAULT 'pending'
  CHECK(review_status IN ('pending','accepted','rejected')),
 evidence_notes text, reviewed_by uuid REFERENCES accounts(id),
 created_at timestamptz NOT NULL DEFAULT now(),
 CHECK(left_staged_id <> right_staged_id)
);
CREATE TABLE IF NOT EXISTS field_assertions (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 source_record_id uuid NOT NULL REFERENCES source_records(id),
 target_type text NOT NULL
  CHECK(target_type IN ('spot','club','installation','boat','trainer','offer','feature')),
 target_id uuid NOT NULL, field_path text NOT NULL,
 value_json jsonb NOT NULL,
 asserted_at timestamptz, observed_at timestamptz,
 valid_from timestamptz, valid_to timestamptz,
 verification_status text NOT NULL DEFAULT 'proposed'
  CHECK(verification_status IN ('proposed','accepted','rejected','superseded','disputed')),
 confidence_level text NOT NULL DEFAULT 'low'
  CHECK(confidence_level IN ('low','medium','high')),
 reviewed_by uuid REFERENCES accounts(id), reviewed_at timestamptz,
 created_at timestamptz NOT NULL DEFAULT now(),
 CHECK(valid_from IS NULL OR valid_to IS NULL OR valid_to >= valid_from)
);
CREATE INDEX IF NOT EXISTS ix_assertion_target_field ON field_assertions(target_type,target_id,field_path,verification_status);

CREATE TABLE IF NOT EXISTS entity_aliases (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 target_type text NOT NULL CHECK(target_type IN ('spot','club','installation','trainer')),
 target_id uuid NOT NULL, alias text NOT NULL,
 source_record_id uuid REFERENCES source_records(id), confirmed boolean NOT NULL DEFAULT false,
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(target_type,target_id,alias)
);
CREATE INDEX IF NOT EXISTS ix_entity_alias_name ON entity_aliases USING GIN(alias gin_trgm_ops);
-- Hours are local to owning spot's IANA timezone. Polymorphic target is checked in service layer.
CREATE TABLE IF NOT EXISTS opening_hours (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 target_type text NOT NULL CHECK(target_type IN ('spot','club','installation')),
 target_id uuid NOT NULL,
 weekday int NOT NULL CHECK(weekday BETWEEN 0 AND 6), -- Monday=0
 open_time time, close_time time,
 is_closed boolean NOT NULL DEFAULT false,
 is_overnight boolean NOT NULL DEFAULT false,
 valid_from date, valid_to date,
 verified_at timestamptz,
 CHECK((is_closed AND open_time IS NULL AND close_time IS NULL)
       OR (NOT is_closed AND open_time IS NOT NULL AND close_time IS NOT NULL)),
 CHECK(valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to)
);
CREATE INDEX IF NOT EXISTS ix_opening_hours_target ON opening_hours(target_type,target_id,weekday);

CREATE TABLE IF NOT EXISTS claim_requests (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 club_id uuid NOT NULL REFERENCES clubs(id), applicant_id uuid NOT NULL REFERENCES accounts(id),
 evidence_json jsonb NOT NULL DEFAULT '{}'::jsonb,
 status text NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected','disputed')),
 decided_by uuid REFERENCES accounts(id), decided_at timestamptz,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS change_proposals (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 author_id uuid REFERENCES accounts(id),
 target_type text NOT NULL CHECK(target_type IN ('spot','club','installation','boat','trainer','offer','feature')),
 target_id uuid, proposed_field_path text, old_value_json jsonb,
 proposed_value_json jsonb NOT NULL,
 source_url text, status text NOT NULL DEFAULT 'pending'
  CHECK(status IN ('pending','approved','rejected','needs_evidence')),
 moderated_by uuid REFERENCES accounts(id), moderated_at timestamptz,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS reviews (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 author_id uuid NOT NULL REFERENCES accounts(id),
 spot_id uuid REFERENCES spots(id), club_id uuid REFERENCES clubs(id),
 installation_id uuid REFERENCES cable_installations(id),
 context_spot_id uuid REFERENCES spots(id),
 discipline_slug text NOT NULL REFERENCES disciplines(slug),
 visited_at timestamptz, body text,
 proof_type text NOT NULL DEFAULT 'unverified'
  CHECK(proof_type IN ('unverified','geo','qr','booking','trainer','admin')),
 moderation_status text NOT NULL DEFAULT 'pending'
  CHECK(moderation_status IN ('pending','published','hidden','rejected')),
 conflict_of_interest boolean NOT NULL DEFAULT false,
 fraud_factor numeric(4,3) NOT NULL DEFAULT 1.000 CHECK(fraud_factor BETWEEN 0 AND 1),
 created_at timestamptz NOT NULL DEFAULT now(),
 CHECK(num_nonnulls(spot_id,club_id,installation_id) = 1)
);
CREATE INDEX IF NOT EXISTS ix_reviews_spot ON reviews(spot_id,moderation_status);
CREATE INDEX IF NOT EXISTS ix_reviews_club ON reviews(club_id,moderation_status);
CREATE INDEX IF NOT EXISTS ix_reviews_installation ON reviews(installation_id,moderation_status);
CREATE TABLE IF NOT EXISTS review_dimensions (
 review_id uuid NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
 dimension text NOT NULL
  CHECK(dimension IN ('riding_conditions','course_setup','coaching','equipment','safety','service','infrastructure','value')),
 stars int NOT NULL CHECK(stars BETWEEN 1 AND 5),
 PRIMARY KEY(review_id,dimension)
);
CREATE TABLE IF NOT EXISTS score_assessments (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 subject_type text NOT NULL CHECK(subject_type IN ('club_at_spot','spot','cable_installation')),
 subject_id uuid NOT NULL, context_spot_id uuid REFERENCES spots(id),
 discipline_slug text NOT NULL REFERENCES disciplines(slug),
 dimension text NOT NULL CHECK(dimension IN ('riding_conditions','course_setup','coaching','equipment','safety','service','infrastructure','value')),
 value_0_100 numeric(6,3) NOT NULL CHECK(value_0_100 BETWEEN 0 AND 100),
 evidence_assertion_id uuid REFERENCES field_assertions(id),
 review_id uuid REFERENCES reviews(id),
 assessment_kind text NOT NULL CHECK(assessment_kind IN ('independent_expert','verified_visit','unverified_visit')),
 author_ref text, independent_source_group text,
 observed_at timestamptz NOT NULL, fraud_factor numeric(4,3) NOT NULL DEFAULT 1 CHECK(fraud_factor BETWEEN 0 AND 1),
 conflict_of_interest boolean NOT NULL DEFAULT false,
 created_at timestamptz NOT NULL DEFAULT now(),
 CHECK(subject_type <> 'club_at_spot' OR context_spot_id IS NOT NULL),
 CHECK(num_nonnulls(evidence_assertion_id,review_id) >= 1)
);
CREATE INDEX IF NOT EXISTS ix_score_assessments_subject ON score_assessments(subject_type,subject_id,discipline_slug,dimension,observed_at);
CREATE TABLE IF NOT EXISTS score_snapshots (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 subject_type text NOT NULL CHECK(subject_type IN ('club_at_spot','spot','cable_installation')),
 subject_id uuid NOT NULL, context_spot_id uuid REFERENCES spots(id),
 discipline_slug text NOT NULL REFERENCES disciplines(slug),
 formula_version text NOT NULL, profile_version text NOT NULL,
 score integer CHECK(score BETWEEN 0 AND 100),
 raw_score numeric(7,3) CHECK(raw_score BETWEEN 0 AND 100),
 score_status text NOT NULL CHECK(score_status IN ('unrated','preliminary','verified','restricted')),
 coverage numeric(5,4) NOT NULL CHECK(coverage BETWEEN 0 AND 1),
 effective_n numeric(10,4) NOT NULL CHECK(effective_n >= 0),
 confidence text NOT NULL DEFAULT 'low' CHECK(confidence IN ('low','medium','high')),
 domain_breakdown jsonb NOT NULL DEFAULT '{}'::jsonb,
 safety_gate text NOT NULL CHECK(safety_gate IN ('passed','missing','restricted')),
 calculated_at timestamptz NOT NULL DEFAULT now(),
 input_hash char(64),
 CHECK(subject_type <> 'club_at_spot' OR context_spot_id IS NOT NULL),
 CHECK((score_status IN ('unrated','restricted') AND score IS NULL)
       OR (score_status IN ('preliminary','verified') AND score IS NOT NULL)),
 CHECK((score IS NULL AND raw_score IS NULL) OR (score IS NOT NULL AND raw_score IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS ix_snapshots_lookup ON score_snapshots(subject_type,subject_id,discipline_slug,calculated_at DESC);

CREATE TABLE IF NOT EXISTS saved_spots (
 account_id uuid NOT NULL REFERENCES accounts(id), spot_id uuid NOT NULL REFERENCES spots(id),
 created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(account_id,spot_id)
);
CREATE TABLE IF NOT EXISTS media_assets (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 target_type text NOT NULL CHECK(target_type IN ('spot','club','installation','boat','trainer')),
 target_id uuid NOT NULL, kind text NOT NULL CHECK(kind IN ('image','video')),
 storage_key text NOT NULL, author_credit text, rights_basis text,
 moderation_status text NOT NULL DEFAULT 'pending'
  CHECK(moderation_status IN ('pending','published','rejected')),
 captured_at timestamptz, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS audit_events (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 actor_id uuid REFERENCES accounts(id),
 action text NOT NULL, target_type text NOT NULL, target_id uuid,
 before_json jsonb, after_json jsonb, source_record_id uuid REFERENCES source_records(id),
 reason text, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_audit_target ON audit_events(target_type,target_id,created_at DESC);

-- Canonical public layer: site and every verified, geocoded installation separately.
-- This is NOT a claim of active operating status; clients must render operation_status.
CREATE OR REPLACE VIEW public_map_points AS
 SELECT 'spot'::text AS entity_type, s.id AS entity_id, s.id AS spot_id,
        s.display_name AS label, s.point, s.operation_status, s.geo_verified_at
 FROM spots s
 WHERE s.publication_status='published' AND s.geo_status='verified' AND s.point IS NOT NULL
 UNION ALL
 SELECT 'cable_installation'::text, i.id, i.spot_id,
        i.name, i.point, i.operation_status, i.geo_verified_at
 FROM cable_installations i
 JOIN spots s ON s.id=i.spot_id
 WHERE i.publication_status='published' AND i.geo_status='verified' AND i.point IS NOT NULL
   AND s.publication_status='published';

COMMIT;

-- APP-LAYER / NEXT MIGRATIONS REQUIRED:
-- 1) Enforce polymorphic target FK integrity for field_assertions/media_assets/etc.
-- 2) Enforce installation_disciplines.propulsion='cable', boat offers.propulsion='boat',
--    and offers.boat_id belongs to the offer's club, installation_id belongs to
--    its operator or is explicitly authorized. Add triggers/service validation.
-- 3) Enforce review subject and discipline coherence and source review owner checks.
-- 4) Add row-level-security policies for restricted staging, claim evidence and anti-fraud.
-- 5) Add an immutable audit trail (DB triggers or event-sourcing) for all writes.
-- 6) Implement update_at triggers, geofence QA, and canonical alias redirects.
-- 7) Add schedules/forecast/session/geo history in P1 migrations.
