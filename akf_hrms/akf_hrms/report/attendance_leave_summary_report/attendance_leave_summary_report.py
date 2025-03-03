# Developer Mubashir Bashir

from __future__ import unicode_literals
import frappe
from frappe import _
from datetime import datetime

def execute(filters=None):
    columns, data = [], []
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
        _("Casual Leave Allowed") + ":Data:220",
        _("Casual Leave Availed") + ":Data:220",
        _("Casual Leave Balance") + ":Data:220",
        _("Medical Leave Allowed") + ":Data:220",
        _("Medical Leave Availed") + ":Data:220",
        _("Medical Leave Balance") + ":Data:220",
        _("Earned/Recreational Leave Allowed") + ":Data:220",
        _("Earned/Recreational Leave Availed") + ":Data:220",
        _("Earned/Recreational Leave Balance") + ":Data:220",
        _("Late Ded") + ":Data:120",
        _("Early Ded") + ":Data:120",
        _("Missing Ded") + ":Data:120",
        _("Absent") + ":Data:120",
        _("Paid Days") + ":Data:120",
    ]

def get_employee_data(filters):
    conditions = get_conditions(filters)

    # Main query to fetch employee_data, leave_balances, and attendance_counts
    query = """
        WITH FinalBalance AS (
            SELECT 
                e.name AS employee,
                e.employee_name,
                e.branch,
                e.department,
                e.designation,
                e.employment_type AS status,
                le.leave_type,
                SUM(CASE WHEN le.transaction_type = 'Leave Allocation' THEN le.leaves ELSE 0 END) AS allocated_leaves,
                SUM(CASE WHEN le.transaction_type = 'Leave Application' THEN (-1 * le.leaves) ELSE 0 END) AS used_leaves
            FROM 
                `tabEmployee` e
            LEFT JOIN 
                `tabLeave Ledger Entry` le ON e.name = le.employee
            WHERE 
                e.status = 'Active'
                AND e.custom_no_attendance = 0
                {conditions}
                AND (
                    %(from_date)s BETWEEN le.from_date AND le.to_date
                    OR le.to_date <= %(to_date)s
                )
                AND le.leave_type IN ('Casual Leave', 'Medical Leave', 'Earned Leave', 'Recreational Leave')
            GROUP BY 
                e.name, le.leave_type
        ),
        AttendanceSummary AS (
            SELECT 
                a.employee,
                SUM(CASE WHEN a.late_entry = 1 AND a.status = 'Present' THEN 1 ELSE 0 END) AS late_count,
                SUM(CASE WHEN a.early_exit = 1 THEN 1 ELSE 0 END) AS early_count,
                SUM(CASE WHEN (a.custom_in_times IS NULL OR a.custom_out_times IS NULL) THEN 1 ELSE 0 END) AS missing_count,
                SUM(CASE WHEN a.leave_type = 'Leave Without Pay' THEN 1 ELSE 0 END) AS lwp_count,
                COUNT(*) AS total_attendance
            FROM 
                `tabAttendance` a
            WHERE 
                a.attendance_date BETWEEN %(from_date)s AND %(to_date)s
            GROUP BY 
                a.employee
        ),
        HolidayCount AS (
            SELECT 
                e.name AS employee,
                COUNT(h.holiday_date) AS holiday_count
            FROM 
                `tabEmployee` e
            LEFT JOIN 
                `tabHoliday` h ON e.holiday_list = h.parent
            WHERE 
                h.holiday_date BETWEEN %(from_date)s AND %(to_date)s
            GROUP BY 
                e.name
        )
        SELECT 
            e.name AS employee,
            e.employee_name,
            e.branch,
            e.department,
            e.designation,
            e.employment_type,
            COALESCE(SUM(CASE WHEN fb.leave_type = 'Casual Leave' THEN fb.allocated_leaves ELSE 0 END), 0) AS casual_leave_allowed,
            COALESCE(SUM(CASE WHEN fb.leave_type = 'Casual Leave' THEN fb.used_leaves ELSE 0 END), 0) AS casual_leave_availed,
            COALESCE(SUM(CASE WHEN fb.leave_type = 'Casual Leave' THEN (fb.allocated_leaves - fb.used_leaves) ELSE 0 END), 0) AS casual_leave_balance,
            COALESCE(SUM(CASE WHEN fb.leave_type = 'Medical Leave' THEN fb.allocated_leaves ELSE 0 END), 0) AS medical_leave_allowed,
            COALESCE(SUM(CASE WHEN fb.leave_type = 'Medical Leave' THEN fb.used_leaves ELSE 0 END), 0) AS medical_leave_availed,
            COALESCE(SUM(CASE WHEN fb.leave_type = 'Medical Leave' THEN (fb.allocated_leaves - fb.used_leaves) ELSE 0 END), 0) AS medical_leave_balance,
            COALESCE(SUM(CASE WHEN fb.leave_type IN ('Earned Leave', 'Recreational Leave') THEN fb.allocated_leaves ELSE 0 END), 0) AS earned_recreational_leave_allowed,
            COALESCE(SUM(CASE WHEN fb.leave_type IN ('Earned Leave', 'Recreational Leave') THEN fb.used_leaves ELSE 0 END), 0) AS earned_recreational_leave_availed,
            COALESCE(SUM(CASE WHEN fb.leave_type IN ('Earned Leave', 'Recreational Leave') THEN (fb.allocated_leaves - fb.used_leaves) ELSE 0 END), 0) AS earned_recreational_leave_balance,
            COALESCE(a.late_count, 0) AS late_ded,
            COALESCE(a.early_count, 0) AS early_ded,
            COALESCE(a.missing_count, 0) AS missing_ded,
            COALESCE((DATEDIFF(%(to_date)s, %(from_date)s) + 1 - COALESCE(h.holiday_count, 0) - COALESCE(a.total_attendance, 0) + COALESCE(a.lwp_count, 0)), 0) AS absent,
            COALESCE((DATEDIFF(%(to_date)s, %(from_date)s) + 1 - (DATEDIFF(%(to_date)s, %(from_date)s) + 1 - COALESCE(h.holiday_count, 0) - COALESCE(a.total_attendance, 0) + COALESCE(a.lwp_count, 0))), 0) AS paid_days
        FROM 
            `tabEmployee` e
        LEFT JOIN 
            FinalBalance fb ON e.name = fb.employee
        LEFT JOIN 
            AttendanceSummary a ON e.name = a.employee
        LEFT JOIN 
            HolidayCount h ON e.name = h.employee
        WHERE 
            e.status = 'Active'
            AND e.custom_no_attendance = 0
            {conditions}
        GROUP BY 
            e.name, e.employee_name, e.branch, e.department, e.designation, e.employment_type
    """.format(conditions=conditions)

    data = frappe.db.sql(query, filters, as_dict=1)

    # Format the final result
    result = []
    for emp in data:
        result.append([
            emp.employee,
            emp.employee_name,
            emp.branch,
            emp.department,
            emp.designation,
            emp.status,
            emp.casual_leave_allowed,
            emp.casual_leave_availed,
            emp.casual_leave_balance,
            emp.medical_leave_allowed,
            emp.medical_leave_availed,
            emp.medical_leave_balance,
            emp.earned_recreational_leave_allowed,
            emp.earned_recreational_leave_availed,
            emp.earned_recreational_leave_balance,
            emp.late_ded,
            emp.early_ded,
            emp.missing_ded,
            emp.absent,
            emp.paid_days
        ])

    return result

