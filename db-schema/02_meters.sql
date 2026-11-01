-- Owner: meters and household sharing. Depends on: 01_auth.sql
-- Roles: one owner per meter (registered under their name); members are invited and must accept.
-- Privacy: store meter numbers encrypted + a hash for lookup.
USE cashpower;

-- ---------- METERS ----------
CREATE TABLE meters (
  id                BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  label             VARCHAR(50)  NOT NULL,               -- "Home", "Shop"
  meter_number_enc  VARBINARY(255) NOT NULL,             -- encrypted (e.g. Fernet)
  meter_number_hash CHAR(64)     NOT NULL,               -- HMAC for lookups; not unique across users
  meter_last4       CHAR(4)      NOT NULL,               -- for masked display
  tariff_class      VARCHAR(30)  NOT NULL DEFAULT 'residential',
  owner_id          BIGINT UNSIGNED NOT NULL,            -- person the meter is registered under
  created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (owner_id) REFERENCES users(id),
  INDEX (meter_number_hash)
);

CREATE TABLE meter_members (                             -- owner + family members who accepted
  meter_id    BIGINT UNSIGNED NOT NULL,
  user_id     BIGINT UNSIGNED NOT NULL,
  role        ENUM('owner','member') NOT NULL DEFAULT 'member',
  can_log     TINYINT(1) NOT NULL DEFAULT 0,             -- member may add readings/purchases
  notify_sms  TINYINT(1) NOT NULL DEFAULT 1,             -- member can switch alerts off
  joined_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (meter_id, user_id),
  FOREIGN KEY (meter_id) REFERENCES meters(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id)  REFERENCES users(id)  ON DELETE CASCADE
);

CREATE TABLE meter_invitations (                         -- owner adds a family member
  id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  meter_id      BIGINT UNSIGNED NOT NULL,
  invited_by    BIGINT UNSIGNED NOT NULL,
  invitee_name  VARCHAR(100) NULL,
  invitee_phone VARCHAR(15)  NULL,
  invitee_email VARCHAR(254) NULL,
  can_log       TINYINT(1) NOT NULL DEFAULT 0,
  token_hash    CHAR(64) NOT NULL UNIQUE,                -- SHA-256 of the invite link token
  status        ENUM('pending','accepted','declined','revoked','expired') NOT NULL DEFAULT 'pending',
  expires_at    DATETIME NOT NULL,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (meter_id)   REFERENCES meters(id) ON DELETE CASCADE,
  FOREIGN KEY (invited_by) REFERENCES users(id),
  INDEX (invitee_phone), INDEX (invitee_email)
);