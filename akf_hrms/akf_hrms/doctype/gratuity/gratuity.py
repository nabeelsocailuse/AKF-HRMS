# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


from math import floor

import frappe
from frappe import _, bold
from frappe.query_builder.functions import Sum
from frappe.utils import flt, get_datetime, get_link_to_form

from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.controllers.accounts_controller import AccountsController


class Gratuity(AccountsController):
	def validate(self):
		data = self.calculate_work_experience_and_amount()
		self.current_work_experience = data["current_work_experience"]
		self.amount = data["amount"]
		self.work_experience_duration = data["work_experience_duration"]
		self.set_status()

	@frappe.whitelist()
	def calculate_work_experience_and_amount(self):
		rule = get_gratuity_rule_config(self.gratuity_rule)
		
		# Nabeel Saleem, 02-05-2025
		work_experience = frappe._dict({})
		if(rule.gratuity_by_pass_on_alkhidmat_rule):
			work_experience  = calculate_work_experience_alkhidmat(self.employee)
			
		elif rule.method == "Manual":
			work_experience.update({"current_work_experience": self.current_work_experience})
		else:
			current_work_experience = (
				calculate_work_experience(self.employee, self.gratuity_rule) or 0
			)
			work_experience.update({"current_work_experience": current_work_experience})

		gratuity_amount = (
			calculate_gratuity_amount(
				self.employee, self.gratuity_rule, work_experience.current_work_experience
			)
			or 0
		)

		return work_experience.update({
			# "current_work_experience": current_work_experience,
			"amount": gratuity_amount,
		})

	def set_status(self, update=False):
		precision = self.precision("paid_amount")
		status = None

		if self.docstatus == 0:
			status = "Draft"
		elif self.docstatus == 1:
			if flt(self.paid_amount) > 0 and flt(self.amount, precision) == flt(
				self.paid_amount, precision
			):
				status = "Paid"
			else:
				status = "Unpaid"
		elif self.docstatus == 2:
			status = "Cancelled"

		if update:
			self.db_set("status", status)
		else:
			self.status = status

	def on_submit(self):
		if self.pay_via_salary_slip:
			self.create_additional_salary()
		else:
			self.create_gl_entries()

	def on_cancel(self):
		self.ignore_linked_doctypes = ["GL Entry"]
		self.create_gl_entries(cancel=True)
		self.set_status(update=True)

	def create_gl_entries(self, cancel=False):
		gl_entries = self.get_gl_entries()
		make_gl_entries(gl_entries, cancel)

	def get_gl_entries(self):
		gl_entry = []
		# payable entry
		if self.amount:
			gl_entry.append(
				self.get_gl_dict(
					{
						"account": self.payable_account,
						"credit": self.amount,
						"credit_in_account_currency": self.amount,
						"against": self.expense_account,
						"party_type": "Employee",
						"party": self.employee,
						"against_voucher_type": self.doctype,
						"against_voucher": self.name,
						"cost_center": self.cost_center,
					},
					item=self,
				)
			)

			# expense entries
			gl_entry.append(
				self.get_gl_dict(
					{
						"account": self.expense_account,
						"debit": self.amount,
						"debit_in_account_currency": self.amount,
						"against": self.payable_account,
						"cost_center": self.cost_center,
					},
					item=self,
				)
			)
		else:
			frappe.throw(_("Total Amount can not be zero"))

		return gl_entry

	def create_additional_salary(self):
		if self.pay_via_salary_slip:
			additional_salary = frappe.new_doc("Additional Salary")
			additional_salary.employee = self.employee
			additional_salary.salary_component = self.salary_component
			additional_salary.overwrite_salary_structure_amount = 0
			additional_salary.amount = self.amount
			additional_salary.payroll_date = self.payroll_date
			additional_salary.company = self.company
			additional_salary.ref_doctype = self.doctype
			additional_salary.ref_docname = self.name
			additional_salary.submit()

	def set_total_advance_paid(self):
		gle = frappe.qb.DocType("GL Entry")
		paid_amount = (
			frappe.qb.from_(gle)
			.select(Sum(gle.debit_in_account_currency).as_("paid_amount"))
			.where(
				(gle.against_voucher_type == "Gratuity")
				& (gle.against_voucher == self.name)
				& (gle.party_type == "Employee")
				& (gle.party == self.employee)
				& (gle.docstatus == 1)
				& (gle.is_cancelled == 0)
			)
		).run(as_dict=True)[0].paid_amount or 0

		if flt(paid_amount) > self.amount:
			frappe.throw(_("Row {0}# Paid Amount cannot be greater than Total amount"))

		self.db_set("paid_amount", paid_amount)
		self.set_status(update=True)


