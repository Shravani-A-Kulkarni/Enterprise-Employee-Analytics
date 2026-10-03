import os
from dotenv import load_dotenv
import mysql.connector
import pandas as pd
from datetime import date, timedelta

# Load variables from .env
load_dotenv()

# Read database configuration
HOST = os.getenv("MYSQL_HOST")
USER = os.getenv("MYSQL_USER")
PASSWORD = os.getenv("MYSQL_PASSWORD")
OLTP_DB = os.getenv("OLTP_DB")
OLAP_DB = os.getenv("OLAP_DB")


def read_employees():
    connection = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=OLTP_DB
    )

    query = """
    SELECT
        employee_id,
        employee_number,
        first_name,
        last_name,
        age,
        gender,
        marital_status,
        department_id,
        job_role_id,
        education_field_id,
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
        attrition
    FROM Employee;
"""

    df = pd.read_sql(query, connection)

    connection.close()

    return df

def clean_employee_data(df):
    """Clean and transform employee data before loading into the warehouse."""

    # Remove leading/trailing spaces from text columns
    text_columns = [
        "first_name",
        "last_name",
        "gender",
        "marital_status",
        "overtime",
        "attrition"
    ]

    for column in text_columns:
        df[column] = df[column].astype(str).str.strip()

    # Standardize categorical values
    df["overtime"] = df["overtime"].str.title()
    df["attrition"] = df["attrition"].str.title()
    df["gender"] = df["gender"].str.title()
    df["marital_status"] = df["marital_status"].str.title()

    # Ensure numeric columns contain numeric values
    numeric_columns = [
        "employee_id",
        "employee_number",
        "age",
        "department_id",
        "job_role_id",
        "education_field_id",
        "monthly_income",
        "job_level"
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    # Remove duplicate employee records
    before_duplicates = len(df)

    df = df.drop_duplicates(subset=["employee_number"])

    duplicates_removed = before_duplicates - len(df)

    # Remove records missing mandatory identifiers
    before_missing = len(df)

    df = df.dropna(
        subset=[
            "employee_number",
            "department_id",
            "job_role_id",
            "education_field_id"
        ]
    )

    missing_removed = before_missing - len(df)

    print("Data cleaning completed.")
    print(f"Duplicate records removed: {duplicates_removed}")
    print(f"Records with missing mandatory IDs removed: {missing_removed}")
    print(f"Clean employee records: {len(df)}")

    return df

def check_olap_tables():
    connection = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=OLAP_DB
    )

    cursor = connection.cursor()

    cursor.execute("SHOW TABLES;")

    tables = cursor.fetchall()

    cursor.close()
    connection.close()

    return tables

def load_dim_department():
    connection = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=OLTP_DB
    )

    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            department_id,
            department_name
        FROM Department;
    """)

    departments = cursor.fetchall()

    cursor.close()
    connection.close()

    olap_connection = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=OLAP_DB
    )

    olap_cursor = olap_connection.cursor()

    insert_query = """
    INSERT INTO DimDepartment (
        department_id,
        department_name
    )
    VALUES (%s, %s)
    ON DUPLICATE KEY UPDATE
        department_name = VALUES(department_name);
"""

    for department in departments:
        olap_cursor.execute(
            insert_query,
            (
                department["department_id"],
                department["department_name"]
            )
        )

    olap_connection.commit()

    olap_cursor.close()
    olap_connection.close()

    print(f"Loaded {len(departments)} departments into DimDepartment.")

def load_dim_job_role():
    connection = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=OLTP_DB
    )

    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            job_role_id,
            job_role_name
        FROM JobRole;
    """)

    job_roles = cursor.fetchall()

    cursor.close()
    connection.close()

    olap_connection = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=OLAP_DB
    )

    olap_cursor = olap_connection.cursor()

    insert_query = """
        INSERT INTO DimJobRole (
            job_role_id,
            job_role_name
        )
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE
            job_role_name = VALUES(job_role_name);
    """

    for job_role in job_roles:
        olap_cursor.execute(
            insert_query,
            (
                job_role["job_role_id"],
                job_role["job_role_name"]
            )
        )

    olap_connection.commit()

    olap_cursor.close()
    olap_connection.close()

    print(f"Loaded {len(job_roles)} job roles into DimJobRole.")

