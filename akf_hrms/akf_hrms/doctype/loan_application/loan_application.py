# Module overriden by Mubashir


import json
import math

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import cint, flt, rounded, fmt_money, today, add_months, getdate, nowdate
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

from akf_hrms.utils.loan_utils import (
    set_employee_defaults,
	record_terminal_workflow_state
)

class LoanApplication(Document):
	def validate(self):
		self.set_pledge_amount()
		self.set_loan_amount()
		self.validate_permanent_employee()					# Mubashir Bashir 03-01-2025
		self.validate_applicant_experience()					# Mubashir Bashir 03-01-2025
		self.validate_applicant_eligibility()					# Mubashir Bashir 03-01-2025
		self.validate_guaranters()	        				# Mubashir Bashir 03-01-2025
		self.validate_eligiblity_on_the_basis_of_grade()	# Mubashir Bashir 08-01-2025
		self.validate_loan_amount()

		if self.is_term_loan:
			self.validate_repayment_method()

		self.validate_loan_product()
		self.set_branch() #mubarrim 06-01-2025

		self.get_repayment_details()
		self.check_sanctioned_amount_limit()
		# self.validations()
		self.validate_both_guarantor_cannot_be_same() # nabeel saleem, 19-12-2024
		self.validate_loan_amount_not_exceed_to_max_loan_amount() # nabeel saleem, 19-12-2024
		self.check_total_loan_budget()		# Mubashir Bashir 13-11-2024
		self.advance_salary()
		set_employee_defaults(self) # nabeel saleem, 23-05-2025
	
	# Mubashir Bashir Start 13-11-2024
	def on_submit(self):
		self.check_total_loan_budget()
	# Mubashir Bashir End 13-11-2024
	
	# Mubashir Bashir Start 30-June-2025
	def on_cancel(self):
		self.db_set("status", "Cancelled")
		self.db_set("workflow_state", "Cancelled")
		record_terminal_workflow_state(self)
	# Mubashir Bashir End 30-June-2025

	def set_branch(self): #mubarrim 06-01-2025
		if(self.applicant_type == "Employee"):
			self.branch=frappe.db.get_value("Employee",self.applicant,"branch")


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
		required_days = 10

		if frappe.db.exists("Loan Application", {
			"applicant": self.applicant, 
			"docstatus": 1,
			"custom_loan_category": "Advance Salary"
		}):
			frappe.throw("You have already applied for Advanced Salary and cannot apply again.")
			return

		if self.custom_loan_category == "Advance Salary":
			today = datetime.now()

			if self.posting_date:
				try:
					posting_date = datetime.strptime(self.posting_date, '%Y-%m-%d') if isinstance(self.posting_date, str) else self.posting_date
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
	
	# nabeel saleem, 19-12-2024
	def validate_both_guarantor_cannot_be_same(self):
		if(self.custom_guarantor_of_loan_application and self.custom_guarantor_2_of_loan_application):
			if(self.custom_guarantor_of_loan_application == self.custom_guarantor_2_of_loan_application):
				frappe.throw(f"Both guarantor cannot be same.", title="Guarantor")
    
	# Mubashir Bashir 25-June-2025
	def validate_loan_amount_not_exceed_to_max_loan_amount(self):
		if(self.custom_maximum_allowed_loan and self.loan_amount):
			if(float(self.loan_amount) > float(self.custom_maximum_allowed_loan)):
				frappe.throw(f"Loan amount: <b>{fmt_money(self.loan_amount)}</b> is exceeding the maximum allowed loan: <b>{fmt_money(self.custom_maximum_allowed_loan)}</b>.", title="Loan Conflict")
	
	# Mubashir Bashir Start 03-01-2025
	def validate_permanent_employee(self):
		# loan_type = ['Advance Salary', 'Car Loan', 'Bike Loan']
		applicant_employment_type = frappe.db.get_value("Employee", {"name": self.applicant}, "employment_type")
		# if self.loan_product in loan_type and applicant_employment_type != 'Permanent':
		if applicant_employment_type != 'Permanent':
			frappe.throw("Only Permanent Employees are eligible for this Loan")

	# Mubashir Bashir Start 26-06-2025
	def validate_applicant_eligibility(self):
		
		has_active_application = frappe.db.exists("Loan Application", {
			"applicant": self.applicant,
			"docstatus": ["<", 2],
			"name": ["!=", self.name]
		})

		has_active_loan = frappe.db.exists("Loan", {
			"applicant": self.applicant,
			"status": ["!=", "Closed"]
		})

		if has_active_application or has_active_loan:
			frappe.throw(f"Applicant {self.applicant_name} already has an active Loan or Loan Application.")
			return

		closed_loans = frappe.get_all("Loan", 
			filters={"applicant": self.applicant, "status": "Closed"},
			fields=["name"]
		)

		for loan in closed_loans:
			lrs = frappe.get_all("Loan Repayment Schedule", 
				filters={"loan": loan.name}, 
				fields=["name"]
			)

			for schedule in lrs:
				repayment_dates = frappe.get_all("Repayment Schedule",
					filters={"parent": schedule.name},
					fields=["payment_date"],
					order_by="payment_date desc",
					limit=1
				)

				if repayment_dates:
					last_payment_date = getdate(repayment_dates[0].payment_date)
					if getdate(today()) < add_months(last_payment_date, 3):
						frappe.throw(
							f"Applicant {self.applicant_name} must wait 3 months after loan closure. "
							f"Last loan was closed on {last_payment_date.strftime('%Y-%m-%d')}."
						)
						return

	def validate_applicant_experience(self):
		if self.custom_loan_category in ['Advance Salary', 'Vehicle Loan']: return
		# validate 2 years experience
		today = datetime.now()
		required_experience_days = 730  # 2 years

		applicant_details = frappe.db.get_value("Employee", 
			self.applicant, 
			['employment_type', 'date_of_joining'], 
			as_dict=1
		)

		date_of_joining = applicant_details.date_of_joining
		if not date_of_joining:
			frappe.throw(f"Applicant {self.applicant_name} does not have a valid date of joining.")

		# Convert to datetime if needed
		if isinstance(date_of_joining, datetime):
			date_of_joining_dt = date_of_joining
		else:
			date_of_joining_dt = datetime.combine(date_of_joining, datetime.min.time())

		experience_days = (today - date_of_joining_dt).days
		if experience_days < required_experience_days:
			frappe.throw(f"Applicant {self.applicant_name} should have at least 2 years of experience.")
		
	def validate_guaranters(self):
		guarantor_1 = self.custom_guarantor_of_loan_application
		guarantor_2 = self.custom_guarantor_2_of_loan_application

		# Early returns for basic validations
		if not (guarantor_1 and guarantor_2):
			return

		if self.applicant in [guarantor_1, guarantor_2]:
			frappe.throw("Applicant can not be their own guarantor.")

		if guarantor_1 == guarantor_2:
			frappe.throw("Both guarantors cannot be the same person.")
			
		# Get all employee details in one query for each guarantor
		guarantor_1_details = frappe.db.get_value("Employee", 
			guarantor_1, 
			['employment_type', 'date_of_joining'], 
			as_dict=1
		)
		guarantor_2_details = frappe.db.get_value("Employee", 
			guarantor_2, 
			['employment_type', 'date_of_joining'], 
			as_dict=1
		)

		# Validate employment types
		for guarantor, details in [
			(guarantor_1, guarantor_1_details),
			(guarantor_2, guarantor_2_details)
		]:
			if not details or details.employment_type != 'Permanent':
				frappe.throw(f"Only permanent employees can be guarantor. Check guarantor {guarantor}")

		# Check for existing loans
		for guarantor in [guarantor_1, guarantor_2]:
			# Check if guarantor has an active loan
			if frappe.db.exists("Loan Application", {
				"applicant": guarantor,
				"docstatus": ["<", 2],
				"name": ["!=", self.name]
			}):
				frappe.throw(f"Guarantor {guarantor} already has an active loan application.")

			# Check if guarantor is already a guarantor in another loan
			if frappe.db.exists("Loan Application", {
				"custom_guarantor_of_loan_application": guarantor,
				"docstatus": ["<", 2],
				"name": ["!=", self.name]
			}) or frappe.db.exists("Loan Application", {
				"custom_guarantor_2_of_loan_application": guarantor,
				"docstatus": ["<", 2],
				"name": ["!=", self.name]
			}):
				frappe.throw(f"Guarantor {guarantor} is already acting as a guarantor for another loan application.")

		# Validate experience
		today = datetime.now()
		required_experience_days = 730  # 2 years

		for guarantor, details in [
			(guarantor_1, guarantor_1_details),
			(guarantor_2, guarantor_2_details)
		]:
			date_of_joining = details.date_of_joining
			if not date_of_joining:
				frappe.throw(f"Guarantor {guarantor} does not have a valid date of joining.")

			# Convert to datetime if needed
			if isinstance(date_of_joining, datetime):
				date_of_joining_dt = date_of_joining
			else:
				date_of_joining_dt = datetime.combine(date_of_joining, datetime.min.time())

			experience_days = (today - date_of_joining_dt).days
			if experience_days < required_experience_days:
				frappe.throw(f"Guarantor {guarantor} should have at least 2 years of experience.")
	
	# Implemented by Mubsahir 8-1-2025
	def validate_eligiblity_on_the_basis_of_grade(self):
		if self.loan_product not in ['Car Loan', 'Bike Loan']:
			return
		employee = frappe.get_doc("Employee", self.applicant)
		if not employee.grade:
			frappe.throw("Grade is not set for the employee")

		# Get Employee Grade doc
		grade_doc = frappe.get_doc("Employee Grade", employee.grade)
		
		# Calculate current experience in years
		if not employee.date_of_joining:
			frappe.throw("Date of Joining is not set for the employee")
			
		today = datetime.now().date()
		experience_days = (today - employee.date_of_joining).days
		experience_years = experience_days / 365.0  # Convert days to years
		
		# Find matching loan entitlement
		matching_entitlement = None
		for entitlement in grade_doc.custom_loan_entitlement:
			if entitlement.loan_entitlement == self.loan_product:
				if experience_years >= entitlement.services_in_years:
					matching_entitlement = entitlement
					break
		
		if not matching_entitlement:
			frappe.throw(f"Employee is not eligible for {self.loan_product} based on grade {employee.grade}")
		
		# Validate repayment periods if method is 'Repay Over Number of Periods'
		if self.repayment_method == 'Repay Over Number of Periods':
			if self.repayment_periods > matching_entitlement.repayment_period:
				frappe.throw(f"Repayment periods cannot exceed {matching_entitlement.repayment_period} months for {self.loan_product}")

	# Mubashir Bashir Start 03-01-2025
	def check_total_loan_budget(self):
		if self.custom_loan_category != 'Vehicle Loan':
			return

		today = getdate(nowdate())

		fiscal_year = frappe.get_all(
			"Fiscal Year",
			filters={
				"year_start_date": ["<=", today],
				"year_end_date": [">=", today]
			},
			fields=["name"]
		)

		if not fiscal_year:
			frappe.throw("No Fiscal Year defined for the current date.")

		current_fiscal_year = fiscal_year[0].name

		loan_product_doc = frappe.get_doc("Loan Product", self.loan_product)

		matched_row = None
		for loan_limit_row in loan_product_doc.custom_loan_limit:
			if loan_limit_row.fiscal_year == current_fiscal_year:
				matched_row = loan_limit_row
				break

		if not matched_row:
			frappe.throw(f"No loan limit set for the current fiscal year ({current_fiscal_year}).")

		total_loan_budget = flt(matched_row.total_loan_budget)

		# total approved loans amount
		total_approved = frappe.db.sql("""
			SELECT SUM(loan_amount) AS total
			FROM `tabLoan Application`
			WHERE docstatus = 1
			AND loan_product = %s
		""", (self.loan_product,), as_dict=True)[0].get('total') or 0.0

		# plus current application amount
		total_approved += flt(self.loan_amount)

		if total_approved > total_loan_budget:
			frappe.throw(
				f"The total loan amount for {self.loan_product} exceeds the total budget limit of {total_loan_budget} in fiscal year {current_fiscal_year}."
			)
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

