# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.query_builder.functions import Sum
from frappe.utils import cstr, flt, get_link_to_form, getdate, formatdate

import erpnext
from erpnext.accounts.doctype.sales_invoice.sales_invoice import get_bank_cash_account
from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.controllers.accounts_controller import AccountsController

import hrms
from hrms.hr.utils import set_employee_name, share_doc_with_approver, validate_active_employee
from hrms.mixins.pwa_notifications import PWANotificationsMixin
from frappe.utils import today
from datetime import datetime, timedelta

# Mubarrim, April 18-2025
from akf_hrms.akf_hrms.doctype.expense_claim.one_day_salary import get_one_day_salary

# Nabeel Saleem, May 16'2025
from akf_hrms.utils.expense_claim_utils import (
	set_next_workflow_approver,
	# record_set_next_workflow_approverworkflow_approver_states
)

class InvalidExpenseApproverError(frappe.ValidationError):
	pass


class ExpenseApproverIdentityError(frappe.ValidationError):
	pass


class ExpenseClaim(AccountsController, PWANotificationsMixin):
	def onload(self):
		self.get("__onload").make_payment_via_journal_entry = frappe.db.get_single_value(
			"Accounts Settings", "make_payment_via_journal_entry"
		)

	def after_insert(self):
		self.notify_approver()
		# set_next_workflow_approver(self)
		# record_workflow_approver_states(self) # nabeel saleem on 21-05-2025

	#Override
	def validate(self):
		if(self.travel_request):
			self.validate_travel_dates()
			self.validate_compensatory_leave_request()

		self.validate_overlap_expense_claim()
		self.validate_ta_da_expense()
		
		self.validate_travel_expenses()

		self.validate_da()

		self.validate_expenses_table()

		self.get_travel_attendance()


		validate_active_employee(self.employee)
		set_employee_name(self)
		self.validate_sanctioned_amount()
		self.validate_medical_expenses()	# Mubashir Bashir 24-01-25
		self.calculate_total_amount()
		self.validate_advances()
		self.set_expense_account(validate=True)
		self.set_payable_account()
		self.set_cost_center()
		self.calculate_taxes()
		self.set_status()
		if self.task and not self.project:
			self.project = frappe.db.get_value("Task", self.task, "project")
		# nabeel saleem, 19-12-2024	
		self.validate_and_set_vehicle_expense()
		# nabeel saleem, 16-05-2025
		# set_next_workflow_approver(self)
		# if(not self.is_new()): record_workflow_approver_states(self)
		self.validate_expense_amounts()	# Mubashir Bashir 04-06-25

	def set_status(self, update=False):
		status = {"0": "Draft", "1": "Submitted", "2": "Cancelled"}[cstr(self.docstatus or 0)]

		precision = self.precision("grand_total")

		if self.docstatus == 1:
			if self.approval_status == "Approved":
				if (
					# set as paid
					self.is_paid
					or (
						flt(self.total_sanctioned_amount) > 0
						and (
							# grand total is reimbursed
							(flt(self.grand_total, precision) == flt(self.total_amount_reimbursed, precision))
							# grand total (to be paid) is 0 since linked advances already cover the claimed amount
							or (flt(self.grand_total, precision) == 0)
						)
					)
				):
					status = "Paid"
				elif flt(self.total_sanctioned_amount) > 0:
					status = "Unpaid"
			elif self.approval_status == "Rejected":
				status = "Rejected"

		if update:
			self.db_set("status", status)
			self.publish_update()
			self.notify_update()
		else:
			self.status = status

	def on_update(self):
		# Nabeel Saleem, 13-05-2025
		if(hasattr(self, "workflow_state")):
			if(self.docstatus==1):
				self.approval_status="Approved"
		share_doc_with_approver(self, self.expense_approver)
		self.publish_update()
		self.notify_approval_status()
		set_next_workflow_approver(self)

	def after_delete(self):
		self.publish_update()

	def before_submit(self):
		if not self.payable_account and not self.is_paid:
			frappe.throw(_("Payable Account is mandatory to submit an Expense Claim"))

	def publish_update(self):
		employee_user = frappe.db.get_value("Employee", self.employee, "user_id", cache=True)
		hrms.refetch_resource("hrms:my_claims", employee_user)

	def set_payable_account(self):
		if not self.payable_account and not self.is_paid:
			self.payable_account = frappe.get_cached_value(
				"Company", self.company, "default_expense_claim_payable_account"
			)

	def set_cost_center(self):
		if not self.cost_center:
			self.cost_center = frappe.get_cached_value("Company", self.company, "cost_center")

	#Override
	def on_submit(self):
		if(self.travel_request):
			self.validate_travel_dates()
			self.validate_compensatory_leave_request()

		
		# if self.approval_status == "Draft":
		# 	frappe.throw(_("""Approval Status must be 'Approved' or 'Rejected'"""))

		self.update_task_and_project()
		self.make_gl_entries()
		self.validate_travel_expenses()


		update_reimbursed_amount(self)

		self.update_claimed_amount_in_employee_advance()
		create_additional_salary_for_expense_claim(self)

	def on_cancel(self):
		self.update_task_and_project()
		self.ignore_linked_doctypes = ("GL Entry", "Stock Ledger Entry", "Payment Ledger Entry")
		if self.payable_account:
			self.make_gl_entries(cancel=True)

		update_reimbursed_amount(self)

		self.update_claimed_amount_in_employee_advance()
		self.publish_update()

	def update_claimed_amount_in_employee_advance(self):
		for d in self.get("advances"):
			frappe.get_doc("Employee Advance", d.employee_advance).update_claimed_amount()

	def update_task_and_project(self):
		if self.task:
			task = frappe.get_doc("Task", self.task)

			ExpenseClaim = frappe.qb.DocType("Expense Claim")
			task.total_expense_claim = (
				frappe.qb.from_(ExpenseClaim)
				.select(Sum(ExpenseClaim.total_sanctioned_amount))
				.where(
					(ExpenseClaim.docstatus == 1)
					& (ExpenseClaim.project == self.project)
					& (ExpenseClaim.task == self.task)
				)
			).run()[0][0]

			task.save()
		elif self.project:
			frappe.get_doc("Project", self.project).update_project()

	def make_gl_entries(self, cancel=False):
		if flt(self.total_sanctioned_amount) > 0:
			gl_entries = self.get_gl_entries()
			make_gl_entries(gl_entries, cancel)

	def get_gl_entries(self):
		gl_entry = []
		self.validate_account_details()

		# payable entry
		if self.grand_total:
			gl_entry.append(
				self.get_gl_dict(
					{
						"account": self.payable_account,
						"credit": self.grand_total,
						"credit_in_account_currency": self.grand_total,
						"against": ",".join([d.default_account for d in self.expenses]),
						"party_type": "Employee",
						"party": self.employee,
						"against_voucher_type": self.doctype,
						"against_voucher": self.name,
						"cost_center": self.cost_center,
						"project": self.project,
					},
					item=self,
				)
			)

		# expense entries
		for data in self.expenses:
			gl_entry.append(
				self.get_gl_dict(
					{
						"account": data.default_account,
						"debit": data.sanctioned_amount,
						"debit_in_account_currency": data.sanctioned_amount,
						"against": self.employee,
						"cost_center": data.cost_center or self.cost_center,
						"project": data.project or self.project,
					},
					item=data,
				)
			)

		for data in self.advances:
			gl_entry.append(
				self.get_gl_dict(
					{
						"account": data.advance_account,
						"credit": data.allocated_amount,
						"credit_in_account_currency": data.allocated_amount,
						"against": ",".join([d.default_account for d in self.expenses]),
						"party_type": "Employee",
						"party": self.employee,
						"against_voucher_type": "Employee Advance",
						"against_voucher": data.employee_advance,
					}
				)
			)

		self.add_tax_gl_entries(gl_entry)

		if self.is_paid and self.grand_total:
			# payment entry
			payment_account = get_bank_cash_account(self.mode_of_payment, self.company).get("account")
			gl_entry.append(
				self.get_gl_dict(
					{
						"account": payment_account,
						"credit": self.grand_total,
						"credit_in_account_currency": self.grand_total,
						"against": self.employee,
					},
					item=self,
				)
			)

			gl_entry.append(
				self.get_gl_dict(
					{
						"account": self.payable_account,
						"party_type": "Employee",
						"party": self.employee,
						"against": payment_account,
						"debit": self.grand_total,
						"debit_in_account_currency": self.grand_total,
						"against_voucher": self.name,
						"against_voucher_type": self.doctype,
					},
					item=self,
				)
			)

		return gl_entry

	def add_tax_gl_entries(self, gl_entries):
		# tax table gl entries
		for tax in self.get("taxes"):
			gl_entries.append(
				self.get_gl_dict(
					{
						"account": tax.account_head,
						"debit": tax.tax_amount,
						"debit_in_account_currency": tax.tax_amount,
						"against": self.employee,
						"cost_center": tax.cost_center or self.cost_center,
						"project": tax.project or self.project,
						"against_voucher_type": self.doctype,
						"against_voucher": self.name,
					},
					item=tax,
				)
			)

	def validate_account_details(self):
		for data in self.expenses:
			if not data.cost_center:
				frappe.throw(
					_("Row {0}: {1} is required in the expenses table to book an expense claim.").format(
						data.idx, frappe.bold("Cost Center")
					)
				)

		if self.is_paid:
			if not self.mode_of_payment:
				frappe.throw(_("Mode of payment is required to make a payment").format(self.employee))

	def calculate_total_amount(self):
		self.total_claimed_amount = 0
		self.total_sanctioned_amount = 0

		for d in self.get("expenses"):
			self.round_floats_in(d)

			if self.approval_status == "Rejected":
				d.sanctioned_amount = 0.0

			self.total_claimed_amount += flt(d.amount)
			self.total_sanctioned_amount += flt(d.sanctioned_amount)

		self.round_floats_in(self, ["total_claimed_amount", "total_sanctioned_amount"])

	@frappe.whitelist()
	def calculate_taxes(self):
		self.total_taxes_and_charges = 0
		for tax in self.taxes:
			self.round_floats_in(tax)

			if tax.rate:
				tax.tax_amount = flt(
					flt(self.total_sanctioned_amount) * flt(flt(tax.rate) / 100),
					tax.precision("tax_amount"),
				)

			tax.total = flt(tax.tax_amount) + flt(self.total_sanctioned_amount)
			self.total_taxes_and_charges += flt(tax.tax_amount)

		self.round_floats_in(self, ["total_taxes_and_charges"])

		self.grand_total = (
			flt(self.total_sanctioned_amount)
			+ flt(self.total_taxes_and_charges)
			- flt(self.total_advance_amount)
		)
		self.round_floats_in(self, ["grand_total"])

	def validate_advances(self):
		self.total_advance_amount = 0

		for d in self.get("advances"):
			self.round_floats_in(d)

			ref_doc = frappe.db.get_value(
				"Employee Advance",
				d.employee_advance,
				["posting_date", "paid_amount", "claimed_amount", "advance_account"],
				as_dict=1,
			)
			d.posting_date = ref_doc.posting_date
			d.advance_account = ref_doc.advance_account
			d.advance_paid = ref_doc.paid_amount
			d.unclaimed_amount = flt(ref_doc.paid_amount) - flt(ref_doc.claimed_amount)

			if d.allocated_amount and flt(d.allocated_amount) > flt(d.unclaimed_amount):
				frappe.throw(
					_("Row {0}# Allocated amount {1} cannot be greater than unclaimed amount {2}").format(
						d.idx, d.allocated_amount, d.unclaimed_amount
					)
				)

			self.total_advance_amount += flt(d.allocated_amount)

		if self.total_advance_amount:
			self.round_floats_in(self, ["total_advance_amount"])
			precision = self.precision("total_advance_amount")
			amount_with_taxes = flt(
				(flt(self.total_sanctioned_amount, precision) + flt(self.total_taxes_and_charges, precision)),
				precision,
			)

			if flt(self.total_advance_amount, precision) > amount_with_taxes:
				frappe.throw(_("Total advance amount cannot be greater than total sanctioned amount"))

	def validate_sanctioned_amount(self):
		for d in self.get("expenses"):
			if flt(d.sanctioned_amount) > flt(d.amount):
				frappe.throw(
					_("Sanctioned Amount cannot be greater than Claim Amount in Row {0}.").format(d.idx)
				)

	def validate_medical_expenses(self):	# Mubashir Bashir 24-01-25 Start

		from akf_hrms.patches.skip_validations import skip
		if(skip()):
			return
		
		social_security_amount = frappe.db.get_single_value('AKF Payroll Settings', 'social_security_amount')
		employee_doc = frappe.get_doc("Employee", self.employee)
		branch = employee_doc.branch
		employment_type = employee_doc.employment_type
		employment_status = employee_doc.status
				
		salary_structure = frappe.db.sql("""
			SELECT base
			FROM `tabSalary Structure Assignment`
			WHERE docstatus = 1 AND employee = %s
			ORDER BY from_date DESC
			LIMIT 1
		""", (self.employee), as_dict=True)

		if not salary_structure:
			frappe.throw(_("No Salary Structure Assignment found for the employee."))

		current_salary = salary_structure[0].get('base', 0)

		for d in self.get("expenses"):
			if (d.expense_type in ['Medical', 'Vision Support Equipment', 
				'Hearing Support Equipment', 'Artificial Limbs'] and not
				(self.company == "Alkhidmat Foundation Pakistan" and
				branch == "Central Office" and
				employment_type == "Permanent" and
				employment_status == "Active" and
				current_salary > social_security_amount)):
				frappe.throw(_(
					"Only permanent employees in the Central Office with a current salary greater than the social security amount are eligible for {0} expense reimbursement."
				).format(d.expense_type), title=_("Not Eligible"))		

		current_fiscal_year = frappe.db.sql("""
		SELECT name, year_start_date, year_end_date
		FROM `tabFiscal Year`
		WHERE %s BETWEEN year_start_date AND year_end_date
		LIMIT 1
		""", frappe.utils.today(), as_dict=True)[0]

		previous_reimbursements = frappe.db.sql("""
		SELECT child.expense_type, SUM(child.amount * 0.8) as reimbursed_amount
		FROM `tabExpense Claim` parent
		JOIN `tabExpense Claim Detail` child ON parent.name = child.parent
		WHERE parent.employee = %s
		AND parent.docstatus = 1
		AND parent.posting_date BETWEEN %s AND %s
		AND parent.name != %s
		GROUP BY child.expense_type
		""", (self.employee, current_fiscal_year.year_start_date, 
		current_fiscal_year.year_end_date, self.name), as_dict=True)
		
		previous_claims = {d.expense_type: d.reimbursed_amount for d in previous_reimbursements}

		for d in self.get("expenses"):
			if d.expense_type in ['Medical', 'Vision Support Equipment', 
				'Hearing Support Equipment', 'Artificial Limbs']:
				
				if d.expense_type == 'Medical':
					max_reimbursement = max(current_salary * 2, 50000)
				elif d.expense_type == 'Vision Support Equipment':
					max_reimbursement = 1000
				elif d.expense_type == 'Hearing Support Equipment':
					max_reimbursement = 18000
				elif d.expense_type == 'Artificial Limbs':
					max_reimbursement = 45000

				current_allowed = min(d.amount * 0.8, max_reimbursement)					
				previous_amount = previous_claims.get(d.expense_type, 0)					
				remaining_limit = max_reimbursement - previous_amount

				if remaining_limit <= 0:
					frappe.throw(_(
						"You have already reached the maximum reimbursement limit of {0} "
						"for {1} in this fiscal year ({2})."
					).format(
						frappe.format_value(max_reimbursement, "Currency"),
						d.expense_type,
						current_fiscal_year.name
					))

				if current_allowed > remaining_limit:
					frappe.throw(_(
						"The medical expense for {0} cannot exceed {1} "
						"(Remaining limit for fiscal year {2}). "
						"You have already claimed {3} this fiscal year."
					).format(
						d.expense_type,
						frappe.format_value(remaining_limit, "Currency"),
						current_fiscal_year.name,
						frappe.format_value(previous_amount, "Currency")
					))
				else:
					d.sanctioned_amount = current_allowed
		# Mubashir Bashir 24-01-25 End

	def set_expense_account(self, validate=False):
		for expense in self.expenses:
			if not expense.default_account or not validate:
				expense.default_account = get_expense_claim_account(expense.expense_type, self.company)[
					"account"
				]
				
	# =================== > Custom Functions < =======================

	def validate_ta_da_expense(self):
		from akf_hrms.patches.skip_validations import skip
		if skip():
			return

		if not self.grade:
			frappe.throw("Grade is not set. Please provide a valid grade to proceed with the validation.")
		if self.ownership:
			return

		# Skip validation for these expense types
		for e in self.expenses:
			if e.expense_type in ['Medical', 'Vision Support Equipment', 'Hearing Support Equipment', 'Artificial Limbs']:
				return

		error_messages = []

		for e in self.expenses:
			if not e.expense_type:
				error_messages.append("Expense type is missing in one of the entries.")
				continue

			ect_doc = frappe.get_doc("Expense Claim Type", e.expense_type)			

			matched_row = next((row for row in ect_doc.expense_amounts if row.grade == self.grade), None)

			if not matched_row:
				error_messages.append(f"No amount defined for grade '{self.grade}' in Expense Claim Type '{e.expense_type}'.")
				continue

			try:
				allowed_amount = float(matched_row.amount)
				expense_amount = float(e.amount)

				if e.expense_type == "Daily Allowance":
					duty_hours, comp_off = self.get_travel_attendance()
					if expense_amount > allowed_amount and comp_off < 2:
						error_messages.append(f"<b>{e.expense_type.upper()}</b> exceeds the limit of {allowed_amount}.")
				elif expense_amount > allowed_amount:
					error_messages.append(f"<b>{e.expense_type.upper()}</b> exceeds the limit of {allowed_amount}.")

			except Exception as ex:
				error_messages.append(f"Error validating {e.expense_type}: {ex}")

		if error_messages:
			frappe.throw("<br>".join(error_messages))

	def validate_travel_dates(self):
		query = f"""
						SELECT departure_date, arrival_date
						FROM `tabTravel Itinerary`
						WHERE parent = '{self.travel_request}'
					"""
		result = frappe.db.sql(query, as_dict=1)
		if(result):
			departure_date=getdate(result[0].departure_date)
			arrival_date=getdate(result[0].arrival_date)
		else:
			frappe.throw(f"No date found for travel request: {self.travel_request}")
		for row in self.expenses:
			if (not departure_date<= getdate(row.expense_date) <= arrival_date):
				frappe.throw(_("Expense Date should be between Departure Date and Arrival Date"))
				
					
	def validate_compensatory_leave_request(self):
		compensatory_leave_request = frappe.db.sql(
			"""
			select name, work_from_date, work_end_date
			from `tabCompensatory Leave Request`
			where employee=%(employee)s and against = 'Travel'
				and docstatus=1
				and travel_request=%(travel_request)s
		""",
			{
				"employee": self.employee,
				"travel_request": self.travel_request,
			},
			as_dict=1,
		)
		
		expense_type = self.validate_da()
		if(expense_type):
			for expense in expense_type:
				if(expense.expense_type == "Daily Allowance"):
					if compensatory_leave_request:
						if(expense.expense_date >= compensatory_leave_request[0].work_from_date and expense.expense_date <= compensatory_leave_request[0].work_end_date):
							frappe.throw(f"You can't avail <b>Daily Allowance</b> against travel request: {self.travel_request}, as Compensatory Leave '{compensatory_leave_request[0].name}' already taken against '{expense.expense_date}'!")

	def validate_da(self):
		expense_claim = frappe.db.sql(
			"""
			select ecd.expense_type, ecd.expense_date
			From `tabExpense Claim` ec
			INNER JOIN `tabExpense Claim Detail` ecd ON ecd.parent = ec.name
			where ec.name = %(name)s
		""",
			{
				"name": self.name
			},
			as_dict=1,
		)

		if(expense_claim):
			return expense_claim
		else:
			return False

	def validate_overlap_expense_claim(self):
		expense_claim = frappe.db.sql(
			"""
			select name
			from `tabExpense Claim`
			where employee=%(employee)s
				and docstatus=1
				and travel_request=%(travel_request)s
		""",
			{
				"employee": self.employee,
				"travel_request": self.travel_request,
			},
			as_dict=1,
		)
		
		if expense_claim:
			frappe.throw(f"You can't apply twice for Expense Claim against travel request: {self.travel_request}")

	def validate_travel_expenses(self): # Mubashir Bashir
		for e in self.expenses:
			if e.expense_type in ['Medical', 'Vision Support Equipment', 'Hearing Support Equipment', 'Artificial Limbs']:
				return

		for expense in self.expenses:
			if not expense.expense_type:
				frappe.throw("Expense type is missing in one of the entries.")

			ect_doc = frappe.get_doc("Expense Claim Type", expense.expense_type)

			matched_row = next((row for row in ect_doc.expense_amounts if row.grade == self.grade), None)

			if not matched_row or matched_row.amount is None:
				frappe.throw(f"Amount not configured for grade '{self.grade}' in Expense Claim Type '{expense.expense_type}'.")

			amount = float(matched_row.amount)
			holiday = True

			if expense.expense_type == "Daily Allowance":
				duty_hours, comp_off = self.get_travel_attendance()
				one_day_salary = get_one_day_salary(self.employee)
				da = round(comp_off * one_day_salary, 2)

				if comp_off > 1:
					if duty_hours > 10:
						amount = da
						holiday = False
					elif 6 <= duty_hours <= 10:
						amount = (da * 0.5)
						holiday = False
					elif 1 <= duty_hours < 6:
						amount = (da * 0.25)
						holiday = False
				else:
					if duty_hours > 10:
						amount = amount
					elif 6 <= duty_hours <= 10:
						amount *= 0.5
					elif 1 <= duty_hours < 6:
						amount *= 0.25

			try:
				if float(expense.amount) > float(amount) and holiday:
					frappe.throw(f"{expense.expense_type} amount for Grade '{self.grade}' can't exceed {amount}")
			except Exception as ex:
				frappe.throw(f"Error validating expense '{expense.expense_type}': {ex}")

	def get_travel_attendance(self):
		if self.expense_type == 'Travel':
			duration = 0
			comp_off = 1
			for expense in self.expenses:
				holiday_list= frappe.db.get_value("Employee",self.employee,"holiday_list")

				compensatory_off = frappe.db.sql("""
					SELECT compensatory_leave
					FROM `tabHoliday`
					WHERE parent = %s AND holiday_date = %s
				""", (holiday_list, expense.expense_date), as_dict=1)

				if compensatory_off:
					comp_off = compensatory_off[0].get('compensatory_leave')
					
				query_result = frappe.db.sql("""
					SELECT att.in_time, att.out_time
					FROM `tabAttendance` att
					LEFT JOIN `tabAttendance Request` ar ON ar.name = att.attendance_request
					WHERE att.employee = %s
						AND att.attendance_date = %s
						AND ar.travel_request = %s
						AND att.docstatus = 1
				""", (self.employee, expense.expense_date, self.travel_request), as_dict=1)

				if not query_result:
					frappe.throw(f"No attendance Record found against travel request '{self.travel_request}' for date '{expense.expense_date}'")
				
				attendance = query_result[0]
				in_time_str = attendance.get('in_time')
				out_time_str = attendance.get('out_time')

				if not in_time_str or not out_time_str:
					frappe.throw(f"In Time or Out Time missing for date '{expense.expense_date}'")

				in_time = in_time_str if isinstance(in_time_str, datetime) else datetime.strptime(in_time_str, "%Y-%m-%d %H:%M:%S")
				out_time = out_time_str if isinstance(out_time_str, datetime) else datetime.strptime(out_time_str, "%Y-%m-%d %H:%M:%S")

				time_diff = out_time - in_time
				time_in_hours = time_diff.total_seconds() / 3600
				duration += time_in_hours
			
			return duration, int(comp_off)
	
	@frappe.whitelist()
	def validate_expenses_table(self):
		types = {d.expense_type:[] for d in self.expenses}
		for d in self.expenses:
			if(d.expense_type in types):
				if(d.expense_date in types[d.expense_type]):
					frappe.throw(f"You are not allowed to take <b>{d.expense_type}</b> on '{formatdate(d.expense_date)}' twice!")
				else:
					types[d.expense_type].append(d.expense_date)

	@frappe.whitelist()
	def get_travel_expense_amount(self):
		if not self.grade:
			frappe.throw("Grade is not set. Please provide a valid grade to proceed with the validation.")
		
		for d in self.expenses:

			if d.expense_type in ['Medical', 'Vision Support Equipment', 'Hearing Support Equipment', 'Artificial Limbs']:
				return

			ect_doc = frappe.get_doc("Expense Claim Type", d.expense_type)

			matched_row = next((row for row in ect_doc.expense_amounts if row.grade == self.grade), None)

			if not matched_row or matched_row.amount is None:
				frappe.throw(f"Amount is not defined for grade '{self.grade}' in Expense Claim Type '{d.expense_type}'.")

			try:
				amount = float(matched_row.amount)

				if d.expense_type == 'Daily Allowance':
					duty_hours, comp_off = self.get_travel_attendance()
					one_day_salary = get_one_day_salary(self.employee)
					da = round(comp_off * one_day_salary, 2)

					if comp_off > 1:
						if duty_hours > 10:
							amount = da
						elif 6 <= duty_hours <= 10:
							amount = (da * 0.5)
						elif 1 <= duty_hours < 6:
							amount = (da * 0.25)
					else:
						if duty_hours > 10:
							amount = amount
						elif 6 <= duty_hours <= 10:
							amount *= 0.5
						elif 1 <= duty_hours < 6:
							amount *= 0.25

					d.amount = d.sanctioned_amount = round(amount, 2)

			except Exception as ex:
				frappe.throw(f"Error calculating amount for '{d.expense_type}': {ex}")
	# Mubashir Bashir 4-6-25 Start
	def validate_expense_amounts(self):
		for expense in self.expenses:
			if expense.amount <= 0: 
				frappe.throw(f'Expense amount for type {expense.expense_type} must be greater than 0', title= 'Invalid Expense Amount')
	# Mubashir Bashir 4-6-25 End
	# nabeel saleem, 19-12-2024	
	@frappe.whitelist()
	def validate_and_set_vehicle_expense(self):
		if(self.ownership):
			if(not self.expense_rate): frappe.throw(f"Please select, vehicle.", title="Ownership Details")
			if(float(self.expense_rate)<=0): frappe.throw(f"In vehicle, expense rate must be greater than zero.", title="Ownership Details")
			if(float(self.kilometers)<=0): frappe.throw(f"Kilometers must be greater than zero.", title="Ownership Details")
			ownership_not_found = True 
			for d in self.expenses:
				if(d.expense_type):
					if(d.expense_type=="Vehicle Expense"): 
						ownership_not_found = False
						# frappe.throw(f"Expense Claim Type must be <b>Vehicle Expense</b>.", title="Expenses Table")
						d.amount = (self.expense_rate * self.kilometers)
						d.sanctioned_amount = d.amount
			if(ownership_not_found):
				frappe.throw(f"Please select, `Vehicle Expense` expenses table.", title="Expenses Table")

	@frappe.whitelist()
	def get_medical_expenses_amount(self):			
		social_security_amount = frappe.db.get_single_value('AKF Payroll Settings', 'social_security_amount')
		employee_doc = frappe.get_doc("Employee", self.employee)
		branch = employee_doc.branch
		employment_type = employee_doc.employment_type
		employment_status = employee_doc.status
				
		salary_structure = frappe.db.sql("""
			SELECT base
			FROM `tabSalary Structure Assignment`
			WHERE docstatus = 1 AND employee = %s
			ORDER BY from_date DESC
			LIMIT 1
		""", (self.employee), as_dict=True)

		if not salary_structure:
			frappe.throw(_("No Salary Structure Assignment found for the employee."))

		current_salary = salary_structure[0].get('base', 0)

		for d in self.get("expenses"):
			if (d.expense_type in ['Medical', 'Vision Support Equipment', 
				'Hearing Support Equipment', 'Artificial Limbs'] and not
				(self.company == "Alkhidmat Foundation Pakistan" and
				branch == "Central Office" and
				employment_type == "Permanent" and
				employment_status == "Active" and
				current_salary > social_security_amount)):
				frappe.throw(_(
					"Only permanent employees in the Central Office with a current salary greater than the social security amount are eligible for {0} expense reimbursement."
				).format(d.expense_type), title=_("Not Eligible"))		

		current_fiscal_year = frappe.db.sql("""
		SELECT name, year_start_date, year_end_date
		FROM `tabFiscal Year`
		WHERE %s BETWEEN year_start_date AND year_end_date
		LIMIT 1
		""", frappe.utils.today(), as_dict=True)[0]

		previous_reimbursements = frappe.db.sql("""
		SELECT child.expense_type, SUM(child.amount * 0.8) as reimbursed_amount
		FROM `tabExpense Claim` parent
		JOIN `tabExpense Claim Detail` child ON parent.name = child.parent
		WHERE parent.employee = %s
		AND parent.docstatus = 1
		AND parent.posting_date BETWEEN %s AND %s
		AND parent.name != %s
		GROUP BY child.expense_type
		""", (self.employee, current_fiscal_year.year_start_date, 
		current_fiscal_year.year_end_date, self.name), as_dict=True)
		
		previous_claims = {d.expense_type: d.reimbursed_amount for d in previous_reimbursements}

		for d in self.get("expenses"):
			if d.expense_type in ['Medical', 'Vision Support Equipment', 
				'Hearing Support Equipment', 'Artificial Limbs']:
				
				if d.expense_type == 'Medical':
					max_reimbursement = max(current_salary * 2, 50000)
				elif d.expense_type == 'Vision Support Equipment':
					max_reimbursement = 1000
				elif d.expense_type == 'Hearing Support Equipment':
					max_reimbursement = 18000
				elif d.expense_type == 'Artificial Limbs':
					max_reimbursement = 45000

				current_allowed = min(d.amount * 0.8, max_reimbursement)					
				previous_amount = previous_claims.get(d.expense_type, 0)					
				remaining_limit = max_reimbursement - previous_amount

				if remaining_limit <= 0:
					frappe.throw(_(
						"You have already reached the maximum reimbursement limit of {0} "
						"for {1} in this fiscal year ({2})."
					).format(
						frappe.format_value(max_reimbursement, "Currency"),
						d.expense_type,
						current_fiscal_year.name
					))

				if current_allowed > remaining_limit:
					frappe.throw(_(
						"The medical expense for {0} cannot exceed {1} "
						"(Remaining limit for fiscal year {2}). "
						"You have already claimed {3} this fiscal year."
					).format(
						d.expense_type,
						frappe.format_value(remaining_limit, "Currency"),
						current_fiscal_year.name,
						frappe.format_value(previous_amount, "Currency")
					))
				else:
					d.sanctioned_amount = current_allowed
