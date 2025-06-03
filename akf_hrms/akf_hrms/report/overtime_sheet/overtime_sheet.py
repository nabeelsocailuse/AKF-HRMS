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

def get_data(filters):
    conditions = get_conditions(filters)

    emp_record = """ 
        SELECT 
            employee_name, 
            designation, 
            department, 
            cnic,
            month, 
            basic_salary, 
            shift, 
            hourly_rate, 
            total_overtime_hours, 
            '-' as col1,
            amount_in_figures,
            '-' as col2,
            '-' as col3
        FROM `tabOvertime Claim Form`
        WHERE docstatus != 2 {condition}
    """.format(condition=conditions)

    # Fetch the data and process in a single function
    raw_data = frappe.db.sql(emp_record, filters, as_dict=True)
    
    # Initialize totals and data list
    total_basic_salary = 0
    total_hourly_rate = 0
    total_amount = 0
    data = []

    # Helper function for currency formatting
    def format_currency(value):
        if not value:
            return "Rs 0"
        return frappe.utils.fmt_money(value, currency='Rs').replace('.00', '')

    # Process each row and calculate totals
    for row in raw_data:
        # Add to totals
        total_basic_salary += frappe.utils.flt(row.get('basic_salary', 0))
        total_hourly_rate += frappe.utils.flt(row.get('hourly_rate', 0))
        total_amount += frappe.utils.flt(row.get('amount_in_figures', 0))

        # Format and append row
        data.append([
            row.get('employee_name'),
            row.get('designation'),
            row.get('department'),
            row.get('cnic'),
            row.get('month'),
            format_currency(row.get('basic_salary')),
            row.get('shift'),
            format_currency(row.get('hourly_rate')),
            row.get('total_overtime_hours'),
            '-',
            format_currency(row.get('amount_in_figures')),
            '-',
            '-'
        ])

    # Add total row
    # format_currency(total_basic_salary)
    data.append([
        'Total',
        '',
        '',
        '',
        '',
        '',
        '',
        format_currency(total_hourly_rate),
        '',
        '',
        format_currency(total_amount),
        '',
        ''
    ])

    return data


def get_conditions(filters):
	conditions = ""
	if filters.get("company"):
		conditions += " and company = %(company)s"
	if filters.get("year"):
		conditions += " and year = %(year)s"
	if filters.get("month"):
		conditions += " and month = %(month)s"
	
	return conditions
