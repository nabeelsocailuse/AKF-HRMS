# Developer Mubashir Bashir

from __future__ import unicode_literals

# from akf_hrms.overrides.leave_application.leave_application import get_leave_details
import frappe
from frappe import _
from frappe.utils import (
	get_first_day,
	get_last_day,
	date_diff,
	add_to_date
)

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{	
			"label": "CNIC",
			"fieldname": "custom_cnic",
			"fieldtype": "Data",
			"options": "",
			"width": "180"
		},
		  {	
			"label": "ID",
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Employee",
			"width": "220"
		},
		{	
			"label": "Name",
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"options": "",
			"width": "220",
		},
		{
			"label": "Designation",
			"fieldname": "designation",
			"fieldtype": "Link",
			"options": "Designation",
			"width": "160"
		},
		{
			"label": "Department",
			"fieldname": "department",
			"fieldtype": "Link",
			"options": "Department",
			"width": "160"
		},
		{
			"label": "Employee Status",
			"fieldname": "employment_type",
			"fieldtype": "Link",
			"options": "Employment Type",
			"width": "160"
		},
		{
			"label": "(Cur) Late Entry",
			"fieldname": "late_entry_count",
			"fieldtype": "Float",
			"precision": "1",
			"width": "140"
		},
		{
			"label": "(Pre) Late Ded",
			"fieldname": "late_ded",
			"fieldtype": "Float",
			"precision": "1",
			"width": "140"
		},
		{
			"label": "Early Exit",
			"fieldname": "early_exit_count",
			"fieldtype": "Float",
			"precision": "1",
			"width": "130"
		},
		{
			"label": "Early Ded",
			"fieldname": "early_ded",
			"fieldtype": "Float",
			"precision": "1",
			"width": "120"
		},
		{
			"label": "Missing In-Out",
			"fieldname": "missing_in_out_count",
			"fieldtype": "Float",
			"precision": "1",
			"width": "130"
		},
		{
			"label": "Absents",
			"fieldname": "absents",
			"fieldtype": "float",
			"precision": "1",
			"width": "100"
		},
		{
			"label": "Total Days",
			"fieldname": "total_days",
			"fieldtype": "Float",
			"precision": "1",
			"width": "130"
		},
		{
			"label": "Total Ded",
			"fieldname": "total_deduction",
			"fieldtype": "Float",
			"precision": "1",
			"width": "130"
		},
		{
			"label": "Paid Days",
			"fieldname": "paid_days",
			"fieldtype": "float",
			"precision": "1",
			"width": "100"
		},
		{
			"label": "Fuel Days",
			"fieldname": "fuel_days",
			"fieldtype": "float",
			"precision": "1",
			"width": "100"
		},
		{
			"label": "Fuel Eligibility",
			"fieldname": "fuel_eligibility",
			"fieldtype": "Data",
			"precision": "1",
			"width": "100"
		},
		{
			"label": "HR Remarks",
			"fieldname": "hr_remarks",
			"fieldtype": "Data",
			"precision": "1",
			"width": "100"
		},
		{
			"label": "Late Entry Dates",
			"fieldname": "late_dates",
			"fieldtype": "Data",
			"width": "130",
			"hidden": 0
		},
		{
			"label": "Early Exit Dates",
			"fieldname": "early_dates",
			"fieldtype": "Data",
			"width": "130",
			"hidden": 0
		},
		{
			"label": "Missing In-Out Dates",
			"fieldname": "missing_dates",
			"fieldtype": "Data",
			"width": "130",
			"hidden": 0
		},
		{
			"label": "Absent Dates",
			"fieldname": "absent_dates",
			"fieldtype": "Data",
			"width": "130",
			"hidden": 0
		},
		{
			"label": "Late Ded Dates",
			"fieldname": "late_ded_dates",
			"fieldtype": "Data",
			"width": "130",
			"hidden": 0
		},
		  {
			"label": "Early Ded Dates",
			"fieldname": "early_ded_dates",
			"fieldtype": "Data",
			"width": "130",
			"hidden": 0
		},
		{
			"label": "Paid Dates",
			"fieldname": "paid_dates",
			"fieldtype": "Data",
			"width": "130",
			"hidden": 1
		},
		{
			"label": "Casual Leave Allowed",
			"fieldname": "casual_leaves_allowed",
			"fieldtype": "Float",
			"precision": "1",
			"width": "160"
		},
		{
			"label": "Casual Leave Availed",
			"fieldname": "casual_leaves_availed",
			"fieldtype": "Float",
			"precision": "1",
			"width": "160"
		},
		{
			"label": "Casual Leave Balance",
			"fieldname": "casual_leaves_balance",
			"fieldtype": "Float",
			"precision": "1",
			"width": "160"
		},
		{
			"label": "Medical Leave Allowed",
			"fieldname": "medical_leaves_allowed",
			"fieldtype": "Float",
			"precision": "1",
			"width": "160"
		},
		{
			"label": "Medical Leave Availed",
			"fieldname": "medical_leaves_availed",
			"fieldtype": "Float",
			"precision": "1",
			"width": "160"
		},
		{
			"label": "Medical Leave Balance",
			"fieldname": "medical_leaves_balance",
			"fieldtype": "Float",
			"precision": "1",
			"width": "160"
		},
		{
			"label": "Earned Leave Allowed",
			"fieldname": "earned_leaves_allowed",
			"fieldtype": "Float",
			"precision": "1",
			"width": "160"
		},
		{
			"label": "Earned Leave Availed",
			"fieldname": "earned_leaves_availed",
			"fieldtype": "Float",
			"precision": "1",
			"width": "160"
		},
		{
			"label": "Earned Leave Balance",
			"fieldname": "earned_leaves_balance",
			"fieldtype": "Float",
			"precision": "1",
			"width": "160"
		},
		{
			"label": "Recreational Leave Allowed",
			"fieldname": "recreational_leaves_allowed",
			"fieldtype": "Float",
			"precision": "1",
			"width": "160"
		},
		{
			"label": "Recreational Leave Availed",
			"fieldname": "recreational_leaves_availed",
			"fieldtype": "Float",
			"precision": "1",
			"width": "160"
		},
		{
			"label": "Recreational Leave Balance",
			"fieldname": "recreational_leaves_balance",
			"fieldtype": "Float",
			"precision": "1",
			"width": "160"
		},
	]

