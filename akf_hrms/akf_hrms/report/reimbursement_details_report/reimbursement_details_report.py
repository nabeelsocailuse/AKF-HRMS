# Copyright (c) 2024, Nabeel Saleem and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	columns = [
		{
			"label": "Applied Date",
			"fieldname": "applied_date",
			"fieldtype": "Date",
			"options": "",
			"width": 110,
		},
		{
			"label": "Approval Date",
			"fieldname": "approval_date",
			"fieldtype": "Date",
			"options": "",
			"width": 110,
		},
        {
			"label": "Employee",
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 230,
		},
		{
			"label": "Employee Name",
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"options": "",
			"width": 180,
		},
		{
			"label": "Department",
			"fieldname": "department",
			"fieldtype": "Link",
			"options": "Department",
			"width": 180,
		},
		{
			"label": "Designation",
			"fieldname": "designation",
			"fieldtype": "Link",
			"options": "Designation",
			"width": 180,
		},
        {
			"label": "Company",
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			"width": 180,
		},
		{
			"label": "Leave Application",
			"fieldname": "leave_application",
			"fieldtype": "Link",
			"options": "Leave Application",
			"width": 180,
		},
		{
			"label": "Month",
			"fieldname": "month",
			"fieldtype": "Data",
			"options": "",
			"width": 100,
		},
        {
			"label": "Amount",
			"fieldname": "amount",
			"fieldtype": "Currency",
			"options": "",
			"width": 100,
		}
    ]
	return columns

def get_data(filters):
	return frappe.db.sql(""" 
		Select 
			(posting_date) as applied_date, 
			cast(modified as date) approval_date,
			employee, 
			employee_name, 
			department, 
			(select designation from `tabEmployee` where name=la.employee) as designation,
			company, 
			(name) as leave_application, 
			monthname(posting_date) as month, 
			(select base/30 from `tabSalary Structure Assignment` where docstatus=1 and employee=la.employee order by from_date limit 1) as amount
		From 
			`tabLeave Application` la
		Where
			docstatus=1
			{0}

	 """.format(get_conditions(filters)), filters, as_dict=0)

def get_conditions(filters):
	conditions = " and company = %(company)s " if(filters.company) else ""
	conditions += " and employee = %(employee)s " if(filters.employee) else ""
	conditions += " and year(posting_date) = %(year)s " if(filters.year) else ""
	conditions += " and monthname(posting_date) = %(month)s " if(filters.month) else ""
	return conditions