# ================================================================================================================================================== #
# ================================================================================================================================================== #


def update_reimbursed_amount(doc):
	total_amount_reimbursed = get_total_reimbursed_amount(doc)

	doc.total_amount_reimbursed = total_amount_reimbursed
	frappe.db.set_value("Expense Claim", doc.name, "total_amount_reimbursed", total_amount_reimbursed)

	doc.set_status(update=True)


def get_total_reimbursed_amount(doc):
	if doc.is_paid:
		# No need to check for cancelled state here as it will anyways update status as cancelled
		return doc.grand_total
	else:
		amount_via_jv = frappe.db.get_value(
			"Journal Entry Account",
			{"reference_name": doc.name, "docstatus": 1},
			"sum(debit_in_account_currency - credit_in_account_currency)",
		)

		amount_via_payment_entry = frappe.db.get_value(
			"Payment Entry Reference", {"reference_name": doc.name, "docstatus": 1}, "sum(allocated_amount)"
		)

		return flt(amount_via_jv) + flt(amount_via_payment_entry)


def get_outstanding_amount_for_claim(claim):
	if isinstance(claim, str):
		claim = frappe.db.get_value(
			"Expense Claim",
			claim,
			(
				"total_sanctioned_amount",
				"total_taxes_and_charges",
				"total_amount_reimbursed",
				"total_advance_amount",
			),
			as_dict=True,
		)

	outstanding_amt = (
		flt(claim.total_sanctioned_amount)
		+ flt(claim.total_taxes_and_charges)
		- flt(claim.total_amount_reimbursed)
		- flt(claim.total_advance_amount)
	)

	return outstanding_amt