def load_dim_education_field():
    connection = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=OLTP_DB
    )

    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            education_field_id,
            education_field_name
        FROM EducationField;
    """)

    education_fields = cursor.fetchall()

    cursor.close()
    connection.close()

    olap_connection = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=OLAP_DB
    )

    olap_cursor = olap_connection.cursor()

    insert_query = """
        INSERT INTO DimEducationField (
            education_field_id,
            education_field_name
        )
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE
            education_field_name = VALUES(education_field_name);
    """

    for education_field in education_fields:
        olap_cursor.execute(
            insert_query,
            (
                education_field["education_field_id"],
                education_field["education_field_name"]
            )
        )

    olap_connection.commit()

    olap_cursor.close()
    olap_connection.close()

    print(
        f"Loaded {len(education_fields)} education fields "
        "into DimEducationField."
    )

def load_dim_project():
    connection = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=OLTP_DB
    )

    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            p.project_id,
            p.project_name,
            p.department_id,
            d.department_name,
            p.start_date,
            p.end_date,
            p.status
        FROM Project p
        LEFT JOIN Department d
            ON p.department_id = d.department_id;
    """)

    projects = cursor.fetchall()

    cursor.close()
    connection.close()

    olap_connection = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=OLAP_DB
    )

    olap_cursor = olap_connection.cursor()

    insert_query = """
        INSERT INTO DimProject (
            project_id,
            project_name,
            department_id,
            department_name,
            start_date,
            end_date,
            status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            project_name = VALUES(project_name),
            department_id = VALUES(department_id),
            department_name = VALUES(department_name),
            start_date = VALUES(start_date),
            end_date = VALUES(end_date),
            status = VALUES(status);
    """

    for project in projects:
        olap_cursor.execute(
            insert_query,
            (
                project["project_id"],
                project["project_name"],
                project["department_id"],
                project["department_name"],
                project["start_date"],
                project["end_date"],
                project["status"]
            )
        )

    olap_connection.commit()

    olap_cursor.close()
    olap_connection.close()

    print(f"Loaded {len(projects)} projects into DimProject.")

def load_dim_date():
    connection = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=OLAP_DB
    )

    cursor = connection.cursor()

    query = """
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
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            full_date = VALUES(full_date),
            year = VALUES(year),
            quarter = VALUES(quarter),
            month = VALUES(month),
            month_name = VALUES(month_name),
            day = VALUES(day),
            day_name = VALUES(day_name);
    """

    import datetime

    start_date = datetime.date(2023, 1, 1)
    end_date = datetime.date(2025, 12, 31)

    current_date = start_date
    dates_loaded = 0

    while current_date <= end_date:

        date_key = (
            current_date.year * 10000
            + current_date.month * 100
            + current_date.day
        )

        quarter = (current_date.month - 1) // 3 + 1

        cursor.execute(
            query,
            (
                date_key,
                current_date,
                current_date.year,
                quarter,
                current_date.month,
                current_date.strftime("%B"),
                current_date.day,
                current_date.strftime("%A")
            )
        )

        dates_loaded += 1
        current_date += datetime.timedelta(days=1)

    connection.commit()

    cursor.close()
    connection.close()

    print(f"Loaded {dates_loaded} dates into DimDate.")