def get_conditions(filters):
	conditions = ""
	if filters.get("company"):
		conditions += " and e.company = %(company)s"
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
	if filters.get("no_attendance"):
		conditions += " and e.custom_no_attendance = %(no_attendance)s"

	return conditions

def get_data(filters):
	curMonthDays = get_current_month(filters)
	monthDates = get_21st_to_20th_of_month(filters)
	Employees = get_employees(filters)
	LeavesDetail = get_leaves_details(filters)
	HolidayLists = get_holiday_list(filters)
	Attendances = get_attendances(filters)
	lateEntryDeduction = get_late_entry_deduction(filters)
	earlyExitDeduction = get_early_exit_deduction(filters)
	fuelEligible = get_fuel_eligibility(filters)

	FROM_DATE = filters.get('from_date')
	LeaveType = ['Casual Leave', 'Medical Leave', 'Earned', 'Recreational Leave']
	data = []
	
	for emp in Employees:
		empId = emp.name
		no_attendance = emp.no_attendance
		# LEAVES
		leaves_allocation = LeavesDetail.get(empId, {})
		# emp.update({
		# 	'casual_leaves_balance': 0,
		# 	'medical_leaves_balance': 0,
		# 	'earned_leaves_balance': 0,
		# 	'recreational_leaves_balance': 0
		# })
		
		if('Casual Leave' in leaves_allocation):
			emp.update({
				'casual_leaves_allowed': leaves_allocation['Casual Leave'].get('allocated_leaves') or 0,
				'casual_leaves_availed': leaves_allocation['Casual Leave'].get('leaves_taken') or 0,
				'casual_leaves_balance': leaves_allocation['Casual Leave'].get('remaining_leaves') or 0,
			})
		if('Medical Leave'  in leaves_allocation):
			emp.update({
				'medical_leaves_allowed': leaves_allocation['Medical Leave'].get('allocated_leaves') or 0,
				'medical_leaves_availed': leaves_allocation['Medical Leave'].get('leaves_taken') or 0,
				'medical_leaves_balance': leaves_allocation['Medical Leave'].get('remaining_leaves') or 0
			})
		if('Earned' in leaves_allocation):
			emp.update({
				'earned_leaves_allowed': leaves_allocation['Earned'].get('allocated_leaves') or 0,
				'earned_leaves_availed': leaves_allocation['Earned'].get('leaves_taken') or 0,
				'earned_leaves_balance': leaves_allocation['Earned'].get('remaining_leaves')
			})
		if('Recreational Leave'  in leaves_allocation):
			emp.update({
				'recreational_leaves_allowed': leaves_allocation['Recreational Leave'].get('allocated_leaves') or 0,
				'recreational_leaves_availed': leaves_allocation['Recreational Leave'].get('leaves_taken') or 0,
				'recreational_leaves_balance': leaves_allocation['Recreational Leave'].get('remaining_leaves') or 0
			})
		
		# ATTENDANCE
		attendance_dates = []
		missing_dates = []
		if(empId in Attendances):
			att = Attendances[empId]
			emp.update(att)
			attendance_dates = att.get('attendance_dates') or []
			if(attendance_dates): 
				attendance_dates = attendance_dates.split(',')
			# Total of deductions from paid days
			missing_dates = att.get('missing_dates', "") or []
			if(missing_dates): 
				if("," in missing_dates): 
					missing_dates = missing_dates.split(',')
				else:
					missing_dates = [missing_dates]
				
		# HOLIDAYS
		holiday_dates = []
		if(emp.holiday_list in HolidayLists):
			holiday_dates = HolidayLists[emp.holiday_list]

		# Total Paid Days
		paid_dates_list = list(set(attendance_dates + holiday_dates))
		paid_dates_list.sort()


	
		# Total Absent Days
		absent_dates_list = [date for date in monthDates if(date not in paid_dates_list)]
		absent_dates_list.sort()

		# frappe.throw(f"{absent_dates_list}")
		# Remove missing logs
		paid_dates_list = [date for date in paid_dates_list if(date not in missing_dates)]

		# Total of deductions from paid days
		total_deduction = 0.0

		total_deduction += len(absent_dates_list)
		total_deduction += len(missing_dates)

		if(empId in lateEntryDeduction):
			late_ded = lateEntryDeduction[empId]
			emp.update(late_ded)
			total_deduction +=  late_ded.get("late_ded", 0.0)

		if(empId in earlyExitDeduction):
			early_ded = earlyExitDeduction[empId]
			emp.update(early_ded)
			total_deduction +=  early_ded.get("early_ded", 0.0)
		
		fuel_days = 0.0
		fuel_eligibility = "No"

		if(empId in fuelEligible):
			if(no_attendance):
				fuel_days = curMonthDays
			else:
				fuel_days = (curMonthDays - total_deduction)
			fuel_eligibility = "Yes"
		
		emp.update({
				'absents': 0.0 if(no_attendance) else len(absent_dates_list),
				'absent_dates': "" if(no_attendance) else ", ".join(absent_dates_list),
				'total_days': curMonthDays,
				'total_deduction': total_deduction,
				'paid_days': curMonthDays if(no_attendance) else (curMonthDays - total_deduction),
				# 'paid_dates': paid_dates_list,
				"fuel_days": fuel_days,		
				"fuel_eligibility": fuel_eligibility
		})
		
	return Employees
	
