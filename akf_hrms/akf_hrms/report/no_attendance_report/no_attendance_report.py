# Mubashir Bashir

from __future__ import unicode_literals
import frappe
from frappe import _


def execute(filters=None):
    columns, data = [], []
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        _("Employee") + ":Link/Employee:180",
        _("Employee Name") + "::180",
        _("Department") + ":Link/Department:150",
        _("Designation") + ":Link/Designation:150",
        _("Branch") + ":Link/Branch:150",
        _("Employment Type") + ":Link/Employment Type:150",
        _("Grade") + "::150",
        _("Job Classification") + ":Link/Job Classification:150",
        _("Region") + "::150"
    ]

def get_data(filters):
    return_list = []
    conditions, filters = get_conditions(filters)

    get_employee = frappe.db.sql(f"""
        SELECT name, employee_name, department, designation, branch, employment_type, grade, custom_job_classification, custom_region 
        FROM `tabEmployee`
        WHERE custom_no_attendance = 0
        AND status = 'Active'
        AND name NOT IN (
            SELECT DISTINCT employee 
            FROM `tabAttendance`
            WHERE docstatus = 1 
            AND attendance_date BETWEEN %(from_date)s AND %(to_date)s
        ) {conditions}
    """, filters, as_dict=1)

    for emp in get_employee:
        single_row = [
            emp.get("name"),
            emp.get("employee_name"),
            emp.get("department"),
            emp.get("designation"),
            emp.get("branch"),
            emp.get("employment_type"),
            emp.get("grade"),
            emp.get("custom_job_classification"),
            emp.get("custom_region")
        ]
        return_list.append(single_row)
    
    return return_list

def get_conditions(filters):
    conditions = ""
    if filters.get("company"):
        conditions += " AND company = %(company)s"
    if filters.get("employee"):
        conditions += " AND name = %(employee)s"

    return conditions, filters

