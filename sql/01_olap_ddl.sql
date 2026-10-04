
-- Enterprise Employee Analytics
-- OLAP / Data Warehouse DDL

CREATE DATABASE IF NOT EXISTS enterprise_employee_analytics_olap;

USE enterprise_employee_analytics_olap;

-- Dimension: Department

CREATE TABLE IF NOT EXISTS DimDepartment (
    department_key INT AUTO_INCREMENT PRIMARY KEY,
    department_id INT,
    department_name VARCHAR(100) NOT NULL,

    CONSTRAINT uq_dimdepartment_id
        UNIQUE (department_id)
);

-- Dimension: Job Role

CREATE TABLE IF NOT EXISTS DimJobRole (
    job_role_key INT AUTO_INCREMENT PRIMARY KEY,
    job_role_id INT,
    job_role_name VARCHAR(100) NOT NULL,

    CONSTRAINT uq_dimjobrole_id
        UNIQUE (job_role_id)
);

-- Dimension: Education Field
CREATE TABLE IF NOT EXISTS DimEducationField (
    education_field_key INT AUTO_INCREMENT PRIMARY KEY,
    education_field_id INT,
    education_field_name VARCHAR(100) NOT NULL,

    CONSTRAINT uq_dimeducationfield_id
        UNIQUE (education_field_id)
);

-- Dimension: Project
CREATE TABLE IF NOT EXISTS DimProject (
    project_key INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT,
    project_name VARCHAR(100) NOT NULL,
    department_id INT,
    department_name VARCHAR(100),
    start_date DATE,
    end_date DATE,
    status VARCHAR(30),

    CONSTRAINT uq_dimproject_id
        UNIQUE (project_id)
);

-- Dimension: Date
CREATE TABLE IF NOT EXISTS DimDate (
    date_key INT PRIMARY KEY,
    full_date DATE NOT NULL,
    year INT,
    quarter INT,
    month INT,
    month_name VARCHAR(20),
    day INT,
    day_name VARCHAR(20)
);

-- Dimension: Employee
-- SCD Type 2

CREATE TABLE IF NOT EXISTS DimEmployee (
    employee_key INT AUTO_INCREMENT PRIMARY KEY,

    employee_number INT NOT NULL,

    first_name VARCHAR(100),
    last_name VARCHAR(100),
    age INT,
    gender VARCHAR(20),
    marital_status VARCHAR(30),

    job_level INT,
    education INT,

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

    department_id INT,
    department_name VARCHAR(100),

    job_role_id INT,
    job_role_name VARCHAR(100),

    education_field_id INT,
    education_field_name VARCHAR(100),

    effective_start_date DATE,
    effective_end_date DATE,

    is_current BOOLEAN
);


-- Fact: Employee Performance

CREATE TABLE IF NOT EXISTS FactEmployee (
    employee_fact_key INT AUTO_INCREMENT PRIMARY KEY,

    employee_key INT NOT NULL,
    department_key INT,
    job_role_key INT,
    education_field_key INT,
    date_key INT,

    monthly_income INT,
    daily_rate INT,
    hourly_rate INT,

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

    FOREIGN KEY (employee_key)
        REFERENCES DimEmployee(employee_key),

    FOREIGN KEY (department_key)
        REFERENCES DimDepartment(department_key),

    FOREIGN KEY (job_role_key)
        REFERENCES DimJobRole(job_role_key),

    FOREIGN KEY (education_field_key)
        REFERENCES DimEducationField(education_field_key),

    FOREIGN KEY (date_key)
        REFERENCES DimDate(date_key)
);



-- Fact: Project Assignments

CREATE TABLE IF NOT EXISTS FactAssignment (
    assignment_fact_key INT AUTO_INCREMENT PRIMARY KEY,

    employee_key INT NOT NULL,
    project_key INT NOT NULL,
    date_key INT,

    assignment_id INT,
    role VARCHAR(100),
    allocation_percentage INT,

    FOREIGN KEY (employee_key)
        REFERENCES DimEmployee(employee_key),

    FOREIGN KEY (project_key)
        REFERENCES DimProject(project_key),

    FOREIGN KEY (date_key)
        REFERENCES DimDate(date_key)
);



-- Fact: Performance Reviews

CREATE TABLE IF NOT EXISTS FactReview (
    review_fact_key INT AUTO_INCREMENT PRIMARY KEY,

    employee_key INT NOT NULL,
    date_key INT,

    review_id INT,
    review_period VARCHAR(30),
    rating INT,
    comments VARCHAR(500),

    FOREIGN KEY (employee_key)
        REFERENCES DimEmployee(employee_key),

    FOREIGN KEY (date_key)
        REFERENCES DimDate(date_key)
);