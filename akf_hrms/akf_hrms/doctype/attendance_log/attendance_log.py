# Copyright (c) 2024, Nabeel Saleem and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import time_diff


class AttendanceLog(Document):
	def after_insert(self):
		attendance = frappe.db.get_value("Attendance", {"attendance_date": self.attendance_date}, ["name", "in_time"], as_dict=1)
		if (attendance):
			frappe.db.set_value("Attendance", attendance.name, "out_time", self.log)
			hours_worked = time_diff(str(self.log), str(attendance.in_time))
			frappe.db.set_value("Attendance", attendance.name, "custom_hours_worked", hours_worked)
		else:
			args = {
				"doctype": "Attendance",
				"employee": self.employee,
				"attendance_date": self.attendance_date,
				"shift": self.shift,
				"in_time": self.log,
			}
			frappe.get_doc(args).insert()
		
