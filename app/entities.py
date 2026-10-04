"""entities.py - domain objects (Employee, Project, Review).

Attributes are private (_name) and exposed through properties that validate on
assignment, so an invalid object can never be built. Each class also owns its
behaviour (full_name(), is_active(), rating_label() ...) and knows how to turn
itself into a database row (to_db_row()).
"""
from datetime import date

GENDERS = ["Male", "Female"]
MARITAL = ["Single", "Married", "Divorced"]
TRAVEL = ["Non-Travel", "Travel_Rarely", "Travel_Frequently"]
PROJECT_STATUS = ["Active", "Completed", "On Hold", "Delayed"]
RATING_LABELS = {
    1: "Needs significant improvement",
    2: "Below expectations",
    3: "Meets expectations",
    4: "Exceeds expectations",
    5: "Outstanding performance",
}


def _check_int(value, name, low, high):
    try:
        value = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a whole number")
    if not low <= value <= high:
        raise ValueError(f"{name} must be between {low} and {high}")
    return value


def _check_text(value, name, max_len=100):
    value = (value or "").strip()
    if not value:
        raise ValueError(f"{name} is required")
    if len(value) > max_len:
        raise ValueError(f"{name} must be at most {max_len} characters")
    return value


def _check_choice(value, name, options):
    if value not in options:
        raise ValueError(f"{name} must be one of: {', '.join(options)}")
    return value


class Employee:
    """An employee as stored in the OLTP ``Employee`` table."""

    def __init__(self, first_name, last_name, age, gender, marital_status,
                 department_id, job_role_id, job_level, education,
                 education_field_id, monthly_income, business_travel="Travel_Rarely",
                 distance_from_home=5, overtime="No", total_working_years=0,
                 num_companies_worked=0, employee_number=None):
        self.employee_number = employee_number
        self.first_name = first_name
        self.last_name = last_name
        self.age = age
        self.gender = gender
        self.marital_status = marital_status
        self.department_id = department_id
        self.job_role_id = job_role_id
        self.job_level = job_level
        self.education = education
        self.education_field_id = education_field_id
        self.monthly_income = monthly_income
        self.business_travel = business_travel
        self.distance_from_home = distance_from_home
        self.overtime = overtime
        self.total_working_years = total_working_years
        self.num_companies_worked = num_companies_worked

    # ---- validated properties -------------------------------------------------
    @property
    def first_name(self): return self._first_name
    @first_name.setter
    def first_name(self, v): self._first_name = _check_text(v, "First name")

    @property
    def last_name(self): return self._last_name
    @last_name.setter
    def last_name(self, v): self._last_name = _check_text(v, "Last name")

    @property
    def age(self): return self._age
    @age.setter
    def age(self, v): self._age = _check_int(v, "Age", 18, 70)

    @property
    def gender(self): return self._gender
    @gender.setter
    def gender(self, v): self._gender = _check_choice(v, "Gender", GENDERS)

    @property
    def marital_status(self): return self._marital_status
    @marital_status.setter
    def marital_status(self, v): self._marital_status = _check_choice(v, "Marital status", MARITAL)

    @property
    def department_id(self): return self._department_id
    @department_id.setter
    def department_id(self, v): self._department_id = _check_int(v, "Department", 1, 10**6)

    @property
    def job_role_id(self): return self._job_role_id
    @job_role_id.setter
    def job_role_id(self, v): self._job_role_id = _check_int(v, "Job role", 1, 10**6)

    @property
    def job_level(self): return self._job_level
    @job_level.setter
    def job_level(self, v): self._job_level = _check_int(v, "Job level", 1, 5)

    @property
    def education(self): return self._education
    @education.setter
    def education(self, v): self._education = _check_int(v, "Education", 1, 5)

    @property
    def education_field_id(self): return self._education_field_id
    @education_field_id.setter
    def education_field_id(self, v): self._education_field_id = _check_int(v, "Education field", 1, 10**6)

    @property
    def monthly_income(self): return self._monthly_income
    @monthly_income.setter
    def monthly_income(self, v): self._monthly_income = _check_int(v, "Monthly income", 1000, 1_000_000)

    @property
    def business_travel(self): return self._business_travel
    @business_travel.setter
    def business_travel(self, v): self._business_travel = _check_choice(v, "Business travel", TRAVEL)

    @property
    def distance_from_home(self): return self._distance_from_home
    @distance_from_home.setter
    def distance_from_home(self, v): self._distance_from_home = _check_int(v, "Distance from home", 0, 500)

    @property
    def overtime(self): return self._overtime
    @overtime.setter
    def overtime(self, v): self._overtime = _check_choice(v, "Overtime", ["Yes", "No"])

    @property
    def total_working_years(self): return self._total_working_years
    @total_working_years.setter
    def total_working_years(self, v): self._total_working_years = _check_int(v, "Total working years", 0, 50)

    @property
    def num_companies_worked(self): return self._num_companies_worked
    @num_companies_worked.setter
    def num_companies_worked(self, v): self._num_companies_worked = _check_int(v, "Companies worked", 0, 30)

    # ---- behaviour -----------------------------------------------------------
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def annual_income(self):
        return self.monthly_income * 12

    def to_db_row(self):
        """Column -> value dict for INSERT INTO Employee (all 34 columns)."""
        income = self.monthly_income
        return {
            "employee_number": self.employee_number,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "age": self.age,
            "gender": self.gender,
            "marital_status": self.marital_status,
            "department_id": self.department_id,
            "job_role_id": self.job_role_id,
            "job_level": self.job_level,
            "education": self.education,
            "education_field_id": self.education_field_id,
            "business_travel": self.business_travel,
            "distance_from_home": self.distance_from_home,
            "daily_rate": round(income / 22),
            "hourly_rate": round(income / 160),
            "monthly_income": income,
            "monthly_rate": income,
            "overtime": self.overtime,
            # neutral defaults for the survey-style columns of the IBM dataset
            "job_satisfaction": 3, "environment_satisfaction": 3, "job_involvement": 3,
            "performance_rating": 3, "relationship_satisfaction": 3, "work_life_balance": 3,
            "percent_salary_hike": 0, "stock_option_level": 0,
            "total_working_years": self.total_working_years,
            "years_at_company": 0, "years_in_current_role": 0,
            "years_since_last_promotion": 0, "years_with_current_manager": 0,
            "num_companies_worked": self.num_companies_worked,
            "training_times_last_year": 0,
            "attrition": "No",
        }

    def __repr__(self):
        return f"Employee(#{self.employee_number}, {self.full_name()}, level {self.job_level})"


