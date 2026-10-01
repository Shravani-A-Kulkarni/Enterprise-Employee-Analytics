CREATE DATABASE enterprise_employee_analytics;

USE enterprise_employee_analytics;
CREATE TABLE Department (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE
);
CREATE TABLE Employee (
    employee_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_number INT NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    age INT,
    gender VARCHAR(20),
    marital_status VARCHAR(30),
    department_id INT,
    job_role VARCHAR(100),
    job_level INT,
    education INT,
    education_field VARCHAR(100),
    business_travel VARCHAR(50),
    distance_from_home INT,
    daily_rate INT,
    hourly_rate INT,
    monthly_income INT,
    monthly_rate INT,
    overtime VARCHAR(10),
    job_satisfaction INT,
    environment_satisfaction INT,
    job_involvement INT,
    performance_rating INT,
    relationship_satisfaction INT,
    work_life_balance INT,
    percent_salary_hike INT,
    stock_option_level INT,
    total_working_years INT,
    years_at_company INT,
    years_in_current_role INT,
    years_since_last_promotion INT,
    years_with_current_manager INT,
    num_companies_worked INT,
    training_times_last_year INT,
    attrition VARCHAR(10),
    FOREIGN KEY (department_id) REFERENCES Department(department_id)
);
CREATE TABLE JobRole (
    job_role_id INT AUTO_INCREMENT PRIMARY KEY,
    job_role_name VARCHAR(100) NOT NULL UNIQUE
);
CREATE TABLE EducationField (
    education_field_id INT AUTO_INCREMENT PRIMARY KEY,
    education_field_name VARCHAR(100) NOT NULL UNIQUE
);
USE enterprise_employee_analytics;

SHOW TABLES;

DESCRIBE Department;
DESCRIBE Employee;
DESCRIBE JobRole;
DESCRIBE EducationField;

DROP TABLE Employee;

CREATE TABLE Employee (
    employee_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_number INT NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    age INT,
    gender VARCHAR(20),
    marital_status VARCHAR(30),

    department_id INT,
    job_role_id INT,
    job_level INT,
    education INT,
    education_field_id INT,

    business_travel VARCHAR(50),
    distance_from_home INT,
    daily_rate INT,
    hourly_rate INT,
    monthly_income INT,
    monthly_rate INT,
    overtime VARCHAR(10),

    job_satisfaction INT,
    environment_satisfaction INT,
    job_involvement INT,
    performance_rating INT,
    relationship_satisfaction INT,
    work_life_balance INT,
    percent_salary_hike INT,
    stock_option_level INT,

    total_working_years INT,
    years_at_company INT,
    years_in_current_role INT,
    years_since_last_promotion INT,
    years_with_current_manager INT,
    num_companies_worked INT,
    training_times_last_year INT,

    attrition VARCHAR(10),

    FOREIGN KEY (department_id)
        REFERENCES Department(department_id),

    FOREIGN KEY (job_role_id)
        REFERENCES JobRole(job_role_id),

    FOREIGN KEY (education_field_id)
        REFERENCES EducationField(education_field_id)
);

SHOW TABLES;
DESCRIBE Employee;

USE enterprise_employee_analytics;

INSERT INTO Department (department_name)
VALUES
('Research & Development'),
('Sales'),
('Human Resources');

INSERT INTO JobRole (job_role_name)
VALUES
('Sales Executive'),
('Research Scientist'),
('Laboratory Technician'),
('Manufacturing Director'),
('Healthcare Representative'),
('Manager'),
('Sales Representative'),
('Research Director'),
('Human Resources');

INSERT INTO EducationField (education_field_name)
VALUES
('Life Sciences'),
('Medical'),
('Marketing'),
('Technical Degree'),
('Other'),
('Human Resources');

SELECT * FROM Department;
SELECT * FROM JobRole;
SELECT * FROM EducationField;

USE enterprise_employee_analytics;

