# Copyright (c) 2025, Nabeel Saleem and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        _("Employee ID") + ":Link/Employee:120",
        _("Employee Name") + ":Data:180",
        _("Salary Component") + ":Data:180",
        _("Amount") + ":Currency:110",
        _("Start Date") + ":Date:110",        
        _("End Date") + ":Date:110",        
    ]

def get_data(filters=None):
    conditions = get_condition(filters) if filters else ""

    query = """
        SELECT 
            ss.employee, ss.employee_name, sd.salary_component, sd.amount, 
            ss.start_date, ss.end_date
        FROM `tabSalary Slip` ss 
        INNER JOIN `tabSalary Detail` sd ON ss.name = sd.parent
        WHERE ss.docstatus = 1 
            AND sd.is_tax_applicable = 1
            AND sd.salary_component IN (SELECT name FROM `tabSalary Component` WHERE type = 'Earning')
            {conditions}
    """.format(conditions=conditions)

    results = frappe.db.sql(query, filters or {}, as_dict=True)
    
    return [
        [
            row.get("employee"),
            row.get("employee_name"),
            row.get("salary_component"),
            frappe.utils.fmt_money(row.get("amount"), currency="Rs"),
            row.get("start_date"),
            row.get("end_date")
        ]
        for row in results
    ]

def get_condition(filters):
    conditions = ""
    if filters:
        if filters.get("company"):
            conditions += " AND ss.company = %(company)s"
        if filters.get("employee"):
            conditions += " AND ss.employee = %(employee)s"
        if filters.get("start_date"):
            conditions += " AND ss.start_date >= %(start_date)s"
        if filters.get("end_date"):
            conditions += " AND ss.end_date <= %(end_date)s"
    return conditions