def load_dim_employee_scd():
    # Connect to OLTP
    oltp_conn = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=OLTP_DB
    )

    # Current employee data
    employee_query = """
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
            d.department_name,
            e.job_role_id,
            j.job_role_name,
            e.education_field_id,
            ef.education_field_name
        FROM Employee e
        LEFT JOIN Department d
            ON e.department_id = d.department_id
        LEFT JOIN JobRole j
            ON e.job_role_id = j.job_role_id
        LEFT JOIN EducationField ef
            ON e.education_field_id = ef.education_field_id;
    """

    employees = pd.read_sql(employee_query, oltp_conn)

    # SCD history
    history_query = """
        SELECT
            employee_number,
            department_id,
            job_role_id,
            education_field_id,
            monthly_income,
            job_level,
            effective_start_date,
            effective_end_date,
            is_current
        FROM employee_scd_history
        ORDER BY employee_number, effective_start_date;
    """

    history = pd.read_sql(history_query, oltp_conn)

    oltp_conn.close()

    # Connect to OLAP
    olap_conn = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=OLAP_DB
    )

    cursor = olap_conn.cursor(dictionary=True)

    # Existing current records in warehouse
    cursor.execute("""
        SELECT *
        FROM DimEmployee
        WHERE is_current = 1
    """)

    current_records = cursor.fetchall()

    current_map = {
        row["employee_number"]: row
        for row in current_records
    }

    inserted = 0
    updated = 0
    unchanged = 0

    # Process each employee
    

    for _, employee in employees.iterrows():

        employee_number = int(employee["employee_number"])

        # Find SCD history for this employee
        employee_history = history[
            history["employee_number"] == employee_number
        ]

        # -----------------------------------------------------
        # Employee does not exist in DimEmployee
        # -----------------------------------------------------

        if employee_number not in current_map:

            insert_query = """
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
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s
                )
            """

            values = tuple(
                employee[col]
                for col in [
                    "employee_number",
                    "first_name",
                    "last_name",
                    "age",
                    "gender",
                    "marital_status",
                    "job_level",
                    "education",
                    "business_travel",
                    "distance_from_home",
                    "daily_rate",
                    "hourly_rate",
                    "monthly_income",
                    "monthly_rate",
                    "overtime",
                    "job_satisfaction",
                    "environment_satisfaction",
                    "job_involvement",
                    "performance_rating",
                    "relationship_satisfaction",
                    "work_life_balance",
                    "percent_salary_hike",
                    "stock_option_level",
                    "total_working_years",
                    "years_at_company",
                    "years_in_current_role",
                    "years_since_last_promotion",
                    "years_with_current_manager",
                    "num_companies_worked",
                    "training_times_last_year",
                    "attrition",
                    "department_id",
                    "department_name",
                    "job_role_id",
                    "job_role_name",
                    "education_field_id",
                    "education_field_name"
                ]
            )

            # Use SCD current start date if available
            if not employee_history.empty:
                current_history = employee_history[
                    employee_history["is_current"] == 1
                ]

                if not current_history.empty:
                    start_date = current_history.iloc[0]["effective_start_date"]
                else:
                    start_date = date.today()
            else:
                start_date = date.today()

            cursor.execute(
                insert_query,
                values + (start_date, None, 1)
            )

            inserted += 1
            continue

        # Employee already exists → check for SCD changes
        

        old_record = current_map[employee_number]

        tracked_columns = [
            "department_id",
            "job_role_id",
            "education_field_id",
            "monthly_income",
            "job_level"
        ]

        changed = any(
            old_record[column] != employee[column]
            for column in tracked_columns
        )

        if not changed:
            unchanged += 1
            continue

        
        # SCD Type 2 change detected
       

        change_date = date.today()

        # Close old version
        cursor.execute(
            """
            UPDATE DimEmployee
            SET
                effective_end_date = %s,
                is_current = 0
            WHERE employee_key = %s
              AND is_current = 1
            """,
            (
                change_date - timedelta(days=1),
                old_record["employee_key"]
            )
        )

        # Insert new current version
        insert_query = """
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
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s
            )
        """

        values = tuple(
            employee[col]
            for col in [
                "employee_number",
                "first_name",
                "last_name",
                "age",
                "gender",
                "marital_status",
                "job_level",
                "education",
                "business_travel",
                "distance_from_home",
                "daily_rate",
                "hourly_rate",
                "monthly_income",
                "monthly_rate",
                "overtime",
                "job_satisfaction",
                "environment_satisfaction",
                "job_involvement",
                "performance_rating",
                "relationship_satisfaction",
                "work_life_balance",
                "percent_salary_hike",
                "stock_option_level",
                "total_working_years",
                "years_at_company",
                "years_in_current_role",
                "years_since_last_promotion",
                "years_with_current_manager",
                "num_companies_worked",
                "training_times_last_year",
                "attrition",
                "department_id",
                "department_name",
                "job_role_id",
                "job_role_name",
                "education_field_id",
                "education_field_name"
            ]
        )

        cursor.execute(
            insert_query,
            values + (change_date, None, 1)
        )

        updated += 1

        # Update dictionary with new current record
        current_map[employee_number] = {
            "employee_key": cursor.lastrowid,
            **employee.to_dict()
        }

    olap_conn.commit()

    cursor.close()
    olap_conn.close()

    print("SCD Type 2 processing completed.")
    print(f"New employees inserted: {inserted}")
    print(f"SCD changes detected: {updated}")
    print(f"Unchanged employees: {unchanged}")