def get_current_month(filters):
	to_date = filters.get('to_date')
	from_date = get_first_day(to_date)
	to_date = get_last_day(to_date)
	days_in_month = date_diff(to_date, from_date) + 1

	return days_in_month

def get_21st_to_20th_of_month(filters):
	from_date = filters.get('from_date')
	to_date = filters.get('to_date')
	days_in_month = date_diff(to_date, from_date) + 1

	dates_list = []
	for day in range(days_in_month):
		dates_list.append(add_to_date(from_date, days=day))

	return dates_list

def get_employees(filters=None):
	return frappe.db.sql("""
			SELECT 
				e.name, 
				e.employee_name, 
				e.custom_cnic,
				e.branch, 
				   e.department, 
				  e.designation, 
				e.employment_type, 
				ifnull(e.holiday_list, '') as holiday_list,
				(e.custom_no_attendance) as no_attendance
			FROM 
				`tabEmployee` as e
			WHERE 
				e.status = 'Active'
				{condition} 
		""".format(condition=get_conditions(filters)), filters, as_dict=1)

# bench --site erp.alkhidmat.org execute akf_hrms.akf_hrms.report.attendance_leave_summary.attendance_leave_summary.get_leaves_details
def get_leaves_details(filters=None):
	# filters = {
	# 	'from_date': '2025-07-31'
	# }
	query = '''
		Select 
			employee, 
			leave_type,
			sum(case when transaction_type in ('Leave Allocation') then leaves else 0 end) as allocated_leaves,
			sum(case when transaction_type in ('Leave Application') then (-1 * leaves) else 0 end) as leaves_taken,
			sum(leaves) as remaining_leaves
		From
			`tabLeave Ledger Entry`
		Where 
			docstatus=1
			-- and is_expired = 0
			and is_lwp = 0
			and leave_type in ('Casual Leave', 'Medical Leave', 'Earned', 'Recreational Leave')
			-- and employee='AKFP-PK-CO-00014'
			
	'''	
	query += ''' and company<=%(company)s ''' if(filters.get("company")) else ""	
	query += ''' and employee<=%(employee)s ''' if(filters.get("employee")) else ""	
	query += ''' and from_date<=%(to_date)s ''' if(filters.get("to_date")) else ""
	query += ''' Group By employee, leave_type '''
	
	details = frappe.db.sql(query, filters, as_dict=1)
	
	response = frappe._dict()

	for row in details:
		employee = row.employee
		leave_type = row.leave_type
		
		if(employee not in response):
			response[employee] = {}
		
		response[employee][leave_type] = {k: v for k, v in row.items() if k not in ['employee', 'leave_type']}
		
	return response

