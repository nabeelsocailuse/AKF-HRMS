import frappe
from frappe import _
from datetime import datetime, timedelta
from frappe.model.document import Document

class AttendanceAdjustment(Document):
    def validate(self):
        if self.compensation_date:
            self.check_and_mark_attendance_adjustment()
    def check_and_mark_attendance_adjustment(self):
        attendance_doc = frappe.get_doc("Attendance", {"attendance_date": self.compensation_date, "employee": self.employee})
        if attendance_doc:
            frappe.db.set_value("Attendance", attendance_doc.name, "late_entry", 0)
            frappe.db.set_value("Attendance", attendance_doc.name, "custom_attendance_adjustment", 1)

@frappe.whitelist()
def validate_custom_adjustment_date(custom_adjustment_date, employee):
    if custom_adjustment_date and employee:
        custom_adjustment_date = datetime.strptime(custom_adjustment_date, '%Y-%m-%d').date()
        current_date = datetime.now().date()
        seven_days_ago = current_date - timedelta(days=7)
        
        if custom_adjustment_date < seven_days_ago:
            frappe.throw(_("The Adjustment date must be within the last 7 days."))
        elif custom_adjustment_date > current_date:
            frappe.throw(_("Future dates are not allowed for the Adjustment date."))

        if not frappe.db.exists("Attendance", {"attendance_date": custom_adjustment_date, "employee": employee}):
            frappe.throw(_("Attendance record does not exist on date {0} for employee {1}")
                         .format(custom_adjustment_date, employee))

        attendance = frappe.get_doc("Attendance", {"attendance_date": custom_adjustment_date, "employee": employee})
        if attendance.custom_attendance_adjustment:
            frappe.throw(_("The Adjustment is already availed on {0} against employee {1}")
                         .format(custom_adjustment_date, employee))
        if not attendance.custom_overtime_hours:
            frappe.throw(_("There are no overtime hours against this adjustment date {0}")
                         .format(custom_adjustment_date))

        # Check if an overtime claim is applied for the employee on the custom_adjustment_date
        overtime_claim = frappe.db.sql("""
            SELECT
                ot.name
            FROM
                `tabOvertime Claim Form` ot
            JOIN
                `tabDetails of OT` dot ON ot.name = dot.parent
            WHERE
                ot.employee = %s
                AND dot.date = %s
                AND ot.docstatus < 2
        """, (employee, custom_adjustment_date))

        if overtime_claim:
            frappe.throw(_("Overtime Claim is applied against this employee on {0}")
                         .format(custom_adjustment_date))

        # Return the custom_overtime_hours value
        return attendance.custom_overtime_hours

@frappe.whitelist()
def validate_compensation_date(compensation_date, employee):
    if compensation_date and employee:
        compensation_date = datetime.strptime(compensation_date, '%Y-%m-%d').date()
        current_date = datetime.now().date()
        seven_days_ago = current_date - timedelta(days=7)
        
        if compensation_date < seven_days_ago:
            frappe.throw(_("The Compensation date must be within the last 7 days."))
        elif compensation_date > current_date:
            frappe.throw(_("Future dates are not allowed for the Compensation date."))

        if not frappe.db.exists("Attendance", {"attendance_date": compensation_date, "employee": employee}):
            frappe.throw(_("Attendance record does not exist on date {0} for employee {1}")
                         .format(compensation_date, employee))
        
        # Check if late_entry is marked as 1 in the attendance record
        attendance = frappe.get_doc("Attendance", {"attendance_date": compensation_date, "employee": employee})
        if not attendance.late_entry:
            frappe.throw(_("Late entry check is not marked for the compensation date {0} and employee {1}")
                         .format(compensation_date, employee))