def load_fact_employee(df):

    olap_conn = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=OLAP_DB
    )

    cursor = olap_conn.cursor()

    # Clear existing fact data to make ETL rerunnable
    cursor.execute("DELETE FROM FactEmployee")

    # Use ETL execution date as the employee snapshot date
    load_date = date.today()
    date_key = int(load_date.strftime("%Y%m%d"))

    # Make sure the snapshot date exists in DimDate
    cursor.execute(
        "SELECT 1 FROM DimDate WHERE date_key = %s",
        (date_key,)
    )

    if cursor.fetchone() is None:
        cursor.execute("""
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
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """, (
            date_key,
            load_date,
            load_date.year,
            (load_date.month - 1) // 3 + 1,
            load_date.month,
            load_date.strftime("%B"),
            load_date.day,
            load_date.strftime("%A")
        ))

    # Get current employee surrogate keys
    cursor.execute("""
        SELECT employee_key, employee_number
        FROM DimEmployee
        WHERE is_current = 1
    """)

    employee_keys = {
        row[1]: row[0]
        for row in cursor.fetchall()
    }

    # Get department surrogate keys
    cursor.execute("""
        SELECT department_key, department_id
        FROM DimDepartment
    """)

    department_keys = {
        row[1]: row[0]
        for row in cursor.fetchall()
    }

    # Get job role surrogate keys
    cursor.execute("""
        SELECT job_role_key, job_role_id
        FROM DimJobRole
    """)

    job_role_keys = {
        row[1]: row[0]
        for row in cursor.fetchall()
    }

    # Get education field surrogate keys
    cursor.execute("""
        SELECT education_field_key, education_field_id
        FROM DimEducationField
    """)

    education_field_keys = {
        row[1]: row[0]
        for row in cursor.fetchall()
    }

    insert_query = """
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
    VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s
    )
    """

    values = []

    for _, row in df.iterrows():

        employee_key = employee_keys.get(int(row["employee_number"]))

        department_key = department_keys.get(
            int(row["department_id"])
        )

        job_role_key = job_role_keys.get(
            int(row["job_role_id"])
        )

        education_field_key = education_field_keys.get(
            int(row["education_field_id"])
        )

        if (
            employee_key is not None
            and department_key is not None
            and job_role_key is not None
            and education_field_key is not None
        ):
            values.append((
                employee_key,
                department_key,
                job_role_key,
                education_field_key,
                date_key,
                row["monthly_income"],
                row["daily_rate"],
                row["hourly_rate"],
                row["job_satisfaction"],
                row["environment_satisfaction"],
                row["job_involvement"],
                row["performance_rating"],
                row["relationship_satisfaction"],
                row["work_life_balance"],
                row["percent_salary_hike"],
                row["stock_option_level"],
                row["total_working_years"],
                row["years_at_company"],
                row["years_in_current_role"],
                row["years_since_last_promotion"],
                row["years_with_current_manager"],
                row["num_companies_worked"],
                row["training_times_last_year"],
                row["attrition"]
            ))

    cursor.executemany(insert_query, values)

    olap_conn.commit()

    print(f"Loaded {len(values)} records into FactEmployee.")
    print(f"FactEmployee snapshot date: {load_date}")

    cursor.close()
    olap_conn.close()

