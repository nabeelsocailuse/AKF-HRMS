# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from datetime import timedelta, datetime
from frappe.utils import  today
from frappe import _

def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	if ("Leave Approver" in frappe.get_roles()) or ("Principle" in frappe.get_roles()):
		columns = [
			_("Employee") + ":Data:180"
		]
	else:
		columns = [
			_("Employee") + ":Link/Employee:180"
		]
	columns.extend([
		_("Employee Name") + "::180", 
		_("Branch") + ":Link/Branch:150",
		_("Department") + ":Link/Department:150",
		_("Designation") + ":Link/Designation:150",
		_("WD") + ":Float:50", 
		_("HW") + ":Data:50", 
		_("Total Present") + ":Float:140", 
		_("Total Leaves") + ":Float:140",  
		_("Total Absent") + ":Float:140", 
		_("") + "::40"
		])

	for days in get_days_in_month(filters):
		columns.append(str(frappe.utils.formatdate(str(days), "dd-MMM")) +"::80")
	# frappe.msgprint(frappe.as_json(len(columns)))
	return columns

def get_data(filters):
	# Required 
	data = []

	days_list = get_days_in_month(filters)
	attendnace_map = get_attendance_list(filters)
	employee_map = get_employee_details(filters)
	holiday_map = get_holiday(employee_map, filters)
	default_holiday_list = frappe.db.get_value("Company", filters.get("company"), "default_holiday_list")


	""" dictionary of status """
	status_map = {
		"On Leave": "<font color='blue'><center><b>L</b></center></font>", 
		"None": "<font color='red'><center><b>A</b></center></font>",
		"Absent": "<font color='red'><center><b>A</b></center></font>", 
		"Holiday":"<center><b>H</b></center>",
		"Work From Home": "<b>WFH</b>"
	}
	""" end """

	""" Now run a loop on Attendance Map data """
	for employee_id in sorted(attendnace_map):
		""" get single employee data from employee map """
		employee_data = employee_map.get(employee_id)
		# Date of joining
		# date_of_joining = employee_data.date_of_joining
		# Current date
		today_date = datetime.strptime(str(today()), "%Y-%m-%d").date()
		# Total Days In Month
		total_days_worked = 0
		# Total (Presents, Absent, Leaves)
		total_present = total_absent = total_leaves = total_h = 0.0
		# 
		hours_worked_time_list = ["0:00:00"]
		""" Now loop on all days in month """
		inlist = []
		outlist = []
		hwlist= []
		for day in days_list:
			
			# convert string date of month to object
			month_date = datetime.strptime(str(day), "%Y-%m-%d").date()
			# day_number = str(frappe.utils.formatdate(str(day), "dd"))
			# get data from Attendance Map
			# status_data = attendnace_map.get(employee_id).get(int(day), ["None"])
			status_data = attendnace_map.get(employee_id).get(day, ["None"])
			
			# status can be {Present, Absent, On Leave} etc
			status = status_data[0]
			# set status to Holiday if there is no status
			
			if status== "None" and holiday_map:
				emp_holiday_list = employee_data.holiday_list if employee_data.holiday_list else default_holiday_list
				# if emp_holiday_list in holiday_map and (int(day)) in holiday_map[emp_holiday_list]:
				if emp_holiday_list in holiday_map and day in holiday_map[emp_holiday_list]:
					status = "Holiday"
			# 
			if status in ["None" , "Absent", "Holiday","On Leave", "Work From Home"]:
				# condition to verify employee have attendance in Attendance Doctype
				status_value= status_map[status_data[0]] if today_date >= month_date else ""		
				inlist += [status_value]
				outlist += [status_value]
				hwlist += [status_value]
				
				total_absent += 1 if (today_date >= month_date) and status in ["None" , "Absent"] else 0
				total_leaves += 1 if (today_date >= month_date) and status in ["On Leave" ] else 0
			elif status in ["Present", "Half Day"]:
				total_days_worked += 1
				# 
				check_in_time = str(status_data[1]).split(':')
				check_out_time = str(status_data[2]).split(':')
				hours_worked = str(status_data[3]).split(':')
				# frappe.throw(frappe.as_json(hours_worked))
				if status == "Present":
					inlist += [check_in_time[0] + ":" + check_in_time[1] if (check_in_time) else ""]
					outlist += [check_out_time[0] + ":" + check_out_time[1] if (check_out_time) else ""]
					hwlist += [hours_worked[0] + ":" + hours_worked[1] if(hours_worked) else ""]
					# total present sum
					total_present += 1
				elif status == "Half Day":
					inlist += ["HD " + check_in_time[0] + ":" +check_in_time[1] if (check_in_time) else ""]
					outlist += ["HD "+check_out_time[0]+ ":" +check_out_time[1] if (check_out_time) else ""]
					hwlist += ["HD "+hours_worked[0]+ ":" +hours_worked[1] if(hours_worked) else ""]
					# total present, leaveas half sum
					total_present += 0.5
					total_leaves += 0.5
				# append in list
				hours_worked_time_list.append(status_data[3])		
			else:
				inlist += [status]
				outlist += [status]
				hwlist += [status]
		# Init 3 rows for employee {in, out, hours work}
		working_hours = get_total_hours_worked(hours_worked_time_list)
		row1 = [employee_id, employee_data.employee_name, employee_data.branch, employee_data.department, employee_data.designation, total_days_worked, working_hours, float(total_present), float(total_leaves), float(total_absent), "<b>In</b>"] + inlist
		row2 = ["", "", "", "", "", "", "", "", "", "", "<b>Out</b>"] + outlist
		row3 = ["", "", "", "", "", "", "", "", "", "", "<b>HW</b>"] + hwlist
		
		data.append(row1)
		data.append(row2)
		data.append(row3)
	
	return data

