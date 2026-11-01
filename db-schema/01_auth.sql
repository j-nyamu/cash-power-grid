-- Owner: authentication. Depends on: nothing.
USE cashpower;

-- ---------- AUTH ----------
CREATE TABLE users (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  email           VARCHAR(254) NULL UNIQUE,              -- web login; NULL for phone-only (USSD) accounts
  name            VARCHAR(100) NULL,                     -- optional on USSD; show phone if empty
  phone           VARCHAR(15)  NOT NULL UNIQUE,          -- E.164, e.g. +2507XXXXXXXX (SMS + USSD identity)
  password_hash   VARCHAR(255) NULL,                     -- web login; NULL for phone-only accounts. argon2id/bcrypt/scrypt
  ussd_failed_attempts TINYINT UNSIGNED NOT NULL DEFAULT 0,   -- wrong SMS codes on USSD; lock after 3
  ussd_locked_until    DATETIME NULL,                         -- USSD lock lasts 15 minutes
  language        ENUM('en','rw') NOT NULL DEFAULT 'en',
  role            ENUM('user','admin') NOT NULL DEFAULT 'user',
  signup_channel  ENUM('web','ussd') NOT NULL DEFAULT 'web',
  phone_verified  TINYINT(1)   NOT NULL DEFAULT 0,       -- SMS alerts only go to verified phones (USSD sign-up: number is network-authenticated)
  email_verified  TINYINT(1)   NOT NULL DEFAULT 0,
  consent_at      DATETIME     NULL,                     -- when privacy consent was given
  failed_logins   TINYINT UNSIGNED NOT NULL DEFAULT 0,       -- wrong passwords on web; lock after 5
  locked_until    DATETIME     NULL,                         -- web lock lasts 15 minutes
  created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted_at      DATETIME     NULL,                     -- soft delete, purge later
  CONSTRAINT chk_has_credential CHECK (password_hash IS NOT NULL OR signup_channel = 'ussd')  -- USSD accounts log in by SMS code, no password or PIN
);

CREATE TABLE refresh_tokens (
  id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id     BIGINT UNSIGNED NOT NULL,
  token_hash  CHAR(64)  NOT NULL UNIQUE,                 -- SHA-256 of the token, never the token
  expires_at  DATETIME  NOT NULL,
  revoked_at  DATETIME  NULL,
  created_at  DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX (user_id)
);

CREATE TABLE otp_codes (                                 -- one-time SMS codes: verify, reset, USSD login (valid ~5 min, single use)
  id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  phone       VARCHAR(15) NOT NULL,
  code_hash   CHAR(64)    NOT NULL,
  purpose     ENUM('verify','reset','ussd_login') NOT NULL,
  attempts    TINYINT UNSIGNED NOT NULL DEFAULT 0,
  expires_at  DATETIME    NOT NULL,
  used_at     DATETIME    NULL,
  INDEX (phone, purpose)
);

CREATE TABLE audit_log (
  id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id     BIGINT UNSIGNED NULL,
  action      VARCHAR(60) NOT NULL,                      -- login, login_failed, meter_added, data_deleted...
  ip          VARCHAR(45) NULL,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX (user_id, created_at)
);