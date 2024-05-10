from __future__ import unicode_literals
import frappe
from frappe.utils import formatdate, today
from datetime import datetime

@frappe.whitelist()
def send_absent_employee_notification():
    absent_employees = frappe.db.sql("""
        SELECT 
            att.employee,
            att.employee_name,
            emp.department,
            emp.designation,
            GROUP_CONCAT(att.attendance_date) AS absent_dates,
            COUNT(*) AS absent_days,
            (SELECT e.user_id FROM `tabEmployee` AS e WHERE e.employee = emp.reports_to) AS reports_to,            
            emp.user_id
        FROM 
            `tabAttendance` att
        INNER JOIN
            `tabEmployee` emp ON att.employee = emp.employee
        WHERE 
            att.status = 'Absent'
        GROUP BY 
            att.employee
        HAVING 
            COUNT(*) >= 3
    """, as_dict=True)
     
    # Email template
    if absent_employees:
        table_header_absentees = """
            <p>Dear Concerned,</p>
            <p>This email is to notify that the %s is Absent consecutively for the last 03 days. The details are as under.</p>
            <table class="table table-bordered" style="border: 2px solid black; background-color: #f6151;">
                <thead style="background-color: #0b4d80; color: white; text-align: left;">
                <tr>
                    <th style="border: 1px solid black;">Employee ID</th>
                    <th style="border: 1px solid black;">Employee Name</th>
                    <th style="border: 1px solid black;">Department</th>
                    <th style="border: 1px solid black;">Designation</th>
                    <th style="border: 1px solid black;">Absent Dates</th>
                    <th style="border: 1px solid black;">Absent Days</th>
                </tr>
                </thead>
                <tbody>
                
        """

        employee_rows = ""
        for employee in absent_employees:
            
            # Convert absent dates to list of datetime objects
            absent_dates = employee.absent_dates.split(',')
            absent_dates_formatted = []
            absent_day_names = []
            for date_str in absent_dates:
                # Convert date string to datetime object
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                # Format the date as "01 March, 2024" and append to the list
                formatted_date = date_obj.strftime('%d %B, %Y')
                absent_dates_formatted.append(formatted_date)
                # Get the corresponding day name and append to the list
                day_name = date_obj.strftime('%A')
                absent_day_names.append(day_name)

            # Join absent dates and day names into strings
            absent_dates_str = ', '.join(absent_dates_formatted)
            absent_days_str = ', '.join(absent_day_names)

            employee_row = """
                <tr style= "background-color: #d1e0e4; text-align: left;">
                            <td class="text-left" style="border: 1px solid black;">{}</td>
                            <td class="text-left" style="border: 1px solid black;">{}</td>
                            <td class="text-left" style="border: 1px solid black;">{}</td>
                            <td class="text-left" style="border: 1px solid black;">{}</td>
                            <td class="text-left" style="border: 1px solid black;">{}</td>
                            <td class="text-left" style="border: 1px solid black;">{}</td>
                        </tr>
            """.format(employee.get('employee', ''), employee.get('employee_name', ''), employee.get('department', ''), employee.get('designation', ''), absent_dates_str, absent_days_str)
            employee_rows += employee_row
            routing_message = "<p>The email is routed for any further necessary action please.</p>"
        html_content = table_header_absentees%employee.employee_name + employee_rows + "</tbody></table><br>" + routing_message
        # frappe.throw(html_content)

        #Populating the recipients list (HR Manager, Reports_to and Absent Employee User ID)
        recipients = []
<<<<<<< HEAD
        if hr_manager_email:
            recipients.append(hr_manager_email)
        if hr_user_email:
            recipients.append(hr_user_email)
            
        # Concatenating email addresses into a comma-separated string
        recipient_emails = ", ".join(recipients)
=======

        # Extracting email addresses of absent employees, their reporting managers, and HR Managers
        for employee in absent_employees:
            # Add email address of the absent employee
            if employee.get('user_id'):
                recipients.append(employee.get('user_id'))
            # Add email address of the reporting manager
            if employee.get('reports_to'):
                recipients.append(employee.get('reports_to'))
>>>>>>> 3c82d97 (Attendance module completed. zk tool upgrade tables of employee and log details.)
        
        # Fetch HR Manager's email addresses
        hr_manager_email = frappe.db.sql("""
            SELECT u.email 
            FROM `tabUser` AS u 
            INNER JOIN `tabHas Role` AS h ON (u.name = h.parent) 
            WHERE u.name NOT IN ("Administrator") 
            AND h.role = 'HR Manager' 
            GROUP BY u.name
        """, as_dict=False)

        # Extracting email addresses from the result
        recipients.extend([row[0] for row in hr_manager_email])

        # Remove duplicates from the recipients list
        recipients = list(set(recipients))

        # Convert recipients list to a formatted string
        recipients_str = "<br>".join(recipients)

        # Display recipients using frappe.msgprint
        frappe.msgprint(f"Recipients:<br>{recipients_str}")
        # Send email only if there are recipients and html content
        if recipients and html_content:
            frappe.sendmail(
                recipients=recipients,
                subject='Notification of the Absence of the Employee',
                message=html_content,
            )