def load_fact_assignment():
    oltp_conn = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=OLTP_DB
    )

    query = """
        SELECT
            a.assignment_id,
            e.employee_number,
            a.project_id,
            a.assigned_date,
            a.role,
            a.allocation_percentage
        FROM Assignment a
        JOIN Employee e
            ON a.employee_id = e.employee_id;
    """

    df = pd.read_sql(query, oltp_conn)
    oltp_conn.close()

    olap_conn = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=OLAP_DB
    )

    cursor = olap_conn.cursor()

    # Clear existing fact data
    cursor.execute("DELETE FROM FactAssignment")

    cursor.execute("""
        SELECT employee_key, employee_number
        FROM DimEmployee
        WHERE is_current = 1
    """)

    employee_keys = {
        row[1]: row[0]
        for row in cursor.fetchall()
    }

    cursor.execute("""
        SELECT project_key, project_id
        FROM DimProject
    """)

    project_keys = {
        row[1]: row[0]
        for row in cursor.fetchall()
    }

    cursor.execute("""
        SELECT date_key, full_date
        FROM DimDate
    """)

    date_keys = {
        row[1]: row[0]
        for row in cursor.fetchall()
    }

    insert_query = """
        INSERT INTO FactAssignment (
            employee_key,
            project_key,
            date_key,
            assignment_id,
            role,
            allocation_percentage
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    values = []

    for _, row in df.iterrows():

        employee_key = employee_keys.get(int(row["employee_number"]))
        project_key = project_keys.get(int(row["project_id"]))
        date_key = date_keys.get(row["assigned_date"])

        if employee_key is not None and project_key is not None and date_key is not None:
            values.append((
                employee_key,
                project_key,
                date_key,
                row["assignment_id"],
                row["role"],
                row["allocation_percentage"]
            ))

    cursor.executemany(insert_query, values)

    olap_conn.commit()

    print(f"Loaded {len(values)} records into FactAssignment.")

    cursor.close()
    olap_conn.close()


def load_fact_review():
    oltp_conn = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=OLTP_DB
    )

    query = """
        SELECT
            r.review_id,
            e.employee_number,
            r.review_date,
            r.review_period,
            r.rating,
            r.comments
        FROM Reviews r
        JOIN Employee e
            ON r.employee_id = e.employee_id;
    """

    df = pd.read_sql(query, oltp_conn)
    oltp_conn.close()

    olap_conn = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=OLAP_DB
    )

    cursor = olap_conn.cursor()

    # Clear existing fact data
    cursor.execute("DELETE FROM FactReview")

    cursor.execute("""
        SELECT employee_key, employee_number
        FROM DimEmployee
        WHERE is_current = 1
    """)

    employee_keys = {
        row[1]: row[0]
        for row in cursor.fetchall()
    }

    cursor.execute("""
        SELECT date_key, full_date
        FROM DimDate
    """)

    date_keys = {
        row[1]: row[0]
        for row in cursor.fetchall()
    }

    insert_query = """
        INSERT INTO FactReview (
            employee_key,
            date_key,
            review_id,
            review_period,
            rating,
            comments
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    values = []

    for _, row in df.iterrows():

        employee_key = employee_keys.get(int(row["employee_number"]))
        date_key = date_keys.get(row["review_date"])

        if employee_key is not None and date_key is not None:
            values.append((
                employee_key,
                date_key,
                row["review_id"],
                row["review_period"],
                row["rating"],
                row["comments"]
            ))

    cursor.executemany(insert_query, values)

    olap_conn.commit()

    print(f"Loaded {len(values)} records into FactReview.")

    cursor.close()
    olap_conn.close()


if __name__ == "__main__":
    employees = read_employees()

    print("Total employees before cleaning:", len(employees))

    employees = clean_employee_data(employees)

    print("Total employees after cleaning:", len(employees))

    load_dim_department()
    load_dim_job_role()
    load_dim_education_field()
    load_dim_project()
    load_dim_date()
    load_dim_employee_scd()
    load_fact_employee(employees)
    load_fact_assignment()
    load_fact_review()
    print("ETL pipleline completed.")