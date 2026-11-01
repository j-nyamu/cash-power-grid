-- Owner: SMS alerts (system-initiated). Depends on: 01_auth.sql, 02_meters.sql
-- Alerts are sent by SMS only; USSD is user-initiated and cannot push messages.
USE cashpower;

CREATE TABLE alerts (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  meter_id        BIGINT UNSIGNED NOT NULL,
  user_id         BIGINT UNSIGNED NOT NULL,
  channel         ENUM('sms') NOT NULL DEFAULT 'sms',
  scheduled_for   DATETIME NOT NULL,
  sent_at         DATETIME NULL,
  status          ENUM('pending','sent','failed','cancelled') NOT NULL DEFAULT 'pending',
  provider_msg_id VARCHAR(100) NULL,
  FOREIGN KEY (meter_id) REFERENCES meters(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id)  REFERENCES users(id)  ON DELETE CASCADE,
  INDEX (status, scheduled_for)
);