# Module overriden by Mubashir


import json
import math

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import cint, flt, rounded
from datetime import datetime, timedelta, date

from lending.loan_management.doctype.loan.loan import (
	get_sanctioned_amount_limit,
	get_total_loan_amount,
)
from lending.loan_management.doctype.loan_repayment_schedule.loan_repayment_schedule import (
	get_monthly_repayment_amount,
)
from lending.loan_management.doctype.loan_security_price.loan_security_price import (
	get_loan_security_price,
)


class LoanApplication(Document):
	def validate(self):
		self.set_pledge_amount()
		self.set_loan_amount()
		self.validate_loan_amount()

		if self.is_term_loan:
			self.validate_repayment_method()

		self.validate_loan_product()

		self.get_repayment_details()
		self.check_sanctioned_amount_limit()
		self.validations()
		self.check_overall_loan_limit()		# Mubashir Bashir 13-11-2024
		self.advance_salary()
	
	# Mubashir Bashir Start 13-11-2024
	def on_submit(self):
		self.check_overall_loan_limit()
	# Mubashir Bashir End 13-11-2024


	def validate_repayment_method(self):
		if self.repayment_method == "Repay Over Number of Periods" and not self.repayment_periods:
			frappe.throw(_("Please enter Repayment Periods"))

		if self.repayment_method == "Repay Fixed Amount per Period":
			if not self.repayment_amount:
				frappe.throw(_("Please enter repayment Amount"))
			if self.repayment_amount > self.loan_amount:
				frappe.throw(_("Monthly Repayment Amount cannot be greater than Loan Amount"))

	def validate_loan_product(self):
		company = frappe.get_value("Loan Product", self.loan_product, "company")
		if company != self.company:
			frappe.throw(_("Please select Loan Product for company {0}").format(frappe.bold(self.company)))

	def validate_loan_amount(self):
		if not self.loan_amount:
			frappe.throw(_("Loan Amount is mandatory"))

		maximum_loan_limit = frappe.db.get_value(
			"Loan Product", self.loan_product, "maximum_loan_amount"
		)
		if maximum_loan_limit and self.loan_amount > maximum_loan_limit:
			frappe.throw(
				_("Loan Amount cannot exceed Maximum Loan Amount of {0}").format(maximum_loan_limit)
			)

		if self.maximum_loan_amount and self.loan_amount > self.maximum_loan_amount:
			frappe.throw(
				_("Loan Amount exceeds maximum loan amount of {0} as per proposed securities").format(
					self.maximum_loan_amount
				)
			)

	def check_sanctioned_amount_limit(self):
		sanctioned_amount_limit = get_sanctioned_amount_limit(
			self.applicant_type, self.applicant, self.company
		)

		if sanctioned_amount_limit:
			total_loan_amount = get_total_loan_amount(self.applicant_type, self.applicant, self.company)

		if sanctioned_amount_limit and flt(self.loan_amount) + flt(total_loan_amount) > flt(
			sanctioned_amount_limit
		):
			frappe.throw(
				_("Sanctioned Amount limit crossed for {0} {1}").format(
					self.applicant_type, frappe.bold(self.applicant)
				)
			)

	def advance_salary(self):
		# frappe.msgprint("Advanced Salary!")
		required_days = 10
		permanent_employee = frappe.db.get_value("Employee", {"name": self.applicant}, "employment_type")

		if frappe.db.exists("Loan Application", {
			"applicant": self.applicant, 
			"docstatus": 1,
			"loan_product": "Advance Salary"
		}):
			frappe.throw("You have already applied for Advanced Salary and cannot apply again.")
			return

		if permanent_employee == "Permanent":
			if self.loan_product == "Advance Salary":
				today = datetime.now()

				if self.posting_date:
					try:
						posting_date = datetime.strptime(self.posting_date, '%Y-%m-%d')
						current_month = today.month
						current_year = today.year

						if posting_date.month == current_month and posting_date.year == current_year:
							if posting_date.day > required_days:
								gross_salary = frappe.db.get_value(
									"Salary Structure Assignment",
									{"employee": ["like", f"{self.applicant}%"], "docstatus": 1},
									"base"
								)

								if gross_salary:
									assigned_gross_salary = gross_salary / 2
									if float(assigned_gross_salary) < float(self.loan_amount):
										frappe.throw(f"The requested amount exceeds the limit PKR: {assigned_gross_salary}")
										return
							else:
								frappe.throw("Cannot apply for advanced salary before the 10th of the current month.")
						else:
							frappe.throw("Advanced Salary Application must be within the current month.")
					except ValueError:
						frappe.throw("Posting date is not in the correct format. Please use 'YYYY-MM-DD'.")
				else:
					frappe.throw("Posting date is required.")

	# def validations(self):		# Mubashir Bashir Start 13-11-2024
		if self.loan_product == "Vehicle Loan" or self.loan_product == "Bike Loan":

			today = datetime.now()
			required_experience_days = 730  

			permanent_employee = frappe.db.get_value("Employee", {"name": self.applicant}, "employment_type")

			if self.loan_product == "Vehicle Loan" and frappe.db.exists("Loan Application", {
				"applicant": self.applicant, 
				"docstatus": 1
			}):
				frappe.throw("You have already applied for Loan cannot apply again.")
				return

			if permanent_employee == "Permanent":
				guarantor_1 = self.custom_guarantor_of_loan_application
				date_of_joining_1 = frappe.db.get_value("Employee", {"name": guarantor_1}, "date_of_joining")

				guarantor_2 = self.custom_guarantor_2_of_loan_application
				date_of_joining_2 = frappe.db.get_value("Employee", {"name": guarantor_2}, "date_of_joining")
													
				# Check if the guarantors have existing loan applications
				if frappe.db.exists("Loan Application", {
					"applicant": guarantor_1,
					"docstatus": 1
				}):
					frappe.throw(f"Guarantor {guarantor_1} already has an active loan application.")
				
				if frappe.db.exists("Loan Application", {
					"applicant": guarantor_2,
					"docstatus": 1
				}):
					frappe.throw(f"Guarantor {guarantor_2} already has an active loan application.")

				# Check if the guarantors are already guarantors in other loan applications
				if frappe.db.exists("Loan Application", {
					"custom_guarantor_of_loan_application": guarantor_1,
					"docstatus": 1
				}) or frappe.db.exists("Loan Application", {
					"custom_guarantor_2_of_loan_application": guarantor_1,
					"docstatus": 1
				}):
					frappe.throw(f"Guarantor {guarantor_1} is already acting as a guarantor for another loan application.")

				if frappe.db.exists("Loan Application", {
					"custom_guarantor_of_loan_application": guarantor_2,
					"docstatus": 1
				}) or frappe.db.exists("Loan Application", {
					"custom_guarantor_2_of_loan_application": guarantor_2,
					"docstatus": 1
				}):
					frappe.throw(f"Guarantor {guarantor_2} is already acting as a guarantor for another loan application.")

				# Mubashir Bashir End 13-11-2024


				# Convert date_of_joining to datetime if it's a date
				if isinstance(date_of_joining_1, datetime):
					date_of_joining_1_dt = date_of_joining_1
				else:
					date_of_joining_1_dt = datetime.combine(date_of_joining_1, datetime.min.time())

				if isinstance(date_of_joining_2, datetime):
					date_of_joining_2_dt = date_of_joining_2
				else:
					date_of_joining_2_dt = datetime.combine(date_of_joining_2, datetime.min.time())

				experience_valid_1 = date_of_joining_1_dt and (today - date_of_joining_1_dt).days >= required_experience_days
				experience_valid_2 = date_of_joining_2_dt and (today - date_of_joining_2_dt).days >= required_experience_days

				if not experience_valid_1:
					if not date_of_joining_1:
						frappe.throw(f"Guarantor {guarantor_1} does not have a valid date of joining.")
					else:
						frappe.throw(f"Guarantor {guarantor_1} should have at least 2 years of experience.")

				if not experience_valid_2:
					if not date_of_joining_2:
						frappe.throw(f"Guarantor {guarantor_2} does not have a valid date of joining.")
					else:
						frappe.throw(f"Guarantor {guarantor_2} should have at least 2 years of experience.")

				# if experience_valid_1 and experience_valid_2:
				# 	frappe.throw("Both guarantors have the required experience.")
			else:
				frappe.throw("Only Permanent Employees are Eligible")
	
	
	def validations(self):	# Mubashir Bashir Start 13-11-2024
		# List of eligible grades for loan applications
		eligible_grades = [
			"A-1", "A-3", "A-4", "A-5", "A-6", "B-1", "B-2", "B-3",
			"C-1", "C-2", "Contractual - Part time", "D-1", "D-2", "D-3",
			"Data Management Officer", "F-1", "F-2", "F-3", "G-1", "G-2", "G-3",
			"G-4", "G-5", "G-8", "M-1", "M-2", "M-3", "M-4", "M-5", "M-6",
			"O-1", "O-2", "O-3", "O-4", "PC-1", "S-1", "S-2", "S-3", "X-1"
		]

		if self.loan_product in ["Vehicle Loan", "Bike Loan"]:		
			employee = frappe.get_doc("Employee", self.applicant)
			employment_type = employee.employment_type
			grade = employee.grade

			if grade not in eligible_grades:
				frappe.throw(f"Employees with grade '{grade}' are not eligible to apply for Vehicle or Bike loans.")
			
			today = datetime.now()
			two_years_experience_days = 730
			three_years_experience_days = 1095

			if self.loan_product == "Vehicle Loan" and frappe.db.exists("Loan Application", {
				"applicant": self.applicant,
				"docstatus": 1
			}):
				frappe.throw("You cannot avail a vehicle loan after availing any other loan")
				return

			if employment_type != "Permanent":
				frappe.throw("Only Permanent Employees are Eligible.")

			if grade in ["M-4", "M-5", "M-6", "O-1", "O-2", "O-3", "O-4", "PC-1", "S-3", "X-1"]:
				required_experience_days = three_years_experience_days
			else:
				required_experience_days = two_years_experience_days

			if grade in ["A-1", "A-3", "A-4", "A-5", "A-6", "B-1", "B-2", "B-3", "C-1", "C-2", "Contractual - Part time", "D-1", "D-2", "D-3", "Data Management Officer", "F-1", "F-2", "F-3", "G-1", "G-2", "G-3", "G-4", "G-5", "G-8"]:
				if self.loan_product == "Vehicle Loan":
					frappe.throw("Employees below grade M-3 are only eligible for a Bike Loan.")

			# Validate guarantors' experience and loan application statuses
			guarantor_1 = self.custom_guarantor_of_loan_application
			guarantor_2 = self.custom_guarantor_2_of_loan_application

			if (self.applicant == guarantor_1 or self.applicant == guarantor_2):
				frappe.throw(f"You cannot add yourself as Gurantor")
			for guarantor in [guarantor_1, guarantor_2]:
				if guarantor:
					if frappe.db.exists("Loan Application", {"applicant": guarantor, "docstatus": 1}):
						frappe.throw(f"Guarantor {guarantor} already has an active loan application.")
					if frappe.db.exists("Loan Application", {
						"custom_guarantor_of_loan_application": guarantor, "docstatus": 1
					}) or frappe.db.exists("Loan Application", {
						"custom_guarantor_2_of_loan_application": guarantor, "docstatus": 1
					}):
						frappe.throw(f"Guarantor {guarantor} is already acting as a guarantor for another loan application.")
					
					date_of_joining = frappe.db.get_value("Employee", {"name": guarantor}, "date_of_joining")
					if not date_of_joining:
						frappe.throw(f"Guarantor {guarantor} does not have a valid date of joining.")
					
					date_of_joining_dt = datetime.combine(date_of_joining, datetime.min.time())
					experience_days = (today - date_of_joining_dt).days
					if experience_days < two_years_experience_days:
						experience_years = two_years_experience_days // 365
						frappe.throw(f"Guarantor {guarantor} should have at least {experience_years} years of experience.")

			# Validate applicant's experience
			applicant_date_of_joining = employee.date_of_joining
			if not applicant_date_of_joining:
				frappe.throw("Applicant does not have a valid date of joining.")

			# Convert applicant_date_of_joining to datetime.datetime if it's a datetime.date object
			if isinstance(applicant_date_of_joining, date):
				applicant_date_of_joining = datetime.combine(applicant_date_of_joining, datetime.min.time())

			applicant_experience_days = (today - applicant_date_of_joining).days

			# applicant_experience_days = (today - applicant_date_of_joining).days
			if applicant_experience_days < required_experience_days:
				experience_years = required_experience_days // 365
				frappe.throw(f"Applicant should have at least {experience_years} years of experience for this loan.")
			
	def check_overall_loan_limit(self):
		if self.loan_product == "Vehicle Loan" or self.loan_product == "Bike Loan":
			loan_product_doc = frappe.get_doc("Loan Product", self.loan_product)

			latest_fiscal_year = None
			latest_overall_loan_limit = 0

			for loan_limit_row in loan_product_doc.custom_loan_limit:
				fiscal_year_doc = frappe.get_doc("Fiscal Year", loan_limit_row.fiscal_year)
				# to_date = datetime.strptime(fiscal_year_doc.year_end_date, '%Y-%m-%d')
				to_date = datetime.combine(fiscal_year_doc.year_end_date, datetime.min.time())

				if not latest_fiscal_year or to_date > latest_fiscal_year:
					latest_fiscal_year = to_date
					latest_overall_loan_limit = flt(loan_limit_row.overall_loan_limit)

			if not latest_overall_loan_limit:
				frappe.throw("No total loan limit set for the latest fiscal year.")

			total_loan_amount = frappe.db.sql("""
									SELECT SUM(loan_amount) 
									FROM `tabLoan Application` 
									WHERE docstatus = 1
								""", as_dict=True)[0].get('SUM(loan_amount)', 0)

			total_loan_amount = flt(self.loan_amount)
			total_loan_amount += flt(self.loan_amount) if self.loan_amount else 0.0

			if total_loan_amount > latest_overall_loan_limit:
				frappe.throw(f"The loan amount for {self.loan_product} applications exceeds the total limit of {latest_overall_loan_limit}.")
	# Mubashir Bashir End 14-11-2024


	def set_pledge_amount(self):
		for proposed_pledge in self.proposed_pledges:

			if not proposed_pledge.qty and not proposed_pledge.amount:
				frappe.throw(_("Qty or Amount is mandatroy for loan security"))

			proposed_pledge.loan_security_price = get_loan_security_price(proposed_pledge.loan_security)

			if not proposed_pledge.qty:
				proposed_pledge.qty = cint(proposed_pledge.amount / proposed_pledge.loan_security_price)

			proposed_pledge.amount = proposed_pledge.qty * proposed_pledge.loan_security_price
			proposed_pledge.post_haircut_amount = cint(
				proposed_pledge.amount - (proposed_pledge.amount * proposed_pledge.haircut / 100)
			)

	def get_repayment_details(self):

		if self.is_term_loan:
			if self.repayment_method == "Repay Over Number of Periods":
				self.repayment_amount = get_monthly_repayment_amount(
					self.loan_amount, self.rate_of_interest, self.repayment_periods
				)

			if self.repayment_method == "Repay Fixed Amount per Period":
				monthly_interest_rate = flt(self.rate_of_interest) / (12 * 100)
				if monthly_interest_rate:
					min_repayment_amount = self.loan_amount * monthly_interest_rate
					if self.repayment_amount - min_repayment_amount <= 0:
						frappe.throw(_("Repayment Amount must be greater than " + str(flt(min_repayment_amount, 2))))
					self.repayment_periods = math.ceil(
						(math.log(self.repayment_amount) - math.log(self.repayment_amount - min_repayment_amount))
						/ (math.log(1 + monthly_interest_rate))
					)
				else:
					self.repayment_periods = self.loan_amount / self.repayment_amount

			self.calculate_payable_amount()
		else:
			self.total_payable_amount = self.loan_amount

	def calculate_payable_amount(self):
		balance_amount = self.loan_amount
		self.total_payable_amount = 0
		self.total_payable_interest = 0

		while balance_amount > 0:
			interest_amount = rounded(balance_amount * flt(self.rate_of_interest) / (12 * 100))
			balance_amount = rounded(balance_amount + interest_amount - self.repayment_amount)

			self.total_payable_interest += interest_amount

		self.total_payable_amount = self.loan_amount + self.total_payable_interest

	def set_loan_amount(self):
		if self.is_secured_loan and not self.proposed_pledges:
			frappe.throw(_("Proposed Pledges are mandatory for secured Loans"))

		if self.is_secured_loan and self.proposed_pledges:
			self.maximum_loan_amount = 0
			for security in self.proposed_pledges:
				self.maximum_loan_amount += flt(security.post_haircut_amount)

		if not self.loan_amount and self.is_secured_loan and self.proposed_pledges:
			self.loan_amount = self.maximum_loan_amount


