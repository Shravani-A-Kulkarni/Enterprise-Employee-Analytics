USE enterprise_employee_analytics_olap;


SELECT
    de.employee_number,
    CONCAT(de.first_name, ' ', de.last_name) AS employee_name,
    dd.department_name,
    fe.monthly_income,
    RANK() OVER (
        PARTITION BY dd.department_name
        ORDER BY fe.monthly_income DESC
    ) AS salary_rank
FROM FactEmployee fe
JOIN DimEmployee de
    ON fe.employee_key = de.employee_key
JOIN DimDepartment dd
    ON fe.department_key = dd.department_key
WHERE de.is_current = 1
ORDER BY
    dd.department_name,
    salary_rank;


SELECT
    de.employee_number,
    CONCAT(de.first_name, ' ', de.last_name) AS employee_name,
    dd.department_name,
    fe.monthly_income,
    ROW_NUMBER() OVER (
        PARTITION BY dd.department_name
        ORDER BY fe.monthly_income DESC
    ) AS employee_number_within_department
FROM FactEmployee fe
JOIN DimEmployee de
    ON fe.employee_key = de.employee_key
JOIN DimDepartment dd
    ON fe.department_key = dd.department_key
WHERE de.is_current = 1
ORDER BY
    dd.department_name,
    employee_number_within_department;


SELECT
    de.employee_number,
    CONCAT(de.first_name, ' ', de.last_name) AS employee_name,
    dd.department_name,
    fe.monthly_income,
    ROUND(
        AVG(fe.monthly_income) OVER (
            PARTITION BY dd.department_name
        ),
        2
    ) AS department_average_income
FROM FactEmployee fe
JOIN DimEmployee de
    ON fe.employee_key = de.employee_key
JOIN DimDepartment dd
    ON fe.department_key = dd.department_key
WHERE de.is_current = 1
ORDER BY
    dd.department_name,
    fe.monthly_income DESC;


SELECT
    de.employee_number,
    CONCAT(de.first_name, ' ', de.last_name) AS employee_name,
    dd.department_name,
    fe.monthly_income,
    ROUND(
        fe.monthly_income
        - AVG(fe.monthly_income) OVER (
            PARTITION BY dd.department_name
        ),
        2
    ) AS difference_from_department_average
FROM FactEmployee fe
JOIN DimEmployee de
    ON fe.employee_key = de.employee_key
JOIN DimDepartment dd
    ON fe.department_key = dd.department_key
WHERE de.is_current = 1
ORDER BY
    dd.department_name,
    difference_from_department_average DESC;


SELECT
    de.employee_number,
    CONCAT(de.first_name, ' ', de.last_name) AS employee_name,
    fe.monthly_income,
    ROUND(
        AVG(fe.monthly_income) OVER (
            ORDER BY fe.monthly_income
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ),
        2
    ) AS running_average_income
FROM FactEmployee fe
JOIN DimEmployee de
    ON fe.employee_key = de.employee_key
WHERE de.is_current = 1
ORDER BY fe.monthly_income;