# Mubashir Bashir

from __future__ import unicode_literals
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
		_("Date") + ":Date:120",
		_("In Time") + ":Data:120",
		_("Out Time") + ":Data:120",
		_("App. Date") + ":Date:120",
		_("Reason") + ":Data:120",
		_("Description") + ":Data:120"
	]
# 
def get_employee_data(filters):
	
	conditions = get_conditions(filters)

	emp_record = """ 
		SELECT 
			employee, employee_name, from_date, custom_from,
			custom_to, creation, reason, explanation	
		FROM `tabAttendance Request`
		WHERE {condition}
		""".format(condition = conditions)		
	
	data = frappe.db.sql(emp_record, filters)

	# frappe.msgprint(frappe.as_json(data))
	
	return data

def get_conditions(filters):
	conditions = ""
	if filters.get("company"):
		conditions += " company = %(company)s"
	if filters.get("employee"):
		conditions += " and employee = %(employee)s"
	if filters.get("department"):
		conditions += " and department = %(department)s"
	if filters.get("department"):
		conditions += " and department = %(department)s"
	if filters.get("branch"):
		conditions += " and branch = %(branch)s"
	if filters.get("status"):
		conditions += " and custom_approval_status = %(status)s"
	if filters.get("from_date") and filters.get("to_date"):
		conditions += " and from_date between %(from_date)s and %(to_date)s"
	if filters.get("from_time") and filters.get("to_time"):
		conditions += " and custom_from between %(from_time)s and %(to_time)s"
	
	return conditions