class Project:
    """A project as stored in the OLTP ``Project`` table."""

    def __init__(self, project_name, department_id, start_date, end_date=None, status="Active"):
        self.project_name = project_name
        self.department_id = department_id
        self.status = status
        self.start_date = start_date
        self.end_date = end_date

    @property
    def project_name(self): return self._project_name
    @project_name.setter
    def project_name(self, v): self._project_name = _check_text(v, "Project name")

    @property
    def department_id(self): return self._department_id
    @department_id.setter
    def department_id(self, v): self._department_id = _check_int(v, "Department", 1, 10**6)

    @property
    def status(self): return self._status
    @status.setter
    def status(self, v): self._status = _check_choice(v, "Status", PROJECT_STATUS)

    @property
    def start_date(self): return self._start_date
    @start_date.setter
    def start_date(self, v):
        if not isinstance(v, date):
            raise ValueError("Start date is required")
        self._start_date = v

    @property
    def end_date(self): return self._end_date
    @end_date.setter
    def end_date(self, v):
        if v is not None and v < self._start_date:
            raise ValueError("End date cannot be before the start date")
        self._end_date = v

    def is_active(self):
        return self.status == "Active"

    def duration_days(self):
        return ((self.end_date or date.today()) - self.start_date).days

    def to_db_row(self):
        return (self.project_name, self.department_id, self.start_date, self.end_date, self.status)

    def __repr__(self):
        return f"Project({self.project_name!r}, {self.status})"


class Review:
    """A performance review as stored in the OLTP ``Reviews`` table."""

    def __init__(self, employee_id, rating, review_date=None, comments=""):
        self.employee_id = employee_id
        self.rating = rating
        self.review_date = review_date or date.today()
        self.comments = comments

    @property
    def employee_id(self): return self._employee_id
    @employee_id.setter
    def employee_id(self, v): self._employee_id = _check_int(v, "Employee", 1, 10**9)

    @property
    def rating(self): return self._rating
    @rating.setter
    def rating(self, v): self._rating = _check_int(v, "Rating", 1, 5)

    @property
    def review_date(self): return self._review_date
    @review_date.setter
    def review_date(self, v):
        if not isinstance(v, date):
            raise ValueError("Review date is required")
        if v > date(2027, 12, 31):
            raise ValueError("Review date is beyond the warehouse date range (2027-12-31)")
        self._review_date = v

    @property
    def comments(self): return self._comments
    @comments.setter
    def comments(self, v):
        v = (v or "").strip()
        if len(v) > 500:
            raise ValueError("Comments must be at most 500 characters")
        self._comments = v or RATING_LABELS[self._rating]

    @property
    def review_period(self):
        return f"{self.review_date.year} Annual"

    def rating_label(self):
        return RATING_LABELS[self.rating]

    def to_db_row(self):
        return (self.employee_id, self.review_date, self.review_period, self.rating, self.comments)

    def __repr__(self):
        return f"Review(employee_id={self.employee_id}, {self.review_period}, rating={self.rating})"
