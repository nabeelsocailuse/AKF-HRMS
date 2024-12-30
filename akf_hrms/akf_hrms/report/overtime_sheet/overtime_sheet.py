# Copyright (c) 2024, Nabeel Saleem and contributors
# For license information, please see license.txt

# import frappe


from __future__ import unicode_literals
import frappe
from frappe import _
def execute(filters=None):


	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		_("Employee Name") + ":Link/Employee:120",
		_("Designation") + ":Data:120",
		_("Department") + ":Data:120",
		_("CNIC") + ":Data:120",
		_("Period Covered") + ":Data:120",
		_("Salary") + ":Data:120",
		_("Standard Working Hours") + ":Data:120",
		_("Overtime Rate") + ":Data:120",
		_("Total Overtime Hours") + ":Data:120",
		_("HOD Recommended Overtime Hours") + ":Data:120",
		_("Original Amount Payable(Rs)") + ":Data:120",
		_("HOD Recommended Amount Payable(Rs)") + ":Data:120",
		_("Remarks") + ":Data:120",
	]
# 
def get_data(filters):
	
	conditions = get_conditions(filters)

	emp_record = """ 
		SELECT 
			employee_name, employee_designation, employee_department, employee_cnic,
			month, basic_salary, employee_shift, hourly_rate, total_overtime_hours, "-",amount_in_figures,"-","-"
		FROM `tabOvertime Claim Form`
		WHERE docstatus != 2 {condition}
		""".format(condition = conditions)		
	
	data = frappe.db.sql(emp_record, filters)

	# frappe.msgprint(frappe.as_json(data))
	
	return data

def get_conditions(filters):
	conditions = ""
	# if filters.get("company"):
	# 	conditions += " company = %(company)s"
	# if filters.get("employee"):
	# 	conditions += " and employee = %(employee)s"
	# if filters.get("department"):
	# 	conditions += " and department = %(department)s"
	# if filters.get("department"):
	# 	conditions += " and department = %(department)s"
	# if filters.get("branch"):
	# 	conditions += " and branch = %(branch)s"
	# if filters.get("status"):
	# 	conditions += " and custom_approval_status = %(status)s"
	# if filters.get("from_date") and filters.get("to_date"):
	# 	conditions += " and from_date between %(from_date)s and %(to_date)s"
	# if filters.get("from_time") and filters.get("to_time"):
	# 	conditions += " and custom_from between %(from_time)s and %(to_time)s"
	
	return conditions