def get_conditions(filters):
    conditions = ""
    if filters.get("company"):
        conditions += " AND e.company = %(company)s"
    if filters.get("employee"):
        conditions += " AND e.name = %(employee)s"
    if filters.get("branch"):
        conditions += " AND e.branch = %(branch)s"
    if filters.get("department"):
        conditions += " AND e.department = %(department)s"
    if filters.get("designation"):
        conditions += " AND e.designation = %(designation)s"
    if filters.get("employment_type"):
        conditions += " AND e.employment_type = %(employment_type)s"
    return conditions



# |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
# |||///////////////////////////////////////////////////////////////////////////////////|||
# |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||

# from __future__ import unicode_literals

# from akf_hrms.overrides.leave_application import get_leave_details
# import frappe
# from frappe import _
# def execute(filters=None):

# 	columns, data = [], []
# 	columns = get_employee_columns()
# 	data = get_employee_data(filters)
# 	return columns, data

# def get_employee_columns():
# 	return [
# 		_("ID") + ":Link/Employee:120",
# 		_("Name") + ":Data:120",
# 		_("Branch") + ":Link/Branch:120",
# 		_("Department") + ":Link/Department:120",
# 		_("Designation") + ":Link/Designation:120",
# 		_("Status") + ":Data:120",
# 		_("Casual Leave Allowed") + ":Data:220",
# 		_("Casual Leave Availed") + ":Data:220",
# 		_("Casual Leave Balance") + ":Data:220",
# 		_("Medical Leave Allowed") + ":Data:220",
# 		_("Medical Leave Availed") + ":Data:220",
# 		_("Medical Leave Balance") + ":Data:220",
# 		_("Earned/Recreational Leave Allowed") + ":Data:220",
# 		_("Earned/Recreational Leave Availed") + ":Data:220",
# 		_("Earned/Recreational Leave Balance") + ":Data:220",
# 		_("Late.Ded") + ":Data:120",
# 		_("Early.Ded") + ":Data:120",
# 		_("Missing.Ded") + ":Data:120",
# 		_("Absent") + ":Data:120",
# 		_("Paid Days") + ":Data:120",
# 	]
# # 