def get_gratuity_rule_config(gratuity_rule: str) -> dict:
	return frappe.db.get_value(
		"Gratuity Rule",
		gratuity_rule,
		[
			"work_experience_calculation_function as method",
			"total_working_days_per_year",
			"minimum_year_for_gratuity",
			"gratuity_by_pass_on_alkhidmat_rule"
		],
		as_dict=True,
	)


def calculate_work_experience(employee, gratuity_rule):
	rule = get_gratuity_rule_config(gratuity_rule)

	final_confirmation_date, relieving_date = frappe.db.get_value(
		"Employee", employee, ["final_confirmation_date", "relieving_date"]
	)
	if not relieving_date:
		frappe.throw(
			_("Please set Relieving Date for employee: {0}").format(
				bold(get_link_to_form("Employee", employee))
			)
		)

	employee_total_workings_days = calculate_employee_total_workings_days(
		employee, final_confirmation_date, relieving_date
	)

	current_work_experience = (
		employee_total_workings_days / rule.total_working_days_per_year or 1
	)
	
	current_work_experience = get_work_experience_using_method(
		rule.method, current_work_experience, rule.minimum_year_for_gratuity, employee
	)
	return current_work_experience

def calculate_work_experience_alkhidmat(employee):
	from datetime import datetime
	from dateutil.relativedelta import relativedelta
	# Define the start date
	# start_date = datetime.strptime(final_confirmation_date, "%d-%m-%Y")
	# Get the current date
	# end_date = datetime.strptime(relieving_date, "%d-%m-%Y")
	# Calculate the difference

	gratuity_issuance_date, relieving_date = frappe.db.get_value(
		"Employee", employee, ["custom_gratuity_issuance_date", "relieving_date"]
	)
	
	if not gratuity_issuance_date:
		frappe.throw(
			_("Please set Gratuity Issuance Date for employee: {0}").format(
				bold(get_link_to_form("Employee", employee))
			)
		)

	if not relieving_date:
		frappe.throw(
			_("Please set Relieving Date for employee: {0}").format(
				bold(get_link_to_form("Employee", employee))
			)
		)

	delta = relativedelta(relieving_date, gratuity_issuance_date)
	years = delta.years
	months = delta.months
	days = delta.days
	
	current_work_experience = years
	if(years>0):
		if(months==6 and days>0): 
			current_work_experience += 1
		elif(months>6): 
			current_work_experience += 1
	
	return frappe._dict({
    	"current_work_experience": current_work_experience,
		"work_experience_duration": f"{years} yrs, {months} months, {days} days",
     })

def calculate_employee_total_workings_days(
	employee, final_confirmation_date, relieving_date
):
	employee_total_workings_days = (
		get_datetime(relieving_date) - get_datetime(final_confirmation_date)
	).days
	
	payroll_based_on = (
		frappe.db.get_value("Payroll Settings", None, "payroll_based_on") or "Leave"
	)
	if payroll_based_on == "Leave":
		total_lwp = get_non_working_days(employee, relieving_date, "On Leave")
		employee_total_workings_days -= total_lwp
	elif payroll_based_on == "Attendance":
		total_absents = get_non_working_days(employee, relieving_date, "Absent")
		employee_total_workings_days -= total_absents
		
	return employee_total_workings_days

def get_work_experience_using_method(
	method, current_work_experience, minimum_year_for_gratuity, employee
):
	if method == "Round off Work Experience" and current_work_experience > 1.5:
		current_work_experience = round(current_work_experience)
	else:
		current_work_experience = floor(current_work_experience)

	if current_work_experience < minimum_year_for_gratuity:
		frappe.throw(
			_("Employee: {0} have to complete minimum {1} years for gratuity").format(
				bold(employee), minimum_year_for_gratuity
			)
		)
	return current_work_experience


def get_non_working_days(employee, relieving_date, status):
	filters = {
		"docstatus": 1,
		"status": status,
		"employee": employee,
		"attendance_date": ("<=", get_datetime(relieving_date)),
	}

	if status == "On Leave":
		lwp_leave_types = frappe.get_list("Leave Type", filters={"is_lwp": 1})
		lwp_leave_types = [leave_type.name for leave_type in lwp_leave_types]
		filters["leave_type"] = ("IN", lwp_leave_types)

	record = frappe.get_all(
		"Attendance", filters=filters, fields=["COUNT(name) as total_lwp"]
	)
	return record[0].total_lwp if len(record) else 0