CREATE TABLE employee_staging (
    Age INT,
    Attrition VARCHAR(10),
    BusinessTravel VARCHAR(50),
    DailyRate INT,
    Department VARCHAR(100),
    DistanceFromHome INT,
    Education INT,
    EducationField VARCHAR(100),
    EmployeeCount INT,
    EmployeeNumber INT,
    EnvironmentSatisfaction INT,
    Gender VARCHAR(20),
    HourlyRate INT,
    JobInvolvement INT,
    JobLevel INT,
    JobRole VARCHAR(100),
    JobSatisfaction INT,
    MaritalStatus VARCHAR(30),
    MonthlyIncome INT,
    MonthlyRate INT,
    NumCompaniesWorked INT,
    Over18 VARCHAR(10),
    OverTime VARCHAR(10),
    PercentSalaryHike INT,
    PerformanceRating INT,
    RelationshipSatisfaction INT,
    StandardHours INT,
    StockOptionLevel INT,
    TotalWorkingYears INT,
    TrainingTimesLastYear INT,
    WorkLifeBalance INT,
    YearsAtCompany INT,
    YearsInCurrentRole INT,
    YearsSinceLastPromotion INT,
    YearsWithCurrManager INT,
    FirstName VARCHAR(100),
    LastName VARCHAR(100),
    Email VARCHAR(150)
);

SHOW TABLES;
DESCRIBE employee_staging;

USE enterprise_employee_analytics;

SHOW VARIABLES LIKE 'local_infile';
SET GLOBAL local_infile = 1;
SHOW VARIABLES LIKE 'local_infile';

LOAD DATA LOCAL INFILE 'C:/Users/subha/Downloads/Enterprise-Employee-Analytics/data/employees_100k.csv'
INTO TABLE employee_staging
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

USE enterprise_employee_analytics;

SELECT COUNT(*) AS total_records
FROM employee_staging;

SELECT *
FROM employee_staging
LIMIT 10;

SELECT COUNT(*) AS records_with_nulls
FROM employee_staging;

DESCRIBE employee_staging;

SELECT
    COUNT(*) AS total_records,
    COUNT(EmployeeNumber) AS employee_number_present,
    COUNT(FirstName) AS first_name_present,
    COUNT(LastName) AS last_name_present,
    COUNT(Age) AS age_present,
    COUNT(JobRole) AS job_role_present,
    COUNT(Department) AS department_present
FROM employee_staging;

DESCRIBE Employee;

SELECT DISTINCT s.Department
FROM employee_staging s
LEFT JOIN Department d
    ON s.Department = d.department_name
WHERE d.department_id IS NULL;

SELECT DISTINCT s.JobRole
FROM employee_staging s
LEFT JOIN JobRole j
    ON s.JobRole = j.job_role_name
WHERE j.job_role_id IS NULL;

SELECT DISTINCT s.EducationField
FROM employee_staging s
LEFT JOIN EducationField e
    ON s.EducationField = e.education_field_name
WHERE e.education_field_id IS NULL;

SELECT COUNT(*) AS employee_records
FROM Employee;

INSERT INTO Employee (
    employee_number,
    first_name,
    last_name,
    age,
    gender,
    marital_status,
    department_id,
    job_role_id,
    job_level,
    education,
    education_field_id,
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
    attrition
)
SELECT
    s.EmployeeNumber,
    s.FirstName,
    s.LastName,
    s.Age,
    s.Gender,
    s.MaritalStatus,
    d.department_id,
    j.job_role_id,
    s.JobLevel,
    s.Education,
    e.education_field_id,
    s.BusinessTravel,
    s.DistanceFromHome,
    s.DailyRate,
    s.HourlyRate,
    s.MonthlyIncome,
    s.MonthlyRate,
    s.Over18,
    s.JobSatisfaction,
    s.EnvironmentSatisfaction,
    s.JobInvolvement,
    s.PerformanceRating,
    s.RelationshipSatisfaction,
    s.WorkLifeBalance,
    s.PercentSalaryHike,
    s.StockOptionLevel,
    s.TotalWorkingYears,
    s.YearsAtCompany,
    s.YearsInCurrentRole,
    s.YearsSinceLastPromotion,
    s.YearsWithCurrManager,
    s.NumCompaniesWorked,
    s.TrainingTimesLastYear,
    s.Attrition
FROM employee_staging s
LEFT JOIN Department d
    ON s.Department = d.department_name
LEFT JOIN JobRole j
    ON s.JobRole = j.job_role_name
LEFT JOIN EducationField e
    ON s.EducationField = e.education_field_name;
    
