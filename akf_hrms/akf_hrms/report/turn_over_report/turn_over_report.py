# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# Mubashir Bashir

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
		_("Department")+ ":Data:250",_("Total Employees")+ ":Data:250"
	]

def get_data(filters):
	total_emp_count = []
	conditions, filters = get_conditions(filters)

	if filters.get("department"):
		emp_info = frappe.db.sql("""select count(*) from `tabEmployee` where docstatus < 2 %s""" % conditions, filters)
		total_emp_count.append([filters.get("department"),emp_info[0][0]])
	else:
		total_dep = frappe.db.sql("""select name from `tabDepartment` where docstatus < 2 """)
		for x in total_dep:
			emp_info = frappe.db.sql("""select count(*) from `tabEmployee` where department = '%s' %s """ % (x[0], conditions), filters )
			total_emp_count.append([x[0],emp_info[0][0]])
	return total_emp_count

def get_conditions(filters):
	conditions = ""
	if filters.get("company"): conditions += " and company = %(company)s"
	if filters.get("department"): conditions += " and department = %(department)s"
	if filters.get("status") == 'Active':
		conditions += " and date_of_joining between %(from_date)s and %(to_date)s and status = 'Active'"
	if filters.get("status") == 'Left':
		conditions += " and relieving_date between %(from_date)s and %(to_date)s and status = 'Left'"
	if filters.get("status") != 'Active' and filters.get("status") != 'Left':
		conditions += " and ((date_of_joining between %(from_date)s and %(to_date)s) or (relieving_date between %(from_date)s and %(to_date)s))"
	return conditions, filters

