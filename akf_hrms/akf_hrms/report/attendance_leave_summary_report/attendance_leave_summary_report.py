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
        _("Employment Type") + ":Data:120",
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
    
    data = frappe.db.sql("""
        SELECT e.name, e.employee_name, e.branch, e.department, e.designation, e.employment_type,
            COALESCE(CL.allocated, 0) AS casual_leave_allowed, COALESCE(CL.used, 0) AS casual_leave_availed,
            COALESCE(CL.allocated - CL.used, 0) AS casual_leave_balance,
            COALESCE(ML.allocated, 0) AS medical_leave_allowed, COALESCE(ML.used, 0) AS medical_leave_availed,
            COALESCE(ML.allocated - ML.used, 0) AS medical_leave_balance,
            COALESCE(EL.allocated, 0) AS earned_recreational_leave_allowed, COALESCE(EL.used, 0) AS earned_recreational_leave_availed,
            COALESCE(EL.allocated - EL.used, 0) AS earned_recreational_leave_balance,
            COALESCE(A.late_count, 0) AS late_ded, COALESCE(A.early_count, 0) AS early_ded,
            COALESCE(A.missing_count, 0) AS missing_ded,
            GREATEST((DATEDIFF(%(to_date)s, %(from_date)s) + 1) - COALESCE(H.holidays, 0) - COALESCE(A.total, 0), 0) AS absent,
            (COALESCE(A.total, 0) + COALESCE(H.holidays, 0)) AS paid_days
        FROM `tabEmployee` e
        LEFT JOIN 
            (SELECT employee, 
                SUM(CASE WHEN transaction_type='Leave Allocation' THEN leaves ELSE 0 END) AS allocated,
                SUM(CASE WHEN transaction_type='Leave Application' THEN -1 * leaves ELSE 0 END) AS used
            FROM `tabLeave Ledger Entry` WHERE leave_type = 'Casual Leave' 
            GROUP BY employee) CL ON e.name = CL.employee
        LEFT JOIN
            (SELECT employee, 
                SUM(CASE WHEN transaction_type='Leave Allocation' THEN leaves ELSE 0 END) AS allocated,
                SUM(CASE WHEN transaction_type='Leave Application' THEN -1 * leaves ELSE 0 END) AS used
            FROM `tabLeave Ledger Entry` WHERE leave_type = 'Medical Leave' 
            GROUP BY employee) ML ON e.name = ML.employee
        LEFT JOIN 
            (SELECT employee, 
                SUM(CASE WHEN transaction_type='Leave Allocation' THEN leaves ELSE 0 END) AS allocated,
                SUM(CASE WHEN transaction_type='Leave Application' THEN -1 * leaves ELSE 0 END) AS used
            FROM `tabLeave Ledger Entry` WHERE leave_type IN ('Earned Leave', 'Recreational Leave') 
            GROUP BY employee) EL ON e.name = EL.employee
        LEFT JOIN 
            (SELECT employee, SUM(late_entry) AS late_count, SUM(early_exit) AS early_count, 
                SUM(CASE WHEN (custom_in_times IS NULL OR custom_out_times IS NULL) THEN 1 ELSE 0 END) AS missing_count, 
                COUNT(*) AS total 
            FROM `tabAttendance` WHERE attendance_date BETWEEN %(from_date)s AND %(to_date)s 
            GROUP BY employee) A ON e.name = A.employee
        LEFT JOIN 
            (SELECT e.name AS employee, COUNT(h.holiday_date) AS holidays 
            FROM `tabEmployee` e 
            LEFT JOIN `tabHoliday` h ON e.holiday_list = h.parent 
            WHERE h.holiday_date BETWEEN %(from_date)s AND %(to_date)s 
            GROUP BY e.name) H ON e.name = H.employee
        WHERE e.status = 'Active' {conditions}
    """.format(conditions=conditions), filter_values, as_dict=1)

    frappe.msgprint(frappe.as_json(data))
    
    return data


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




