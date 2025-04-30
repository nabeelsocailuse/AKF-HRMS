import frappe
from datetime import datetime

def get_one_day_salary(employee):
    posting_date = datetime.today()

    assignment = frappe.get_all("Salary Structure Assignment",
        filters={
            "employee": employee,
            "from_date": ["<=", posting_date]
        },
        fields=["base", "from_date"],
        order_by="from_date desc",
        limit=1
    )

    if not assignment:
        frappe.throw(f"No Salary Structure Assignment found for employee {employee}")

    monthly_salary = assignment[0].base

    if monthly_salary:
        return round(monthly_salary / 30, 2)
    else:
        return 0
