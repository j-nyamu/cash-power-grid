-- Mirrors app/models.py: Entry.
-- Depends on: 01_auth.sql, 02_meters.sql
USE cashpower;

CREATE TABLE entries (                             -- a purchase (money and units) or a meter reading (units left)
  id         INT NOT NULL AUTO_INCREMENT,
  meter_id   INT NOT NULL,
  user_id    INT NOT NULL,
  kind       VARCHAR(8) NOT NULL,                  -- purchase / reading
  day        VARCHAR(10) NOT NULL,                 -- YYYY-MM-DD
  rwf        INT NULL,
  kwh        FLOAT NOT NULL,
  estimated  INT NULL DEFAULT 0,                   -- 1 = units were calculated, 0 = copied from the receipt
  created    VARCHAR(32) NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT fk_entries_meter FOREIGN KEY (meter_id) REFERENCES meters (id),
  CONSTRAINT fk_entries_user  FOREIGN KEY (user_id)  REFERENCES users (id),
  CONSTRAINT ck_entries_kind  CHECK (kind IN ('purchase','reading'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;