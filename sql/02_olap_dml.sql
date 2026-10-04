USE enterprise_employee_analytics_olap;

SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE TABLE FactReview;
TRUNCATE TABLE FactAssignment;
TRUNCATE TABLE FactEmployee;

TRUNCATE TABLE DimEmployee;
TRUNCATE TABLE DimProject;
TRUNCATE TABLE DimEducationField;
TRUNCATE TABLE DimJobRole;
TRUNCATE TABLE DimDepartment;
TRUNCATE TABLE DimDate;

SET FOREIGN_KEY_CHECKS = 1;


INSERT INTO DimDepartment (
    department_id,
    department_name
)
SELECT
    department_id,
    department_name
FROM enterprise_employee_analytics.Department;


INSERT INTO DimJobRole (
    job_role_id,
    job_role_name
)
SELECT
    job_role_id,
    job_role_name
FROM enterprise_employee_analytics.JobRole;


INSERT INTO DimEducationField (
    education_field_id,
    education_field_name
)
SELECT
    education_field_id,
    education_field_name
FROM enterprise_employee_analytics.EducationField;


INSERT INTO DimProject (
    project_id,
    project_name,
    department_id,
    department_name,
    start_date,
    end_date,
    status
)
SELECT
    p.project_id,
    p.project_name,
    p.department_id,
    d.department_name,
    p.start_date,
    p.end_date,
    p.status
FROM enterprise_employee_analytics.Project p
LEFT JOIN enterprise_employee_analytics.Department d
    ON p.department_id = d.department_id;


INSERT INTO DimDate (
    date_key,
    full_date,
    year,
    quarter,
    month,
    month_name,
    day,
    day_name
)
SELECT
    DATE_FORMAT(d, '%Y%m%d') + 0 AS date_key,
    d AS full_date,
    YEAR(d) AS year,
    QUARTER(d) AS quarter,
    MONTH(d) AS month,
    MONTHNAME(d) AS month_name,
    DAY(d) AS day,
    DAYNAME(d) AS day_name
FROM (
    SELECT
        DATE_ADD('2023-01-01', INTERVAL seq DAY) AS d
    FROM (
        SELECT
            a.n
            + b.n * 10
            + c.n * 100
            + d.n * 1000 AS seq
        FROM
            (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL
             SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL
             SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL
             SELECT 9) a
        CROSS JOIN
            (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL
             SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL
             SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL
             SELECT 9) b
        CROSS JOIN
            (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL
             SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL
             SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL
             SELECT 9) c
        CROSS JOIN
            (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL
             SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL
             SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL
             SELECT 9) d
    ) numbers
    WHERE DATE_ADD('2023-01-01', INTERVAL seq DAY)
          <= '2025-12-31'
) dates;


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
    h.job_level,
    e.education,
    e.business_travel,
    e.distance_from_home,
    e.daily_rate,
    e.hourly_rate,
    h.monthly_income,
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
    h.department_id,
    dep.department_name,
    h.job_role_id,
    jr.job_role_name,
    h.education_field_id,
    ef.education_field_name,
    h.effective_start_date,
    h.effective_end_date,
    h.is_current
FROM enterprise_employee_analytics.employee_scd_history h
JOIN enterprise_employee_analytics.Employee e
    ON h.employee_number = e.employee_number
LEFT JOIN enterprise_employee_analytics.Department dep
    ON h.department_id = dep.department_id
LEFT JOIN enterprise_employee_analytics.JobRole jr
    ON h.job_role_id = jr.job_role_id
LEFT JOIN enterprise_employee_analytics.EducationField ef
    ON h.education_field_id = ef.education_field_id
WHERE h.is_current = 0;


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
    e.department_id,
    dep.department_name,
    e.job_role_id,
    jr.job_role_name,
    e.education_field_id,
    ef.education_field_name,
    h.effective_start_date,
    NULL AS effective_end_date,
    1 AS is_current
FROM enterprise_employee_analytics.Employee e
LEFT JOIN enterprise_employee_analytics.Department dep
    ON e.department_id = dep.department_id
LEFT JOIN enterprise_employee_analytics.JobRole jr
    ON e.job_role_id = jr.job_role_id
LEFT JOIN enterprise_employee_analytics.EducationField ef
    ON e.education_field_id = ef.education_field_id
LEFT JOIN (
    SELECT
        employee_number,
        MAX(effective_start_date) AS effective_start_date
    FROM enterprise_employee_analytics.employee_scd_history
    WHERE is_current = 1
    GROUP BY employee_number
) h
    ON e.employee_number = h.employee_number;


INSERT INTO FactEmployee (
    employee_key,
    department_key,
    job_role_key,
    education_field_key,
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
SELECT
    de.employee_key,
    dd.department_key,
    dj.job_role_key,
    def.education_field_key,
    e.monthly_income,
    e.daily_rate,
    e.hourly_rate,
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
    e.attrition
FROM enterprise_employee_analytics.Employee e
JOIN DimEmployee de
    ON e.employee_number = de.employee_number
   AND de.is_current = 1
JOIN DimDepartment dd
    ON e.department_id = dd.department_id
JOIN DimJobRole dj
    ON e.job_role_id = dj.job_role_id
JOIN DimEducationField def
    ON e.education_field_id = def.education_field_id;


INSERT INTO FactAssignment (
    employee_key,
    project_key,
    date_key,
    assignment_id,
    role,
    allocation_percentage
)
SELECT
    de.employee_key,
    dp.project_key,
    DATE_FORMAT(a.assigned_date, '%Y%m%d') + 0,
    a.assignment_id,
    a.role,
    a.allocation_percentage
FROM enterprise_employee_analytics.Assignment a
JOIN enterprise_employee_analytics.Employee e
    ON a.employee_id = e.employee_id
JOIN DimEmployee de
    ON e.employee_number = de.employee_number
   AND de.is_current = 1
JOIN DimProject dp
    ON a.project_id = dp.project_id;


INSERT INTO FactReview (
    employee_key,
    date_key,
    review_id,
    review_period,
    rating,
    comments
)
SELECT
    de.employee_key,
    DATE_FORMAT(r.review_date, '%Y%m%d') + 0,
    r.review_id,
    r.review_period,
    r.rating,
    r.comments
FROM enterprise_employee_analytics.Reviews r
JOIN enterprise_employee_analytics.Employee e
    ON r.employee_id = e.employee_id
JOIN DimEmployee de
    ON e.employee_number = de.employee_number
   AND de.is_current = 1;


SELECT 'DimDepartment' AS table_name, COUNT(*) AS row_count
FROM DimDepartment

UNION ALL

SELECT 'DimJobRole', COUNT(*)
FROM DimJobRole

UNION ALL

SELECT 'DimEducationField', COUNT(*)
FROM DimEducationField

UNION ALL

SELECT 'DimProject', COUNT(*)
FROM DimProject

UNION ALL

SELECT 'DimDate', COUNT(*)
FROM DimDate

UNION ALL

SELECT 'DimEmployee', COUNT(*)
FROM DimEmployee

UNION ALL

SELECT 'FactEmployee', COUNT(*)
FROM FactEmployee

UNION ALL

SELECT 'FactAssignment', COUNT(*)
FROM FactAssignment

UNION ALL

SELECT 'FactReview', COUNT(*)
FROM FactReview;