@frappe.whitelist()
def make_bank_entry(dt, dn):
	from erpnext.accounts.doctype.journal_entry.journal_entry import get_default_bank_cash_account

	expense_claim = frappe.get_doc(dt, dn)
	default_bank_cash_account = get_default_bank_cash_account(expense_claim.company, "Bank")
	if not default_bank_cash_account:
		default_bank_cash_account = get_default_bank_cash_account(expense_claim.company, "Cash")

	payable_amount = get_outstanding_amount_for_claim(expense_claim)

	je = frappe.new_doc("Journal Entry")
	je.voucher_type = "Bank Entry"
	je.company = expense_claim.company
	je.remark = "Payment against Expense Claim: " + dn

	je.append(
		"accounts",
		{
			"account": expense_claim.payable_account,
			"debit_in_account_currency": payable_amount,
			"reference_type": "Expense Claim",
			"party_type": "Employee",
			"party": expense_claim.employee,
			"cost_center": erpnext.get_default_cost_center(expense_claim.company),
			"reference_name": expense_claim.name,
		},
	)

	je.append(
		"accounts",
		{
			"account": default_bank_cash_account.account,
			"credit_in_account_currency": payable_amount,
			"balance": default_bank_cash_account.balance,
			"account_currency": default_bank_cash_account.account_currency,
			"cost_center": erpnext.get_default_cost_center(expense_claim.company),
			"account_type": default_bank_cash_account.account_type,
		},
	)

	return je.as_dict()