@frappe.whitelist()
def create_loan(source_name, target_doc=None, submit=0):
	def update_accounts(source_doc, target_doc, source_parent):
		account_details = frappe.get_all(
			"Loan Product",
			fields=[
				"payment_account",
				"loan_account",
				"interest_income_account",
				"penalty_income_account",
			],
			filters={"name": source_doc.loan_product},
		)[0]

		if source_doc.is_secured_loan:
			target_doc.maximum_loan_amount = 0

		target_doc.payment_account = account_details.payment_account
		target_doc.loan_account = account_details.loan_account
		target_doc.interest_income_account = account_details.interest_income_account
		target_doc.penalty_income_account = account_details.penalty_income_account
		target_doc.loan_application = source_name

	doclist = get_mapped_doc(
		"Loan Application",
		source_name,
		{
			"Loan Application": {
				"doctype": "Loan",
				"validation": {"docstatus": ["=", 1]},
				"postprocess": update_accounts,
			}
		},
		target_doc,
	)

	if submit:
		doclist.submit()

	return doclist


@frappe.whitelist()
def create_pledge(loan_application, loan=None):
	loan_application_doc = frappe.get_doc("Loan Application", loan_application)

	lsp = frappe.new_doc("Loan Security Pledge")
	lsp.applicant_type = loan_application_doc.applicant_type
	lsp.applicant = loan_application_doc.applicant
	lsp.loan_application = loan_application_doc.name
	lsp.company = loan_application_doc.company

	if loan:
		lsp.loan = loan

	for pledge in loan_application_doc.proposed_pledges:

		lsp.append(
			"securities",
			{
				"loan_security": pledge.loan_security,
				"qty": pledge.qty,
				"loan_security_price": pledge.loan_security_price,
				"haircut": pledge.haircut,
			},
		)

	lsp.save()
	lsp.submit()

	message = _("Loan Security Pledge Created : {0}").format(lsp.name)
	frappe.msgprint(message)

	return lsp.name


# This is a sandbox method to get the proposed pledges
@frappe.whitelist()
def get_proposed_pledge(securities):
	if isinstance(securities, str):
		securities = json.loads(securities)

	proposed_pledges = {"securities": []}
	maximum_loan_amount = 0

	for security in securities:
		security = frappe._dict(security)
		if not security.qty and not security.amount:
			frappe.throw(_("Qty or Amount is mandatroy for loan security"))

		security.loan_security_price = get_loan_security_price(security.loan_security)

		if not security.qty:
			security.qty = cint(security.amount / security.loan_security_price)

		security.amount = security.qty * security.loan_security_price
		security.post_haircut_amount = cint(security.amount - (security.amount * security.haircut / 100))

		maximum_loan_amount += security.post_haircut_amount

		proposed_pledges["securities"].append(security)

	proposed_pledges["maximum_loan_amount"] = maximum_loan_amount

	return proposed_pledges
