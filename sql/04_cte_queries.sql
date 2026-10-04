USE enterprise_employee_analytics_olap;


WITH department_attrition AS (
    SELECT
        dd.department_name,
        COUNT(*) AS total_employees,
        SUM(
            CASE
                WHEN fe.attrition = 'Yes' THEN 1
                ELSE 0
            END
        ) AS attrition_count
    FROM FactEmployee fe
    JOIN DimEmployee de
        ON fe.employee_key = de.employee_key
    JOIN DimDepartment dd
        ON fe.department_key = dd.department_key
    WHERE de.is_current = 1
    GROUP BY dd.department_name
)
SELECT
    department_name,
    total_employees,
    attrition_count,
    ROUND(
        100.0 * attrition_count / total_employees,
        2
    ) AS attrition_rate
FROM department_attrition
ORDER BY attrition_rate DESC;


WITH employee_income AS (
    SELECT
        de.employee_number,
        CONCAT(de.first_name, ' ', de.last_name) AS employee_name,
        fe.monthly_income
    FROM FactEmployee fe
    JOIN DimEmployee de
        ON fe.employee_key = de.employee_key
    WHERE de.is_current = 1
)
SELECT
    employee_number,
    employee_name,
    monthly_income
FROM employee_income
WHERE monthly_income > (
    SELECT AVG(monthly_income)
    FROM employee_income
)
ORDER BY monthly_income DESC;


WITH department_salary AS (
    SELECT
        dd.department_name,
        AVG(fe.monthly_income) AS average_department_income
    FROM FactEmployee fe
    JOIN DimEmployee de
        ON fe.employee_key = de.employee_key
    JOIN DimDepartment dd
        ON fe.department_key = dd.department_key
    WHERE de.is_current = 1
    GROUP BY dd.department_name
),
overall_salary AS (
    SELECT
        AVG(monthly_income) AS overall_average_income
    FROM FactEmployee
)
SELECT
    department_name,
    ROUND(average_department_income, 2) AS average_department_income,
    ROUND(overall_average_income, 2) AS overall_average_income
FROM department_salary
CROSS JOIN overall_salary
WHERE average_department_income > overall_average_income
ORDER BY average_department_income DESC;


WITH ranked_reviews AS (
    SELECT
        fr.review_id,
        fr.employee_key,
        fr.review_period,
        fr.rating,
        fr.comments,
        ROW_NUMBER() OVER (
            PARTITION BY fr.employee_key
            ORDER BY fr.date_key DESC
        ) AS review_rank
    FROM FactReview fr
)
SELECT
    de.employee_number,
    CONCAT(de.first_name, ' ', de.last_name) AS employee_name,
    rr.review_period,
    rr.rating,
    rr.comments
FROM ranked_reviews rr
JOIN DimEmployee de
    ON rr.employee_key = de.employee_key
WHERE rr.review_rank = 1
  AND de.is_current = 1;