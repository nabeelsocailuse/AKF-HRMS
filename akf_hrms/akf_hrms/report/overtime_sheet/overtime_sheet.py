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
# def get_data(filters):
#     conditions = get_conditions(filters)

#     emp_record = """ 
#         SELECT 
#             employee_name, employee_designation, employee_department, employee_cnic,
#             month, basic_salary, employee_shift, hourly_rate, total_overtime_hours, "-",amount_in_figures,"-","-"
#         FROM `tabOvertime Claim Form`
#         WHERE docstatus != 2 {condition}
#     """.format(condition=conditions)

#     # Fetch the data from the database
#     raw_data = frappe.db.sql(emp_record, filters, as_dict=false)

#     # Format monetary fields using fmt_money
#     data = []
#     for row in raw_data:
#         row['basic_salary'] = frappe.utils.fmt_money(row['basic_salary'])
#         row['basic_salary'] = frappe.utils.fmt_money(row['basic_salary'])
#         row['hourly_rate'] = frappe.utils.fmt_money(row['hourly_rate'])
#         row['amount_in_figures'] = frappe.utils.fmt_money(row['amount_in_figures'])
#         data.append(row)
	
#     frappe.msgprint(frappe.as_json(data))

#     return data

# def get_data(filters):
#     conditions = get_conditions(filters)

#     emp_record = """ 
#         SELECT 
#             employee_name, 
#             employee_designation, 
#             employee_department, 
#             employee_cnic,
#             month, 
#             basic_salary, 
#             employee_shift, 
#             hourly_rate, 
#             total_overtime_hours, 
#             '-' as col1,
#             amount_in_figures,
#             '-' as col2,
#             '-' as col3
#         FROM `tabOvertime Claim Form`
#         WHERE docstatus != 2 {condition}
#     """.format(condition=conditions)

#     # Fetch the data from the database
#     raw_data = frappe.db.sql(emp_record, filters, as_dict=True)  # Changed to True

#     # Format monetary fields using fmt_money
#     data = []
#     for row in raw_data:
#         formatted_row = [
#             row.get('employee_name'),
#             row.get('employee_designation'),
#             row.get('employee_department'),
#             row.get('employee_cnic'),
#             row.get('month'),
#             frappe.utils.fmt_money(row.get('basic_salary'), currency='Rs'),
#             row.get('employee_shift'),
#             frappe.utils.fmt_money(row.get('hourly_rate'), currency='Rs'),
#             row.get('total_overtime_hours'),
#             row.get('col1'),
#             frappe.utils.fmt_money(row.get('amount_in_figures'), currency='Rs'),
#             row.get('col2'),
#             row.get('col3')
#         ]
#         data.append(formatted_row)

#     return data

def get_data(filters):
    conditions = get_conditions(filters)

    emp_record = """ 
        SELECT 
            employee_name, 
            employee_designation, 
            employee_department, 
            employee_cnic,
            month, 
            basic_salary, 
            employee_shift, 
            hourly_rate, 
            total_overtime_hours, 
            '-' as col1,
            amount_in_figures,
            '-' as col2,
            '-' as col3
        FROM `tabOvertime Claim Form`
        WHERE docstatus != 2 {condition}
        ORDER BY employee_name
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
            row.get('employee_designation'),
            row.get('employee_department'),
            row.get('employee_cnic'),
            row.get('month'),
            format_currency(row.get('basic_salary')),
            row.get('employee_shift'),
            format_currency(row.get('hourly_rate')),
            row.get('total_overtime_hours'),
            '-',
            format_currency(row.get('amount_in_figures')),
            '-',
            '-'
        ])

    # Add total row
    data.append([
        'Total',
        '',
        '',
        '',
        '',
        format_currency(total_basic_salary),
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
