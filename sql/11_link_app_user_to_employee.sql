-- =====================================================================
-- 11_link_app_user_to_employee.sql  -- OPTIONAL, MANUAL, OLTP database only.
-- The app NEVER runs this. Review each result, then run the UPDATE yourself.
--
-- Use it to link an EXISTING login whose employee_number is NULL to the
-- employee record that has exactly the same email.
-- =====================================================================
USE enterprise_employee_analytics;

-- STEP 1 (read-only): unlinked Employee logins that have an exact-email employee record.
-- Only rows listed here are safe candidates. Logins with no row here (for example
-- testemployee101@example.com) have no matching employee and must stay unlinked.
SELECT u.user_id, u.email AS login_email, e.employee_number,
       CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
       (SELECT COUNT(*) FROM AppUser x WHERE x.employee_number = e.employee_number) AS already_linked_logins
FROM AppUser u
JOIN Employee e ON e.email = u.email
WHERE u.role = 'Employee' AND u.employee_number IS NULL;
-- Only continue when already_linked_logins = 0 and the name looks right.

-- STEP 2: link ONE account. Change the email if needed. Touches one row at most.
UPDATE AppUser u
JOIN Employee e ON e.email = u.email
SET u.employee_number = e.employee_number
WHERE u.email = 'jus@gmail.com'
  AND u.role = 'Employee'
  AND u.employee_number IS NULL;

-- STEP 3: check the result
SELECT user_id, email, role, employee_number FROM AppUser WHERE email = 'jus@gmail.com';
