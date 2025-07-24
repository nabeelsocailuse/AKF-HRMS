# Developer Mubashir Bashir

from __future__ import unicode_literals

from akf_hrms.overrides.leave_application.leave_application import get_leave_details
import frappe
from frappe import _
from frappe.utils import (
	get_first_day
)

def execute(filters=None):
	columns, data = [], []
	columns = get_employee_columns()
	data = get_employee_data(filters)
	return columns, data

def get_employee_columns():
	return [
		_("ID") + ":Link/Employee:220",
		_("Name") + ":Data:220",
		_("Branch") + ":Link/Branch:220",
		_("Department") + ":Link/Department:220",
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
		_("Late Entry") + ":Data:120",
		_("Early Exit") + ":Data:120",
		_("Missing Attendance") + ":Data:120",
		# _("Leaves Deduction") + ":Data:120",
		_("Late Entry Deduction") + ":Data:120",
		_("Early Exit Deduction") + ":Data:120",
		_("Absent") + ":Data:120",
		_("Payment Days") + ":Data:120",
		_("Actual Payment Days") + ":Data:120",
		_("Late Dates") + ":Data:200:Hidden",
		_("Early Dates") + ":Data:200:Hidden",
		_("Missing Dates") + ":Data:200:Hidden",
		_("Late Entry Deduction Dates") + ":Data:200:Hidden",
		_("Early Exit Deduction Dates") + ":Data:200:Hidden",
		# _("Leaves Deduction Dates") + ":Data:200:Hidden",
		_("Absent Dates") + ":Data:200:Hidden",
		_("Payment Dates") + ":Data:200:Hidden"
	]

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

def get_employee_data(filters):
	conditions = get_conditions(filters)
	
	lateEntryDeduction = get_late_entry_deduction(filters)
	earlyExitDeduction = get_early_exit_deduction(filters)
	
	# Get base employee data
	emp_record = """
		SELECT 
			e.name, e.employee_name, e.branch, e.department, e.designation, e.employment_type,
			COALESCE(e.holiday_list, '') as _holiday_list
		FROM `tabEmployee` as e
		WHERE {condition} AND e.custom_no_attendance != 1 AND e.status = 'Active'
	""".format(condition=conditions)

	data = frappe.db.sql(emp_record, filters, as_dict=1)

	for emp in data:
		# Get leave details using the imported function
		leave_details = get_leave_details(emp.name, filters.get('from_date'))
		leave_allocation = leave_details.get('leave_allocation', {})

