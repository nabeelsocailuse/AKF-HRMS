# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


# from hrms.controllers.employee_boarding_controller import EmployeeBoardingController

from akf_hrms.overrides.employee_boarding_controller import (
    OverrideEmployeeBoardingController,
)


class EmployeeSeparation(OverrideEmployeeBoardingController):
    def validate(self):
        super(EmployeeSeparation, self).validate()

    def on_submit(self):
        super(EmployeeSeparation, self).on_submit()

    def on_update_after_submit(self):
        self.create_task_and_notify_user()

    def on_cancel(self):
        super(EmployeeSeparation, self).on_cancel()
