import pandas as pd

file_path = "data/WA_Fn-UseC_-HR-Employee-Attrition.csv"

df = pd.read_csv(file_path)

print("=" * 60)
print("DATASET OVERVIEW")
print("=" * 60)

print("Number of rows:", len(df))
print("Number of columns:", len(df.columns))

print("\n" + "=" * 60)
print("COLUMN INFORMATION")
print("=" * 60)

print(df.dtypes)

print("\n" + "=" * 60)
print("UNIQUE VALUES IN IMPORTANT COLUMNS")
print("=" * 60)

columns_to_check = [
    "Department",
    "EducationField",
    "Gender",
    "JobRole",
    "MaritalStatus",
    "BusinessTravel",
    "OverTime",
    "Attrition"
]

for column in columns_to_check:
    print(f"\n{column}:")
    print(df[column].value_counts())

print("\n" + "=" * 60)
print("NUMERIC SUMMARY")
print("=" * 60)

print(df.describe())

print("\n" + "=" * 60)
print("MISSING VALUES")
print("=" * 60)

print(df.isnull().sum())