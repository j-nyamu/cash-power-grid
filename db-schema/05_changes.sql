-- Later changes go here as ALTER / CREATE statements, one block per change, newest last.
-- Rule: change app/models.py and this folder together, and tell the team before running anything on the shared database.
-- Depends on: 01-04.
USE cashpower;

-- (nothing yet)

-- Ideas that are NOT in app/models.py yet (do not run until the models change too):
--   tariff_blocks, appliances, forecasts, alerts, ussd_sessions  -> features still to be built.
--   Phone-only (USSD) accounts would need:
--     ALTER TABLE users MODIFY email VARCHAR(255) NULL, MODIFY pw_hash VARCHAR(255) NULL;
--   Optional speed-ups for frequent lookups:
--     CREATE INDEX ix_otps_phone_purpose ON otps (phone, purpose);
--     CREATE INDEX ix_entries_meter_day  ON entries (meter_id, day);
--     CREATE INDEX ix_activity_meter_ts  ON activity (meter_id, ts);