# def get_employee_data(filters):
#     conditions, filter_values = get_conditions(filters)
    
#     query = """
#         SELECT e.name, e.employee_name, e.branch, e.department, e.designation, e.employment_type,
#             COALESCE(CL.allocated, 0) AS casual_leave_allowed, COALESCE(CL.availed, 0) AS casual_leave_availed,
#             COALESCE(CL.balance, 0) AS casual_leave_balance,
#             COALESCE(ML.allocated, 0) AS medical_leave_allowed, COALESCE(ML.availed, 0) AS medical_leave_availed,
#             COALESCE(ML.balance, 0) AS medical_leave_balance,
#             COALESCE(EL.allocated, 0) AS earned_recreational_leave_allowed, COALESCE(EL.availed, 0) AS earned_recreational_leave_availed,
#             COALESCE(EL.balance, 0) AS earned_recreational_leave_balance,
#             COALESCE(A.late_count, 0) AS late_ded, COALESCE(A.early_count, 0) AS early_ded,
#             COALESCE(A.missing_count, 0) AS missing_ded,
#             GREATEST((DATEDIFF(%(to_date)s, %(from_date)s) + 1) - COALESCE(H.holidays, 0) - COALESCE(A.total, 0), 0) AS absent,
#             (COALESCE(A.total, 0) + COALESCE(H.holidays, 0)) AS paid_days
#         FROM `tabEmployee` e
#         LEFT JOIN 
#             (SELECT employee, SUM(leaves) AS allocated, SUM(used) AS availed, SUM(leaves) - SUM(used) AS balance FROM `tabLeave Ledger Entry` WHERE leave_type = 'Casual Leave' GROUP BY employee) CL ON e.name = CL.employee
#         LEFT JOIN
#             (SELECT employee, SUM(leaves) AS allocated, SUM(used) AS availed, SUM(leaves) - SUM(used) AS balance FROM `tabLeave Ledger Entry` WHERE leave_type = 'Medical Leave' GROUP BY employee) ML ON e.name = ML.employee
#         LEFT JOIN 
#             (SELECT employee, SUM(leaves) AS allocated, SUM(used) AS availed, SUM(leaves) - SUM(used) AS balance FROM `tabLeave Ledger Entry` WHERE leave_type IN ('Earned Leave', 'Recreational Leave') GROUP BY employee) EL ON e.name = EL.employee
#         LEFT JOIN 
#             (SELECT employee, SUM(late_entry) AS late_count, SUM(early_exit) AS early_count, SUM(CASE WHEN (custom_in_times IS NULL OR custom_out_times IS NULL) THEN 1 ELSE 0 END) AS missing_count, COUNT(*) AS total FROM `tabAttendance` WHERE attendance_date BETWEEN %(from_date)s AND %(to_date)s GROUP BY employee) A ON e.name = A.employee
#         LEFT JOIN 
#             (SELECT e.name AS employee, COUNT(h.holiday_date) AS holidays FROM `tabEmployee` e LEFT JOIN `tabHoliday` h ON e.holiday_list = h.parent WHERE h.holiday_date BETWEEN %(from_date)s AND %(to_date)s GROUP BY e.name) H ON e.name = H.employee
#         WHERE e.status = 'Active' {conditions}
#     """.format(conditions=conditions)
    
#     return frappe.db.sql(query, filter_values, as_dict=1)






# def get_employee_data(filters):
#     conditions, filter_values = get_conditions(filters)

#     # Fetching employees
#     employees = frappe.db.sql("""
#         SELECT e.name, e.employee_name, e.branch, e.department, e.designation, e.employment_type
#         FROM `tabEmployee` e
#         WHERE status = 'Active' {conditions}
#     """.format(conditions=conditions), filter_values, as_dict=1)

#     if not employees:
#         return []

#     employee_ids = [emp["name"] for emp in employees]