<<<<<<< Updated upstream
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
=======
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
>>>>>>> Stashed changes

		# Calculate combined Earned/Recreational leave
		combined_earned_allowed = (leave_counts['Earned Leave']['allowed'] + 
								   leave_counts['Recreational Leave']['allowed'])
		combined_earned_availed = (leave_counts['Earned Leave']['availed'] + 
								   leave_counts['Recreational Leave']['availed'])
		combined_earned_balance = (leave_counts['Earned Leave']['balance'] + 
								   leave_counts['Recreational Leave']['balance'])

		# Get attendance related counts and dates
		attendance_details = frappe.db.sql("""
			SELECT
				COALESCE(COUNT(*), 0) as total_attendance,
				COALESCE(SUM(CASE WHEN leave_type = 'Leave Without Pay' THEN 1 ELSE 0 END), 0) as lwp_count, 
				COALESCE(SUM(CASE WHEN late_entry = 1 AND status = 'Present' THEN 1 ELSE 0 END), 0) as late_count,
				COALESCE(SUM(CASE WHEN early_exit = 1 THEN 1 ELSE 0 END), 0) as early_count,
				COALESCE(SUM(CASE WHEN (custom_in_times IS NULL OR custom_out_times IS NULL) THEN 1 ELSE 0 END), 0) as missing_count,
				GROUP_CONCAT(DISTINCT CASE WHEN late_entry = 1 AND status = 'Present' THEN attendance_date END) as late_dates,
				GROUP_CONCAT(DISTINCT CASE WHEN early_exit = 1 THEN attendance_date END) as early_dates,
				GROUP_CONCAT(DISTINCT CASE WHEN (custom_in_times IS NULL OR custom_out_times IS NULL) THEN attendance_date END) as missing_dates
			FROM `tabAttendance`
			WHERE employee = %s 
			AND attendance_date BETWEEN %s AND %s
		""", (emp.name, filters.get('from_date'), filters.get('to_date')), as_dict=1)[0]

		# Get leaves deduction details
		# leaves_deduction_details = frappe.db.sql("""
		# 	SELECT 
		# 		COALESCE(SUM(total_deduction), 0) as total_leaves_deduction,
		# 		GROUP_CONCAT(DISTINCT posting_date) as leaves_deduction_dates
		# 	FROM `tabDeduction Ledger Entry`
		# 	WHERE employee = %s 
		# 	AND company = %s
		# 	AND posting_date BETWEEN %s AND %s
		# """, (emp.name, filters.get('company'), filters.get('deduction_from_date'), filters.get('deduction_to_date')), as_dict=1)[0]

		# Get holidays
		holiday_count = 0
		holiday_dates = []
		if emp._holiday_list:
			holidays = frappe.db.sql("""
				SELECT holiday_date
				FROM `tabHoliday`
				WHERE parent = %s 
				AND holiday_date BETWEEN %s AND %s
			""", (emp._holiday_list, filters.get('from_date'), filters.get('to_date')), as_dict=1)
			holiday_count = len(holidays)
			holiday_dates = [h.holiday_date.strftime('%Y-%m-%d') for h in holidays]

		# Get all dates in the range
		from datetime import datetime, timedelta
		from_date = datetime.strptime(filters.get('from_date'), '%Y-%m-%d')
		to_date = datetime.strptime(filters.get('to_date'), '%Y-%m-%d')
		total_days = (to_date - from_date).days + 1
		
		# Get all dates in the range
		all_dates = []
		current_date = from_date
		while current_date <= to_date:
			all_dates.append(current_date.strftime('%Y-%m-%d'))
			current_date += timedelta(days=1)

		# Get attendance records
		attendance_records = frappe.db.sql("""
			SELECT attendance_date, status, leave_type
			FROM `tabAttendance`
			WHERE employee = %s 
			AND attendance_date BETWEEN %s AND %s
		""", (emp.name, filters.get('from_date'), filters.get('to_date')), as_dict=1)

		# Create a dictionary of attendance records for easy lookup
		attendance_dict = {}
		for record in attendance_records:
			# Convert date to string format for dictionary key
			date_str = record.attendance_date.strftime('%Y-%m-%d')
			attendance_dict[date_str] = {
				'status': record.status,
				'leave_type': record.leave_type
			}

		# Calculate absent dates and payment dates
		absent_dates = []
		payment_dates = []

		for date in all_dates:
			# Check if it's a holiday first
			if date in holiday_dates:
				payment_dates.append(date)
				continue

			# Then check attendance record for this date
			if date in attendance_dict:
				record = attendance_dict[date]
				if record['status'] == 'Present' or record['status'] == 'Half Day' or (record['status'] == 'On Leave' and record['leave_type'] != 'Leave Without Pay'):
					payment_dates.append(date)
				else:
					absent_dates.append(date)
			else:
				# No attendance record found, mark as absent
				absent_dates.append(date)

		# Calculate absent days and payment days
		absent_days = len(absent_dates)
		payment_days = len(payment_dates)

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
			'late_entry': attendance_details.late_count,
			'early_exit': attendance_details.early_count,
			'missing_attendance': attendance_details.missing_count,
			# 'leaves_deduction': leaves_deduction_details.total_leaves_deduction,
			'absent': absent_days,
			'payment_days': payment_days,
			'actual_payment_days': payment_days,
			'late_dates': attendance_details.get('late_dates', ''),
			'early_dates': attendance_details.get('early_dates', ''),
			'missing_dates': attendance_details.get('missing_dates', ''),
			# 'leaves_deduction_dates': leaves_deduction_details.leaves_deduction_dates,
			'absent_dates': ','.join(absent_dates),
			'payment_dates': ','.join(payment_dates)
		})

	# Format the final result
	result = []
	for emp in data:
		employeeID = emp.name
		lateDedDates = ''
		earlyDedDates = ''
		lateDedTotal = 0
		earlyDedTotal = 0
		
		if(employeeID in lateEntryDeduction): 
			lateDedTotal = lateEntryDeduction[employeeID][0] or 0
			lateDedDates = lateEntryDeduction[employeeID][1] or ''
		if(employeeID in earlyExitDeduction): 
			earlyDedTotal = earlyExitDeduction[employeeID][0] or 0
			earlyDedDates = earlyExitDeduction[employeeID][1] or ''
		
		payment_days = emp.payment_days
		actual_payment_days = payment_days - (lateDedTotal + earlyDedTotal)
			
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
			emp.late_entry,
			emp.early_exit,
			emp.missing_attendance,
			# emp.leaves_deduction,
			
			lateDedTotal,
			earlyDedTotal,

			emp.absent,
			payment_days,
			actual_payment_days,
			emp.late_dates,
			emp.early_dates,
			emp.missing_dates,
			lateDedDates,
			earlyDedDates,
			# emp.leaves_deduction_dates,
			emp.absent_dates,
			emp.payment_dates
		])

	return result

# bench --site erp.alkhidmat.org execute akf_hrms.akf_hrms.report.attendance_leave_summary.attendance_leave_summary.get_late_entry_deduction
def get_late_entry_deduction(filters=None):
	# company = filters.get("company")
	# start_date = filters.get("from_date")
	# end_date = filters.get("to_date")
	# company = "Alkhidmat Foundation Pakistan"
	# start_date = "2025-06-21"
	# end_date = "2025-07-20"
	data = frappe.db.sql(""" 
				Select 
					employee, ifnull(sum(total_deduction),0) as total, 
					GROUP_CONCAT(DISTINCT posting_date) as deduction_dates 
				From `tabDeduction Ledger Entry` 
				Where case_no in (1,2,3)
					and company = %(company)s
					and posting_date between %(from_date)s and %(to_date)s
				Group by employee
			   """, filters, as_dict=1)
	
	dleDict = frappe._dict()

	for d in data:
		dleDict.update({f'{d.employee}': [d.total, d.deduction_dates]})
	
	return dleDict

# bench --site erp.alkhidmat.org execute akf_hrms.akf_hrms.report.attendance_leave_summary.attendance_leave_summary.get_early_exit_deduction
def get_early_exit_deduction(filters=None):
	# company = filters.get("company")
	# end_date = filters.get("to_date")
	# start_date = get_first_day(end_date)
	
	data = frappe.db.sql(""" 
				Select 
					employee, ifnull(sum(total_deduction),0) as total, 
					GROUP_CONCAT(DISTINCT posting_date) as deduction_dates 
				From `tabDeduction Ledger Entry` 
				Where
					case_no in (4)
					and company = %(company)s
					and posting_date between %(from_date)s and %(to_date)s
				Group by employee              
			   """, filters, as_dict=1)
	
	dleDict = frappe._dict()
	
	for d in data:
		dleDict.update({f'{d.employee}': [d.total, d.deduction_dates]})
	
	return dleDict