@frappe.whitelist()
def get_expense_claim_account_and_cost_center(expense_claim_type, company):
	data = get_expense_claim_account(expense_claim_type, company)
	cost_center = erpnext.get_default_cost_center(company)

	return {"account": data.get("account"), "cost_center": cost_center}


@frappe.whitelist()
def get_expense_claim_account(expense_claim_type, company):
	account = frappe.db.get_value(
		"Expense Claim Account", {"parent": expense_claim_type, "company": company}, "default_account"
	)
	if not account:
		frappe.throw(
			_("Set the default account for the {0} {1}").format(
				frappe.bold("Expense Claim Type"), get_link_to_form("Expense Claim Type", expense_claim_type)
			)
		)

	return {"account": account}


@frappe.whitelist()
def get_advances(employee, advance_id=None):
	advance = frappe.qb.DocType("Employee Advance")

	query = frappe.qb.from_(advance).select(
		advance.name,
		advance.purpose,
		advance.posting_date,
		advance.paid_amount,
		advance.claimed_amount,
		advance.advance_account,
	)

	if not advance_id:
		query = query.where(
			(advance.docstatus == 1)
			& (advance.employee == employee)
			& (advance.paid_amount > 0)
			& (advance.status.notin(["Claimed", "Returned", "Partly Claimed and Returned"]))
		)
	else:
		query = query.where(advance.name == advance_id)

	return query.run(as_dict=True)


