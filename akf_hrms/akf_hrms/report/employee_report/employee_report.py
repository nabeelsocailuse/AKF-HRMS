# Mubashir Bashir

from __future__ import unicode_literals
import frappe
from frappe import _
def execute(filters=None):


	columns, data = [], []
	# columns = get_employee_columns()
	# data = get_employee_data(filters)
	return columns, data

def get_employee_columns():
	return [
		_("Name") + ":Data:120",
		_("Father") + ":Data:120",
		_("Department") + ":Link/Department:120",
		_("Designation") + ":Link/Designation:120",
		_("Contract Signed") + ":Date:120",
		_("Contract End") + ":Date:120",
		_("Branch") + ":Link/Branch:120",
		_("Reported to") + ":Link/Employee:120",
		# _("Experience") + ":Data:120",
		_("DOB") + ":Date:120",
		_("Joining Date") + ":Date:120",
		_("Address") + ":Data:120",
		_("Primary Number") + ":Data:120",
		_("Bank Account") + ":Data:120",
		_("Land line") + ":Data:120",
		_("CNIC") + ":Data:120",
		_("Disability") + ":Data:120",
		_("Labor Type") + ":Data:120",
		_("Religion") + ":Data:120",
		_("Email") + ":Data:120",
		_("Personal Email") + ":Data:120",
		_("Working Hours") + ":Data:120",
		_("Employee Type") + ":Data:120",
		_("Pay by") + ":Data:120",
		_("Bank Name") + ":Data:120",
		_("Confirmation Date") + ":Data:120",
		_("Grade Type") + ":Data:120",
		_("Job Grade") + ":Data:120",
		_("Allowance") + ":Data:120",
		_("Last Promotion Date") + ":Date:120",
		_("Last Increment Date") + ":Date:120",
		_("Qualification") + ":Data:120",
		_("Gross Salary") + ":Data:120",
		_("Salary Type") + ":Data:120",
		_("Gender") + ":Data:120",
		_("Marital Status") + ":Data:120",
		_("From Shift") + ":Data:120",
		_("To Shift") + ":Data:120",
		_("Blood Group") + ":Data:120",
	]
# 
def get_employee_data(filters):
	
	conditions = get_conditions(filters)
	

	emp_record = """ 
		SELECT 
			e.employee_name, e.custmo_father_name, e.department, e.designnation,
			e.final_confirmation_date, e.contract_end_date, e.branch, e.reports_to,


		FROM `tabEmployee` e
		WHERE {condition}
		""".format(condition = conditions)		
	
	

	data = frappe.db.sql(emp_record, filters)
	
	return data


def get_conditions(filters):
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
	
	return conditions