# bench --site erp.alkhidmat.org execute akf_hrms.akf_hrms.report.attendance_leave_summary.attendance_leave_summary.get_holiday_list
def get_holiday_list(filters=None):
	holiday_list = frappe.db.sql('''
		SELECT 
			(parent) as holiday_list,
			GROUP_CONCAT(holiday_date) as holiday_dates
		FROM 
			`tabHoliday`
			
		WHERE 
			docstatus = 0
			and holiday_date BETWEEN %(from_date)s and %(to_date)s
		Group By
			parent
	''', filters, as_dict=1)

	response = frappe._dict()

	for d in holiday_list:
		holiday_dates = (d.holiday_dates).split(",")
		holiday_dates.sort()
		response.update({d.holiday_list: holiday_dates})

	return response

def get_attendances(filters=None):
	conditions = " and company = %(company)s" if filters.get("company") else ""
	conditions += " and custom_branch = %(branch)s" if filters.get("branch") else ""
	conditions += " and department = %(department)s" if filters.get("department") else ""
	conditions += " and custom_designation = %(designation)s" if filters.get("designation") else ""
	conditions += " and employee = %(employee)s" if filters.get("employee") else ""
	conditions += " and attendance_date BETWEEN %(from_date)s AND %(to_date)s " if filters.get("from_date") and filters.get("to_date") else ""
	
	attendances = frappe.db.sql(f'''
				SELECT
					employee, 

					COALESCE(COUNT(*), 0) as total_attendance,
					
					COALESCE(SUM(CASE WHEN leave_type = 'Leave Without Pay' THEN 1 ELSE 0 END), 0) as lwp_count, 

					COALESCE(SUM(CASE WHEN late_entry = 1 AND status = 'Present' THEN 1 ELSE 0 END), 0) as late_entry_count,

					COALESCE(SUM(CASE WHEN early_exit = 1 THEN 1 ELSE 0 END), 0) as early_exit_count,

					COALESCE(SUM(CASE WHEN (custom_in_times IS NULL OR custom_out_times IS NULL) THEN 1 ELSE 0 END), 0) as missing_in_out_count,

					GROUP_CONCAT(DISTINCT CASE WHEN late_entry = 1 AND status = 'Present' THEN attendance_date END) as late_dates,

					GROUP_CONCAT(DISTINCT CASE WHEN early_exit = 1 THEN attendance_date END) as early_dates,

					GROUP_CONCAT(DISTINCT CASE WHEN (custom_in_times IS NULL OR custom_out_times IS NULL) THEN attendance_date END) as missing_dates,

					GROUP_CONCAT(attendance_date) as attendance_dates
				
				FROM 
					`tabAttendance`
				WHERE 
					docstatus=1 
					and status not in ("Cancelled", "Absent")
					{conditions}
				Group By
					employee
	''', filters, as_dict=1)
	
	response = frappe._dict()

	for att in attendances:
		response.update({att.employee: att})
	
	return response

