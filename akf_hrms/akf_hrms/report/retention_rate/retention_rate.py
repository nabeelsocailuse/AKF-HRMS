# Developer Mubashir Bashir

import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
    columns, data = [], []

    if filters['from_date'] > filters['to_date']:
        frappe.throw(_("From Date cannot be greater than To Date"))

    data = get_data(filters)
    columns = get_columns()
    chart_data = get_chart_data(data)

    return columns, data, None, chart_data

def get_data(filters):
    from_date = filters.get('from_date')
    to_date = filters.get('to_date')
    company = filters.get('company')
    branch = filters.get('branch')

    branch_conditions = {}
    if branch:
        branch_conditions["name"] = branch

    branches = frappe.get_all("Branch", filters=branch_conditions, fields=["name"])

    overall_employees_on_start = 0
    overall_employees_on_end = 0
    overall_employees_left = 0

    report_data = []

    for branch in branches:
        branch_name = branch["name"]
        
        # Get the employee count for each branch
        employees_on_start_date = get_employee_count_on_from_date(from_date, to_date, company, branch_name)
        employees_on_end_date = get_employee_count_on_to_date(to_date, company, branch_name)
        employees_left = employees_on_start_date - employees_on_end_date

        retention_rate = 0
        if employees_on_start_date > 0:
            retention_rate = (employees_on_end_date / employees_on_start_date) * 100

        # Add branch-specific data to report
        report_data.append({
            "branch": branch_name,
            "employees_on_start": employees_on_start_date,
            "employees_on_end": employees_on_end_date,
            "employees_left": employees_left,
            "retention_rate": flt(retention_rate, 2),
            "is_bold": 0
        })

        # Accumulate for overall summary
        overall_employees_on_start += employees_on_start_date
        overall_employees_on_end += employees_on_end_date
        overall_employees_left += employees_left

    # Calculate overall retention rate
    overall_retention_rate = 0
    if overall_employees_on_start > 0:
        overall_retention_rate = (overall_employees_on_end / overall_employees_on_start) * 100

    # Add overall summary to report
    report_data.append({
        "branch": _("Overall"),
        "employees_on_start": overall_employees_on_start,
        "employees_on_end": overall_employees_on_end,
        "employees_left": overall_employees_left,
        "retention_rate": flt(overall_retention_rate, 2),
        "is_bold": 1
    })

    return report_data

def get_employee_count_on_from_date(from_date, to_date, company=None, branch=None):
    filters = {"status": "Active", "date_of_joining": ["<=", to_date]}
    if company:
        filters["company"] = company
    if branch:
        filters["branch"] = branch

    active_count = frappe.db.count("Employee", filters)

    left_filters = {"status": "Left", "relieving_date": ["between", [from_date, to_date]]}
    if company:
        left_filters["company"] = company
    if branch:
        left_filters["branch"] = branch

    left_count = frappe.db.count("Employee", left_filters)

    total_count = active_count + left_count

    return total_count

def get_employee_count_on_to_date(to_date, company=None, branch=None):
    filters = {"status": "Active", "date_of_joining": ["<=", to_date]}
    if company:
        filters["company"] = company
    if branch:
        filters["branch"] = branch

    count = frappe.db.count("Employee", filters)
    return count

def get_columns():
    columns = [
        {"fieldname": "branch", "label": _("Branch"), "fieldtype": "Link", "options": "Branch", "width": 200},
        {"fieldname": "employees_on_start", "label": _("Number of Employees on Start Date"), "fieldtype": "Int", "width": 250},
        {"fieldname": "employees_on_end", "label": _("Number of Employees on End Date"), "fieldtype": "Int", "width": 250},
        {"fieldname": "employees_left", "label": _("Number of Employees Left"), "fieldtype": "Int", "width": 250},
        {"fieldname": "retention_rate", "label": _("Retention Rate (%)"), "fieldtype": "Float", "width": 250},
    ]
    return columns

def get_chart_data(data):
    """Generate chart data for retention"""
    # Create a dataset for each branch
    labels = [entry["branch"] for entry in data]
    employees_on_start = [entry["employees_on_start"] for entry in data]
    employees_on_end = [entry["employees_on_end"] for entry in data]
    employees_left = [entry["employees_left"] for entry in data]

    chart = {
        "data": {
            "labels": labels,
            "datasets": [
                {"name": _("Employees on Start Date"), "values": employees_on_start},
                {"name": _("Employees on End Date"), "values": employees_on_end},
                {"name": _("Employees Left"), "values": employees_left},
            ],
        },
        "type": "bar",
        "colors": ["#84D5BA", "#CB4B5F", "#FFC65C"],
    }
    return chart
