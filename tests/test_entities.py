from datetime import date, timedelta

import pytest

from entities import Employee, Project, Review, _check_email, _check_int, _check_text, check_role


def make_employee(**overrides):
    data = dict(
        first_name="Keerthi",
        last_name="Kumar",
        age=25,
        gender="Female",
        marital_status="Single",
        department_id=1,
        job_role_id=1,
        job_level=2,
        education=3,
        education_field_id=1,
        monthly_income=50000,
        employee_number=1001,
    )
    data.update(overrides)
    return Employee(**data)


def test_check_int_converts_integer_string():
    assert _check_int("12", "Age", 1, 20) == 12


@pytest.mark.parametrize("value", ["abc", None])
def test_check_int_rejects_non_whole_values(value):
    with pytest.raises(ValueError):
        _check_int(value, "Age", 1, 20)


@pytest.mark.parametrize("value", [0, 21])
def test_check_int_rejects_out_of_range(value):
    with pytest.raises(ValueError):
        _check_int(value, "Age", 1, 20)


def test_check_text_strips_whitespace():
    assert _check_text("  hello  ", "Name") == "hello"


@pytest.mark.parametrize("value", ["", "   ", None])
def test_check_text_requires_value(value):
    with pytest.raises(ValueError):
        _check_text(value, "Name")


def test_check_text_rejects_too_long():
    with pytest.raises(ValueError):
        _check_text("x" * 6, "Name", max_len=5)


def test_check_email_normalizes_case_and_spaces():
    assert _check_email("  USER@Example.COM ") == "user@example.com"


@pytest.mark.parametrize("value", ["", None, "not-an-email", "x@localhost", "a@" + "x" * 250 + ".com"])
def test_check_email_rejects_invalid_email(value):
    with pytest.raises(ValueError):
        _check_email(value)


def test_employee_defaults_and_email_normalization():
    employee = make_employee(email="  K@Example.com ")
    assert employee.email == "k@example.com"
    assert employee.full_name() == "Keerthi Kumar"
    assert employee.annual_income() == 600000


def test_employee_email_can_be_omitted_for_legacy_records():
    assert make_employee().email is None


@pytest.mark.parametrize("field,value", [
    ("first_name", ""),
    ("first_name", "K3erthi"),
    ("last_name", "Kumar!"),
    ("age", 17),
    ("age", 71),
    ("gender", "Other"),
    ("marital_status", "Unknown"),
    ("department_id", 0),
    ("job_role_id", 0),
    ("job_level", 6),
    ("education", 0),
    ("education_field_id", 0),
    ("monthly_income", 999),
    ("business_travel", "Plane"),
    ("distance_from_home", 501),
    ("overtime", "Sometimes"),
    ("total_working_years", 51),
    ("num_companies_worked", 31),
    ("email", ""),
])
def test_employee_rejects_invalid_field(field, value):
    with pytest.raises(ValueError):
        make_employee(**{field: value})


def test_employee_to_db_row_contains_email_and_derived_rates():
    row = make_employee(email="k@example.com").to_db_row()
    assert row["email"] == "k@example.com"
    assert row["monthly_income"] == 50000
    assert row["daily_rate"] == round(50000 / 22)
    assert row["hourly_rate"] == round(50000 / 160)
    assert row["attrition"] == "No"


def test_employee_repr():
    assert "Keerthi Kumar" in repr(make_employee())


def test_project_normalizes_name_and_behaviour():
    project = Project("  Analytics Platform  ", 1, date(2026, 1, 1))
    assert project.project_name == "Analytics Platform"
    assert project.is_active() is True
    assert project.duration_days() == (date.today() - date(2026, 1, 1)).days
    assert project.to_db_row() == ("Analytics Platform", 1, date(2026, 1, 1), None, "Active")


@pytest.mark.parametrize("kwargs", [
    {"project_name": "", "department_id": 1, "start_date": date(2026, 1, 1)},
    {"project_name": "!!!", "department_id": 1, "start_date": date(2026, 1, 1)},
    {"project_name": "Good Project", "department_id": 0, "start_date": date(2026, 1, 1)},
    {"project_name": "Good Project", "department_id": 1, "start_date": "2026-01-01"},
    {"project_name": "Good Project", "department_id": 1, "start_date": date(2026, 1, 2), "end_date": date(2026, 1, 1)},
    {"project_name": "Good Project", "department_id": 1, "start_date": date(2026, 1, 1), "status": "Unknown"},
])
def test_project_rejects_invalid_data(kwargs):
    with pytest.raises(ValueError):
        Project(**kwargs)


def test_completed_project_is_not_active():
    project = Project("Migration Project", 1, date(2026, 1, 1), status="Completed")
    assert project.is_active() is False


def test_project_duration_with_end_date():
    project = Project("Migration Project", 1, date(2026, 1, 1), date(2026, 1, 10))
    assert project.duration_days() == 9


def test_project_repr():
    assert "Migration Project" in repr(Project("Migration Project", 1, date(2026, 1, 1)))


def test_check_role_normalizes_spaces():
    assert check_role("  Data   Engineer ") == "Data Engineer"


@pytest.mark.parametrize("value", ["", "x", "!!!", "123", "a" * 51])
def test_check_role_rejects_invalid_role(value):
    with pytest.raises(ValueError):
        check_role(value)


def test_review_defaults_and_helpers():
    review = Review(10, 5, date(2026, 4, 1), "  Excellent work  ")
    assert review.comments == "Excellent work"
    assert review.review_period == "2026 Annual"
    assert review.rating_label() == "Outstanding performance"
    assert review.to_db_row() == (10, date(2026, 4, 1), "2026 Annual", 5, "Excellent work")


def test_review_default_date_and_comment():
    review = Review(10, 3)
    assert review.review_date == date.today()
    assert review.comments == "Meets expectations"


@pytest.mark.parametrize("employee_id,rating", [(0, 3), (1, 0), (1, 6), ("bad", 3)])
def test_review_rejects_invalid_id_or_rating(employee_id, rating):
    with pytest.raises(ValueError):
        Review(employee_id, rating)


def test_review_rejects_future_date_outside_warehouse_range():
    with pytest.raises(ValueError):
        Review(10, 4, date(2028, 1, 1))


def test_review_rejects_long_comments():
    with pytest.raises(ValueError):
        Review(10, 4, comments="x" * 501)


def test_review_repr():
    assert "employee_id=10" in repr(Review(10, 4))
