# Developer Mubashir Bashir


from __future__ import unicode_literals

from akf_hrms.overrides.leave_application import get_leave_details
import frappe
from frappe import _
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
		_("Late.Ded") + ":Data:120",
		_("Early.Ded") + ":Data:120",
		_("Missing.Ded") + ":Data:120",
		_("Absent") + ":Data:120",
		_("Paid Days") + ":Data:120",
	]
# 

# updated on 31-12-2024
def get_employee_data(filters):
    conditions = get_conditions(filters)

    # Get base employee data
    emp_record = """
        SELECT 
            e.name, e.employee_name, e.branch, e.department, e.designation, e.employment_type,
            COALESCE(e.holiday_list, '') as _holiday_list
        FROM `tabEmployee` as e
        WHERE {condition}
    """.format(condition=conditions)

    data = frappe.db.sql(emp_record, filters, as_dict=1)

    for emp in data:
        # Get leave details using the imported function
        leave_details = get_leave_details(emp.name, filters.get('from_date'))
        leave_allocation = leave_details.get('leave_allocation', {})

        # Initialize leave counts
        leave_counts = {
            'Casual Leave': {'allowed': 0, 'availed': 0, 'balance': 0},
            'Medical Leave': {'allowed': 0, 'availed': 0, 'balance': 0},
            'Earned Leave': {'allowed': 0, 'availed': 0, 'balance': 0},
            'Recreational Leave': {'allowed': 0, 'availed': 0, 'balance': 0}
        }

        # Update leave counts from leave_details
        for leave_type, details in leave_allocation.items():
            if leave_type in leave_counts:
                leave_counts[leave_type]['allowed'] = details.get('total_leaves', 0)
                leave_counts[leave_type]['availed'] = details.get('leaves_taken', 0)
                leave_counts[leave_type]['balance'] = details.get('remaining_leaves', 0)

        # Calculate combined Earned/Recreational leave
        combined_earned_allowed = (leave_counts['Earned Leave']['allowed'] + 
                                leave_counts['Recreational Leave']['allowed'])
        combined_earned_availed = (leave_counts['Earned Leave']['availed'] + 
                                leave_counts['Recreational Leave']['availed'])
        combined_earned_balance = (leave_counts['Earned Leave']['balance'] + 
                                leave_counts['Recreational Leave']['balance'])

        # Get attendance related counts
        attendance_counts = frappe.db.sql("""
            SELECT 
                COALESCE(SUM(CASE WHEN late_entry = 1 AND status = 'Present' THEN 1 ELSE 0 END), 0) as late_count,
                COALESCE(SUM(CASE WHEN early_exit = 1 THEN 1 ELSE 0 END), 0) as early_count,
                COALESCE(SUM(CASE WHEN (custom_in_times IS NULL OR custom_out_times IS NULL) THEN 1 ELSE 0 END), 0) as missing_count,
                COALESCE(SUM(CASE WHEN leave_type = 'Leave Without Pay' THEN 1 ELSE 0 END), 0) as lwp_count,
                COALESCE(COUNT(*), 0) as total_attendance
            FROM `tabAttendance`
            WHERE employee = %s 
            AND attendance_date BETWEEN %s AND %s
        """, (emp.name, filters.get('from_date'), filters.get('to_date')), as_dict=1)[0]

        # Get holidays
        holiday_count = 0
        if emp._holiday_list:
            holidays = frappe.db.sql("""
                SELECT COALESCE(COUNT(*), 0) as holiday_count
                FROM `tabHoliday`
                WHERE parent = %s 
                AND holiday_date BETWEEN %s AND %s
            """, (emp._holiday_list, filters.get('from_date'), filters.get('to_date')), as_dict=1)[0]
            holiday_count = holidays.holiday_count or 0

        # Calculate total days in period
        from datetime import datetime
        from_date = datetime.strptime(filters.get('from_date'), '%Y-%m-%d')
        to_date = datetime.strptime(filters.get('to_date'), '%Y-%m-%d')
        total_days = (to_date - from_date).days + 1

        # Calculate absent days
        absent_days = (total_days - holiday_count - 
                      attendance_counts.total_attendance + 
                      attendance_counts.lwp_count)

        # Calculate paid days
        paid_days = total_days - absent_days

        # Update employee record with all calculated values
        emp.update({
            'name': emp.name,
            'employee_name': emp.employee_name,
            'branch': emp.branch,
            'department': emp.department,
            'designation': emp.designation,
            'status': emp.employment_type,
            'casual_leave_allowed': leave_counts['Casual Leave']['allowed'],
            'casual_leave_availed': leave_counts['Casual Leave']['availed'],
            'casual_leave_balance': leave_counts['Casual Leave']['balance'],
            'medical_leave_allowed': leave_counts['Medical Leave']['allowed'],
            'medical_leave_availed': leave_counts['Medical Leave']['availed'],
            'medical_leave_balance': leave_counts['Medical Leave']['balance'],
            'earned_leave_allowed': combined_earned_allowed,
            'earned_leave_availed': combined_earned_availed,
            'earned_leave_balance': combined_earned_balance,
            'late_ded': attendance_counts.late_count,
            'early_ded': attendance_counts.early_count,
            'missing_ded': attendance_counts.missing_count,
            'absent': absent_days,
            'paid_days': paid_days
        })

    # Format the final result
    result = []
    for emp in data:
        result.append([
            emp.name,
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
            emp.earned_leave_allowed,
            emp.earned_leave_availed,
            emp.earned_leave_balance,
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
		conditions += " e.company = %(company)s"
	if filters.get("employee"):
		conditions += " and e.employee = %(employee)s"
	if filters.get("branch"):
		conditions += " and e.branch = %(branch)s"
	if filters.get("department"):
		conditions += " and e.department = %(department)s"
	if filters.get("designation"):
		conditions += " and e.designation = %(designation)s"
	if filters.get("status"):
		conditions += " and e.employment_type = %(status)s"
	
	return conditions
