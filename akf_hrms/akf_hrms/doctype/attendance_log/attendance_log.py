# Copyright (c) 2024, Nabeel Saleem and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import time_diff, getdate, get_datetime


class AttendanceLog(Document):
	def after_insert(self):
		self.process_attendance()

	def process_attendance(self):
		attendance = self.get_attendance()
		if (attendance):
			self.update_attendance(attendance)
		else:
			self.create_attendance()

	def get_attendance(self):
		return frappe.db.get_value("Attendance", 
				{	
					"docstatus": 1,
					"employee": self.employee,
					"attendance_date": self.attendance_date,
				}, ["name", "in_time"], as_dict=1)

	def update_attendance(self, attendance):
		frappe.db.set_value("Attendance", attendance.name, "out_time", self.log)
		hours_worked = self.cal_hours_worked(attendance.in_time)
		frappe.db.set_value("Attendance", attendance.name, "custom_hours_worked", hours_worked)
		frappe.db.set_value("Attendance", attendance.name, "custom_overtime_hours", self.cal_overtime_hours(hours_worked))
		frappe.db.set_value("Attendance", attendance.name, "early_exit", self.early_exit())
	
	def cal_hours_worked(self, in_time):
		return time_diff(str(self.log), str(in_time))

	def create_attendance(self):
		args = {
				"doctype": "Attendance",
				"employee": self.employee,
				"attendance_date": self.attendance_date,
				"status": "Present",
				"shift": self.shift,
				"in_time": self.log,
				"late_entry": self.late_entry()
			}
		frappe.get_doc(args).submit()

	def late_entry(self):
		if (not self.shift or not self.log): 
			return False
		doc = frappe.get_doc("Shift Type", self.shift)
		
		if(not doc.enable_auto_attendance or not doc.custom_grace_in_time): 
			return False
		
		log = get_datetime(self.log)
		grace_datetime = get_datetime("%s %s"%(getdate(self.log), doc.custom_grace_in_time))
		
		if(log>grace_datetime):
			return True
		return False

	def early_exit(self):
		if (not self.shift or not self.log): 
			return False
		doc = frappe.get_doc("Shift Type", self.shift)
		
		if(not doc.enable_auto_attendance or not doc.custom_grace_out_time): 
			return False
		
		log = get_datetime(self.log)
		# log_date = 
		grace_datetime = get_datetime("%s %s"%(getdate(self.log), doc.custom_grace_out_time))

		# frappe.throw(str(log<grace_datetime))
		if(log<grace_datetime):
			return True
		return False

	def cal_overtime_hours(self, hours_worked):
		overtime_hours = None
		if(not self.shift): 
			return overtime_hours
		total_working_hours = frappe.db.get_value("Shift Type", self.shift, "custom_total_working_hours")
		if(not total_working_hours): 
			return overtime_hours
		if(hours_worked>total_working_hours):
			overtime_hours = time_diff(str(hours_worked), str(total_working_hours))

		return overtime_hours

@frappe.whitelist()
def get_logs_details(filters=None):
	return frappe.db.sql("""
		select device_ip, log_type, log
		from `tabAttendance Log`
		where
			docstatus=0
			and company=%(company)s
			and employee=%(employee)s
			and attendance_date=%(attendance_date)s
	""", filters, as_dict=1)

