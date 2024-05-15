# Copyright (c) 2024, Nabeel Saleem and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class OvertimeClaimForm(Document):
	def autoname(self):
		from frappe.model.naming import make_autoname
		self.name = make_autoname(self.naming_series%{
			"employee_id": self.employee_id, 
			"month": self.month, 
			"year": self.year
			})

	@frappe.whitelist()
	def get_details_of_overtime(self):
		attendance_list = frappe.db.sql(""" 
			Select (attendance_date) as date, in_time, out_time, 
				(custom_total_working_hours) as total_working_hours,
				(custom_hours_worked) as hours_worked,
				(custom_overtime_hours) as overtime_hours
			From `tabAttendance`
			Where
				docstatus=1
				and ifnull(custom_overtime_hours, "")!=""
				and year(attendance_date) = '{0}'
				and monthname(attendance_date) = '{1}'
				and employee = '{2}'
		""".format(self.year, self.month, self.employee_id), as_dict=1)
		
		self.set("detail_of_overtime", attendance_list)
		self.set("total_hours_worked", get_total_hours_worked(attendance_list))
		self.set("total_overtime_hours", get_total_overtime_hours(attendance_list))
		return True if(attendance_list) else False

def get_total_hours_worked(hours_worked_time_list):
	total_h_worked= '0'	
	hours_worked_ = 0
	for tm in hours_worked_time_list:
		timeParts = [int(s) for s in str(tm.hours_worked).split(':')]
		hours_worked_ += (timeParts[0] * 60 + timeParts[1]) * 60 + timeParts[2]
	hours_worked_, sec = divmod(hours_worked_, 60)
	hr, min_ = divmod(hours_worked_, 60)
	total_h_worked = '{}:{}'.format(int(hr), str(str(int(min_)).zfill(2)))
	return total_h_worked

def get_total_overtime_hours(hours_worked_time_list):
	total_h_worked= '0'	
	hours_worked_ = 0
	for tm in hours_worked_time_list:
		timeParts = [int(s) for s in str(tm.overtime_hours).split(':')]
		hours_worked_ += (timeParts[0] * 60 + timeParts[1]) * 60 + timeParts[2]
	hours_worked_, sec = divmod(hours_worked_, 60)
	hr, min_ = divmod(hours_worked_, 60)
	total_h_worked = '{}:{}'.format(int(hr), str(str(int(min_)).zfill(2)))
	return total_h_worked
