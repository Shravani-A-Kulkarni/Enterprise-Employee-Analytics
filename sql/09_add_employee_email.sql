-- Run ONCE against the existing OLTP database (local MySQL and Aiven).
-- Old rows get NULL; MySQL allows many NULLs under a UNIQUE index.
ALTER TABLE Employee ADD COLUMN email VARCHAR(255) NULL UNIQUE AFTER last_name;
