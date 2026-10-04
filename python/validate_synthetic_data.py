import pandas as pd

employee_file = "data/employees_100k.csv"
history_file = "data/employee_scd_history.csv"

employees = pd.read_csv(employee_file)
history = pd.read_csv(history_file)

print("=" * 60)
print("EMPLOYEE DATASET")
print("=" * 60)

print("Rows:", len(employees))
print("Columns:", len(employees.columns))

print("\nDuplicate Employee Numbers:")
print(employees["EmployeeNumber"].duplicated().sum())

print("\nMissing Values:")
print(employees.isnull().sum().sum())

print("\nFirst 5 rows:")
print(employees.head())

print("\n" + "=" * 60)
print("SCD TYPE 2 HISTORY")
print("=" * 60)

print("Rows:", len(history))
print("Columns:", len(history.columns))

print("\nCurrent records:")
print((history["is_current"] == 1).sum())

print("\nHistorical records:")
print((history["is_current"] == 0).sum())

print("\nEmployee IDs with history:")
print(history["EmployeeNumber"].nunique())

print("\nMissing Values:")
print(history.isnull().sum().sum())