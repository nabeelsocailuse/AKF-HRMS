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
            emp.reports_to
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
                    <th style="border: 1px solid black;">Employee</th>
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
        html_content = table_header_absentees%employee.employee_name + employee_rows + "</tbody></table><br>"
        frappe.throw(html_content)

        if html_content:
            frappe.sendmail(
                recipients=['maarijsiddiqui01@gmail.com'],
                subject=(' Notification of the Absence of the Employee: {employee} - {employee_name} '),
                message=html_content,
            )
