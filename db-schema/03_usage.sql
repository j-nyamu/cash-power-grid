-- Owner: usage data and forecasting. Depends on: 01_auth.sql, 02_meters.sql
-- Privacy: never store full tokens.
USE cashpower;

-- ---------- USAGE DATA ----------
CREATE TABLE purchases (                                 -- NO token column on purpose
  id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  meter_id      BIGINT UNSIGNED NOT NULL,
  amount_rwf    DECIMAL(10,2) NOT NULL CHECK (amount_rwf > 0),
  kwh_credited  DECIMAL(8,2)  NOT NULL CHECK (kwh_credited > 0),
  purchased_at  DATETIME NOT NULL,
  source        ENUM('web','ussd','vending') NOT NULL DEFAULT 'web',
  logged_by     BIGINT UNSIGNED NOT NULL,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (meter_id)  REFERENCES meters(id) ON DELETE CASCADE,
  FOREIGN KEY (logged_by) REFERENCES users(id),
  INDEX (meter_id, purchased_at)
);

CREATE TABLE readings (
  id             BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  meter_id       BIGINT UNSIGNED NOT NULL,
  kwh_remaining  DECIMAL(8,2) NOT NULL CHECK (kwh_remaining >= 0),
  read_at        DATETIME NOT NULL,
  source         ENUM('web','ussd') NOT NULL DEFAULT 'web',
  logged_by      BIGINT UNSIGNED NOT NULL,
  created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (meter_id)  REFERENCES meters(id) ON DELETE CASCADE,
  FOREIGN KEY (logged_by) REFERENCES users(id),
  INDEX (meter_id, read_at)
);

CREATE TABLE tariff_blocks (                             -- versioned: update when RURA revises rates
  id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  tariff_class    VARCHAR(30) NOT NULL,
  from_kwh        DECIMAL(8,2) NOT NULL,
  to_kwh          DECIMAL(8,2) NULL,                     -- NULL = no upper limit
  rate_rwf_per_kwh DECIMAL(8,2) NOT NULL,
  effective_from  DATE NOT NULL,
  effective_to    DATE NULL,
  INDEX (tariff_class, effective_from)
);

CREATE TABLE appliances (                                -- for the what-if feature
  id             BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  meter_id       BIGINT UNSIGNED NOT NULL,
  name           VARCHAR(60) NOT NULL,
  watts          SMALLINT UNSIGNED NOT NULL,
  hours_per_day  DECIMAL(4,2) NOT NULL,
  FOREIGN KEY (meter_id) REFERENCES meters(id) ON DELETE CASCADE
);

CREATE TABLE forecasts (                                 -- cached output of the forecasting engine
  id                BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  meter_id          BIGINT UNSIGNED NOT NULL,
  computed_at       DATETIME NOT NULL,
  kwh_remaining_est DECIMAL(8,2) NOT NULL,
  daily_use_kwh     DECIMAL(6,2) NOT NULL,
  run_out_earliest  DATETIME NOT NULL,
  run_out_latest    DATETIME NOT NULL,
  FOREIGN KEY (meter_id) REFERENCES meters(id) ON DELETE CASCADE,
  INDEX (meter_id, computed_at)
);

-- Example tariff rows (verify with REG/RURA before use):
-- INSERT INTO tariff_blocks (tariff_class, from_kwh, to_kwh, rate_rwf_per_kwh, effective_from)
-- VALUES ('residential', 0, 20, 89, '2025-10-01'), ('residential', 20, 50, 310, '2025-10-01'),
--        ('residential', 50, NULL, 369, '2025-10-01');