#To check the employee who got absent for three consecutive days
# C:\Users\Acer\AppData\Local\Temp\fz3temp-2\custom_cron.py
import frappe
@frappe.whitelist()
def check_absent_employees():
    # Query employees who are absent for three consecutive days
    absent_employees = frappe.db.sql("""
        SELECT employee
        FROM `tabAttendance`
        WHERE status = 'Absent'
        GROUP BY employee
        HAVING COUNT(*) >= 3
    """, as_dict=True)


    # Notify or perform actions for absent employees
    for employee in absent_employees:
         frappe.msgprint(f"Employee {employee.employee} has been absent for three consecutive days.")
