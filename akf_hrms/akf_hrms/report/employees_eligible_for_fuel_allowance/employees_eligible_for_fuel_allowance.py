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
		_("Joining Date") + ":Data:180",
		_("Employee Type") + ":Data:110",
		_("CNIC") + ":Data:110",        
		_("Fuel Allowance") + ":Data:110",        
	]

def get_data(filters):
    conditions = get_condition(filters)    
    query = """ 
        SELECT
            e.name, 
            e.employee_name, 
            e.branch, 
            e.department, 
            e.designation,
            DATE_FORMAT(e.date_of_joining, '%%d-%%m-%%Y') as date_of_joining,
            e.employment_type,             
            e.custom_cnic,
            COALESCE(
                (SELECT custom_fuel_allowance 
                FROM `tabSalary Structure Assignment` ssa
                WHERE ssa.employee = e.name 
                AND ssa.docstatus = 1
                AND ssa.from_date <= CURDATE()
                ORDER BY ssa.from_date DESC
                LIMIT 1), 
                0
            ) as custom_fuel_allowance         
        FROM `tabEmployee` e
        WHERE e.status = 'Active' 
        AND (
            e.employment_type = 'Permanent'
            OR EXISTS (
                SELECT 1 
                FROM `tabSalary Structure Assignment` ssa
                WHERE ssa.employee = e.name 
                AND ssa.docstatus = 1
                AND ssa.from_date <= CURDATE()
                AND ssa.custom_fuel_allowance > 0
            )
        )
        {condition}
    """.format(condition=conditions)

    results = frappe.db.sql(query, filters, as_dict=1)
    
    return [
        [
            row.get("name"),
            row.get("employee_name"),
            row.get("branch"),
            row.get("department"),
            row.get("designation"),
            row.get("date_of_joining"),
            row.get("employment_type"),
            row.get("custom_cnic"),
            frappe.utils.fmt_money(row.get("custom_fuel_allowance"), currency="Rs")
        ]
        for row in results
    ]


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
    if filters.get("branch"):
        conditions += " AND e.branch = %(branch)s"
    # if filters.get("grade"):
    #     conditions += " AND e.grade = %(grade)s"
    
    return conditions  