@frappe.whitelist()
def get_expense_claim(
	employee_name, company, employee_advance_name, posting_date, paid_amount, claimed_amount
):
	default_payable_account = frappe.get_cached_value(
		"Company", company, "default_expense_claim_payable_account"
	)
	default_cost_center = frappe.get_cached_value("Company", company, "cost_center")

	expense_claim = frappe.new_doc("Expense Claim")
	expense_claim.company = company
	expense_claim.employee = employee_name
	expense_claim.payable_account = default_payable_account
	expense_claim.cost_center = default_cost_center
	expense_claim.is_paid = 1 if flt(paid_amount) else 0
	expense_claim.append(
		"advances",
		{
			"employee_advance": employee_advance_name,
			"posting_date": posting_date,
			"advance_paid": flt(paid_amount),
			"unclaimed_amount": flt(paid_amount) - flt(claimed_amount),
			"allocated_amount": flt(paid_amount) - flt(claimed_amount),
		},
	)

	return expense_claim


def update_payment_for_expense_claim(doc, method=None):
	"""
	Updates payment/reimbursed amount in Expense Claim
	on Payment Entry/Journal Entry cancellation/submission
	"""
	if doc.doctype == "Payment Entry" and not (doc.payment_type == "Pay" and doc.party):
		return

	payment_table = "accounts" if doc.doctype == "Journal Entry" else "references"
	doctype_field = "reference_type" if doc.doctype == "Journal Entry" else "reference_doctype"

	for d in doc.get(payment_table):
		if d.get(doctype_field) == "Expense Claim" and d.reference_name:
			expense_claim = frappe.get_doc("Expense Claim", d.reference_name)
			if doc.docstatus == 2:
				update_reimbursed_amount(expense_claim)
			else:
				update_reimbursed_amount(expense_claim)


