# Developer Mubashir Bashir

from __future__ import unicode_literals
from frappe import _
import frappe
import ast

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)	
	return columns, data

def get_columns():
	return [
		_("Employee ID") + ":Link/Employee:120",
		_("Employee name") + ":Data:180",
		_("Branch") + ":Data:180",
		_("Department") + ":Data:180",
		_("Designation") + ":Data:180",
		_("Type") + ":Data:110",
		_("Grade") + ":Data:90",
		_("Mobile Allowance") + ":Data:180",
		_("CNIC") + ":Data:120",
		_("Contact") + ":Data:120",
		_("Issue Date") + ":Date:120",
		_("Balance on Issue") + ":Data:120",
		_("Return Date") + ":Date:120",
		_("Balance on Return") + ":Data:120",
	]


def get_data(filters):
    conditions = get_condition(filters)    
    query = """ 
        SELECT
            e.name, e.employee_name, e.branch, e.department, e.designation, e.employment_type, e.grade,
            COALESCE(
                (SELECT custom_mobile_allowance 
                FROM `tabSalary Structure Assignment` ssa
                WHERE ssa.employee = e.name 
                AND ssa.docstatus = 1
                AND ssa.from_date <= CURDATE()
                ORDER BY ssa.from_date DESC
                LIMIT 1), 
                0
            ) as custom_mobile_allowence,
            e.custom_cnic, ah.sim_number, ah.issue_date, ah.balance_on_issue, ah.return_date, ah.balance_on_return
        FROM `tabEmployee` e
        LEFT JOIN `tabAsset History` ah ON ah.parent = e.name
        WHERE e.status = 'Active' {condition}
        ORDER BY e.name, ah.issue_date DESC
    """.format(condition=conditions)

    results = frappe.db.sql(query, filters, as_dict=1)
    
    def format_currency(value):
        if not value:
            return "Rs 0"
        return frappe.utils.fmt_money(value, currency='Rs').replace('.00', '')

    formatted_result = []
    previous_employee = None

    for row in results:
        if row.get("name") == previous_employee:
            formatted_row = ['-'] * 9
        else:
            formatted_row = [
                row.get("name"),
                row.get("employee_name"),
                row.get("branch"),
                row.get("department"),
                row.get("designation"),
                row.get("employment_type"),
                row.get("grade"),
                format_currency(row.get("custom_mobile_allowence")),
                row.get("custom_cnic"),                 
            ]
            previous_employee = row.get("name")
        
        formatted_row += [            
            row.get("sim_number"),
            row.get("issue_date"),
            format_currency(row.get("balance_on_issue")),
            row.get("return_date"),
            format_currency(row.get("balance_on_return"))
        ]

        formatted_result.append(formatted_row)
    return formatted_result

def get_condition(filters):
    conditions = ""
    if filters.get("company"):
        conditions += " and e.company = %(company)s"
    if filters.get("employee"):
        conditions += " AND e.employee = %(employee)s"
    if filters.get("designation"):
        conditions += " AND e.designation = %(designation)s"
    if filters.get("department"):
        conditions += " AND e.department = %(department)s"
    if filters.get("employment_type"):
        conditions += " AND e.employment_type = %(employment_type)s"
    if filters.get("grade"):
        conditions += " AND e.grade = %(grade)s"
    if filters.get("branch"):
        conditions += " AND e.branch = %(branch)s"
    
    return conditions  