# # updated on 31-12-2024
# def get_employee_data(filters):
#     conditions = get_conditions(filters)

#     # Get base employee data
#     emp_record = """
#         SELECT 
#             e.name, e.employee_name, e.branch, e.department, e.designation, e.employment_type,
#             COALESCE(e.holiday_list, '') as _holiday_list
#         FROM `tabEmployee` as e
#         WHERE {condition} AND e.custom_no_attendance != 1 AND e.status = 'Active'
#     """.format(condition=conditions)

#     data = frappe.db.sql(emp_record, filters, as_dict=1)

#     for emp in data:
#         # Get leave details using the imported function
#         leave_details = get_leave_details(emp.name, filters.get('from_date'))
#         leave_allocation = leave_details.get('leave_allocation', {})

#         # Initialize leave counts
#         leave_counts = {
#             'Casual Leave': {'allowed': 0, 'availed': 0, 'balance': 0},
#             'Medical Leave': {'allowed': 0, 'availed': 0, 'balance': 0},
#             'Earned Leave': {'allowed': 0, 'availed': 0, 'balance': 0},
#             'Recreational Leave': {'allowed': 0, 'availed': 0, 'balance': 0}
#         }

#         # Update leave counts from leave_details
#         for leave_type, details in leave_allocation.items():
#             if leave_type in leave_counts:
#                 leave_counts[leave_type]['allowed'] = details.get('total_leaves', 0)
#                 leave_counts[leave_type]['availed'] = details.get('leaves_taken', 0)
#                 leave_counts[leave_type]['balance'] = details.get('remaining_leaves', 0)

#         # Calculate combined Earned/Recreational leave
#         combined_earned_allowed = (leave_counts['Earned Leave']['allowed'] + 
#                                 leave_counts['Recreational Leave']['allowed'])
#         combined_earned_availed = (leave_counts['Earned Leave']['availed'] + 
#                                 leave_counts['Recreational Leave']['availed'])
#         combined_earned_balance = (leave_counts['Earned Leave']['balance'] + 
#                                 leave_counts['Recreational Leave']['balance'])

#         # Get attendance related counts
#         attendance_counts = frappe.db.sql("""
#             SELECT 
#                 COALESCE(SUM(CASE WHEN late_entry = 1 AND status = 'Present' THEN 1 ELSE 0 END), 0) as late_count,
#                 COALESCE(SUM(CASE WHEN early_exit = 1 THEN 1 ELSE 0 END), 0) as early_count,
#                 COALESCE(SUM(CASE WHEN (custom_in_times IS NULL OR custom_out_times IS NULL) THEN 1 ELSE 0 END), 0) as missing_count,
#                 COALESCE(SUM(CASE WHEN leave_type = 'Leave Without Pay' THEN 1 ELSE 0 END), 0) as lwp_count,
#                 COALESCE(COUNT(*), 0) as total_attendance
#             FROM `tabAttendance`
#             WHERE employee = %s 
#             AND attendance_date BETWEEN %s AND %s
#         """, (emp.name, filters.get('from_date'), filters.get('to_date')), as_dict=1)[0]

