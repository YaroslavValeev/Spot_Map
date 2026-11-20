-- Public club profile: contacts + convenience facts for embed card.
-- Missing fact ≠ false. No invented SpotScore.

CREATE TABLE IF NOT EXISTS spot_public_profiles (
  spot_id uuid PRIMARY KEY REFERENCES spots(id) ON DELETE CASCADE,
  website text,
  phone text,
  telegram_url text,
  whatsapp_url text,
  booking_url text,
  notes_public text,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS spot_convenience_facts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  spot_id uuid NOT NULL REFERENCES spots(id) ON DELETE CASCADE,
  checklist_key text NOT NULL
    CHECK (checklist_key IN (
      'booking_contact',
      'pricing_clarity',
      'parking_access',
      'changing_facilities',
      'gear_rental',
      'coaching_available',
      'safety_basics',
      'riding_quality',
      'guest_comfort',
      'hours_freshness'
    )),
  state text NOT NULL DEFAULT 'unknown'
    CHECK (state IN ('yes', 'no', 'unknown', 'unsupported')),
  evidence_note text,
  source_url text,
  observed_at timestamptz,
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (spot_id, checklist_key)
);

CREATE INDEX IF NOT EXISTS ix_spot_convenience_spot
  ON spot_convenience_facts(spot_id);