# bench --site erp.alkhidmat.org execute akf_hrms.akf_hrms.report.attendance_leave_summary.attendance_leave_summary.get_late_entry_deduction
def get_late_entry_deduction(filters=None):
	conditions = ""
	if(filters.get("company")):
		conditions += " and company = %(company)s "
	if(filters.get("employee")):
		conditions += " and employee = %(employee)s "
	if(filters.get("deduction_from_date") and filters.get("deduction_to_date")):
		conditions += " and posting_date between %(deduction_from_date)s and %(deduction_to_date)s "

	data = frappe.db.sql(f""" 
				Select 
					employee, 
					 ifnull(sum(total_deduction),0) as late_ded, 
					GROUP_CONCAT(DISTINCT posting_date) as late_ded_dates 
				From `tabDeduction Ledger Entry` 
				Where 
					case_no in (1,2,3)
					and leave_type = 'Leave Without Pay'
				{conditions}
				Group by employee
			   """, filters, as_dict=1)
	
	response = frappe._dict()

	for d in data:
		response.update({f'{d.employee}': d})
	
	return response

# bench --site erp.alkhidmat.org execute akf_hrms.akf_hrms.report.attendance_leave_summary.attendance_leave_summary.get_early_exit_deduction
def get_early_exit_deduction(filters=None):
	conditions = ""
	if(filters.get("company")):
		conditions += " and company = %(company)s "
	if(filters.get("employee")):
		conditions += " and employee = %(employee)s "
	if(filters.get("from_date") and filters.get("to_date")):
		conditions += " and posting_date between %(from_date)s and %(to_date)s "

	data = frappe.db.sql(f""" 
				Select 
					employee, 
					 ifnull(sum(total_deduction),0) as early_ded, 
					GROUP_CONCAT(DISTINCT posting_date) as early_ded_dates 
				From `tabDeduction Ledger Entry` 
				Where
					case_no in (4)
					and leave_type = 'Leave Without Pay'
					{conditions}
				Group by employee              
			   """, filters, as_dict=1)
	
	response = frappe._dict()
	
	for d in data:
		response.update({f'{d.employee}': d})
	
	return response

def get_fuel_eligibility(filters=None):
	data = frappe.db.sql('''Select 
		employee
	From 
		`tabSalary Structure Assignment`
	Where
		docstatus=1
		and ifnull(custom_fuel_allowance, 0)!=0
		and from_date<=%(to_date)s
	Group by 
		employee''', filters, as_dict=1)
	
	response = set()
	
	for d in data:
		response.add(d.employee)
	
	return response