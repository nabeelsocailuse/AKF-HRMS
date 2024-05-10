# Copyright (c) 2024, Nabeel Saleem and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta



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
				-- and custom_overtime_hours>0
				and year(attendance_date) = '{0}'
				and monthname(attendance_date) = '{1}'
				and employee = '{2}'
		""".format(self.year, self.month, self.employee_id), as_dict=1)
		
		self.set("detail_of_overtime", attendance_list)
		self.save()
		return get_total_hours_worked(attendance_list)
		# return attendance_list

def get_total_hours_worked(attendance_list):
	total_hours = 0
	total_minutes = 0
	total_seconds = 0

	# Parse each time string and sum up the total
	for d in attendance_list:
		# Split the time string into hours, minutes, and seconds
		hours, minutes, seconds = map(int, str(d.hours_worked).split(':'))
		
		# Add hours, minutes, and seconds to the totals
		total_hours += hours
		total_minutes += minutes
		total_seconds += seconds

	# Convert excess minutes and seconds to hours
	total_hours += total_minutes // 60
	total_minutes %= 60
	total_hours += total_seconds // 3600
	total_seconds %= 3600
	# Create a timedelta object with the total hours, minutes, and seconds
	total_time = timedelta(hours=total_hours, minutes=total_minutes, seconds=total_seconds)
	return  str(total_time)
