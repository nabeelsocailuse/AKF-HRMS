from __future__ import unicode_literals
import frappe
from frappe.query_builder import Criterion
from hrms.hr.doctype.attendance.attendance import Attendance
from frappe.utils import getdate, nowdate, time_diff, time_diff_in_seconds
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_link_to_form, cstr
from hrms.hr.doctype.attendance.attendance import Attendance, get_duplicate_attendance_record


class DuplicateAttendanceError(frappe.ValidationError):
    pass


class Attendance(Attendance):
    # Function override and change
    def validate(self):
        if self.check_in:
            self.check_in = str(self.check_in).split(".")[0]
        if self.check_out:
            self.check_out = str(self.check_out).split(".")[0]
        from erpnext.controllers.status_updater import validate_status
        validate_status(self.status, [
                        "Present", "Absent", "On Leave", "Half Day", "Holiday", "On Travel", "Work From Home"])
        self.validate_attendance_date()
        self.validate_duplicate_record()
        self.check_leave_record()
        self.check_in_out_time()
#################################################################################################################################################
        if self.company == 'HR & FM Services' and self.check_in and self.check_out:
            self.total_worked_time = time_diff(self.check_out, self.check_in)
        if self.company == 'MicroMerger (Pvt.) Ltd.' and self.check_in and self.check_out:
            self.hours_worked = time_diff(self.check_out, self.check_in)

    # Function overide
    def validate_attendance_date(self):
        date_of_joining = frappe.db.get_value(
            "Employee", self.employee, "date_of_joining")
        # leaves can be marked for future dates
        if self.status not in ('On Leave', 'Half Day') and getdate(self.attendance_date) > getdate(nowdate()):
            frappe.throw(_("Attendance can not be marked for future dates"))
        elif date_of_joining and getdate(self.attendance_date) < getdate(date_of_joining):
            frappe.throw(
                _("Attendance date can not be less than employee's joining date"))

    # Function overide
    def validate_duplicate_record(self):
        duplicate = get_duplicate_attendance_record(
            self.employee, self.attendance_date, self.shift)
        # duplicate = get_duplicate_attendance_record(self.employee, self.attendance_date, self.shift)

        if duplicate:
            frappe.throw(
                _("Attendance for employee {0} is already marked for the date {1}: {2}").format(
                    frappe.bold(self.employee),
                    frappe.bold(self.attendance_date),
                    get_link_to_form("Attendance", duplicate[0].name),
                ),
                title=_("Duplicate Attendance"),
                exc=DuplicateAttendanceError,
            )
    # Function overide

    def check_leave_record(self):
        leave_record = frappe.db.sql(
            """
			select leave_type, half_day, half_day_date
			from `tabLeave Application`
			where employee = %s
				and %s between from_date and to_date
				and status = 'Approved'
				and docstatus = 1
		""",
            (self.employee, self.attendance_date),
            as_dict=True,
        )
        if leave_record:
            for d in leave_record:
                self.leave_type = d.leave_type
                if d.half_day_date == getdate(self.attendance_date):
                    self.status = "Half Day"
                    frappe.msgprint(
                        _("Employee {0} on Half day on {1}").format(
                            self.employee, formatdate(self.attendance_date))
                    )
                else:
                    self.status = "On Leave"
                    frappe.msgprint(
                        _("Employee {0} is on Leave on {1}").format(
                            self.employee, formatdate(self.attendance_date))
                    )

        if self.status in ("On Leave", "Half Day"):
            if not leave_record:
                frappe.throw(
                    _("No leave record found for employee {0} on {1}").format(
                        self.employee, formatdate(self.attendance_date)
                    ),
                    alert=1,
                )
        elif self.leave_type:
            self.leave_type = None
            self.leave_application = None

    # Custom Function
    def check_in_out_time(self):
        civ = str(self.check_in).split(":")
        cov = str(self.check_out).split(":")

        self.check_in = str(civ[0]).zfill(2) + ":" + \
            str(civ[1]).zfill(2) + ":" + str(civ[2])
        self.check_out = str(cov[0]).zfill(2) + ":" + \
            str(cov[1]).zfill(2) + ":" + str(cov[2])
        if self.check_in > self.check_out:
            frappe.throw(_("Check out must be greater then check in time!"))

    # Custom Function
    def on_update(self):
        if self.company == 'HR & FM Services' and self.check_in and self.check_out:
            self.total_worked_time = time_diff(self.check_out, self.check_in)
        if self.company == 'MicroMerger (Pvt.) Ltd.' and self.check_in and self.check_out:
            self.hours_worked = time_diff(self.check_out, self.check_in)

    # Custom Function
    def on_update_after_submit(self):
        if self.company == 'HR & FM Services' and self.check_in and self.check_out:
            self.total_worked_time = time_diff(self.check_out, self.check_in)
        if self.company == 'MicroMerger (Pvt.) Ltd.' and self.check_in and self.check_out:
            self.hours_worked = time_diff(self.check_out, self.check_in)

# Custom Function


def mark_absent(employee, attendance_date, shift=None):
    employee_doc = frappe.get_doc('Employee', employee)
    if not frappe.db.exists('Attendance', {'employee': employee, 'attendance_date': attendance_date, 'docstatus': ('!=', '2')}):
        doc_dict = {
            'doctype': 'Attendance',
            'employee': employee,
            'attendance_date': attendance_date,
            'status': 'Absent',
            'company': employee_doc.company,
            'shift': shift
        }
        attendance = frappe.get_doc(doc_dict).insert()
        attendance.submit()
        return attendance.name
# Custom Function


@frappe.whitelist()
def get_emp_data(emp):
    return frappe.db.sql("""select company from `tabEmployee` where name=%s """, (emp))[0][0]