def get_attendance_list(filters):
	conditions =  get_conditions(filters)
	# attendance_list = frappe.db.sql("""select employee, day(attendance_date) as day_of_month,
	attendance_list = frappe.db.sql("""select employee, attendance_date as day_of_month,
		status, ifnull(in_time, "0:00:00") as check_in_time, 
		ifnull(out_time ,  "0:00:00") as check_out_time,
		(case when (custom_hours_worked="" or custom_hours_worked is null) then "0:00:00" else  custom_hours_worked end) as hours_worked
		from tabAttendance 
		where docstatus = 1 %s order by employee, attendance_date""" % conditions, filters, as_dict=1)
	att_map = {}
	# frappe.throw(frappe.as_json(attendance_list))
	for d in attendance_list:
		att_map.setdefault(d.employee, frappe._dict()).setdefault(d.day_of_month, "")
		# hours_worked = time_diff(d.out_time, d.in_time)
		# hours_worked = str(hours_worked).split(".")[0]
		
		att_map[d.employee][str(d.day_of_month)] = [d.status, get_times_split(d.check_in_time), get_times_split(d.check_out_time), d.hours_worked]
	return att_map

def get_conditions(filters, is_employee=False):
	conditions = ""
	if (filters.get("from_date") and filters.get("to_date")) and not is_employee:
		conditions += " and attendance_date between %(from_date)s and %(to_date)s"
	if filters.get("company"): conditions += " and company = %(company)s"
	if filters.get("employee"): conditions += " and employee = %(employee)s"
	if filters.get("branch"): conditions += " and branch = %(branch)s"
	return conditions

def get_times_split(_time_):
	_time_ = str(_time_).split(" ")
	_time_ = _time_[1] if(len(_time_)>1) else _time_
	return _time_
def get_employee_details(filters):
	conditions = get_conditions(filters, is_employee=True)
	emp_map = frappe._dict()
	for d in frappe.db.sql("""select name, employee_name, branch, department, designation, date_of_joining
		holiday_list from tabEmployee where docstatus=0 %s """%conditions, filters, as_dict=1):
		emp_map.setdefault(d.name, d)
	return emp_map


def get_holiday(emp_map, filters):
	""" separete related employee holiday list """
	holiday_list = [emp_map[d]["holiday_list"] for d in emp_map if emp_map[d]["holiday_list"]]
	default_holiday_list = frappe.db.get_value("Company", filters.get("company"), "default_holiday_list")
	holiday_list.append(default_holiday_list)
	holiday_list = list(set(holiday_list))
	""" get map of days in holiday child table """
	holiday_map = frappe._dict()
	for d in holiday_list:
		if d:
			# holiday_map.setdefault(d, frappe.db.sql_list('''select day(holiday_date) from `tabHoliday`
			holiday_map.setdefault(d, frappe.db.sql_list('''select holiday_date from `tabHoliday`
				where parent=%s and holiday_date between %s and %s''', (d, filters.get("from_date"), filters.get("to_date"))))

	return holiday_map


""" From Date - End Date date list """
def get_days_in_month(filters):
	days_list = []
	start_date = datetime.strptime(str(filters.get("from_date")), "%Y-%m-%d") 
	end_date = datetime.strptime(str(filters.get("to_date")), "%Y-%m-%d")
	delta = end_date - start_date    
	for i in range(delta.days + 1):
		day = start_date + timedelta(days=i)
		split_day = str(day).split(" ")[0]
		days_list.append(split_day)
	return days_list

def get_total_hours_worked(hours_worked_time_list):
	total_h_worked= '0'	
	hours_worked_ = 0
	for tm in hours_worked_time_list:
		timeParts = [int(s) for s in str(tm).split(':')]
		hours_worked_ += (timeParts[0] * 60 + timeParts[1]) * 60 + timeParts[2]
	hours_worked_, sec = divmod(hours_worked_, 60)
	hr, min_ = divmod(hours_worked_, 60)
	total_h_worked = '{}:{}'.format(int(hr), str(str(int(min_)).zfill(2)))
	
	return total_h_worked