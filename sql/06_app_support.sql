-- =====================================================================
-- 06_app_support.sql   (written by Member 3 for the Streamlit app)
-- Run AFTER 01_olap_ddl.sql and 02_olap_dml.sql.
-- Hand this file to Member 2 so it can live in the warehouse branch.
--
--  1. Index + DimDate extension (reviews dated 2026/2027 need a date_key)
--  2. sp_scd2_update_employee : SCD Type 2 change (close old row, insert new)
--  3. sp_sync_new_employee / project / assignment / review :
--     push ONE new OLTP row into the warehouse right after the app saves it
--
-- These procedures do NOT start/commit transactions. The Python app opens one
-- transaction, writes OLTP + calls these, then commits (or rolls everything back).
-- =====================================================================
USE enterprise_employee_analytics_olap;

-- 1a. Speeds up every join on employee_number (110k+ rows). Run ONCE
--     (if you see "Duplicate key name", it already exists - ignore it).
ALTER TABLE DimEmployee ADD INDEX idx_dimemployee_number (employee_number, is_current);

-- 1b. Extend DimDate to the end of 2027 (safe to re-run).
INSERT IGNORE INTO DimDate (date_key, full_date, year, quarter, month, month_name, day, day_name)
WITH RECURSIVE d AS (
    SELECT DATE('2026-01-01') AS dt
    UNION ALL
    SELECT DATE_ADD(dt, INTERVAL 1 DAY) FROM d WHERE dt < '2027-12-31'
)
SELECT DATE_FORMAT(dt, '%Y%m%d') + 0, dt, YEAR(dt), QUARTER(dt), MONTH(dt),
       MONTHNAME(dt), DAY(dt), DAYNAME(dt)
FROM d;


