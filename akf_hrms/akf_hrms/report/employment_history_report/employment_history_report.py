# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from datetime import timedelta, datetime
from frappe import _


@frappe.whitelist(allow_guest=True)
def execute(filters=None):
    # frappe.msgprint("execute")
    columns, data = [], []
    columns = get_columns()
    data = get_data(filters)
    # frappe.throw(f'The data is: {data}')
    return columns, data

def get_columns():
    columns = [
        {
            "fieldname": "company",
            "label": _("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "width": 120
        },
        {
            "fieldname": "employment_type",
            "label": _("Description"),
            "fieldtype": "Link",
            "options": "Employment Type",
            "width": 120
        },
        {
            "fieldname": "employee",
            "label": _("Employee"),
            "fieldtype": "Data",
            "options": "",
            "width": 120
        },
        {
            "fieldname": "first_name",
            "label": _("Employee Name"),
            "fieldtype": "Data",
            "options": "",
            "width": 120
        },
        {
            "fieldname": "custom_father_name",
            "label": _("Father Name"),
            "fieldtype": "Data",
            "options": "",
            "width": 120
        },
        {
            "fieldname": "cell_number",
            "label": _("Mobile No"),
            "fieldtype": "Data",
            "options": "",
            "width": 120
        },
        {
            "fieldname": "date_of_joining",
            "label": _("Date of Joining"),
            "fieldtype": "Date",
            "options": "",
            "width": 120
        },
        {
            "fieldname": "scheduled_confirmation_date",
            "label": _("Offer Date"),
            "fieldtype": "Data",
            "options": "",
            "width": 120
        },
        {
            "fieldname": "final_confirmation_date",
            "label": _("Confirmation Date"),
            "fieldtype": "Data",
            "options": "",
            "width": 120
        },
        {
            "fieldname": "contract_end_date",
            "label": _("Contract End Date"),
            "fieldtype": "Data",
            "options": "",
            "width": 120
        },
        {
            "fieldname": "status",
            "label": _("Current Employment Status"),
            "fieldtype": "Select",
            "options": "",
            "width": 120
        },
        {
            "fieldname": "branch",
            "label": _("Branch"),
            "fieldtype": "Link",
            "options": "Branch",
            "width": 120
        },
        {
            "fieldname": "department",
            "label": _("Department"),
            "fieldtype": "Link",
            "options": "Department",
            "width": 120
        },
        {
            "fieldname": "designation",
            "label": _("Designation"),
            "fieldtype": "Link",
            "options": "Designation",
            "width": 120
        },
        {
            "fieldname": "from_date",
            "label": _("Effective Date"),
            "fieldtype": "Date",
            "options": "",
            "width": 120
        },
        {
            "fieldname": "custom_salary",
            "label": _("Salary"),
            "fieldtype": "Data",
            "options": "",
            "width": 120
        },
        {
            "fieldname": "custom_increment_amount",
            "label": _("Increment"),
            "fieldtype": "Data",
            "options": "",
            "width": 120
        },
    ]

    return columns


# def get_data(filters):
    data = []
    result = get_query_result(filters)
    history_details = {}
    unique_emp = {row.employee for row in result}
    frappe.msgprint(f"Unique Employees are: {unique_emp}")
    for emp in unique_emp:
        history_details[emp] = [d for d in result if (d.name==emp)]
    frappe.msgprint(f"Employee history details are: {history_details}")
    unique_employees = set()
    for d in result:
        if d.name not in unique_employees:
            temp = [d.company, d.employee, d.first_name, d.date_of_joining, d.scheduled_confirmation_date,d.final_confirmation_date,d.contract_end_date,d.status] + ['-' for i in range(5)]
            data.append(temp)
            history_list = history_details.get(d.employee)
            for history in history_list:
                temp = ['-' for i in range(8)] + [history.get('branch'), history.get('department'), 
                        history.get('designation'), history.get('base'), history.get('from_date')]
                data.append(temp)
            unique_employees.add(d.employee)
    return result


def get_data(filters):
    data = []
    result = get_query_result(filters)
    unique_employees = set()

    # Keep track of the latest salary for each employee
    latest_salary = {}

    for d in result:
        # Populate the latest salary for each employee based on from_date
        if d.employee not in latest_salary:
            latest_salary[d.employee] = {
                'salary': d.custom_salary,
                'from_date': d.from_date
            }
        elif d.from_date and (not latest_salary[d.employee]['from_date'] or d.from_date > latest_salary[d.employee]['from_date']):
            latest_salary[d.employee] = {
                'salary': d.custom_salary,
                'from_date': d.from_date
            }

    for d in result:
        if d.employee not in unique_employees:
            temp = [
                d.company, d.employment_type, d.employee, d.first_name, d.custom_father_name,
                d.cell_number, d.date_of_joining, d.scheduled_confirmation_date,
                d.final_confirmation_date, d.contract_end_date, d.status,
                d.branch, d.department, d.designation, d.from_date, d.custom_salary,
                d.custom_increment_amount
            ]
            # Add the latest salary for the employee and highlight it if it's the latest
            if d.employee in latest_salary and latest_salary[d.employee]['salary'] == d.custom_salary:
                temp.append({
                    'value': d.custom_salary,
                    'color': 'green'  # Highlight the latest salary with green color
                })
                temp.append(latest_salary[d.employee]['from_date'])
            else:
                temp.append(d.custom_salary)
                temp.append(d.from_date)

            temp.append(d.custom_increment_amount)
            data.append(temp)
            unique_employees.add(d.employee)
        else:
            temp = [
                '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-',
                d.branch, d.department, d.designation, d.from_date, d.custom_salary,
                d.custom_increment_amount
            ]
            data.append(temp)

    return data





def get_conditions(filters):
    conditions = []

    if filters.get("company"):
        conditions.append("emp.company = %(company)s")

    if filters.get("employee"):
        conditions.append("emp.employee = %(employee)s")

    if filters.get("status"):
        conditions.append("emp.status = %(status)s")

    return " AND ".join(conditions) if conditions else ""


# def get_query_result(filters):
#     conditions = get_conditions(filters)
#     if conditions:
#         conditions = " WHERE " + conditions

#     result = frappe.db.sql(
#         """
#         SELECT 
#             emp.company,
#             emp.employee, 	
#             emp.first_name,
#             emp.custom_father_name,
#             emp.cell_number,
#             emp.date_of_joining,
#             emp.scheduled_confirmation_date, 
#             emp.final_confirmation_date, 
#             emp.contract_end_date, 		
#             emp.status,
#             history.branch,
#             history.department,
#             history.designation,
#             history.custom_salary,
#             history.custom_increment_amount
#         FROM 
#             `tabEmployee` emp
#         JOIN
#             `tabEmployee Internal Work History` history ON emp.name = history.parent
#         GROUP BY emp.employee,history.branch,history.department,history.designation
#         %s
#         """ % conditions, filters, as_dict=1)
#     return result


def get_query_result(filters):
    conditions = get_conditions(filters)
    query = """
        SELECT 
            emp.company,
            emp.employment_type,
            emp.employee, 	
            emp.first_name,
            emp.custom_father_name,
            emp.cell_number,
            emp.date_of_joining,
            emp.scheduled_confirmation_date, 
            emp.final_confirmation_date, 
            emp.contract_end_date, 		
            emp.status,
            history.branch,
            history.department,
            history.designation,
            history.from_date,
            history.custom_salary,
            history.custom_increment_amount
        FROM 
            `tabEmployee` emp
        LEFT JOIN
            `tabEmployee Internal Work History` history ON emp.name = history.parent
        {conditions}
        GROUP BY 
            emp.employee, history.branch, history.department, history.designation
    """.format(conditions="WHERE " + conditions if conditions else "")

    result = frappe.db.sql(query, filters, as_dict=1)
    return result



        


