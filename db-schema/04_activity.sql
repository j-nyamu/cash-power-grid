-- Mirrors app/models.py: Activity.
-- Depends on: 02_meters.sql
USE cashpower;

CREATE TABLE activity (                            -- the log the owner sees: who viewed, added, was invited, left
  id        INT NOT NULL AUTO_INCREMENT,
  meter_id  INT NOT NULL,
  user_id   INT NULL,
  action    VARCHAR(30) NOT NULL,
  detail    VARCHAR(255) NULL,
  ts        VARCHAR(32) NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT fk_activity_meter FOREIGN KEY (meter_id) REFERENCES meters (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;