# Mubashir Bashir 3-July-2025
@frappe.whitelist()
def get_guarantor_details(employee_name):
    doc = frappe.get_doc("Employee", employee_name, ignore_permissions=True)

    return {
        "employment_type": doc.employment_type,
        "date_of_joining": doc.date_of_joining
    }
# Mubashir Bashir 3-July-2025
@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_eligible_guarantors(doctype, txt, searchfield, start, page_len, filters):
    exclude_employee = filters.get("exclude_employee")
    applicant = filters.get("applicant")

    today = frappe.utils.nowdate()
    two_years_ago = frappe.utils.add_days(today, -730)

    conditions = [
        "status = 'Active'",
        "employment_type = 'Permanent'",
        f"date_of_joining <= '{two_years_ago}'"
    ]

    if exclude_employee:
        conditions.append(f"name != '{exclude_employee}'")
    if applicant:
        conditions.append(f"name != '{applicant}'")

    condition_str = " AND ".join(conditions)

    return frappe.db.sql(f"""
        SELECT name, employee_name
        FROM `tabEmployee`
        WHERE {condition_str}
        AND ({searchfield} LIKE %(txt)s OR employee_name LIKE %(txt)s)
        ORDER BY employee_name ASC
        LIMIT %(start)s, %(page_len)s
    """, {
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    })



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


