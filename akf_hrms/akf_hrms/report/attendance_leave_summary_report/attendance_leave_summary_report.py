from __future__ import unicode_literals
import frappe
from frappe import _
from datetime import datetime

def execute(filters=None):
    columns = get_employee_columns()
    data = get_employee_data(filters)
    return columns, data

def get_employee_columns():
    return [
        _("ID") + ":Link/Employee:120",
        _("Name") + ":Data:120",
        _("Branch") + ":Link/Branch:120",
        _("Department") + ":Link/Department:120",
        _("Designation") + ":Link/Designation:120",
        _("Status") + ":Data:120",
        _("Casual Leave Allowed") + ":Int:120",
        _("Casual Leave Availed") + ":Int:120",
        _("Casual Leave Balance") + ":Int:120",
        _("Medical Leave Allowed") + ":Int:120",
        _("Medical Leave Availed") + ":Int:120",
        _("Medical Leave Balance") + ":Int:120",
        _("Earned/Recreational Leave Allowed") + ":Int:120",
        _("Earned/Recreational Leave Availed") + ":Int:120",
        _("Earned/Recreational Leave Balance") + ":Int:120",
        _("Late Ded") + ":Int:100",
        _("Early Ded") + ":Int:100",
        _("Missing Ded") + ":Int:100",
        _("Absent") + ":Int:100",
        _("Paid Days") + ":Int:100",
    ]

def get_employee_data(filters):
    conditions, filter_values = get_conditions(filters)
    
    query = """
        SELECT e.name, e.employee_name, e.branch, e.department, e.designation, e.employment_type,
            COALESCE(CL.allocated, 0) AS casual_leave_allowed, COALESCE(CL.availed, 0) AS casual_leave_availed,
            COALESCE(CL.balance, 0) AS casual_leave_balance,
            COALESCE(ML.allocated, 0) AS medical_leave_allowed, COALESCE(ML.availed, 0) AS medical_leave_availed,
            COALESCE(ML.balance, 0) AS medical_leave_balance,
            COALESCE(EL.allocated, 0) AS earned_recreational_leave_allowed, COALESCE(EL.availed, 0) AS earned_recreational_leave_availed,
            COALESCE(EL.balance, 0) AS earned_recreational_leave_balance,
            COALESCE(A.late_count, 0) AS late_ded, COALESCE(A.early_count, 0) AS early_ded,
            COALESCE(A.missing_count, 0) AS missing_ded,
            GREATEST((DATEDIFF(%(to_date)s, %(from_date)s) + 1) - COALESCE(H.holidays, 0) - COALESCE(A.total, 0), 0) AS absent,
            (COALESCE(A.total, 0) + COALESCE(H.holidays, 0)) AS paid_days
        FROM `tabEmployee` e
        LEFT JOIN 
            (SELECT employee, SUM(leaves) AS allocated, SUM(used) AS availed, SUM(leaves) - SUM(used) AS balance FROM `tabLeave Ledger Entry` WHERE leave_type = 'Casual Leave' GROUP BY employee) CL ON e.name = CL.employee
        LEFT JOIN
            (SELECT employee, SUM(leaves) AS allocated, SUM(used) AS availed, SUM(leaves) - SUM(used) AS balance FROM `tabLeave Ledger Entry` WHERE leave_type = 'Medical Leave' GROUP BY employee) ML ON e.name = ML.employee
        LEFT JOIN 
            (SELECT employee, SUM(leaves) AS allocated, SUM(used) AS availed, SUM(leaves) - SUM(used) AS balance FROM `tabLeave Ledger Entry` WHERE leave_type IN ('Earned Leave', 'Recreational Leave') GROUP BY employee) EL ON e.name = EL.employee
        LEFT JOIN 
            (SELECT employee, SUM(late_entry) AS late_count, SUM(early_exit) AS early_count, SUM(CASE WHEN (custom_in_times IS NULL OR custom_out_times IS NULL) THEN 1 ELSE 0 END) AS missing_count, COUNT(*) AS total FROM `tabAttendance` WHERE attendance_date BETWEEN %(from_date)s AND %(to_date)s GROUP BY employee) A ON e.name = A.employee
        LEFT JOIN 
            (SELECT e.name AS employee, COUNT(h.holiday_date) AS holidays FROM `tabEmployee` e LEFT JOIN `tabHoliday` h ON e.holiday_list = h.parent WHERE h.holiday_date BETWEEN %(from_date)s AND %(to_date)s GROUP BY e.name) H ON e.name = H.employee
        WHERE e.status = 'Active' {conditions}
    """.format(conditions=conditions)
    
    return frappe.db.sql(query, filter_values, as_dict=1)

def get_conditions(filters):
    conditions = ""
    filter_values = {"from_date": filters.get("from_date"), "to_date": filters.get("to_date")}
    
    if filters.get("company"):
        conditions += " AND e.company = %(company)s"
        filter_values["company"] = filters.get("company")
    if filters.get("employee"):
        conditions += " AND e.name = %(employee)s"
        filter_values["employee"] = filters.get("employee")
    if filters.get("branch"):
        conditions += " AND e.branch = %(branch)s"
        filter_values["branch"] = filters.get("branch")
    if filters.get("department"):
        conditions += " AND e.department = %(department)s"
        filter_values["department"] = filters.get("department")
    if filters.get("designation"):
        conditions += " AND e.designation = %(designation)s"
        filter_values["designation"] = filters.get("designation")
    if filters.get("employment_type"):
        conditions += " AND e.employment_type = %(employment_type)s"
        filter_values["employment_type"] = filters.get("employment_type")
    
    return conditions, filter_values
