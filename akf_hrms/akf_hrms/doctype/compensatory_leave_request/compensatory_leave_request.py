# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, cint, date_diff, format_date, get_url_to_list, getdate

from hrms.hr.utils import (
	create_additional_leave_ledger_entry,
	get_holiday_dates_for_employee,
	get_leave_period,
	validate_active_employee,
	validate_dates,
	validate_overlap,
)


class CompensatoryLeaveRequest(Document):
	#Override
	def validate(self):
		validate_active_employee(self.employee)
		validate_dates(self, self.work_from_date, self.work_end_date)

		if self.half_day:
			if not self.half_day_date:
				frappe.throw(_("Half Day Date is mandatory"))
			if (not getdate(self.work_from_date) <= getdate(self.half_day_date) <= getdate(self.work_end_date)):
				frappe.throw(_("Half Day Date should be in between Work From Date and Work End Date"))

		validate_overlap(self, self.work_from_date, self.work_end_date)
		
		if(self.against == "Travel"):
			self.validate_expense_claim_request()
			query = f"""
						SELECT departure_date, arrival_date
						FROM `tabTravel Itinerary`
						WHERE parent = '{self.travel_request}'
					"""
			result = frappe.db.sql(query, as_dict=1)
			departure_date=getdate(result[0].departure_date)
			arrival_date=getdate(result[0].arrival_date)

			if (not departure_date<= getdate(self.work_from_date) <= arrival_date):
				frappe.throw(_(f"Work From Date and Work End Date should be in between: {departure_date} - {arrival_date}"))

			# if (not departure_date<= getdate(self.work_end_date) <= arrival_date):
			# 	frappe.throw(_(f"Arrival Date:  should be in between Work From Date and Work End Date"))

		elif(self.against == "Work on Holiday"):
			self.validate_holidays()
			self.validate_attendance()
		else:
			self.validate_holidays()
			self.validate_attendance()
		
		if not self.leave_type:
			frappe.throw(_("Leave Type is mandatory"))	

	def validate_attendance(self):
		attendance_records = frappe.get_all(
			"Attendance",
			filters={
				"attendance_date": ["between", (self.work_from_date, self.work_end_date)],
				"status": ("in", ["Present", "Work From Home", "Half Day"]),
				"docstatus": 1,
				"employee": self.employee,
			},
			fields=["attendance_date", "status"],
		)

		half_days = [entry.attendance_date for entry in attendance_records if entry.status == "Half Day"]

		if half_days and (not self.half_day or getdate(self.half_day_date) not in half_days):
			frappe.throw(
				_(
					"You were only present for Half Day on {}. Cannot apply for a full day compensatory leave"
				).format(", ".join([frappe.bold(format_date(half_day)) for half_day in half_days]))
			)

		if len(attendance_records) < date_diff(self.work_end_date, self.work_from_date) + 1:
			frappe.throw(_(f"You are not present all day(s) between 'From date: {self.work_from_date}' and 'End date: {self.work_end_date}'"))

	def validate_holidays(self):
		holidays = get_holiday_dates_for_employee(self.employee, self.work_from_date, self.work_end_date)
		if len(holidays) < date_diff(self.work_end_date, self.work_from_date) + 1:
			if date_diff(self.work_end_date, self.work_from_date):
				msg = _("The days between {0} to {1} are not valid holidays.").format(
					frappe.bold(format_date(self.work_from_date)), frappe.bold(format_date(self.work_end_date))
				)
			else:
				msg = _("{0} is not a holiday.").format(frappe.bold(format_date(self.work_from_date)))

			frappe.throw(msg)

	#Override
	def on_submit(self):
		if(self.against== "Travel"):
			self.validate_expense_claim_request()

		company = frappe.db.get_value("Employee", self.employee, "company")
		holiday_list= frappe.db.get_value("Employee",self.employee,"holiday_list")
		compensatory_off=frappe.db.sql(f"""
									SELECT compensatory_leave
									FROM `tabHoliday`
								 	WHERE parent='{holiday_list}' and holiday_date BETWEEN '{self.work_from_date}' AND '{self.work_end_date}'""",as_dict=1)
		
		if(self.against == "Work on Holiday"):
			date_difference = date_diff(self.work_end_date, self.work_from_date) + compensatory_off[0].compensatory_leave
		else:
			date_difference = date_diff(self.work_end_date, self.work_from_date) + 1

		if self.half_day and (self.against == "Work on Holiday"):
			date_difference = date_difference/2	
		elif self.half_day:
			date_difference -= 0.5

		comp_leave_valid_from = add_days(self.work_end_date, 1)
		leave_period = get_leave_period(comp_leave_valid_from, comp_leave_valid_from, company)
		if leave_period:
			leave_allocation = self.get_existing_allocation_for_period(leave_period)
			if leave_allocation:
				leave_allocation.new_leaves_allocated += date_difference
				leave_allocation.validate()
				leave_allocation.db_set("new_leaves_allocated", leave_allocation.total_leaves_allocated)
				leave_allocation.db_set("total_leaves_allocated", leave_allocation.total_leaves_allocated)

				# generate additional ledger entry for the new compensatory leaves off
				create_additional_leave_ledger_entry(leave_allocation, date_difference, comp_leave_valid_from)

			else:
				leave_allocation = self.create_leave_allocation(leave_period, date_difference)
			self.db_set("leave_allocation", leave_allocation.name)
		else:
			comp_leave_valid_from = frappe.bold(format_date(comp_leave_valid_from))
			msg = _("This compensatory leave will be applicable from {0}.").format(comp_leave_valid_from)
			msg += " " + _(
				"Currently, there is no {0} leave period for this date to create/update leave allocation."
			).format(frappe.bold(_("active")))
			msg += "<br><br>" + _("Please create a new {0} for the date {1} first.").format(
				f"""<a href='{get_url_to_list("Leave Period")}'>Leave Period</a>""",
				comp_leave_valid_from,
			)
			frappe.throw(msg, title=_("No Leave Period Found"))

	#Override
	def on_cancel(self):
		if self.leave_allocation:
			if(self.against == "Work on Holiday"):
				holiday_list= frappe.db.get_value("Employee",self.employee,"holiday_list")
				compensatory_off=frappe.db.sql(f"""
									SELECT compensatory_leave
									FROM `tabHoliday`
								 	WHERE parent='{holiday_list}' and holiday_date BETWEEN '{self.work_from_date}' AND '{self.work_end_date}'""",as_dict=1)
				date_difference = date_diff(self.work_end_date, self.work_from_date) + compensatory_off[0].compensatory_leave
			else:
				date_difference = date_diff(self.work_end_date, self.work_from_date) + 1

			if self.half_day:
				date_difference -= 0.5
			leave_allocation = frappe.get_doc("Leave Allocation", self.leave_allocation)
			if leave_allocation:
				leave_allocation.new_leaves_allocated -= date_difference
				if leave_allocation.new_leaves_allocated - date_difference <= 0:
					leave_allocation.new_leaves_allocated = 0
				leave_allocation.validate()
				leave_allocation.db_set("new_leaves_allocated", leave_allocation.total_leaves_allocated)
				leave_allocation.db_set("total_leaves_allocated", leave_allocation.total_leaves_allocated)

				# create reverse entry on cancelation
				create_additional_leave_ledger_entry(
					leave_allocation, date_difference * -1, add_days(self.work_end_date, 1)
				)

	def get_existing_allocation_for_period(self, leave_period):
		leave_allocation = frappe.db.sql(
			"""
			select name
			from `tabLeave Allocation`
			where employee=%(employee)s and leave_type=%(leave_type)s
				and docstatus=1
				and (from_date between %(from_date)s and %(to_date)s
					or to_date between %(from_date)s and %(to_date)s
					or (from_date < %(from_date)s and to_date > %(to_date)s))
		""",
			{
				"from_date": leave_period[0].from_date,
				"to_date": leave_period[0].to_date,
				"employee": self.employee,
				"leave_type": self.leave_type,
			},
			as_dict=1,
		)

		if leave_allocation:
			return frappe.get_doc("Leave Allocation", leave_allocation[0].name)
		else:
			return False

	def create_leave_allocation(self, leave_period, date_difference):
		is_carry_forward = frappe.db.get_value("Leave Type", self.leave_type, "is_carry_forward")
		allocation = frappe.get_doc(
			dict(
				doctype="Leave Allocation",
				employee=self.employee,
				employee_name=self.employee_name,
				leave_type=self.leave_type,
				from_date=add_days(self.work_end_date, 1),
				to_date=leave_period[0].to_date,
				carry_forward=cint(is_carry_forward),
				new_leaves_allocated=date_difference,
				total_leaves_allocated=date_difference,
				description=self.reason,
			)
		)
		allocation.insert(ignore_permissions=True)
		allocation.submit()
		return allocation


