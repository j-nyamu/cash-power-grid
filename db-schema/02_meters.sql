-- Mirrors app/models.py: Meter, Access.
-- Depends on: 01_auth.sql
USE cashpower;

CREATE TABLE meters (
  id        INT NOT NULL AUTO_INCREMENT,
  meter_no  VARCHAR(11) NOT NULL,                  -- one owner per meter number
  nickname  VARCHAR(30) NOT NULL,
  owner_id  INT NOT NULL,
  created   VARCHAR(32) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_meters_meter_no (meter_no),
  CONSTRAINT fk_meters_owner FOREIGN KEY (owner_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE access (                              -- people the owner lets look at (or add to) a meter; keyed by phone so an invite works before sign-up
  id          INT NOT NULL AUTO_INCREMENT,
  meter_id    INT NOT NULL,
  phone       VARCHAR(10) NOT NULL,
  role        VARCHAR(4) NOT NULL,                 -- view / add
  status      VARCHAR(8) NOT NULL,                 -- pending / active
  invited_by  INT NOT NULL,
  created     VARCHAR(32) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_access_meter_phone (meter_id, phone),
  CONSTRAINT fk_access_meter FOREIGN KEY (meter_id) REFERENCES meters (id),
  CONSTRAINT ck_access_role   CHECK (role IN ('view','add')),
  CONSTRAINT ck_access_status CHECK (status IN ('pending','active'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;