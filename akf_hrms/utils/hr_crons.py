# This file is created by Mubashir on 16-01-2025 to define all the cron jobs for AKF-HRMS app.

import frappe

"""
This function is to notify the employee managers (employee.reports_to) before 15 days of job period.
Due to the lack of complete requirements, we'll assume the term period as 3 months and we'll notify 
the managers after 2.5 months.
"""
@frappe.whitelist()
def notify_managers_for_contract_probation_interns():
    today = frappe.utils.today()
    notification_date = frappe.utils.add_days(today, -75)

    employees = frappe.get_all(
        "Employee",
        filters = {
            "date_of_joining": notification_date,
            "employment_type": ["in", ["Permanent", "Intern", "Contract"]],
            "status": "Active"
        },
        fields = ["name", "employee_name", "reports_to", "employment_type", "date_of_joining"]
    )

    for employee in employees:
        if employee.reports_to:
            manager = frappe.get_value("Employee", employee.reports_to, "user_id")
            if not manager:
                continue
            
            end_date = frappe.utils.add_days(employee.date_of_joining, 90)
            remaining_days = frappe.utils.date_diff(end_date, today)
            subject = f"Probation/Internship Period Ending Soon - {employee.employee_name}"
            message = f"""
                <div style="font-family: Arial, sans-serif; padding: 20px;">
                    <p>Dear Manager,</p>
                    
                    <p>This is to inform you that the {employee.employment_type.lower()} period for <strong>{employee.employee_name}</strong> 
                    is about to end in <strong>{remaining_days} days</strong> (on {end_date}).</p>
                    
                    <p>Please take necessary actions regarding their continuation/extension.</p>
                    
                    <p>Regards,<br>HR Team</p>
                </div>
            """.strip()
            
            try:
                frappe.sendmail(
                    recipients = [manager],
                    subject = subject,
                    message = message
                )
                frappe.logger().info(f"Notification sent to {manager} for employee {employee.name}")
                print(f"Notification sent to {manager} for employee {employee.name}")
            except Exception as e:
                frappe.logger().error(f"Failed to send notification for employee {employee.name}: {str(e)}")
                print(f"Failed to send notification for employee {employee.name}: {str(e)}")

# akf_hrms.utils.hr_crons.notify_managers_for_contract_probation_interns