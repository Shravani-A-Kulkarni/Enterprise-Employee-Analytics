-- =====================================================================
-- 10_app_users.sql  -- OLTP database only. Run ONCE (safe to re-run).
-- Creates the login table and 4 demo accounts. Password for ALL of them: Demo@123
--
--   hr@company.com          HR        -> every page
--   manager@company.com     Manager   -> Projects, Reviews, Analytics
--   employee1@company.com   Employee  -> own profile (employee #1)
--   employee2@company.com   Employee  -> own profile (employee #2)
--
-- Run it BEFORE using the new login page. On Aiven run it on the same
-- enterprise_employee_analytics database as the other OLTP scripts.
-- =====================================================================
USE enterprise_employee_analytics;

CREATE TABLE IF NOT EXISTS AppUser (
    user_id         INT AUTO_INCREMENT PRIMARY KEY,
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    role            ENUM('HR', 'Manager', 'Employee') NOT NULL,
    display_name    VARCHAR(150) NOT NULL,
    employee_number INT NULL,
    is_active       TINYINT(1) NOT NULL DEFAULT 1,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- HR and Manager accounts are not tied to an employee record
INSERT IGNORE INTO AppUser (email, password_hash, role, display_name, employee_number) VALUES
('hr@company.com',      'pbkdf2_sha256$200000$502adcd16e1e42822c23cd70962bccaf$3105443871ae4ffa2b539a4daee631ca36738e62cfe3d8bf5555c6eb1bd0b728', 'HR',      'Demo HR',      NULL),
('manager@company.com', 'pbkdf2_sha256$200000$ccd20e7bd80cd2bbe7c48c7c69720f35$e9777001773c5d3c55d81d6216687b531405f8a51d76a920e527621694b65462', 'Manager', 'Demo Manager', NULL);

-- Employee accounts are linked to real employee rows (name is copied from the Employee table)
INSERT IGNORE INTO AppUser (email, password_hash, role, display_name, employee_number)
SELECT 'employee1@company.com', 'pbkdf2_sha256$200000$19044bba767f2ecd7d390064f3a393a4$88153527b93f1a1978d631e4157b3a9c8ce59cc803c2497a39fdff1e8863c62d', 'Employee',
       CONCAT(first_name, ' ', last_name), employee_number
FROM Employee WHERE employee_number = 1;

INSERT IGNORE INTO AppUser (email, password_hash, role, display_name, employee_number)
SELECT 'employee2@company.com', 'pbkdf2_sha256$200000$693650ffe412436b82def786524e1bcc$f9417c1f0a92e347dde9469bb6f24282ef01596d756d2bfdae20aadbf74a176d', 'Employee',
       CONCAT(first_name, ' ', last_name), employee_number
FROM Employee WHERE employee_number = 2;

-- Check: should list 4 rows
SELECT user_id, email, role, display_name, employee_number FROM AppUser;
