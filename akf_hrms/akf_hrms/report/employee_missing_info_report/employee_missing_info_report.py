# Mubashir Bashir 29-05-2025
from __future__ import unicode_literals
import frappe
from frappe import _
def execute(filters=None):
	columns, data = [], []
	if not filters: filters = {}
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	return [
		_("Employee ID") + ":Link/Employee:120",
		_("Employee name") + ":Data:180",
		_("Company") + ":Data:180",
		_("Branch") + ":Data:180",
		_("Department") + ":Data:180",
		_("Designation") + ":Data:180",
		_("Employment Type") + ":Data:180",
		_("Salary Structure Assignment") + ":Data:180",
	]


def get_data(filters):
	conditions = get_conditions(filters)
	query = """
		SELECT
			e.name,
			e.employee_name,
			e.company,
			e.branch,
			e.department,
			e.designation,
			e.employment_type,
			'Not Assigned'
		FROM
			`tabEmployee` e
		LEFT JOIN
			`tabSalary Structure Assignment` ssa
			ON ssa.employee = e.name
			AND ssa.docstatus = 1
		WHERE
			ssa.name IS NULL AND e.status = 'Active' {conditions}
	""".format(conditions=conditions or "")
	
	return frappe.db.sql(query, filters, as_dict=0)


def get_conditions(filters):
	conditions = ""
	if filters.get("company"):
		conditions += " and e.company = %(company)s"
	if filters.get("branch"):
		conditions += " and e.branch = %(branch)s"
	if filters.get("department"):
		conditions += " and e.department = %(department)s"
	if filters.get("designation"):
		conditions += " and e.designation = %(designation)s"
	if filters.get("employment_type"):
		conditions += " and e.employment_type = %(employment_type)s"
	if filters.get("employee"):
		conditions += " and e.name = %(employee)s"
	return conditions

