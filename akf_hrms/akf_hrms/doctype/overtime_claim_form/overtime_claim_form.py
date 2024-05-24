# Copyright (c) 2024, Nabeel Saleem and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import fmt_money, money_in_words, get_link_to_form, get_timedelta
MONTHSLIST = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

class OvertimeClaimForm(Document):
	def autoname(self):
		from frappe.model.naming import make_autoname
		self.name = make_autoname(self.naming_series%{
			"employee": self.employee, 
			"month": self.month, 
			"year": self.year
			})

	def validate(self):
		self.already_applied_for_overtime()

	def already_applied_for_overtime(self):
		name = frappe.db.get_value("Overtime Claim Form", {
			"docstatus": ["<", 2],
			"year": self.year,
			"month": self.month,
			"employee": self.employee,
			"name": ["!=", self.name]
		}, "name")
		if(name):
			link_to_form = get_link_to_form("Overtime Claim Form", name, "Overtime Claim Form")

			frappe.throw(f"{link_to_form} on {self.month}-{self.year}", title="APPLIED")
	
	def on_submit(self):
		self.create_additional_salary()

	def create_additional_salary(self):
		payroll_date = f"{self.year}-{MONTHSLIST.index(self.month)}-21"
		frappe.get_doc({
			"doctype": "Additional Salary",
			"employee": self.employee,
			"payroll_date": payroll_date,
			"salary_component": "Overtime",
			"overwrite_salary_structure_amount": 0,
			"amount": self.amount_in_figures,
		}).submit()
		frappe.msgprint("Addtional Salary has been created.", alert=1)
	
	def on_cancel(self):
		pass

	@frappe.whitelist()
	def get_details_of_overtime(self):
		self.already_applied_for_overtime()
		attendance_list = self.get_attendance()
		self.set("detail_of_overtime", attendance_list)
		self.set("total_hours_worked", get_total_hours_worked(attendance_list))
		self.set("total_overtime_hours", get_total_overtime_hours(attendance_list))
		self.set_overtime_rate_calculate_amount_in_figures()
		return True if(attendance_list) else False
	
	def get_attendance(self):
		return frappe.db.sql(""" 
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
		""".format(self.year, self.month, self.employee), as_dict=1)

	def set_overtime_rate_calculate_amount_in_figures(self):
		ssa = self.get_salary_structure_assignment()
		if(not ssa): return
		hourly_base =  ssa["hourly_base"]
		self.set("hourly_rate", hourly_base)
		_seconds_ = get_timedelta(self.total_overtime_hours or 0)
		total_overtime_hours = (_seconds_.seconds)/3600
		amount_in_figures = float(total_overtime_hours) * float(hourly_base)
		self.set("amount_in_figures", amount_in_figures)
		self.set("amount_in_words", money_in_words(amount_in_figures))

	@frappe.whitelist()
	def get_salary_structure_assignment(self):
		ssa = {}
		result = frappe.db.sql(f""" 
			Select 
				name, salary_structure, base, custom_hourly_base, (custom_hourly_base) as hourly_base
			From 
				`tabSalary Structure Assignment` ssa
			Where
				docstatus = 1
				and employee = "{self.employee}"
			Order by
				from_date desc
			Limit 
				1
		""", as_dict=1)

		for d in result:
			ssa = d
			ssa["base"] = fmt_money(ssa["base"], currency="PKR")
			ssa["custom_hourly_base"] = fmt_money(ssa["hourly_base"], currency="PKR")
		
		return ssa

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