def validate_expense_claim_in_jv(doc, method=None):
	"""Validates Expense Claim amount in Journal Entry"""
	for d in doc.accounts:
		if d.reference_type == "Expense Claim":
			outstanding_amt = get_outstanding_amount_for_claim(d.reference_name)
			if d.debit > outstanding_amt:
				frappe.throw(
					_(
						"Row No {0}: Amount cannot be greater than the Outstanding Amount against Expense Claim {1}. Outstanding Amount is {2}"
					).format(d.idx, d.reference_name, outstanding_amt)
				)


@frappe.whitelist()
def make_expense_claim_for_delivery_trip(source_name, target_doc=None):
	doc = get_mapped_doc(
		"Delivery Trip",
		source_name,
		{"Delivery Trip": {"doctype": "Expense Claim", "field_map": {"name": "delivery_trip"}}},
		target_doc,
	)

	return doc


@frappe.whitelist()
def get_employee_details():
	user_id = frappe.session.user
	employee = frappe.db.get_all('Employee', filters={'user_id': user_id}, fields=['name', 'first_name', 'branch', 'designation', 'department' , 'image', 'date_of_birth', 'date_of_joining', 'custom_cnic', 'employment_type', 'gender', 'custom_reports_to_line_manager_name'])
	
	if employee:
	
		emp_details = employee[0]

		# Fetch education levels for the employee
		education_records = frappe.db.get_all('Employee Education', filters={'parent': emp_details.name}, fields=['qualification', 'year_of_passing'], order_by='year_of_passing desc', limit=1)

		latest_qualification = None
		if education_records:
			latest_qualification = education_records[0].qualification

		return {
			"first_name": emp_details.first_name,
			"branch": emp_details.branch,
			"designation": emp_details.designation,
			"department": emp_details.department,
			"user": user_id,
			"image": emp_details.image,
			"date_of_birth": emp_details.date_of_birth,
			"date_of_joining": emp_details.date_of_joining,
			"cnic": emp_details.custom_cnic,
			"gender":emp_details.gender,
			"employment_type":emp_details.employment_type,
			"custom_reports_to_line_manager_name": emp_details.custom_reports_to_line_manager_name,
			"latest_education_level": latest_qualification if latest_qualification else "No education record"
		}
	else:
		return {
			"message": "No record exists."
		}


