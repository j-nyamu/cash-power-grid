-- Owner: USSD channel (user-initiated). Depends on: 01_auth.sql
-- USSD has the same features as the web app, including self-registration, so people without
-- smartphones can use the service. The caller's phone number (from the aggregator callback) is
-- matched to users.phone; an unknown number is offered "Register" (language, optional name). Known numbers log in with an SMS
-- code (otp_codes, purpose 'ussd_login'): there is no PIN. 3 wrong codes lock USSD for 15 minutes.
USE cashpower;

CREATE TABLE ussd_sessions (
  session_id  VARCHAR(64) PRIMARY KEY,                   -- from the aggregator callback
  phone       VARCHAR(15) NOT NULL,
  state       VARCHAR(40) NOT NULL,
  data        JSON NULL,
  updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX (updated_at)
);