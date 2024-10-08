from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import (
    date_diff,
    add_days,
    getdate,
    get_link_to_form,
    getdate,
    format_date,
    nowdate,
    time_diff,
)
from erpnext.setup.doctype.employee.employee import is_holiday


class OverlappingAttendanceRequestError(frappe.ValidationError):
    pass


class AttendanceRequest(Document):
    # Function overide and Changed
    def validate(self):
        date_of_joining = frappe.db.get_value(
            "Employee", self.employee, "date_of_joining"
        )
        # Attendance can not be marked for future dates
        if getdate(self.from_date) > getdate(nowdate()):
            frappe.throw(
                _("Attendance can not be requested for future dates: {0}").format(
                    frappe.bold(format_date(self.from_date)),
                )
            )
        elif date_of_joining and getdate(self.from_date) < getdate(date_of_joining):
            frappe.throw(
                _(
                    "Attendance date {0} can not be less than employee {1}'s joining date: {2}"
                ).format(
                    frappe.bold(format_date(self.from_date)),
                    frappe.bold(self.employee),
                    frappe.bold(format_date(date_of_joining)),
                )
            )

        if not self.custom_from:
            frappe.throw("Please Enter Valid From Time")
        if not self.custom_to:
            frappe.throw("Please Enter Valid To Time")

        f_hr, f_min, f_sec = str(self.custom_from).split(":")
        t_hr, t_min, t_sec = str(self.custom_to).split(":")
        self.custom_from = (
            str(f_hr).zfill(2) + ":" + str(f_min).zfill(2) + ":" + str(f_sec).zfill(2)
        )
        self.custom_to = (
            str(t_hr).zfill(2) + ":" + str(t_min).zfill(2) + ":" + str(t_sec).zfill(2)
        )

        if str(self.custom_to) < str(self.custom_from):
            frappe.throw("To Time Cannot be less than From Time")
        if self.half_day:
            if (
                not getdate(self.from_date)
                <= getdate(self.half_day_date)
                <= getdate(self.to_date)
            ):
                frappe.throw(
                    _("Half day date should be in between from date and to date")
                )

        if self.reason == "Work From Home":
            if not self.work_from_home_request:
                frappe.throw(
                    _("Mandatory field required <b>Work From Home Request</b>")
                )
            self.check_wfh_days()

    def validate_request_overlap(self):
        if not self.name:
            self.name = "New Attendance Request"

        Request = frappe.qb.DocType("Attendance Request")
        overlapping_request = (
            frappe.qb.from_(Request)
            .select(Request.name)
            .where(
                (Request.employee == self.employee)
                & (Request.docstatus < 2)
                & (Request.name != self.name)
                & (self.to_date >= Request.from_date)
                & (self.from_date <= Request.to_date)
            )
        ).run(as_dict=True)

        if overlapping_request:
            self.throw_overlap_error(overlapping_request[0].name)

    def throw_overlap_error(self, overlapping_request: str):
        msg = _(
            "Employee {0} already has an Attendance Request {1} that overlaps with this period"
        ).format(
            frappe.bold(self.employee),
            get_link_to_form("Attendance Request", overlapping_request),
        )

        frappe.throw(
            msg,
            title=_("Overlapping Attendance Request"),
            exc=OverlappingAttendanceRequestError,
        )

    def on_cancel(self):
        attendance_list = frappe.get_all(
            "Attendance",
            {
                "employee": self.employee,
                "attendance_request": self.name,
                "docstatus": 1,
            },
        )
        if attendance_list:
            for attendance in attendance_list:
                attendance_obj = frappe.get_doc("Attendance", attendance["name"])
                attendance_obj.cancel()

    # Custom Function
    def check_wfh_days(self):
        from_date = frappe.db.get_value(
            "Work From Home Request", self.work_from_home_request, "from_date"
        )
        to_date = frappe.db.get_value(
            "Work From Home Request", self.work_from_home_request, "to_date"
        )
        if from_date <= getdate(self.from_date) <= to_date:
            pass
        else:
            frappe.throw(
                "Attendance Request date must be in between {0} and {1}".format(
                    from_date, to_date
                )
            )

    # Function overide and changed
    def on_submit(self):
        emp_user_id = frappe.get_value("Employee", self.employee, "user_id")
        if emp_user_id == frappe.session.user:
            frappe.throw("You can not Submit your own Attendance Request!")
        self.create_attendance_records()

    def create_attendance_records(self):
        request_days = date_diff(self.to_date, self.from_date) + 1
        for day in range(request_days):
            attendance_date = add_days(self.from_date, day)
            if self.should_mark_attendance(attendance_date):
                self.create_or_update_attendance(attendance_date)

    def create_or_update_attendance(self, date: str):
        attendance_name = self.get_attendance_record(date)
        status = self.get_attendance_status(date)
        hours_worked = time_diff(self.custom_to, self.custom_from)

        if attendance_name:
            # update existing attendance, change the status
            doc = frappe.get_doc("Attendance", attendance_name)
            old_date = str(doc.in_time) + " - " + str(doc.out_time)
            f_date = str(self.from_date) + " " + str(self.custom_from)
            t_date = str(self.from_date) + " " + str(self.custom_to)
            new_date = str(f_date) + " - " + str(t_date)
            doc.db_set(
                {
                    "in_time": f_date,
                    "out_time": t_date,
                    "custom_hours_worked": hours_worked,
                }
            )
            frappe.msgprint(
                _(
                    "Updated In-Out Details from {0} to {1} for date {2} in the attendance record {3}"
                ).format(
                    frappe.bold(old_date),
                    frappe.bold(new_date),
                    frappe.bold(format_date(date)),
                    get_link_to_form("Attendance", doc.name),
                ),
                title=_("Attendance Updated"),
            )
            old_status = doc.status

            if old_status != status:
                doc.db_set({"status": status, "attendance_request": self.name})
                text = _(
                    "changed the status from {0} to {1} via Attendance Request"
                ).format(frappe.bold(old_status), frappe.bold(status))
                doc.add_comment(comment_type="Info", text=text)

                frappe.msgprint(
                    _(
                        "Updated status from {0} to {1} for date {2} in the attendance record {3}"
                    ).format(
                        frappe.bold(old_status),
                        frappe.bold(status),
                        frappe.bold(format_date(date)),
                        get_link_to_form("Attendance", doc.name),
                    ),
                    title=_("Attendance Updated"),
                )
            doc.save(ignore_permissions=True)
        else:
            # submit a new attendance record
            doc = frappe.new_doc("Attendance")
            doc.employee = self.employee
            doc.attendance_date = date
            doc.shift = self.shift
            doc.company = self.company
            doc.attendance_request = self.name
            doc.custom_hours_worked = hours_worked
            doc.in_time = str(self.from_date) + " " + str(self.custom_from)
            doc.out_time = str(self.from_date) + " " + str(self.custom_to)
            doc.status = status
            doc.insert(ignore_permissions=True)
            doc.submit()

    def should_mark_attendance(self, attendance_date: str) -> bool:
        # Check if attendance_date is a holiday
        if not self.include_holidays and is_holiday(self.employee, attendance_date):
            frappe.msgprint(
                _("Attendance not submitted for {0} as it is a Holiday.").format(
                    frappe.bold(format_date(attendance_date))
                )
            )
            return False

        # Check if employee is on leave
        if self.has_leave_record(attendance_date):
            frappe.msgprint(
                _("Attendance not submitted for {0} as {1} is on leave.").format(
                    frappe.bold(format_date(attendance_date)),
                    frappe.bold(self.employee),
                )
            )
            return False

        return True

    def has_leave_record(self, attendance_date: str) -> str | None:
        return frappe.db.exists(
            "Leave Application",
            {
                "employee": self.employee,
                "docstatus": 1,
                "from_date": ("<=", attendance_date),
                "to_date": (">=", attendance_date),
            },
        )

    def get_attendance_record(self, attendance_date: str) -> str | None:
        return frappe.db.exists(
            "Attendance",
            {
                "employee": self.employee,
                "attendance_date": attendance_date,
                "docstatus": ("!=", 2),
            },
        )

    def get_attendance_status(self, attendance_date: str) -> str:
        if (
            self.half_day
            and date_diff(getdate(self.half_day_date), getdate(attendance_date)) == 0
        ):
            return "Half Day"
        elif self.reason == "Work From Home":
            return "Work From Home"
        else:
            return "Present"

    @frappe.whitelist()
    def get_attendance_warnings(self) -> list:
        attendance_warnings = []
        request_days = date_diff(self.to_date, self.from_date) + 1

        for day in range(request_days):
            attendance_date = add_days(self.from_date, day)

            if not self.include_holidays and is_holiday(self.employee, attendance_date):
                attendance_warnings.append(
                    {"date": attendance_date, "reason": "Holiday", "action": "Skip"}
                )
            elif self.has_leave_record(attendance_date):
                attendance_warnings.append(
                    {"date": attendance_date, "reason": "On Leave", "action": "Skip"}
                )
            else:
                attendance = self.get_attendance_record(attendance_date)
                if attendance:
                    doc = frappe.get_doc("Attendance", attendance)
                    attendance_warnings.append(
                        {
                            "date": attendance_date,
                            "reason": "Attendance already marked",
                            "record": attendance,
                            "action": "Overwrite",
                            "in_time": doc.in_time,
                            "out_time": doc.out_time,
                        }
                    )
        return attendance_warnings
