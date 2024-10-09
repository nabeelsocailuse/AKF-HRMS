# Mubashir Bashir

from __future__ import unicode_literals
import frappe
from frappe import _
def execute(filters=None):

	user = frappe.session.user

	columns, data = [], []
	columns = get_late_arrival_columns()
	data = get_late_arrival(filters, user)
	return columns, data

def get_late_arrival_columns():
	return [
		_("Attendance ID") + ":Link/Attendance:120",
		_("Employee ID") + ":Link/Employee:120",
		_("Employee name") + ":Data:120",
		_("Designation") + ":Data:120",
		_("Department") + ":Data:120",
		_("Branch") + ":Data:120",
		_("Attendance Date")+ ":Data:150",
		_("Shift Check In") + ":Data:120",
		_("Shift Check Out") + ":Data:120",
		_("Check In") + ":Data:120",
		_("Check Out") + ":Data:120",
		_("Total hours assigned") + ":Data:120",
		_("Total hours worked") + ":Data:120",
		_("Check In Status") + ":Data:120",
		_("Status") + ":Data:120",

	]
# 
def get_late_arrival(filters, user):
	
	conditions = ""
	if filters.get("employee"):
		conditions += " and att.employee = %(employee)s"
	if filters.get("company"):
		conditions += " and att.company = %(company)s"
	if filters.get("department"):
		conditions += " and att.department = %(department)s"
	if filters.get("region"):
		conditions += " and att.custom_region = %(region)s"
	if filters.get("from_date") and filters.get("to_date"):
		conditions += " and att.attendance_date between %(from_date)s and %(to_date)s"
	
	if "HR Manager" in frappe.get_roles(user):
		late_query = """ SELECT att.name, att.employee, att.employee_name, att.custom_designation, att.department, att.custom_branch, att.attendance_date,
				cast(att.custom_start_time as time) as from_time, cast(att.custom_end_time as time) as to_time,  
				cast(att.in_time as time) as check_in_time, cast(att.out_time as time) as check_out_time,
				att.custom_total_working_hours, att.custom_hours_worked,
				CASE WHEN att.late_entry = 1 THEN 'Late' WHEN att.late_entry = 0 THEN 'on Time' END AS late_status, att.status    
				FROM `tabAttendance` att
				WHERE  late_entry = 1 and att.status = "Present" {condition} order by  att.late_entry desc  """.format(condition = conditions)

		late_arrival_result = frappe.db.sql(late_query, filters)
	else:
		late_query = """ SELECT att.name, att.employee, att.employee_name, att.custom_designation, att.department, att.custom_branch, att.attendance_date,
				cast(att.custom_start_time as time) as from_time, cast(att.custom_end_time as time) as to_time,  
				cast(att.in_time as time) as check_in_time, cast(att.out_time as time) as check_out_time,
				att.custom_total_working_hours, att.custom_hours_worked,
				CASE WHEN att.late_entry = 1 THEN 'Late' WHEN att.late_entry = 0 THEN 'on Time' END AS late_status, att.status      
				FROM `tabAttendance` att INNER JOIN `tabUser Permission` per ON (att.employee=per.for_value)
				WHERE  late_entry = 1 and att.status = "Present" and per.user='{id}' and per.allow='Employee'   {condition} 
				group by att.employee
				order by  att.late_entry desc  """.format(id=user,condition = conditions)

		late_arrival_result = frappe.db.sql(late_query, filters)
	
	return late_arrival_result
