-- =====================================================================
-- 07_seed_demo_data.sql   (Member 3)  -- OLTP database only
-- Run ONCE on enterprise_employee_analytics, then re-run Member 2's
--   python python/etl_pipeline.py
-- so the warehouse picks up the new rows.
--
-- Why: the OLTP currently has only 6 projects, 10 assignments, 10 reviews.
-- The dashboards (year-over-year, top employees, bottlenecks) need real volume.
-- =====================================================================
USE enterprise_employee_analytics;

-- 0. Fix for the overtime bug: the original INSERT copied Over18 ('Y') into overtime.
--    employee_staging still holds the correct OverTime column.
UPDATE Employee e
JOIN employee_staging s ON s.EmployeeNumber = e.employee_number
SET e.overtime = s.OverTime;
-- (if employee_staging is empty/missing on your machine, skip this block)

-- 1. More projects (24 new -> 30 total, spread across the 3 departments)
INSERT INTO Project (project_name, department_id, start_date, end_date, status) VALUES
('Atlas CRM Rollout',            2, '2023-02-01', '2024-03-31', 'Completed'),
('Lab Automation Phase 1',       1, '2023-04-10', '2024-06-30', 'Completed'),
('Payroll Migration',            3, '2023-05-15', '2024-02-28', 'Completed'),
('Regional Sales Expansion',     2, '2023-07-01', NULL,         'Active'),
('Genomics Data Pipeline',       1, '2023-08-01', NULL,         'Active'),
('Talent Pipeline Portal',       3, '2023-09-12', NULL,         'Delayed'),
('Customer Churn Model',         2, '2023-10-01', '2025-01-31', 'Completed'),
('Quality Assurance Overhaul',   1, '2024-01-08', NULL,         'Active'),
('Onboarding Experience',        3, '2024-02-01', '2024-11-30', 'Completed'),
('Partner Portal',               2, '2024-03-18', NULL,         'Delayed'),
('Clinical Trial Tracker',       1, '2024-04-22', NULL,         'Active'),
('Diversity Analytics',          3, '2024-05-06', NULL,         'Active'),
('Pricing Engine v2',            2, '2024-06-03', NULL,         'On Hold'),
('Cold-Chain Monitoring',        1, '2024-07-15', '2025-08-15', 'Completed'),
('Learning Academy',             3, '2024-08-19', NULL,         'Active'),
('Mobile Sales App',             2, '2024-09-09', NULL,         'Active'),
('Predictive Maintenance',       1, '2024-10-14', NULL,         'Delayed'),
('Benefits Self-Service',        3, '2024-11-04', NULL,         'Active'),
('Lead Scoring Automation',      2, '2025-01-13', NULL,         'Active'),
('Materials Traceability',       1, '2025-02-17', NULL,         'Active'),
('Performance Review Redesign',  3, '2025-03-10', NULL,         'On Hold'),
('Key Account Program',          2, '2025-04-07', NULL,         'Active'),
('Digital Lab Notebook',         1, '2025-05-12', NULL,         'Active'),
('Succession Planning',          3, '2025-06-02', NULL,         'Active');

-- 2. Assignments: ~20% of employees on one project (skewed towards the first projects,
--    which creates natural "bottleneck" projects), ~7% on a second project
--    (so some people end up above 100% total allocation).
INSERT INTO Assignment (employee_id, project_id, assigned_date, role, allocation_percentage)
SELECT e.employee_id,
       p.project_id,
       GREATEST(p.start_date, '2023-01-01') + INTERVAL MOD(e.employee_id, 60) DAY,
       jr.job_role_name,
       ELT(1 + MOD(e.employee_id * 7, 6), 20, 40, 50, 60, 80, 100)
FROM Employee e
JOIN JobRole jr ON jr.job_role_id = e.job_role_id
JOIN (SELECT project_id, start_date,
             ROW_NUMBER() OVER (ORDER BY project_id) AS rn,
             COUNT(*) OVER () AS cnt
      FROM Project) p
  ON p.rn = LEAST(p.cnt, 1 + FLOOR(p.cnt * POW(MOD(e.employee_id * 2654435761, 1000) / 1000, 2)))
WHERE MOD(e.employee_id, 5) = 0
  AND NOT EXISTS (SELECT 1 FROM Assignment a WHERE a.employee_id = e.employee_id);

INSERT INTO Assignment (employee_id, project_id, assigned_date, role, allocation_percentage)
SELECT e.employee_id,
       p.project_id,
       GREATEST(p.start_date, '2023-06-01') + INTERVAL MOD(e.employee_id, 90) DAY,
       jr.job_role_name,
       ELT(1 + MOD(e.employee_id * 3, 4), 30, 40, 50, 60)
FROM Employee e
JOIN JobRole jr ON jr.job_role_id = e.job_role_id
JOIN (SELECT project_id, start_date,
             ROW_NUMBER() OVER (ORDER BY project_id) AS rn,
             COUNT(*) OVER () AS cnt
      FROM Project) p
  ON p.rn = 1 + MOD(e.employee_id + 11, p.cnt)
WHERE MOD(e.employee_id, 15) = 0
  AND NOT EXISTS (
        SELECT 1 FROM Assignment a
        WHERE a.employee_id = e.employee_id AND a.project_id = p.project_id);

-- 3. Annual reviews for 2023, 2024, 2025 (about 35% of employees each year).
--    Rating is based on the employee's IBM PerformanceRating +/- 1, with a slight upward trend.
INSERT INTO Reviews (employee_id, review_date, review_period, rating, comments)
SELECT employee_id,
       review_date,
       review_period,
       rating,
       ELT(rating, 'Needs significant improvement', 'Below expectations',
                   'Meets expectations', 'Exceeds expectations', 'Outstanding performance')
FROM (
    SELECT e.employee_id,
           STR_TO_DATE(CONCAT(y.yr, '-12-15'), '%Y-%m-%d') AS review_date,
           CONCAT(y.yr, ' Annual') AS review_period,
           LEAST(5, GREATEST(1,
               COALESCE(e.performance_rating, 3)
               + FLOOR(RAND() * 3) - 1
               + IF(RAND() < (y.yr - 2022) * 0.06, 1, 0))) AS rating
    FROM Employee e
    CROSS JOIN (SELECT 2023 AS yr UNION ALL SELECT 2024 UNION ALL SELECT 2025) y
    WHERE RAND() < 0.35
) r;

SELECT 'projects' AS what, COUNT(*) AS total FROM Project
UNION ALL SELECT 'assignments', COUNT(*) FROM Assignment
UNION ALL SELECT 'reviews',     COUNT(*) FROM Reviews;
