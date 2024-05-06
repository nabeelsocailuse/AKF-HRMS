# update_total_duration.py

import frappe
from datetime import datetime

def update_total_duration():
    # Get all employees
    employees = frappe.get_all("Employee", filters={}, fields=["name", "date_of_joining"])

    for employee in employees:
        date_of_joining = employee.date_of_joining
        employee_name = employee.name

        # Calculate total duration
        now = datetime.now()
        delta = now - date_of_joining

        years = delta.days // 365
        months = (delta.days % 365) // 30

        total_duration = f"{years}Y {months}Months"

        # Update custom_total_duration field
        frappe.db.set_value("Employee", employee_name, "custom_total_duration", total_duration)

# If you want to test this function, uncomment the line below
# update_total_duration()