@frappe.whitelist()
def get_employee_date():
	user_id = frappe.session.user
	employee = frappe.db.get_all('Employee', filters={'user_id': user_id}, fields=['name'])
	
	if employee:
	  
		name = employee[0]['name']  
		return {
			"name": name,
			"date": today()  
		}
	else:
		 return {
			"message": "No Leave Record exists."
		}



@frappe.whitelist()
def get_attendance_logs_when_no_attendance():  # Mubashir Bashir
	user_id = frappe.session.user
	employee = frappe.db.get_all('Employee', filters={'user_id': user_id}, fields=['name'])

	if employee:
		employee_name = employee[0].name
		today = datetime.now()
		
		# Calculate the start_date (from_date)
		day = today.day
		if day > 20:
			start_date = datetime(today.year, today.month, 21)
		else:
			if today.month == 1:  # Handle January edge case
				start_date = datetime(today.year - 1, 12, 21)
			else:
				start_date = datetime(today.year, today.month - 1, 21)
				

		start_date = start_date.date()  

		attendance_logs = frappe.db.sql(
			"""
			SELECT attendance_date 
			FROM `tabAttendance`
			WHERE employee = %s 
			AND attendance_date BETWEEN %s AND %s 
			AND docstatus = 1 
			AND status IN ('Present', 'Half Day', 'Work From Home') 
			AND ((in_time IS NULL AND out_time IS NOT NULL) OR (out_time IS NULL AND in_time IS NOT NULL))
			""",
			(employee_name, start_date, today),
			as_dict=True
		)
		
		attended_dates = {log.attendance_date for log in attendance_logs}
		
		request_statuses_to_exclude = [
			'Pending', 
			'Approved by the Line Manager', 
			'Approved by the Head of Department'
		]

		pending_request_dates = frappe.db.get_all(
			"Attendance Request",
			filters={
				'employee': employee_name,
				'custom_approval_status': ['in', request_statuses_to_exclude],
				'from_date': ['between', [start_date, today]]
			},
			fields=['from_date']
		)
		pending_dates_set = {request.from_date for request in pending_request_dates}
		
		missing_attendance_dates = [
			date for date in attended_dates
			if date not in pending_dates_set
		]
		
		# limited_missing_dates = missing_attendance_dates[-5:]  
		formatted_dates = [date for date in missing_attendance_dates]

		if not formatted_dates:
			return {"message": "All attendance marked for the last 30 days."}
		else:
			return {"missing_attendance_dates": formatted_dates}
	else:
		return {"message": "Employee not found."}


