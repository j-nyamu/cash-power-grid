-- Mirrors app/models.py: User, Otp, Device.
-- Times are stored as ISO text (UTC), exactly as in the models, so SQLite and MySQL behave the same.
USE cashpower;

CREATE TABLE users (
  id            INT NOT NULL AUTO_INCREMENT,
  uid           VARCHAR(12) NULL,                 -- shown to the person: CPG-000001
  name          VARCHAR(120) NOT NULL,
  phone         VARCHAR(10) NOT NULL,             -- one account per phone number
  email         VARCHAR(255) NOT NULL,
  acct_type     VARCHAR(20) NOT NULL,             -- household / business / landlord
  pw_hash       VARCHAR(255) NOT NULL,
  lang          VARCHAR(2) NULL DEFAULT 'en',
  failed        INT NULL DEFAULT 0,               -- wrong passwords in a row
  locked_until  VARCHAR(32) NULL,
  created       VARCHAR(32) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_users_uid (uid),
  UNIQUE KEY uq_users_phone (phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE otps (                                -- one-time codes; only a hash is kept, never the code
  id          INT NOT NULL AUTO_INCREMENT,
  phone       VARCHAR(10) NOT NULL,
  purpose     VARCHAR(10) NOT NULL,                -- signup / login / reset
  code_hash   VARCHAR(64) NOT NULL,
  expires     VARCHAR(32) NOT NULL,
  tries       INT NULL DEFAULT 0,
  used        INT NULL DEFAULT 0,
  created     VARCHAR(32) NOT NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE devices (                             -- "remember this device": the browser keeps a token, we keep its hash
  id          INT NOT NULL AUTO_INCREMENT,
  user_id     INT NOT NULL,
  token_hash  VARCHAR(64) NOT NULL,
  label       VARCHAR(80) NULL,
  expires     VARCHAR(32) NOT NULL,
  created     VARCHAR(32) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_devices_token_hash (token_hash),
  CONSTRAINT fk_devices_user FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;