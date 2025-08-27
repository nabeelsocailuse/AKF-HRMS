# Developer Mubashir Bashir

from __future__ import unicode_literals

# from akf_hrms.overrides.leave_application.leave_application import get_leave_details
import frappe
from frappe import _
import datetime
from frappe.utils import (
	get_first_day,
	get_last_day,
	date_diff,
	add_to_date,
	getdate
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
			"label": "Date of Joining",
			"fieldname": "date_of_joining",
			"fieldtype": "Date",
			"width": "120"
		},
		{
			"label": "(Cur) Late Entry Count",
			"fieldname": "late_entry_count",
			"fieldtype": "Float",
			"precision": "1",
			"width": "140"
		},
		{
			"label": "(Cur) App Late Entry Count",
			"fieldname": "cur_app_late_entry_count",
			"fieldtype": "Float",
			"precision": "1",
			"width": "140"
		},
		{
			"label": "(Pre) Late Entry Count",
			"fieldname": "pre_late_entry_count",
			"fieldtype": "Float",
			"precision": "1",
			"width": "140"
		},
		{
			"label": "(Pre) App Late Entry Count",
			"fieldname": "pre_app_late_entry_count",
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
			"label": "Late Ded After Leaves",
			"fieldname": "late_ded_after_leaves",
			"fieldtype": "Float",
			"precision": "1",
			"width": "140"
		},
		{
			"label": "(Cur) Early Exit Count",
			"fieldname": "early_exit_count",
			"fieldtype": "Float",
			"precision": "1",
			"width": "140"
		},
		{
			"label": "(Cur) App Early Exit Count",
			"fieldname": "cur_app_early_exit_count",
			"fieldtype": "Float",
			"precision": "1",
			"width": "140"
		},
		{
			"label": "(Cur) Early Ded",
			"fieldname": "early_ded",
			"fieldtype": "Float",
			"precision": "1",
			"width": "140"
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
			"label": "(Cur) Late Entry Dates",
			"fieldname": "late_dates",
			"fieldtype": "Data",
			"width": "130",
			"hidden": 0
		},
		{
			"label": "(Cur) App Late Entry Dates",
			"fieldname": "cur_app_late_dates",
			"fieldtype": "Data",
			"width": "130",
			"hidden": 0
		},
		{
			"label": "(Pre) Late Entry Dates",
			"fieldname": "pre_late_dates",
			"fieldtype": "Data",
			"width": "130",
			"hidden": 0
		},
		{
			"label": "(Pre) App Late Entry Dates",
			"fieldname": "pre_app_late_dates",
			"fieldtype": "Data",
			"width": "130",
			"hidden": 0
		},
		{
			"label": "(Cur) Early Exit Dates",
			"fieldname": "early_dates",
			"fieldtype": "Data",
			"width": "130",
			"hidden": 0
		},
		{
			"label": "(Cur) App Early Exit Dates",
			"fieldname": "cur_app_early_dates",
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
    monthDates = [getdate(d) for d in get_21st_to_20th_of_month(filters)]

    Employees = get_employees(filters)
    LeavesDetail = get_leaves_details(filters)

    HolidayLists = get_holiday_list(filters)
    for hlist, dates in HolidayLists.items():
        HolidayLists[hlist] = [getdate(d) for d in dates]

    Attendances = get_attendances(filters)
    Previous_Attendances = get_prev_attendances(filters)
    # lateEntryDeduction = get_late_entry_deduction(filters)
    # earlyExitDeduction = get_early_exit_deduction(filters)
    fuelEligible = get_fuel_eligibility(filters)
    FROM_DATE = getdate(filters.get('from_date'))
    TO_DATE = getdate(filters.get('to_date'))
    cur_month_start = getdate(get_first_day(TO_DATE))
    cur_month_end = getdate(get_last_day(TO_DATE))
    data = []

    for emp in Employees:
        empId = emp.name
        no_attendance = emp.no_attendance
        employment_type = emp.employment_type
        joining_date = getdate(emp.get("date_of_joining")) if emp.get("date_of_joining") else None

        # --- Calculate eligible dates for this employee ---
        if joining_date:
            if FROM_DATE <= joining_date < cur_month_start:
                eligible_month_dates = [d for d in monthDates if d >= joining_date]
                extra_days = date_diff(cur_month_end, TO_DATE)
                days_in_period = date_diff(TO_DATE, joining_date) + 1
                june_end = add_to_date(cur_month_start, days=-1)
                days_in_june = date_diff(june_end, joining_date) + 1
                eligible_cur_month_days = days_in_period + extra_days - days_in_june
            elif cur_month_start <= joining_date <= TO_DATE:
                eligible_month_dates = [d for d in monthDates if d >= joining_date]
                extra_days = date_diff(cur_month_end, TO_DATE)
                days_in_period = date_diff(TO_DATE, joining_date) + 1
                eligible_cur_month_days = days_in_period + extra_days
            elif TO_DATE < joining_date <= cur_month_end:
                eligible_month_dates = []
                eligible_cur_month_days = date_diff(cur_month_end, joining_date) + 1
            else:
                eligible_month_dates = monthDates
                eligible_cur_month_days = date_diff(cur_month_end, cur_month_start) + 1
        else:
            eligible_month_dates = monthDates
            eligible_cur_month_days = date_diff(cur_month_end, cur_month_start) + 1

        # --- Filtering holidays for eligible dates ---
        holiday_dates = []
        if emp.holiday_list in HolidayLists:
            holiday_dates = [d for d in HolidayLists[emp.holiday_list] if d in eligible_month_dates]

        # --- LEAVES ---
        leaves_allocation = LeavesDetail.get(empId, {})
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
                'earned_leaves_balance': leaves_allocation['Earned'].get('remaining_leaves') or 0
            })
        if('Recreational Leave'  in leaves_allocation):
            emp.update({
                'recreational_leaves_allowed': leaves_allocation['Recreational Leave'].get('allocated_leaves') or 0,
                'recreational_leaves_availed': leaves_allocation['Recreational Leave'].get('leaves_taken') or 0,
                'recreational_leaves_balance': leaves_allocation['Recreational Leave'].get('remaining_leaves') or 0
            })

        # --- ATTENDANCE ---
        attendance_dates = []
        missing_dates = []
        late_dates = []
        cur_app_late_dates = []
        pre_late_dates = []
        pre_app_late_dates = []
        early_dates = []
        cur_app_early_dates = []
        late_entry_count = 0
        cur_app_late_entry_count = 0
        pre_late_entry_count = 0
        pre_app_late_entry_count = 0
        early_exit_count = 0
        cur_app_early_exit_count = 0
        missing_in_out_count = 0

        if(empId in Attendances):
            att = Attendances[empId]
            emp.update(att)

            missing_dates = att.get('missing_dates', "") or []
            if missing_dates:
                missing_dates = missing_dates.split(',') if isinstance(missing_dates, str) else missing_dates
                missing_dates = [getdate(d) for d in missing_dates]
                missing_dates = [d for d in missing_dates if d in eligible_month_dates and d not in holiday_dates]
                missing_in_out_count = len(missing_dates)

            #Normalizing attendance dates to date objects
            attendance_dates = att.get('attendance_dates') or []
            if attendance_dates:
                attendance_dates = attendance_dates.split(',') if isinstance(attendance_dates, str) else attendance_dates
                attendance_dates = [getdate(d) for d in attendance_dates]
                attendance_dates = [d for d in attendance_dates if d in eligible_month_dates and d not in holiday_dates]

            late_dates = att.get('late_dates', "") or []
            if late_dates:
                late_dates = late_dates.split(',') if isinstance(late_dates, str) else late_dates
                late_dates = [getdate(d) for d in late_dates]
                late_dates = [d for d in late_dates if d in eligible_month_dates and d not in holiday_dates]
                late_entry_count = len(late_dates)

            cur_app_late_dates = att.get('cur_app_late_dates', "") or []
            if cur_app_late_dates:
                cur_app_late_dates = cur_app_late_dates.split(',') if isinstance(cur_app_late_dates, str) else cur_app_late_dates
                cur_app_late_dates = [getdate(d) for d in cur_app_late_dates]
                cur_app_late_dates = [d for d in cur_app_late_dates if d in eligible_month_dates and d not in holiday_dates]
                cur_app_late_entry_count = len(cur_app_late_dates)

            early_dates = att.get('early_dates', "") or []
            if early_dates:
                early_dates = early_dates.split(',') if isinstance(early_dates, str) else early_dates
                early_dates = [getdate(d) for d in early_dates]
                early_dates = [d for d in early_dates if d in eligible_month_dates and d not in holiday_dates]
                early_exit_count = len(early_dates)

            cur_app_early_dates = att.get('cur_app_early_dates', "") or []
            if cur_app_early_dates:
                cur_app_early_dates = cur_app_early_dates.split(',') if isinstance(cur_app_early_dates, str) else cur_app_early_dates
                cur_app_early_dates = [getdate(d) for d in cur_app_early_dates]
                cur_app_early_dates = [d for d in cur_app_early_dates if d in eligible_month_dates and d not in holiday_dates]
                cur_app_early_exit_count = len(cur_app_early_dates)

        if empId in Previous_Attendances:
            prev_att_list = Previous_Attendances[empId]
            for att in prev_att_list:
                att_date = getdate(att.attendance_date)
                if att_date not in holiday_dates:
                    if att.late_entry == 1:
                        pre_late_dates.append(att_date)
                        pre_late_entry_count += 1
                        if att.attendance_adjustment or att.leave_application or att.attendance_request:
                            pre_app_late_dates.append(att_date)
                            pre_app_late_entry_count += 1

        # --- Paid & Absent Days ---
        paid_dates_list = list(set(attendance_dates + holiday_dates))
        paid_dates_list.sort()
        paid_dates_list = [d for d in paid_dates_list if d not in missing_dates]

        absent_dates_list = [d for d in eligible_month_dates if d not in attendance_dates and d not in holiday_dates]
        absent_dates_list.sort()

        # --- Deductions ---
        if(no_attendance or employment_type == "Volunteer"):
            total_deduction = 0.0
            late_ded = 0.0
            early_ded = 0.0
        else:
            total_deduction = 0.0
            total_deduction += len(absent_dates_list)
            total_deduction += len(missing_dates)

            early_ded = get_early_exit_deduction_runtime(empId, filters.get("from_date"), filters.get("to_date"), holiday_dates)
            emp.update(early_ded)
            total_deduction += early_ded.get("early_ded", 0.0)

            late_ded = get_late_entry_deduction_runtime(empId, filters.get("deduction_from_date"), filters.get("deduction_to_date"), holiday_dates)
            emp.update(late_ded)
            late_ded_value = late_ded.get("late_ded", 0.0)

            leave_balance = (
                emp.get('casual_leaves_balance', 0) +
                emp.get('medical_leaves_balance', 0) +
                emp.get('earned_leaves_balance', 0)
            )
            late_ded_after_leaves = max(late_ded_value - leave_balance, 0)
            emp['late_ded_after_leaves'] = late_ded_after_leaves
            total_deduction += late_ded_after_leaves


        # --- Fuel Days ---
        fuel_days = 0.0
        fuel_eligibility = "No"
        if(empId in fuelEligible):
            if(no_attendance):
                fuel_days = eligible_cur_month_days
            else:
                fuel_days = eligible_cur_month_days - len(absent_dates_list)
            fuel_eligibility = "Yes"

        # --- Updating Employee Dict ---
        emp.update({
            "missing_in_out_count": missing_in_out_count,
            "late_entry_count": late_entry_count,
            "cur_app_late_entry_count": cur_app_late_entry_count,
            "pre_late_entry_count": pre_late_entry_count,
            "pre_app_late_entry_count": pre_app_late_entry_count,
            "early_exit_count": early_exit_count,
            "cur_app_early_exit_count": cur_app_early_exit_count,
            "missing_dates": ", ".join([d.strftime("%Y-%m-%d") for d in missing_dates]),
            "late_dates": ", ".join([d.strftime("%Y-%m-%d") for d in late_dates]),
            "cur_app_late_dates": ", ".join([d.strftime("%Y-%m-%d") for d in cur_app_late_dates]),
            "pre_late_dates": ", ".join([d.strftime("%Y-%m-%d") for d in pre_late_dates]),
            "pre_app_late_dates": ", ".join([d.strftime("%Y-%m-%d") for d in pre_app_late_dates]),
            "early_dates": ", ".join([d.strftime("%Y-%m-%d") for d in early_dates]),
            "cur_app_early_dates": ", ".join([d.strftime("%Y-%m-%d") for d in cur_app_early_dates]),
            'absents': 0.0 if(no_attendance) else len(absent_dates_list),
            'absent_dates': "" if(no_attendance) else ", ".join([d.strftime("%Y-%m-%d") for d in absent_dates_list]),
            'total_days': eligible_cur_month_days,
            'total_deduction': total_deduction,
            'paid_days': 0 if employment_type == "Volunteer" else (eligible_cur_month_days if(no_attendance) else (eligible_cur_month_days - total_deduction)),
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
				e.date_of_joining, 
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

					COALESCE(SUM(CASE WHEN (custom_in_times IS NULL OR custom_out_times IS NULL) AND leave_application IS NULL THEN 1 ELSE 0 END), 0) as missing_in_out_count,

					GROUP_CONCAT(DISTINCT CASE WHEN late_entry = 1 AND status = 'Present' THEN attendance_date END) as late_dates,

					GROUP_CONCAT(DISTINCT CASE WHEN early_exit = 1 THEN attendance_date END) as early_dates,

					GROUP_CONCAT(DISTINCT CASE WHEN (custom_in_times IS NULL OR custom_out_times IS NULL) AND leave_application IS NULL THEN attendance_date END) as missing_dates,

					GROUP_CONCAT(attendance_date) as attendance_dates,

                    GROUP_CONCAT(DISTINCT CASE WHEN late_entry = 1 AND 
                        (attendance_adjustment IS NOT NULL OR leave_application IS NOT NULL OR attendance_request IS NOT NULL) THEN attendance_date END) as cur_app_late_dates,

                    GROUP_CONCAT(DISTINCT CASE WHEN early_exit = 1 AND 
                        (attendance_adjustment IS NOT NULL OR leave_application IS NOT NULL OR attendance_request IS NOT NULL) THEN attendance_date END) as cur_app_early_dates

				FROM 
					`tabAttendance`
				WHERE 
					docstatus=1
					{conditions}
				Group By
					employee
	''', filters, as_dict=1)
	
	response = frappe._dict()

	for att in attendances:
		response.update({att.employee: att})
	
	return response

# Mubashir 21-8-25 Start
def get_prev_attendances(filters=None):
    conditions = ""
    if filters.get("company"):
        conditions += " and company = %(company)s"
    if filters.get("branch"):
        conditions += " and custom_branch = %(branch)s"
    if filters.get("department"):
        conditions += " and department = %(department)s"
    if filters.get("designation"):
        conditions += " and custom_designation = %(designation)s"
    if filters.get("employee"):
        conditions += " and employee = %(employee)s"
    if filters.get("deduction_from_date") and filters.get("deduction_to_date"):
        conditions += " and attendance_date BETWEEN %(deduction_from_date)s AND %(deduction_to_date)s"

    attendances = frappe.db.sql(f"""
        SELECT
            employee,
            attendance_date,
            late_entry,
            early_exit,
            attendance_adjustment,
            leave_application,
            attendance_request,
            status
        FROM `tabAttendance`
        WHERE
            docstatus=1
            {conditions}
    """, filters, as_dict=1)

    response = frappe._dict()
    for att in attendances:
        if att.employee not in response:
            response[att.employee] = []
        response[att.employee].append(att)
    return response
# Mubashir 21-8-25 End

def get_fuel_eligibility(filters=None):
	data = frappe.db.sql('''Select 
		employee
	From 
		`tabSalary Structure Assignment`
	Where
		docstatus=1
		AND (custom_fuel_eligibility = 1 OR ifnull(custom_fuel_allowance, 0)!=0)
		AND from_date<=%(to_date)s
	Group by 
		employee''', filters, as_dict=1)
	
	response = set()
	
	for d in data:
		response.add(d.employee)
	
	return response


# Mubashir Bashir 25-8-25 Start
def get_early_exit_deduction_runtime(employee, from_date, to_date, holiday_dates):
	holiday_dates_str = ",".join([f"'{d}'" for d in holiday_dates]) or "''"

	query = f"""
		SELECT
			attendance_date,
			TIMESTAMPDIFF(
				MINUTE,
				custom_out_times,
				custom_end_time
			) / 60.0 AS hours_diff
		FROM `tabAttendance`
		WHERE employee = %s
		  AND docstatus = 1
		  AND early_exit = 1
		  AND attendance_date BETWEEN %s AND %s
		  AND attendance_date NOT IN ({holiday_dates_str})
		  AND attendance_adjustment IS NULL
		  AND leave_application IS NULL
		  AND attendance_request IS NULL
	"""

	records = frappe.db.sql(query, (employee, from_date, to_date), as_dict=True)

	deduction = 0.0
	deduction_dates = []

	for rec in records:
		hours_diff = rec.hours_diff
		if hours_diff is None or hours_diff <= 0:
			continue
		if hours_diff <= 4:
			deduction += 0.5
		else:
			deduction += 1.0
		deduction_dates.append(rec.attendance_date.strftime("%Y-%m-%d"))

	return {"early_ded": deduction, "early_ded_dates": ", ".join(deduction_dates)}

def get_late_entry_deduction_runtime(employee, deduction_from_date, deduction_to_date, holiday_dates):
	holiday_dates_str = ",".join([f"'{d}'" for d in holiday_dates]) or "''"

	query = f"""
		SELECT
			attendance_date,
			TIMESTAMPDIFF(
				MINUTE,
				custom_start_time,
				custom_in_times
			) / 60.0 AS hours_diff
		FROM `tabAttendance`
		WHERE employee = %s
		  AND docstatus = 1
		  AND late_entry = 1
		  AND attendance_date BETWEEN %s AND %s
		  AND attendance_date NOT IN ({holiday_dates_str})
		  AND attendance_adjustment IS NULL
		  AND leave_application IS NULL
		  AND attendance_request IS NULL
	"""

	records = frappe.db.sql(query, (employee, deduction_from_date, deduction_to_date), as_dict=True)

	deduction = 0.0
	deduction_dates = []
	less_than_2hr_dates = []

	for rec in records:
		hours_diff = rec.hours_diff
		if hours_diff is None or hours_diff <= 0:
			continue

		if hours_diff > 4:
			deduction += 1.0
			deduction_dates.append(rec.attendance_date.strftime("%Y-%m-%d"))
		elif 2 < hours_diff <= 4:
			deduction += 0.5
			deduction_dates.append(rec.attendance_date.strftime("%Y-%m-%d"))
		elif 0 < hours_diff <= 2:
			less_than_2hr_dates.append(rec.attendance_date.strftime("%Y-%m-%d"))

	# For every 3 days late (<=2hr), 1 deduction
	if less_than_2hr_dates:
		deduction += (len(less_than_2hr_dates) // 3)
		deduction_dates.extend(less_than_2hr_dates)

	return {"late_ded": deduction, "late_ded_dates": ", ".join(deduction_dates)}

# Mubashir Bashir 25-8-25 End 

# # bench --site erp.alkhidmat.org execute akf_hrms.akf_hrms.report.attendance_leave_summary.attendance_leave_summary.get_late_entry_deduction
# def get_late_entry_deduction(filters=None):
# 	conditions = ""
# 	if(filters.get("company")):
# 		conditions += " and company = %(company)s "
# 	if(filters.get("employee")):
# 		conditions += " and employee = %(employee)s "
# 	if(filters.get("deduction_from_date") and filters.get("deduction_to_date")):
# 		conditions += " and posting_date between %(deduction_from_date)s and %(deduction_to_date)s "
# 		# conditions += " and posting_date not in (select attendance_date from `tabAttendance` where docstatus=1 and employee=d.employee and %(deduction_from_date)s and %(deduction_to_date)s) "
	
# 	data = frappe.db.sql(f""" 
# 				Select 
# 					employee, 
# 					 ifnull(sum(total_deduction),0) as late_ded, 
# 					GROUP_CONCAT(DISTINCT posting_date) as late_ded_dates 
# 				From `tabDeduction Ledger Entry` d
# 				Where 
# 					case_no in (1,2,3)
# 				{conditions}
# 				Group by employee
# 			   """, filters, as_dict=1)
	
# 	response = frappe._dict()

# 	for d in data:
# 		response.update({f'{d.employee}': d})
	
# 	return response

# # bench --site erp.alkhidmat.org execute akf_hrms.akf_hrms.report.attendance_leave_summary.attendance_leave_summary.get_early_exit_deduction
# def get_early_exit_deduction(filters=None):
# 	conditions = ""
# 	if(filters.get("company")):
# 		conditions += " and company = %(company)s "
# 	if(filters.get("employee")):
# 		conditions += " and employee = %(employee)s "
# 	if(filters.get("from_date") and filters.get("to_date")):
# 		conditions += " and posting_date between %(from_date)s and %(to_date)s "
# 		# conditions += " and posting_date not in (select attendance_date from `tabAttendance` where docstatus=1 and employee=d.employee and %(from_date)s and %(to_date)s) "
	
# 	data = frappe.db.sql(f""" 
# 				Select 
# 					employee, 
# 					 ifnull(sum(total_deduction),0) as early_ded, 
# 					GROUP_CONCAT(DISTINCT posting_date) as early_ded_dates 
# 				From `tabDeduction Ledger Entry` d
# 				Where
# 					case_no in (4)
# 					{conditions}
# 				Group by employee              
# 			   """, filters, as_dict=1)
	
# 	response = frappe._dict()
	
# 	for d in data:
# 		response.update({f'{d.employee}': d})
	
# 	# frappe.msgprint(frappe.as_json(response))
	
# 	return response