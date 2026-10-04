# Member 3 guide - OOP backend, Streamlit app, dashboards

## Architecture
```
Streamlit pages  ->  Managers (DAL)  ->  DatabaseConnection (Singleton)  ->  MySQL
 app/pages/*.py      EmployeeManager        one shared connection per          OLTP: enterprise_employee_analytics
                     ProjectManager         manager class, thread-safe,        OLAP: enterprise_employee_analytics_olap
                     ReviewManager          transactions via transaction()
                     AnalyticsManager
Entities (Employee, Project, Review): validated attributes, behaviour, to_db_row()
```
**Write path (OLTP -> warehouse, one transaction):** form -> entity validation -> manager opens a
transaction -> INSERT/UPDATE in OLTP -> `CALL <olap>.sp_*` -> commit (or rollback of everything).
**SCD Type 2:** `EmployeeManager.update_employee()` writes `employee_scd_history` (OLTP) and calls
`sp_scd2_update_employee`, which closes the current `DimEmployee` row (end date, `is_current=0`) and
inserts a new row with a NEW surrogate key. Reviews attach to the version valid on the review date.
**Read path:** dashboards read only the star schema through `AnalyticsManager` (CTEs, `LAG`,
`DENSE_RANK`, `RANK`).

## Run order (real databases)
1. Member 1: OLTP schema + 100k data loaded.  Member 2: `01_olap_ddl.sql`, `02_olap_dml.sql`.
2. Run `sql/06_app_support.sql` (Workbench -> open file -> run all). Procedures + index + DimDate to 2027.
3. Run `sql/07_seed_demo_data.sql` ONCE (OLTP). Fixes overtime, adds projects/assignments/reviews.
4. `python python/etl_pipeline.py` (Member 2's ETL) to push the seeded rows into the warehouse.
5. `cp .env.example .env`, fill in the password, `pip install -r requirements.txt`
6. `python tests/smoke_test.py`  -> must print ALL CHECKS PASSED
7. `streamlit run app/streamlit_app.py`

## Git
```
git checkout main && git pull
git checkout -b feature/streamlit-app
# copy these files in, then:
git add app tests docs sql/06_app_support.sql sql/07_seed_demo_data.sql requirements.txt .env.example .streamlit/secrets.toml.example
git commit -m "Add OOP backend, Streamlit app and analytics dashboard"
git push -u origin feature/streamlit-app      # then open a Pull Request into main
```
Add `.streamlit/secrets.toml` to `.gitignore`. Never commit `.env`.

## Deploy (Streamlit Community Cloud)
1. Host MySQL online (both schemas on the SAME server; Aiven / Railway / similar) and load the data.
   The host must accept outside connections (Streamlit Cloud has no fixed IP).
2. share.streamlit.io -> New app -> repo, branch `main`, main file `app/streamlit_app.py`.
3. Advanced settings -> Secrets: paste the values from `.streamlit/secrets.toml.example`.
   If the host needs SSL, add `MYSQL_SSL_CA` and commit the CA file path accordingly.

## What was tested
Real SQL scripts from Member 1 + 2 on MariaDB 10.11 (5,000-employee copy), also under MySQL 8's strict
`sql_mode`: 34 end-to-end checks (`tests/smoke_test.py`), all 5 pages load, onboard + SCD2 forms driven
through the UI. NOT tested: MySQL Workbench itself, the 100k-row volume, the hosted/cloud setup.
