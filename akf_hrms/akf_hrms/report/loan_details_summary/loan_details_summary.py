# Copyright (c) 2024, Nabeel Saleem and contributors
# For license information, please see license.txt

import frappe
from datetime import timedelta, datetime
from frappe import msgprint, _


@frappe.whitelist(allow_guest=True)
def execute(filters=None):
    columns, data = [], []
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    columns = [
        _("Company") + ":Link/Company:140",
        _("Employee ID") + ":Dynamic Link/Employee:140",
        _("Employee Name") + ":Data:140",
        _("Loan Application") + ":Link/Loan Application:140",
        _("Loan Type") + ":Link/Loan Category:140",
    ]
    return columns


def get_data(filters):
    result = get_query_result(filters)
    return result


def get_conditions(filters):
    conditions = ""

    if filters.get("company"):
        conditions += "company = %(company)s"
    # if filters.get("probability"):
    #     if conditions:
    #         conditions += " AND "
    #     conditions += "probability = %(probability)s"

    return conditions


def get_query_result(filters):
    conditions = get_conditions(filters)
    result = frappe.db.sql(
        """
        SELECT 
			company,
			applicant,
			applicant_name, 
            loan_application,
            loan_category
        FROM 
            `tabLoan`
        {0}
    """.format(
            "WHERE " + conditions if conditions else ""
        ),
        filters,
        as_dict=0,
    )

    # frappe.msgprint(f"Result from get_query_result: {result}")
    return result
