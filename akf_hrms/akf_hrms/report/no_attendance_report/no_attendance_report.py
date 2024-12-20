# Mubashir Bashir

from __future__ import unicode_literals
import frappe
from frappe import _
from datetime import timedelta

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
        _("Region") + "::150",
        _("Missing Attendance Dates") + "::250"
    ]



def get_data(filters):
    return_list = []
    conditions, filters = get_conditions(filters)

    get_employee = frappe.db.sql(f"""
        SELECT name, employee_name, department, designation, branch, employment_type, grade, custom_region 
        FROM `tabEmployee`
        WHERE custom_no_attendance = 0
        AND status = 'Active'
        {conditions}
    """, filters, as_dict=1)

    
    for emp in get_employee:
        
        attendance_dates = frappe.db.sql(f"""
            SELECT attendance_date 
            FROM `tabAttendance` 
            WHERE employee = %(employee)s 
            AND attendance_date BETWEEN %(from_date)s AND %(to_date)s
            AND docstatus = 1
        """, {"employee": emp.get("name"), "from_date": filters.get("from_date"), "to_date": filters.get("to_date")}, as_dict=1)

       
        attendance_dates_set = {d['attendance_date'].strftime('%Y-%m-%d') for d in attendance_dates}

       
        from_date = frappe.utils.getdate(filters.get("from_date"))
        to_date = frappe.utils.getdate(filters.get("to_date"))
        
        
        all_dates = []
        current_date = from_date
        while current_date <= to_date:
            all_dates.append(current_date)
            current_date += timedelta(days=1)

       
        missing_dates = [d for d in all_dates if d.strftime('%Y-%m-%d') not in attendance_dates_set]

        # frappe.msgprint("Dates")
        # frappe.msgprint(f'all dates: {all_dates}, attendance dates: {attendance_dates}, attendance dates set: {attendance_dates_set}, missing dates: {missing_dates}')
        if missing_dates:
           
            first_row = [
                emp.get("name"),
                emp.get("employee_name"),
                emp.get("department"),
                emp.get("designation"),
                emp.get("branch"),
                emp.get("employment_type"),
                emp.get("grade"),
                emp.get("custom_region"),
                missing_dates[0].strftime('%d-%m-%Y') 
            ]
            return_list.append(first_row)

            for missing_date in missing_dates[1:]:
                return_list.append(['-', '-', '-', '-', '-', '-', '-', '-', missing_date.strftime('%d-%m-%Y')])

    return return_list


def get_conditions(filters):
    conditions = ""
    if filters.get("company"):
        conditions += " AND company = %(company)s"
    if filters.get("employee"):
        conditions += " AND name = %(employee)s"
    if filters.get("branch"):
        conditions += " AND branch = %(branch)s"
    if filters.get("department"):
        conditions += " AND department = %(department)s"

    return conditions, filters