#     # Fetching leave balances
#     leave_types = ["Casual Leave", "Medical Leave", "Earned Leave", "Recreational Leave"]
#     leave_data = frappe.db.sql("""
#         SELECT employee, leave_type, SUM(leaves) AS allocated, SUM(used) AS availed
#         FROM `tabLeave Ledger Entry`
#         WHERE employee IN %(employees)s AND leave_type IN %(leave_types)s
#         GROUP BY employee, leave_type
#     """, {"employees": employee_ids, "leave_types": leave_types}, as_dict=1)

#     leave_lookup = {emp: {} for emp in employee_ids}
#     for row in leave_data:
#         leave_lookup[row.employee][row.leave_type] = {
#             "allocated": row.allocated or 0,
#             "availed": row.availed or 0,
#             "balance": (row.allocated or 0) - (row.availed or 0),
#         }

#     # Fetching attendance data
#     attendance_data = frappe.db.sql("""
#         SELECT employee, SUM(late_entry) AS late_count, SUM(early_exit) AS early_count,
#             SUM(CASE WHEN (custom_in_times IS NULL OR custom_out_times IS NULL) THEN 1 ELSE 0 END) AS missing_count,
#             COUNT(*) AS total
#         FROM `tabAttendance`
#         WHERE employee IN %(employees)s AND attendance_date BETWEEN %(from_date)s AND %(to_date)s
#         GROUP BY employee
#     """, {"employees": employee_ids, "from_date": filters.get("from_date"), "to_date": filters.get("to_date")}, as_dict=1)

#     attendance_lookup = {emp: {"late_ded": 0, "early_ded": 0, "missing_ded": 0, "total": 0} for emp in employee_ids}
#     for row in attendance_data:
#         attendance_lookup[row.employee] = {
#             "late_ded": row.late_count or 0,
#             "early_ded": row.early_count or 0,
#             "missing_ded": row.missing_count or 0,
#             "total": row.total or 0,
#         }

#     # Fetching holiday counts
#     holidays_data = frappe.db.sql("""
#         SELECT e.name AS employee, COUNT(h.holiday_date) AS holidays
#         FROM `tabEmployee` e
#         LEFT JOIN `tabHoliday` h ON e.holiday_list = h.parent
#         WHERE e.name IN %(employees)s AND h.holiday_date BETWEEN %(from_date)s AND %(to_date)s
#         GROUP BY e.name
#     """, {"employees": employee_ids, "from_date": filters.get("from_date"), "to_date": filters.get("to_date")}, as_dict=1)

#     holiday_lookup = {emp: 0 for emp in employee_ids}
#     for row in holidays_data:
#         holiday_lookup[row.employee] = row.holidays or 0

#     # Calculating final report data
#     data = []
#     for emp in employees:
#         casual_leave = leave_lookup.get(emp["name"], {}).get("Casual Leave", {"allocated": 0, "availed": 0, "balance": 0})
#         medical_leave = leave_lookup.get(emp["name"], {}).get("Medical Leave", {"allocated": 0, "availed": 0, "balance": 0})
#         earned_leave = leave_lookup.get(emp["name"], {}).get("Earned Leave", {"allocated": 0, "availed": 0, "balance": 0})

#         attendance = attendance_lookup.get(emp["name"], {"late_ded": 0, "early_ded": 0, "missing_ded": 0, "total": 0})
#         holidays = holiday_lookup.get(emp["name"], 0)

#         days_in_range = (filters.get("to_date") - filters.get("from_date")).days + 1
#         absent_days = max(days_in_range - holidays - attendance["total"], 0)
#         paid_days = attendance["total"] + holidays

#         data.append([
#             emp["name"], emp["employee_name"], emp["branch"], emp["department"], emp["designation"], emp["employment_type"],
#             casual_leave["allocated"], casual_leave["availed"], casual_leave["balance"],
#             medical_leave["allocated"], medical_leave["availed"], medical_leave["balance"],
#             earned_leave["allocated"], earned_leave["availed"], earned_leave["balance"],
#             attendance["late_ded"], attendance["early_ded"], attendance["missing_ded"],
#             absent_days, paid_days
#         ])

#     return data