@frappe.whitelist()
def get_employee_salary():			#Mubashir Bashir
	user_id = frappe.session.user
	employee = frappe.db.get_all('Employee', filters={'user_id': user_id}, fields=['name'])

	if not employee:
		return 0
	employee_name = employee[0].get('name')
	
	salary_structure = frappe.db.sql("""
		SELECT base 
		FROM `tabSalary Structure Assignment`
		WHERE employee = %s
		AND docstatus = 1 
		ORDER BY from_date DESC
		LIMIT 1
	""", (employee_name,), as_dict=True)

	if salary_structure:
		return salary_structure[0].get('base')
	else:
		return 0
	
@frappe.whitelist()
def get_employee_dependents():				#Mubashir Bashir
	user_id = frappe.session.user
	
	employee = frappe.db.get_all('Employee', filters={'user_id': user_id}, fields=['name'])

	if not employee:
		return []

	employee_name = employee[0].get('name')

	dependents = frappe.db.get_all(
		'Employee Dependents',
		filters={'parent': employee_name},
		fields=['dependent_name', 'mobile_number', 'relation', 'cnic'],
		limit = 2
	)

	return dependents

@frappe.whitelist()
def create_additional_salary_for_expense_claim(self):
	if (self.approval_status == "Approved"):
		additional_salary = frappe.new_doc("Additional Salary")
		additional_salary.employee = self.employee
		additional_salary.company = self.company
		additional_salary.payroll_date = self.posting_date
		additional_salary.amount = self.grand_total
		additional_salary.salary_component = "Expense Claim"
		additional_salary.overwrite_salary_structure_amount = 0
		additional_salary.insert()
		additional_salary.submit()
