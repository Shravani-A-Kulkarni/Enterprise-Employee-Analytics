USE enterprise_employee_analytics_olap;

DROP PROCEDURE IF EXISTS sp_attrition_by_department;

DELIMITER $$

CREATE PROCEDURE sp_attrition_by_department()
BEGIN
    SELECT
        dd.department_name,
        COUNT(*) AS total_employees,
        SUM(CASE
            WHEN fe.attrition = 'Yes' THEN 1
            ELSE 0
        END) AS attrition_count,
        ROUND(
            100.0 * SUM(CASE
                WHEN fe.attrition = 'Yes' THEN 1
                ELSE 0
            END) / COUNT(*),
            2
        ) AS attrition_rate
    FROM FactEmployee fe
    JOIN DimEmployee de
        ON fe.employee_key = de.employee_key
    JOIN DimDepartment dd
        ON fe.department_key = dd.department_key
    WHERE de.is_current = 1
    GROUP BY dd.department_name
    ORDER BY attrition_rate DESC;
END$$

DELIMITER ;


DROP PROCEDURE IF EXISTS sp_salary_by_job_role;

DELIMITER $$

CREATE PROCEDURE sp_salary_by_job_role()
BEGIN
    SELECT
        dj.job_role_name,
        COUNT(*) AS employee_count,
        ROUND(AVG(fe.monthly_income), 2) AS average_monthly_income,
        MIN(fe.monthly_income) AS minimum_monthly_income,
        MAX(fe.monthly_income) AS maximum_monthly_income
    FROM FactEmployee fe
    JOIN DimEmployee de
        ON fe.employee_key = de.employee_key
    JOIN DimJobRole dj
        ON fe.job_role_key = dj.job_role_key
    WHERE de.is_current = 1
    GROUP BY dj.job_role_name
    ORDER BY average_monthly_income DESC;
END$$

DELIMITER ;


DROP PROCEDURE IF EXISTS sp_performance_summary;

DELIMITER $$

CREATE PROCEDURE sp_performance_summary()
BEGIN
    SELECT
        dd.department_name,
        fe.performance_rating,
        COUNT(*) AS employee_count,
        ROUND(AVG(fe.monthly_income), 2) AS average_monthly_income,
        ROUND(AVG(fe.job_satisfaction), 2) AS average_job_satisfaction
    FROM FactEmployee fe
    JOIN DimEmployee de
        ON fe.employee_key = de.employee_key
    JOIN DimDepartment dd
        ON fe.department_key = dd.department_key
    WHERE de.is_current = 1
    GROUP BY
        dd.department_name,
        fe.performance_rating
    ORDER BY
        dd.department_name,
        fe.performance_rating;
END$$

DELIMITER ;
