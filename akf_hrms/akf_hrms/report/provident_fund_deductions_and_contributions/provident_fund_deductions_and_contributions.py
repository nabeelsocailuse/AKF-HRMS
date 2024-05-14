# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt
from frappe import _


def execute(filters=None):
    columns, data = [], []

    columns, col_len = get_columns()

    data = get_data(filters, col_len)

    return columns, data


def get_data(filters, col_len):
    conditions, filters = get_conditions(filters)
    detail = []
    # pf_deduction='Yes' and (after where clause in query)
    emp_info = frappe.db.sql(
        """ select name, start_date, employee, employee_name, " --date_of_joining" , designation, branch, " --employment_type", "--job_classification", " -- pf_employer_contribution" from `tabSalary Slip` where  %s  """
        % conditions,
        filters,
    )

    for ei in emp_info:
        total = [""] * col_len
        total[0] = ei[1]
        total[1] = ei[2]
        total[2] = ei[3]
        total[3] = ei[4]
        total[4] = ei[5]
        total[5] = ei[6]
        total[6] = ei[7]
        total[7] = ei[8]
        total[8] = 0
        get_prov = frappe.db.sql(
            """ select amount from `tabSalary Detail` where parent=%s and salary_component='Provident Fund' """,
            (ei[0]),
        )
        if get_prov:
            total[8] = get_prov[0][0]
        total[9] = ei[9]
        total[10] = flt(total[8]) + flt(total[9])

        detail.append(total)

    return detail


def get_columns():
    columns = [
        _("Date") + ":Date:150",
        _("Employee") + ":Link/Employee:150",
        _("Employee Name") + ":Data:150",
        _("Employment Date") + ":Date:100",
        _("Designation") + ":Link/Designation:150",
        _("Location") + ":Link/Branch:150",
        _("Staff Category") + ":Link/Employment Type:150",
        _("Job Classification") + ":Link/Job Classification:150",
        _("PF Employee Contribution") + ":Currency:150",
        _("PF Employer Contribution") + ":Currency:150",
        _("Total PF") + ":Currency:150",
    ]
    return columns, len(columns)


def get_conditions(filters):
    conditions = ""
    doc_status = {"Draft": 0, "Submitted": 1, "Cancelled": 2}

    if filters.get("docstatus"):
        conditions += "docstatus = {0}".format(doc_status[filters.get("docstatus")])

    if filters.get("from_date"):
        conditions += " and start_date >= %(from_date)s"
    if filters.get("to_date"):
        conditions += " and end_date <= %(to_date)s"
    if filters.get("company"):
        conditions += " and company = %(company)s"
    if filters.get("employee"):
        conditions += " and employee = %(employee)s"

    return conditions, filters
