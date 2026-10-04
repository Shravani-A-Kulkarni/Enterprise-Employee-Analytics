import pandas as pd
import random
from faker import Faker


class EmployeeDataSynthesizer:

    def __init__(self, input_file, output_file, history_file, target_rows=100000):
        self.input_file = input_file
        self.output_file = output_file
        self.history_file = history_file
        self.target_rows = target_rows

        self.fake = Faker()
        self.base_data = None
        self.employee_data = None
        self.history_data = None


    def load_data(self):
        print("Loading original dataset...")

        self.base_data = pd.read_csv(self.input_file)

        print(f"Original rows: {len(self.base_data)}")
        print(f"Original columns: {len(self.base_data.columns)}")

   
    def generate_employees(self):

        print("\nGenerating synthetic employees...")

        records = []

        for employee_id in range(1, self.target_rows + 1):

            # Select an existing employee as a realistic template
            template = self.base_data.sample(
                n=1,
                replace=True
            ).iloc[0].copy()

            # Generate unique employee number
            template["EmployeeNumber"] = employee_id

            # Generate employee identity information
            template["FirstName"] = self.fake.first_name()
            template["LastName"] = self.fake.last_name()

            template["Email"] = (
                template["FirstName"].lower()
                + "."
                + template["LastName"].lower()
                + str(employee_id)
                + "@company.com"
            )

            records.append(template)

        self.employee_data = pd.DataFrame(records)

        print(f"Generated employees: {len(self.employee_data)}")


    def generate_history(self):

        print("\nGenerating SCD Type 2 historical records...")

        history_records = []

        # Select approximately 10% of employees
        historical_count = int(self.target_rows * 0.10)

        historical_employees = self.employee_data.sample(
            n=historical_count,
            random_state=42
        )

        for _, employee in historical_employees.iterrows():

            employee_id = employee["EmployeeNumber"]

            # Create an older version of the employee
            old_record = employee.copy()

            old_record["start_date"] = "2023-01-01"
            old_record["end_date"] = "2024-12-31"
            old_record["is_current"] = 0

            # Simulate a salary before the change
            old_record["MonthlyIncome"] = max(
                1000,
                int(employee["MonthlyIncome"] * random.uniform(0.85, 0.95))
            )

            # Simulate promotion for some employees
            if random.choice([True, False]):

                old_record["JobLevel"] = max(
                    1,
                    int(employee["JobLevel"]) - 1
                )

            # Simulate department change for some employees
            if random.choice([True, False]):

                departments = [
                    "Research & Development",
                    "Sales",
                    "Human Resources"
                ]

                current_department = employee["Department"]

                other_departments = [
                    d for d in departments
                    if d != current_department
                ]

                old_record["Department"] = random.choice(
                    other_departments
                )

            history_records.append(old_record)

            # Current version
            current_record = employee.copy()

            current_record["start_date"] = "2025-01-01"
            current_record["end_date"] = None
            current_record["is_current"] = 1

            history_records.append(current_record)

        self.history_data = pd.DataFrame(history_records)

        print(
            f"Historical SCD records generated: "
            f"{len(self.history_data)}"
        )


    def save_data(self):

        print("\nSaving generated datasets...")

        self.employee_data.to_csv(
            self.output_file,
            index=False
        )

        self.history_data.to_csv(
            self.history_file,
            index=False
        )

        print("Employee dataset saved successfully.")
        print("SCD history dataset saved successfully.")


    def run(self):

        self.load_data()

        self.generate_employees()

        self.generate_history()

        self.save_data()

        print("\nData synthesis completed successfully!")




if __name__ == "__main__":

    synthesizer = EmployeeDataSynthesizer(

        input_file=(
            "data/WA_Fn-UseC_-HR-Employee-Attrition.csv"
        ),

        output_file=(
            "data/employees_100k.csv"
        ),

        history_file=(
            "data/employee_scd_history.csv"
        ),

        target_rows=100000
    )

    synthesizer.run()