def calculate_gratuity_amount(employee, gratuity_rule, experience):
	applicable_earnings_component = get_applicable_components(gratuity_rule)
	total_applicable_components_amount = get_total_applicable_component_amount(
		employee, applicable_earnings_component, gratuity_rule
	)

	calculate_gratuity_amount_based_on = frappe.db.get_value(
		"Gratuity Rule", gratuity_rule, "calculate_gratuity_amount_based_on"
	)
	gratuity_amount = 0
	slabs = get_gratuity_rule_slabs(gratuity_rule)
	slab_found = False
	year_left = experience

	for slab in slabs:
		if calculate_gratuity_amount_based_on == "Current Slab":
			slab_found, gratuity_amount = calculate_amount_based_on_current_slab(
				slab.from_year,
				slab.to_year,
				experience,
				total_applicable_components_amount,
				slab.fraction_of_applicable_earnings,
			)
			if slab_found:
				break

		elif calculate_gratuity_amount_based_on == "Sum of all previous slabs":
			if slab.to_year == 0 and slab.from_year == 0:
				gratuity_amount += (
					year_left
					* total_applicable_components_amount
					* slab.fraction_of_applicable_earnings
				)
				slab_found = True
				break

			if (
				experience > slab.to_year
				and experience > slab.from_year
				and slab.to_year != 0
			):
				gratuity_amount += (
					(slab.to_year - slab.from_year)
					* total_applicable_components_amount
					* slab.fraction_of_applicable_earnings
				)
				year_left -= slab.to_year - slab.from_year
				slab_found = True
			elif slab.from_year <= experience and (
				experience < slab.to_year or slab.to_year == 0
			):
				gratuity_amount += (
					year_left
					* total_applicable_components_amount
					* slab.fraction_of_applicable_earnings
				)
				slab_found = True

	if not slab_found:
		frappe.throw(
			_(
				"No Suitable Slab found for Calculation of gratuity amount in Gratuity Rule: {0}"
			).format(bold(gratuity_rule))
		)
	return gratuity_amount


def get_applicable_components(gratuity_rule):
	applicable_earnings_component = frappe.get_all(
		"Gratuity Applicable Component",
		filters={"parent": gratuity_rule},
		fields=["salary_component"],
	)
	if len(applicable_earnings_component) == 0:
		frappe.throw(
			_("No Applicable Earnings Component found for Gratuity Rule: {0}").format(
				bold(get_link_to_form("Gratuity Rule", gratuity_rule))
			)
		)
	applicable_earnings_component = [
		component.salary_component for component in applicable_earnings_component
	]

	return applicable_earnings_component


def get_total_applicable_component_amount(
	employee, applicable_earnings_component, gratuity_rule
):
	sal_slip = get_last_salary_slip(employee)
	if not sal_slip:
		frappe.throw(
			_("No Salary Slip is found for Employee: {0}").format(bold(employee))
		)
	component_and_amounts = frappe.get_all(
		"Salary Detail",
		filters={
			"docstatus": 1,
			"parent": sal_slip,
			"parentfield": "earnings",
			"salary_component": ("in", applicable_earnings_component),
		},
		fields=["amount"],
	)
	total_applicable_components_amount = 0
	if not len(component_and_amounts):
		frappe.throw(_("No Applicable Component is present in last month salary slip"))
	for data in component_and_amounts:
		total_applicable_components_amount += data.amount
	return total_applicable_components_amount


def calculate_amount_based_on_current_slab(
	from_year,
	to_year,
	experience,
	total_applicable_components_amount,
	fraction_of_applicable_earnings,
):
	slab_found = False
	gratuity_amount = 0
	if experience >= from_year and (to_year == 0 or experience < to_year):
		gratuity_amount = (
			total_applicable_components_amount
			* experience
			* fraction_of_applicable_earnings
		)
		if fraction_of_applicable_earnings:
			slab_found = True
	
	return slab_found, gratuity_amount


def get_gratuity_rule_slabs(gratuity_rule):
	return frappe.get_all(
		"Gratuity Rule Slab",
		filters={"parent": gratuity_rule},
		fields=["*"],
		order_by="idx",
	)


def get_salary_structure(employee):
	return frappe.get_list(
		"Salary Structure Assignment",
		filters={"employee": employee, "docstatus": 1},
		fields=["from_date", "salary_structure"],
		order_by="from_date desc",
	)[0].salary_structure


def get_last_salary_slip(employee):
	salary_slips = frappe.get_list(
		"Salary Slip",
		filters={"employee": employee, "docstatus": 1},
		order_by="start_date desc",
	)
	if not salary_slips:
		return
	return salary_slips[0].name