# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	columns, data = [], []

	columns = get_columns(filters)

	data = get_data(filters)

	return columns, data


def get_columns(filters):
	return [
		_("Employee ID") + ":Link/Employee:180", 
		_("Employee Name") + ":Data:200",
		_("Designation")+ ":Data:180",
		_("Department")+ ":Data:180",
		_("Location")+ ":Data:150",
		_("Gender")+ ":Data:150",
		_("Attendance Date")+ ":Data:150",
		_("Status")+ ":Data:150",
		_("Shift Check In")+ ":Data:180", 
		_("Shift Check Out")+ ":Data:180",
		_("Check In")+ ":Data:180", 
		_("Check Out")+ ":Data:180",
		_("Total hours assigned")+ ":Data:150", 
		_("Total hours worked")+ ":Data:150",
		_("Check In/Out Status")+ ":Data:150"
	]

def get_data(filters):
	return_list = []
	conditions, filters = get_conditions(filters)
	emp_info = []
	if ('HR Manager') in frappe.get_roles(frappe.session.user):
		emp_info = frappe.db.sql("""
			select att.employee, att.employee_name, att.custom_designation, att.department,
			att.custom_branch, att.custom_gender, att.attendance_date,
			(CASE WHEN att.status = 'Present' THEN 'P'
				WHEN att.status = 'Absent' THEN 'A'
				WHEN att.status = 'On Leave' THEN 'L' 
			END),
			IFNULL(SUBSTRING(att.custom_start_time, 12, 8),""), IFNULL(SUBSTRING(att.custom_end_time, 12, 8),""), 
			att.custom_total_working_hours, att.custom_hours_worked,
			(CASE
			WHEN att.late_entry = 1 AND att.early_exit = 1 THEN 'Late Entry and Early Exit'
			WHEN att.late_entry = 1 THEN 'Late Entry'
			WHEN att.early_exit = 1 THEN 'Early Exit'
			ELSE 'On Time'
			END)
			from `tabAttendance` as att
			where att.docstatus=1 %s
			""" % conditions, filters)

	else:
		get_emp_from_user_permission = frappe.db.sql("""select Distinct(for_value) from `tabUser Permission` where user=%s and 
								allow='Employee' """,(frappe.session.user))
		if get_emp_from_user_permission:
			for emp_id in get_emp_from_user_permission:
				emp_info = frappe.db.sql("""
				select att.employee, att.employee_name, att.custom_designation, att.department,
				att.custom_branch, att.custom_gender, att.attendance_date,
				(CASE WHEN att.status = 'Present' THEN 'P'
						WHEN att.status = 'Absent' THEN 'A'
						WHEN att.status = 'On Leave' THEN 'L' 
					END),
				IFNULL(SUBSTRING(att.custom_start_time, 12, 8),""), IFNULL(SUBSTRING(att.custom_end_time, 12, 8),""), 
				att.custom_total_working_hours, att.custom_hours_worked,
				(CASE
					WHEN att.late_entry = 1 AND att.early_exit = 1 THEN 'Late Entry and Early Exit'
					WHEN att.late_entry = 1 THEN 'Late Entry'
					WHEN att.early_exit = 1 THEN 'Early Exit'
					ELSE 'On Time'
				END)
				from `tabAttendance` as att
				where att.late_entry = 1 and att.docstatus=1 and att.employee=%s and att.attendance_date between %s and %s
				""", (emp_id[0], filters.get("from_date"), filters.get("to_date")))

				return_list.extend(emp_info)

	return return_list

def get_conditions(filters):
	conditions = ""
	if filters.get("from_date") and filters.get("to_date"): conditions += " and att.attendance_date between %(from_date)s and %(to_date)s"
	if filters.get("company"): conditions += " and att.company = %(company)s"
	if filters.get("employee"): conditions += " and att.employee = %(employee)s"
	if filters.get("department"): conditions += " and att.department = %(department)s"

	return conditions, filters
