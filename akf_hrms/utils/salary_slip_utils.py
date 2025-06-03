import frappe

from hrms.payroll.doctype.payroll_entry.payroll_entry import (
	get_start_end_dates,
	get_end_date
)
from frappe.utils import (
	add_to_date,
	date_diff,
	getdate,
	get_datetime
)

def get_taxable_salary_percentage(company):
	return frappe.get_value(
			"Company",
			{"name": company, "custom_enable_taxable_percentage": 1},
			(
				"custom_taxable_salary_percentage"
			)
		)

# Nabeel Saleem, 11-02-2025
def get_salary_percent_taxable_amount(self, salary_component, amount):
	set_salary_structure_assignment(self)
	if(salary_component=="Basic"): 
		taxable_salary_percentage = get_taxable_salary_percentage(self.company)
		
		if (taxable_salary_percentage):
			if (taxable_salary_percentage>0.0):
				amount = self._salary_structure_assignment.base * (taxable_salary_percentage/100)
				return amount
	return amount

# Nabeel Saleem, 12-02-2025
def get_pre_salary_percent_taxable_amount(
	self,
	# employee,
	start_date,
	end_date,
	parentfield,
	salary_component=None,
	is_tax_applicable=None,
	is_flexible_benefit=0,
	exempted_from_income_tax=0,
	variable_based_on_taxable_salary=0,
	field_to_select="amount"
):
	ss = frappe.qb.DocType("Salary Slip")
	sd = frappe.qb.DocType("Salary Detail")
	
	if field_to_select == "amount":
		field = sd.amount
	else:
		field = sd.additional_amount
	query = (
		frappe.qb.from_(ss)
		.join(sd)
		.on(sd.parent == ss.name)
		.select(sd.parent,sd.salary_component, sd.amount)
		.where(sd.parentfield == parentfield)
		.where(sd.is_flexible_benefit == is_flexible_benefit)
		.where(sd.is_tax_applicable == 1)
		.where(ss.docstatus == 1)
		.where(ss.employee == self.employee)
		.where(ss.start_date.between(start_date, end_date))
		.where(ss.end_date.between(start_date, end_date))
	)
	# frappe.msgprint(f"{start_date} {end_date}")
	result = query.run(as_dict=True)
	# frappe.throw(f"{result}")
	pre_taxable_earnings = 0.0
	for d in result:
		# if(d.is_tax_applicable): 
		pre_taxable_earnings += get_salary_percent_taxable_amount(self, d.salary_component, d.amount)
		# print(f"d: {d}")
		# frappe.msgprint(f"{pre_taxable_earnings}")
	# print(f"---pre_taxable_earnings: {pre_taxable_earnings}")
	return pre_taxable_earnings

# Nabeel Saleem, 11-02-2025
def get_income_tax_additional_salary(eval_locals):
	""" get_additional_salaries(employee, start_date, end_date, component_type) """
	
	if(eval_locals.employee and eval_locals.start_date and eval_locals.end_date):
		amount = frappe.db.get_value("Additional Salary", 
				{
					"docstatus": 1,
					"salary_component": "Income Tax",
					"employee": eval_locals.employee, 
					"payroll_date": ["between", [eval_locals.start_date, eval_locals.end_date]]
		}, "amount") or None
		
		if(amount):
			return (amount)
	return None

# 05-05-2025
def set_salary_structure_assignment(self):
	self.custom_salary_structure_assignment = self._salary_structure_assignment.name
	self.custom_gross_salary = self._salary_structure_assignment.base

""" Created by Nabeel Saleem on 19-05-2025"""
@frappe.whitelist()
def apply_akf_payroll_settings(self):
	doctype = "AKF Payroll Settings"
	if(not frappe.db.exists("DocType", doctype)): return False

	payroll_settings = frappe.get_single(doctype)
	if(not hasattr(payroll_settings, "apply_21st_to_20th_salary_rule")): return False
	
	self.custom_apply_21st_to_20th_salary_rule = payroll_settings.apply_21st_to_20th_salary_rule

def get_date_details_21st_to_20th_salary_rule(self):
	if(self.custom_apply_21st_to_20th_salary_rule):
		# date_details = get_start_end_dates(self.payroll_frequency, self.custom_by_pass_start_date or self.posting_date)
		# self.custom_by_pass_start_date = date_details.start_date 
		# self.custom_by_pass_end_date = date_details.end_date
		by_pass_start_end_dates(self) # Nabeel Saleem, 18-05-2025

def by_pass_start_end_dates(self): # Nabeel Saleem, 18-05-2025
	from hrms.payroll.doctype.payroll_entry.payroll_entry import get_month_details
	
	frequency = self.payroll_frequency
	frequency = frequency.lower() if frequency else "monthly"
	
	monthDetails = date_diff(self.end_date, self.start_date)

	month_21th = add_to_date(self.start_date, months=-1, days=20)
	month_20th = add_to_date(month_21th, days=monthDetails)
	nxt_20th = getdate(get_datetime(month_20th).replace(day=20))
	
	
	if(frequency=="bimonthly"):
		nxt_20th = add_to_date(month_21th, days=14)
	elif(frequency=="fortnightly"):
		nxt_20th = add_to_date(month_21th, days=13)
	elif(frequency=="weekly"):
		nxt_20th = add_to_date(month_21th, days=6)
	elif(frequency=="daily"):
		nxt_20th = add_to_date(month_21th, days=0)
	
	# self.custom_by_pass_start_date = month_21th
	# self.custom_by_pass_end_date = nxt_20th
	
	self.custom_start_date_21st_of_last_month = month_21th
	self.custom_end_date_20th_of_current_month = nxt_20th

	ded_21th = add_to_date(self.start_date, months=-2, days=20)
	ded_20th = getdate(get_datetime(add_to_date(ded_21th, days=monthDetails)).replace(day=20))
	
	self.custom_deduction_start_date = ded_21th
	self.custom_deduction_end_date = ded_20th
	# self.end_date = nxt_20th.get("end_date")