SELECT COUNT(*) AS total_employees
FROM Employee;

SELECT * 
FROM Employee
LIMIT 10;

SELECT COUNT(*) AS invalid_departments
FROM Employee e
LEFT JOIN Department d
    ON e.department_id = d.department_id
WHERE d.department_id IS NULL;

SELECT COUNT(*) AS invalid_job_roles
FROM Employee e
LEFT JOIN JobRole j
    ON e.job_role_id = j.job_role_id
WHERE j.job_role_id IS NULL;

SELECT COUNT(*) AS invalid_education_fields
FROM Employee e
LEFT JOIN EducationField ef
    ON e.education_field_id = ef.education_field_id
WHERE ef.education_field_id IS NULL;

CREATE TABLE employee_scd_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_number INT NOT NULL,
    department_id INT,
    job_role_id INT,
    education_field_id INT,
    monthly_income INT,
    job_level INT,
    effective_start_date DATE,
    effective_end_date DATE,
    is_current BOOLEAN
);

SHOW TABLES;

DESCRIBE employee_scd_history;

LOAD DATA LOCAL INFILE 'C:/Users/subha/Downloads/Enterprise-Employee-Analytics/data/employee_scd_history.csv'
INTO TABLE employee_scd_history
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
    @Age,
    @Attrition,
    @BusinessTravel,
    @DailyRate,
    @Department,
    @DistanceFromHome,
    @Education,
    @EducationField,
    @EmployeeCount,
    employee_number,
    @EnvironmentSatisfaction,
    @Gender,
    @HourlyRate,
    @JobInvolvement,
    job_level,
    @JobRole,
    @JobSatisfaction,
    @MaritalStatus,
    monthly_income,
    @MonthlyRate,
    @NumCompaniesWorked,
    @Over18,
    @OverTime,
    @PercentSalaryHike,
    @PerformanceRating,
    @RelationshipSatisfaction,
    @StandardHours,
    @StockOptionLevel,
    @TotalWorkingYears,
    @TrainingTimesLastYear,
    @WorkLifeBalance,
    @YearsAtCompany,
    @YearsInCurrentRole,
    @YearsSinceLastPromotion,
    @YearsWithCurrManager,
    @FirstName,
    @LastName,
    @Email,
    @start_date,
    @end_date,
    is_current
)
SET
    department_id = (
        SELECT department_id
        FROM Department
        WHERE department_name = @Department
    ),
    job_role_id = (
        SELECT job_role_id
        FROM JobRole
        WHERE job_role_name = @JobRole
    ),
    education_field_id = (
        SELECT education_field_id
        FROM EducationField
        WHERE education_field_name = @EducationField
    ),
    effective_start_date = @start_date,
    effective_end_date = NULLIF(@end_date, '');
    
SELECT COUNT(*) AS total_history_records
FROM employee_scd_history;

SELECT *
FROM employee_scd_history
LIMIT 10;

SELECT 
    is_current,
    COUNT(*) AS record_count
FROM employee_scd_history
GROUP BY is_current;

SELECT 
    employee_number,
    COUNT(*) AS current_records
FROM employee_scd_history
WHERE is_current = 1
GROUP BY employee_number
HAVING COUNT(*) > 1;

SELECT COUNT(*) AS mismatched_current_records
FROM employee_scd_history h
JOIN Employee e
    ON h.employee_number = e.employee_number
WHERE h.is_current = 1
  AND (
      h.department_id <> e.department_id
      OR h.job_role_id <> e.job_role_id
      OR h.education_field_id <> e.education_field_id
      OR h.monthly_income <> e.monthly_income
      OR h.job_level <> e.job_level
  );
  
  SELECT 
    employee_number,
    COUNT(*) AS current_record_count
FROM employee_scd_history
WHERE is_current = 1
GROUP BY employee_number
HAVING COUNT(*) > 1;

SELECT 
    COUNT(DISTINCT employee_number) AS employees_with_current_record
FROM employee_scd_history
WHERE is_current = 1;

SELECT 
    COUNT(*) AS employees_without_current_record
FROM (
    SELECT employee_number
    FROM employee_scd_history
    GROUP BY employee_number
    HAVING SUM(is_current = 1) = 0
) AS x;