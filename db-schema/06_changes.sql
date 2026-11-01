-- Later changes go here as ALTER statements, one block per change, newest last.
-- Depends on: 01-05.
USE cashpower;

-- Purchase recommendation: how many days the owner wants a purchase to cover
ALTER TABLE meters ADD COLUMN cover_days TINYINT UNSIGNED NOT NULL DEFAULT 14;