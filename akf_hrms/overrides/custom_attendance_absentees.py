import frappe
from frappe import _
from hrms.hr.doctype.attendance.attendance import Attendance 

class empabsentemail(Attendance):
    def before_save(self):
        if self.status == 'Absent':
            self.send_absence_email_to_supervisor()

    def send_absence_email_to_supervisor(self):
    # Construct the SQL query to select employees who have been absent for three consecutive days
    sql_query = """
        SELECT e.name AS employee_name, a.date AS absence_date
        FROM `tabAttendance` a
        JOIN `tabEmployee` e ON a.employee = e.name
        WHERE a.status = 'Absent'
        AND a.date >= DATE_SUB(CURDATE(), INTERVAL 3 DAY)
        GROUP BY e.name, a.date
        HAVING COUNT(a.date) = 3
    """

    # Execute the SQL query
    results = frappe.db.sql(sql_query, as_dict=True)

    # Iterate over the results
    for result in results:
        employee_name = result.get('employee_name')
        absence_date = result.get('absence_date')

        # Fetch supervisor email and send the email
        supervisor = frappe.get_value("Employee", employee_name, "supervisor")
        if supervisor:
            email_content = frappe.utils.email.get_email_template('Absence Email to Supervisor', {
                'employee_name': employee_name,
                'absence_date': absence_date
            })
            frappe.sendmail(recipients=[supervisor], subject='Employee Absence', message=email_content)