# ====================== >  Custom Functions  < ===================================

	def validate_expense_claim_request(self):
		expense_claim_request = frappe.db.sql(
			"""
			select name
			from `tabExpense Claim`
			where employee=%(employee)s and approval_status='Approved'
				and docstatus=1
				and travel_request=%(travel_request)s
		""",
			{
				"employee": self.employee,
				"travel_request": self.travel_request,
			},
			as_dict=1,
		)

		
		if expense_claim_request:
			# frappe.throw(f"cd: {expense_claim_request[0].name}")
			expense_type = frappe.db.sql(
			"""
			select ecd.expense_type, ecd.expense_date
			From `tabExpense Claim` ec
			INNER JOIN `tabExpense Claim Detail` ecd ON ecd.parent = ec.name
			where ec.name = %(name)s
			AND ecd.expense_date BETWEEN %(start_date)s and %(end_date)s
		""",
			{
				"name": expense_claim_request[0].name,
				"start_date": self.work_from_date,
				"end_date": self.work_end_date
			},
			as_dict=1,)

			# frappe.throw(f"{expense_type}")

			if(expense_type):
				for expense in expense_type:
				# frappe.msgprint(f"expense_type: {expense.expense_type}")
					if(expense.expense_type == "Daily Allowance"):
						frappe.throw(f"You can't apply for Leave against Travel Request: {self.travel_request}, as Daily Allowance availed in Expense Claim: '{expense_claim_request[0].name}' against '{expense.expense_date}'!")