-- 2. SCD TYPE 2 --------------------------------------------------------
-- NULL for a p_* argument means "this attribute is not changing".
DROP PROCEDURE IF EXISTS sp_scd2_update_employee;
DELIMITER $$
CREATE PROCEDURE sp_scd2_update_employee(
    IN  p_employee_number INT,
    IN  p_department_id   INT,
    IN  p_job_role_id     INT,
    IN  p_job_level       INT,
    IN  p_monthly_income  INT,
    IN  p_effective_date  DATE,
    OUT p_new_key         INT
)
BEGIN
    DECLARE v_old_key   INT;
    DECLARE v_old_start DATE;
    DECLARE v_changed   INT DEFAULT 0;
    DECLARE v_eff       DATE;

    SET p_new_key = NULL;

    SELECT MAX(employee_key) INTO v_old_key
    FROM DimEmployee
    WHERE employee_number = p_employee_number AND is_current = 1;

    IF v_old_key IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'SCD2: no current DimEmployee row for this employee_number';
    END IF;

    IF p_department_id IS NOT NULL
       AND NOT EXISTS (SELECT 1 FROM DimDepartment WHERE department_id = p_department_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'SCD2: unknown department_id';
    END IF;
    IF p_job_role_id IS NOT NULL
       AND NOT EXISTS (SELECT 1 FROM DimJobRole WHERE job_role_id = p_job_role_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'SCD2: unknown job_role_id';
    END IF;

    -- Did any tracked attribute really change?
    SELECT COUNT(*) INTO v_changed
    FROM DimEmployee
    WHERE employee_key = v_old_key
      AND (   (p_department_id  IS NOT NULL AND NOT (department_id  <=> p_department_id))
           OR (p_job_role_id    IS NOT NULL AND NOT (job_role_id    <=> p_job_role_id))
           OR (p_job_level      IS NOT NULL AND NOT (job_level      <=> p_job_level))
           OR (p_monthly_income IS NOT NULL AND NOT (monthly_income <=> p_monthly_income)));

    IF v_changed > 0 THEN
        SELECT effective_start_date INTO v_old_start
        FROM DimEmployee WHERE employee_key = v_old_key;

        SET v_eff = COALESCE(p_effective_date, CURDATE());
        IF v_old_start IS NOT NULL AND v_eff <= v_old_start THEN
            SET v_eff = DATE_ADD(v_old_start, INTERVAL 1 DAY);   -- keep ranges valid
        END IF;

        -- (a) close the old version
        UPDATE DimEmployee
        SET effective_end_date = DATE_SUB(v_eff, INTERVAL 1 DAY),
            is_current = 0
        WHERE employee_key = v_old_key;

        -- (b) insert the new version (new surrogate key is generated automatically)
        INSERT INTO DimEmployee (
        employee_number,
        first_name,
        last_name,
        age,
        gender,
        marital_status,
        job_level,
        education,
        business_travel,
        distance_from_home,
        daily_rate,
        hourly_rate,
        monthly_income,
        monthly_rate,
        overtime,
        job_satisfaction,
        environment_satisfaction,
        job_involvement,
        performance_rating,
        relationship_satisfaction,
        work_life_balance,
        percent_salary_hike,
        stock_option_level,
        total_working_years,
        years_at_company,
        years_in_current_role,
        years_since_last_promotion,
        years_with_current_manager,
        num_companies_worked,
        training_times_last_year,
        attrition,
        department_id,
        department_name,
        job_role_id,
        job_role_name,
        education_field_id,
        education_field_name,
        effective_start_date,
        effective_end_date,
        is_current
        )
        SELECT
        o.employee_number,
        o.first_name,
        o.last_name,
        o.age,
        o.gender,
        o.marital_status,
        o.job_level,
        o.education,
        o.business_travel,
        o.distance_from_home,
        o.daily_rate,
        o.hourly_rate,
        o.monthly_income,
        o.monthly_rate,
        o.overtime,
        o.job_satisfaction,
        o.environment_satisfaction,
        o.job_involvement,
        o.performance_rating,
        o.relationship_satisfaction,
        o.work_life_balance,
        o.percent_salary_hike,
        o.stock_option_level,
        o.total_working_years,
        o.years_at_company,
        o.years_in_current_role,
        o.years_since_last_promotion,
        o.years_with_current_manager,
        o.num_companies_worked,
        o.training_times_last_year,
        o.attrition,
        COALESCE(p_department_id, o.department_id), dep.department_name,
        COALESCE(p_job_role_id,   o.job_role_id),   jr.job_role_name,
        o.education_field_id, o.education_field_name,
        v_eff, NULL, 1
        FROM DimEmployee o
        LEFT JOIN DimDepartment dep ON dep.department_id = COALESCE(p_department_id, o.department_id)
        LEFT JOIN DimJobRole    jr  ON jr.job_role_id    = COALESCE(p_job_role_id,   o.job_role_id)
        WHERE o.employee_key = v_old_key;

        SET p_new_key = LAST_INSERT_ID();

        -- the new version carries the changed level / salary
        UPDATE DimEmployee
        SET job_level      = COALESCE(p_job_level,      job_level),
            monthly_income = COALESCE(p_monthly_income, monthly_income)
        WHERE employee_key = p_new_key;

        -- (c) fact row for the new version, so current-state reports still see this employee
        INSERT INTO FactEmployee (
        employee_key,
        department_key,
        job_role_key,
        education_field_key,
        date_key,
        monthly_income,
        daily_rate,
        hourly_rate,
        job_satisfaction,
        environment_satisfaction,
        job_involvement,
        performance_rating,
        relationship_satisfaction,
        work_life_balance,
        percent_salary_hike,
        stock_option_level,
        total_working_years,
        years_at_company,
        years_in_current_role,
        years_since_last_promotion,
        years_with_current_manager,
        num_companies_worked,
        training_times_last_year,
        attrition
        )
        SELECT n.employee_key, dd.department_key, jr.job_role_key, ef.education_field_key,
               DATE_FORMAT(v_eff, '%Y%m%d') + 0,
        n.monthly_income,
        n.daily_rate,
        n.hourly_rate,
        n.job_satisfaction,
        n.environment_satisfaction,
        n.job_involvement,
        n.performance_rating,
        n.relationship_satisfaction,
        n.work_life_balance,
        n.percent_salary_hike,
        n.stock_option_level,
        n.total_working_years,
        n.years_at_company,
        n.years_in_current_role,
        n.years_since_last_promotion,
        n.years_with_current_manager,
        n.num_companies_worked,
        n.training_times_last_year,
        n.attrition
        FROM DimEmployee n
        LEFT JOIN DimDepartment     dd ON dd.department_id      = n.department_id
        LEFT JOIN DimJobRole        jr ON jr.job_role_id        = n.job_role_id
        LEFT JOIN DimEducationField ef ON ef.education_field_id = n.education_field_id
        WHERE n.employee_key = p_new_key;
    END IF;
END$$
DELIMITER ;


-- 3. Single-row syncs ----------------------------------------------------
DROP PROCEDURE IF EXISTS sp_sync_new_employee;
DELIMITER $$
CREATE PROCEDURE sp_sync_new_employee(IN p_employee_number INT)
BEGIN
    DECLARE v_key INT;
    IF NOT EXISTS (SELECT 1 FROM DimEmployee WHERE employee_number = p_employee_number AND is_current = 1) THEN
        INSERT INTO DimEmployee (
        employee_number,
        first_name,
        last_name,
        age,
        gender,
        marital_status,
        job_level,
        education,
        business_travel,
        distance_from_home,
        daily_rate,
        hourly_rate,
        monthly_income,
        monthly_rate,
        overtime,
        job_satisfaction,
        environment_satisfaction,
        job_involvement,
        performance_rating,
        relationship_satisfaction,
        work_life_balance,
        percent_salary_hike,
        stock_option_level,
        total_working_years,
        years_at_company,
        years_in_current_role,
        years_since_last_promotion,
        years_with_current_manager,
        num_companies_worked,
        training_times_last_year,
        attrition,
        department_id,
        department_name,
        job_role_id,
        job_role_name,
        education_field_id,
        education_field_name,
        effective_start_date,
        effective_end_date,
        is_current
        )
        SELECT
        e.employee_number,
        e.first_name,
        e.last_name,
        e.age,
        e.gender,
        e.marital_status,
        e.job_level,
        e.education,
        e.business_travel,
        e.distance_from_home,
        e.daily_rate,
        e.hourly_rate,
        e.monthly_income,
        e.monthly_rate,
        e.overtime,
        e.job_satisfaction,
        e.environment_satisfaction,
        e.job_involvement,
        e.performance_rating,
        e.relationship_satisfaction,
        e.work_life_balance,
        e.percent_salary_hike,
        e.stock_option_level,
        e.total_working_years,
        e.years_at_company,
        e.years_in_current_role,
        e.years_since_last_promotion,
        e.years_with_current_manager,
        e.num_companies_worked,
        e.training_times_last_year,
        e.attrition,
        e.department_id, dep.department_name, e.job_role_id, jr.job_role_name,
        e.education_field_id, ef.education_field_name, CURDATE(), NULL, 1
        FROM enterprise_employee_analytics.Employee e
        LEFT JOIN enterprise_employee_analytics.Department     dep ON dep.department_id = e.department_id
        LEFT JOIN enterprise_employee_analytics.JobRole        jr  ON jr.job_role_id    = e.job_role_id
        LEFT JOIN enterprise_employee_analytics.EducationField ef  ON ef.education_field_id = e.education_field_id
        WHERE e.employee_number = p_employee_number;
        SET v_key = LAST_INSERT_ID();

        INSERT INTO FactEmployee (
        employee_key,
        department_key,
        job_role_key,
        education_field_key,
        date_key,
        monthly_income,
        daily_rate,
        hourly_rate,
        job_satisfaction,
        environment_satisfaction,
        job_involvement,
        performance_rating,
        relationship_satisfaction,
        work_life_balance,
        percent_salary_hike,
        stock_option_level,
        total_working_years,
        years_at_company,
        years_in_current_role,
        years_since_last_promotion,
        years_with_current_manager,
        num_companies_worked,
        training_times_last_year,
        attrition
        )
        SELECT n.employee_key, dd.department_key, jr.job_role_key, ef.education_field_key,
               DATE_FORMAT(CURDATE(), '%Y%m%d') + 0,
        n.monthly_income,
        n.daily_rate,
        n.hourly_rate,
        n.job_satisfaction,
        n.environment_satisfaction,
        n.job_involvement,
        n.performance_rating,
        n.relationship_satisfaction,
        n.work_life_balance,
        n.percent_salary_hike,
        n.stock_option_level,
        n.total_working_years,
        n.years_at_company,
        n.years_in_current_role,
        n.years_since_last_promotion,
        n.years_with_current_manager,
        n.num_companies_worked,
        n.training_times_last_year,
        n.attrition
        FROM DimEmployee n
        LEFT JOIN DimDepartment     dd ON dd.department_id      = n.department_id
        LEFT JOIN DimJobRole        jr ON jr.job_role_id        = n.job_role_id
        LEFT JOIN DimEducationField ef ON ef.education_field_id = n.education_field_id
        WHERE n.employee_key = v_key;
    END IF;
END$$
DELIMITER ;


DROP PROCEDURE IF EXISTS sp_sync_project;
DELIMITER $$
CREATE PROCEDURE sp_sync_project(IN p_project_id INT)
BEGIN
    INSERT IGNORE INTO DimProject (project_id, project_name, department_id, department_name, start_date, end_date, status)
    SELECT p.project_id, p.project_name, p.department_id, d.department_name, p.start_date, p.end_date, p.status
    FROM enterprise_employee_analytics.Project p
    LEFT JOIN enterprise_employee_analytics.Department d ON d.department_id = p.department_id
    WHERE p.project_id = p_project_id;
END$$
DELIMITER ;


DROP PROCEDURE IF EXISTS sp_sync_assignment;
DELIMITER $$
CREATE PROCEDURE sp_sync_assignment(IN p_assignment_id INT)
BEGIN
    INSERT INTO FactAssignment (employee_key, project_key, date_key, assignment_id, role, allocation_percentage)
    SELECT c.employee_key, dp.project_key, DATE_FORMAT(a.assigned_date, '%Y%m%d') + 0,
           a.assignment_id, a.role, a.allocation_percentage
    FROM enterprise_employee_analytics.Assignment a
    JOIN enterprise_employee_analytics.Employee e ON e.employee_id = a.employee_id
    JOIN DimEmployee c  ON c.employee_number = e.employee_number AND c.is_current = 1
    JOIN DimProject  dp ON dp.project_id = a.project_id
    WHERE a.assignment_id = p_assignment_id
      AND NOT EXISTS (SELECT 1 FROM FactAssignment f WHERE f.assignment_id = a.assignment_id);
END$$
DELIMITER ;


-- A review is attached to the employee VERSION that was valid on the review date
DROP PROCEDURE IF EXISTS sp_sync_review;
DELIMITER $$
CREATE PROCEDURE sp_sync_review(IN p_review_id INT)
BEGIN
    INSERT INTO FactReview (employee_key, date_key, review_id, review_period, rating, comments)
    SELECT COALESCE(
               (SELECT MAX(v.employee_key) FROM DimEmployee v
                 WHERE v.employee_number = e.employee_number
                   AND r.review_date >= v.effective_start_date
                   AND (v.effective_end_date IS NULL OR r.review_date <= v.effective_end_date)),
               c.employee_key),
           DATE_FORMAT(r.review_date, '%Y%m%d') + 0,
           r.review_id, r.review_period, r.rating, r.comments
    FROM enterprise_employee_analytics.Reviews r
    JOIN enterprise_employee_analytics.Employee e ON e.employee_id = r.employee_id
    JOIN DimEmployee c ON c.employee_number = e.employee_number AND c.is_current = 1
    WHERE r.review_id = p_review_id
      AND NOT EXISTS (SELECT 1 FROM FactReview f WHERE f.review_id = r.review_id);
END$$
DELIMITER ;
