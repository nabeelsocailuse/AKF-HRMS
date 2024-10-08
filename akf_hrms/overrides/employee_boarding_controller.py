# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe import _
from frappe.desk.form import assign_to
from frappe.model.document import Document
from frappe.utils import add_days, flt, unique


from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee
from erpnext.setup.doctype.holiday_list.holiday_list import is_holiday


class OverrideEmployeeBoardingController(Document):
    """
    Create the project and the task for the boarding process
    Assign to the concerned person and roles as per the onboarding/separation template
    """

    def validate(self):
        # remove the task if linked before submitting the form
        self.update_status()
<<<<<<< Updated upstream
=======

    def update_status(self):
        for d in self.activities:
            if(d.custom_completed):
                self.db_set("boarding_status", "In Process")
>>>>>>> Stashed changes

    def update_status(self):
        for d in self.activities:
            if(d.custom_completed):
                self.db_set("boarding_status", "In Process")
                
    def on_submit(self):
        self.db_set("boarding_status", "Completed")
        self.reload()

    def create_task_and_notify_user(self):
        pass
        
    def get_holiday_list(self):
        if self.doctype == "Employee Separation":
            return get_holiday_list_for_employee(self.employee)
        else:
            if self.employee:
                return get_holiday_list_for_employee(self.employee)
            else:
                if not self.holiday_list:
                    frappe.throw(
                        _("Please set the Holiday List."), frappe.MandatoryError
                    )
                else:
                    return self.holiday_list

    def get_task_dates(self, activity, holiday_list):
        start_date = end_date = None

        if activity.begin_on is not None:
            start_date = add_days(self.boarding_begins_on, activity.begin_on)
            start_date = self.update_if_holiday(start_date, holiday_list)

            if activity.duration is not None:
                end_date = add_days(
                    self.boarding_begins_on, activity.begin_on + activity.duration
                )
                end_date = self.update_if_holiday(end_date, holiday_list)

        return [start_date, end_date]

    def update_if_holiday(self, date, holiday_list):
        while is_holiday(holiday_list, date):
            date = add_days(date, 1)
        return date

    def assign_task_to_users(self, task, users):
        for user in users:
            args = {
                "assign_to": [user],
                "doctype": task.doctype,
                "name": task.name,
                "description": task.description or task.subject,
                "notify": self.notify_users_by_email,
            }
            assign_to.add(args)

    def on_cancel(self):
        # delete task project
        project = self.project
        for task in frappe.get_all("Task", filters={"project": project}):
            frappe.delete_doc("Task", task.name, force=1)
        frappe.delete_doc("Project", project, force=1)
        self.db_set("project", "")
        for activity in self.activities:
            activity.db_set("task", "")

        frappe.msgprint(
            _("Linked Project {} and Tasks deleted.").format(project),
            alert=True,
            indicator="blue",
        )


@frappe.whitelist()
def get_onboarding_details(parent, parenttype):
    return frappe.get_all(
        "Employee Boarding Activity",
        fields=[
            "activity_name",
            "role",
            "user",
            "required_for_employee_creation",
            "description",
            "task_weight",
            "begin_on",
            "duration",
        ],
        filters={"parent": parent, "parenttype": parenttype},
        order_by="idx",
    )


def update_employee_boarding_status(project, event=None):
    employee_onboarding = frappe.db.exists(
        "Employee Onboarding", {"project": project.name}
    )
    employee_separation = frappe.db.exists(
        "Employee Separation", {"project": project.name}
    )

    if not (employee_onboarding or employee_separation):
        return

    status = "Pending"
    if flt(project.percent_complete) > 0.0 and flt(project.percent_complete) < 100.0:
        status = "In Process"
    elif flt(project.percent_complete) == 100.0:
        status = "Completed"

    if employee_onboarding:
        frappe.db.set_value(
            "Employee Onboarding", employee_onboarding, "boarding_status", status
        )
    elif employee_separation:
        frappe.db.set_value(
            "Employee Separation", employee_separation, "boarding_status", status
        )


def update_task(task, event=None):
    if task.project and not task.flags.from_project:
        update_employee_boarding_status(frappe.get_cached_doc("Project", task.project))