#         # Get holidays
#         holiday_count = 0
#         if emp._holiday_list:
#             holidays = frappe.db.sql("""
#                 SELECT COALESCE(COUNT(*), 0) as holiday_count
#                 FROM `tabHoliday`
#                 WHERE parent = %s 
#                 AND holiday_date BETWEEN %s AND %s
#             """, (emp._holiday_list, filters.get('from_date'), filters.get('to_date')), as_dict=1)[0]
#             holiday_count = holidays.holiday_count or 0

#         # Calculate total days in period
#         from datetime import datetime
#         from_date = datetime.strptime(filters.get('from_date'), '%Y-%m-%d')
#         to_date = datetime.strptime(filters.get('to_date'), '%Y-%m-%d')
#         total_days = (to_date - from_date).days + 1

#         # Calculate absent days
#         absent_days = (total_days - holiday_count - 
#                       attendance_counts.total_attendance + 
#                       attendance_counts.lwp_count)

#         # Calculate paid days
#         paid_days = total_days - absent_days

#         # Update employee record with all calculated values
#         emp.update({
#             'name': emp.name,
#             'employee_name': emp.employee_name,
#             'branch': emp.branch,
#             'department': emp.department,
#             'designation': emp.designation,
#             'status': emp.employment_type,
#             'casual_leave_allowed': leave_counts['Casual Leave']['allowed'],
#             'casual_leave_availed': leave_counts['Casual Leave']['availed'],
#             'casual_leave_balance': leave_counts['Casual Leave']['balance'],
#             'medical_leave_allowed': leave_counts['Medical Leave']['allowed'],
#             'medical_leave_availed': leave_counts['Medical Leave']['availed'],
#             'medical_leave_balance': leave_counts['Medical Leave']['balance'],
#             'earned_leave_allowed': combined_earned_allowed,
#             'earned_leave_availed': combined_earned_availed,
#             'earned_leave_balance': combined_earned_balance,
#             'late_ded': attendance_counts.late_count,
#             'early_ded': attendance_counts.early_count,
#             'missing_ded': attendance_counts.missing_count,
#             'absent': absent_days,
#             'paid_days': paid_days
#         })

#     # Format the final result
#     result = []
#     for emp in data:
#         result.append([
#             emp.name,
#             emp.employee_name,
#             emp.branch,
#             emp.department,
#             emp.designation,
#             emp.status,
#             emp.casual_leave_allowed,
#             emp.casual_leave_availed,
#             emp.casual_leave_balance,
#             emp.medical_leave_allowed,
#             emp.medical_leave_availed,
#             emp.medical_leave_balance,
#             emp.earned_leave_allowed,
#             emp.earned_leave_availed,
#             emp.earned_leave_balance,
#             emp.late_ded,
#             emp.early_ded,
#             emp.missing_ded,
#             emp.absent,
#             emp.paid_days
#         ])

#     return result

# def get_conditions(filters):
# 	conditions = ""
# 	if filters.get("company"):
# 		conditions += " e.company = %(company)s"
# 	if filters.get("employee"):
# 		conditions += " and e.employee = %(employee)s"
# 	if filters.get("branch"):
# 		conditions += " and e.branch = %(branch)s"
# 	if filters.get("department"):
# 		conditions += " and e.department = %(department)s"
# 	if filters.get("designation"):
# 		conditions += " and e.designation = %(designation)s"
# 	if filters.get("status"):
# 		conditions += " and e.employment_type = %(status)s"
	
# 	return conditions




"""

WITH FinalBalance AS (
    Select e.employee, e.employee_name, e.branch, e.department, e.designation, e.employment_type, le.leave_type, 
    sum(case when (le.transaction_type="Leave Allocation") then le.leaves else 0 end) allocated_leaves,
    sum(case when (le.transaction_type="Leave Application") then (-1 * le.leaves) else 0 end) used_leaves
    From 
        `tabEmployee` e inner join `tabLeave Ledger Entry` le on (e.name=le.employee)

    Where 
        e.status = 'Active'
        and e.custom_no_attendance=0
        and e.company = {filters.company}
        and ("2024-12-20" between  le.from_date and le.to_date || le.to_date<="2024-12-20")
        and e.employee= {filters.employee}
        and le.leave_type = "Casual Leave" || "Medical Leave" || Earned Leave || Recreational Leave
)
SELECT 
    leave_type, allocated_leaves,
    used_leaves,
    (allocated_leaves- used_leaves) as balance
FROM FinalBalance;


"""