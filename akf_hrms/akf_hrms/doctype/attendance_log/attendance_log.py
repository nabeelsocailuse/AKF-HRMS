# Copyright (c) 2024, Nabeel Saleem and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import time_diff, getdate, get_datetime


class AttendanceLog(Document):
	def after_insert(self):
		self.process_log()

	def process_log(self):
		attendance = self.is_attendance_exist()
		if (attendance):
			self.update_attendance(attendance)
		else:
			self.create_attendance()

	def is_attendance_exist(self):
		return frappe.db.get_value("Attendance", 
				{	
					"docstatus": 0,
					"employee": self.employee,
					"attendance_date": self.attendance_date,
				}, ["name", "in_time"], as_dict=1)
	
	def update_attendance(self, attendance):
		frappe.db.set_value("Attendance", attendance.name, "out_time", self.log)
		frappe.db.set_value("Attendance", attendance.name, "custom_hours_worked", self.cal_hours_worked(attendance.in_time))
		frappe.db.set_value("Attendance", attendance.name, "early_exit", self.early_exit())

	def cal_hours_worked(self, in_time):
		return time_diff(str(self.log), str(in_time))
	
	def create_attendance(self):
		args = {
				"doctype": "Attendance",
				"employee": self.employee,
				"attendance_date": self.attendance_date,
				"shift": self.shift,
				"in_time": self.log,
				"late_entry": self.late_entry()
			}
		frappe.get_doc(args).insert()

	def late_entry(self):
		if (not self.shift or not self.log): 
			return False
		doc = frappe.get_doc("Shift Type", self.shift)
		
		if(not doc.enable_auto_attendance): 
			return False
		
		log = get_datetime(self.log)
		grace_datetime = get_datetime("%s %s"%(getdate(), doc.custom_grace_in_time))
		
		if(log>grace_datetime):
			return True

	def early_exit(self):
		if (not self.shift or not self.log): 
			return False
		doc = frappe.get_doc("Shift Type", self.shift)
		
		if(not doc.enable_auto_attendance): 
			return False
		
		log = get_datetime(self.log)
		grace_datetime = get_datetime("%s %s"%(getdate(), doc.custom_grace_out_time))
		
		if(log<grace_datetime):
			return True
