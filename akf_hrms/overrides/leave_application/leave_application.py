# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

"""
1- validate_three_casual_leaves_in_current_month (DONE)
2- Short Leave, only one in month
2.1- Short Leave, difference of (to_time - from_time) cannot exceed more than 3 hours
3- Half Day Leave, only one in month
3.1- Half Day Leave, difference of (to_time - from_time) cannot exceed more than 5 hours
4- Earned Leave, employee cannot get before two years. (DONE)
5- Update previous stats of records which may be submitted. (live server)
6- Leave application workflow cancel state is not defined, status 'Approved' is still showing even the doc is cancelled
7- Leave Tracking issue (DONE)
8- Leave work flow for Employee directly reports to HOD
"""
import datetime
from typing import Dict, Optional, Tuple, Union

import frappe
from frappe import _
from frappe.query_builder.functions import Max, Min, Sum
from frappe.utils import (
	add_days,
	cint,
	cstr,
	date_diff,
	flt,
	formatdate,
	get_fullname,
	get_link_to_form,
	getdate,
	nowdate,
)

from erpnext.buying.doctype.supplier_scorecard.supplier_scorecard import daterange
from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee

import hrms
from hrms.hr.doctype.leave_block_list.leave_block_list import get_applicable_block_dates
from hrms.hr.doctype.leave_ledger_entry.leave_ledger_entry import create_leave_ledger_entry
from hrms.hr.utils import (
	get_holiday_dates_for_employee,
	get_leave_period,
	set_employee_name,
	share_doc_with_approver,
	validate_active_employee,
)
from hrms.mixins.pwa_notifications import PWANotificationsMixin
from hrms.utils import get_employee_email


class LeaveDayBlockedError(frappe.ValidationError):
	pass


class OverlapError(frappe.ValidationError):
	pass


class AttendanceAlreadyMarkedError(frappe.ValidationError):
	pass


class NotAnOptionalHoliday(frappe.ValidationError):
	pass


class InsufficientLeaveBalanceError(frappe.ValidationError):
	pass


class LeaveAcrossAllocationsError(frappe.ValidationError):
	pass


from frappe.model.document import Document


class LeaveApplication(Document, PWANotificationsMixin):
	def get_feed(self):
		return _("{0}: From {0} of type {1}").format(self.employee_name, self.leave_type)

	def after_insert(self):
		self.notify_approver()

	def validate(self):
		validate_active_employee(self.employee)
		set_employee_name(self)
		self.validate_dates()
		self.validate_balance_leaves()
		self.validate_leave_overlap()
		self.validate_max_days()
		self.show_block_day_warning()
		self.validate_block_days()
		self.validate_salary_processed_days()
		self.validate_attendance()
		self.set_half_day_date()
		if frappe.db.get_value("Leave Type", self.leave_type, "is_optional_leave"):
			self.validate_optional_leave()
		self.validate_applicable_after()
		self.validate_three_consecutive_casual_leaves_in_period() # Mubashir Bashir 17-07-2025
		self.short_leave_one_in_a_month() # Mubashir Bashir 1-1-2025
		self.half_day_leave_one_in_a_month() # Mubashir Bashir 1-1-2025
		self.short_leave_cannot_exceed_3_hours() # Mubashir Bashir 1-1-2025
		self.half_day_leave_cannot_exceed_4_hours() # Mubashir Bashir 1-1-2025
		self.validate_half_day_leave()
		# self.set_next_workflow_state() # Mubashir Bashir 19-02-2025
		# self.set_next_workflow_approver() # Mubashir Bashir 03-03-2025
		setter_next_workflow_approver(self)
		record_workflow_approver_states(self)
		# self.record_application_state() # Nabeel Saleem, 29-11-2024

	def on_update(self):
		# frappe.throw(self.status)
		if self.status == "Open" and self.docstatus < 1:
			# notify leave approver about creation
			if frappe.db.get_single_value("HR Settings", "send_leave_notification"):
				self.notify_leave_approver()
		# Nabeel Saleem, 13-05-2025
		if(hasattr(self, "workflow_state")):
			if(self.docstatus==1):
				self.status="Approved"
				
		share_doc_with_approver(self, self.leave_approver)
		self.publish_update()
		self.notify_approval_status()

		set_next_workflow_approver_details(self) # Mubashir BAshir 23-7-25

	def on_submit(self):
		if self.status in ["Open", "Cancelled"]:
			frappe.throw(
				_("Only Leave Applications with status 'Approved' and 'Rejected' can be submitted")
			)

		self.validate_back_dated_application()
		self.update_attendance()

		# notify leave applier about approval
		if frappe.db.get_single_value("HR Settings", "send_leave_notification"):
			self.notify_employee()

		self.create_leave_ledger_entry()
		self.reload()

	def before_cancel(self):
		self.status = "Cancelled"

	def on_cancel(self):
		self.create_leave_ledger_entry(submit=False)
		# notify leave applier about cancellation
		if frappe.db.get_single_value("HR Settings", "send_leave_notification"):
			self.notify_employee()
		self.cancel_attendance()
		self.publish_update()
		self.update_status()

	def after_delete(self):
		self.publish_update()

	def publish_update(self):
		employee_user = frappe.db.get_value("Employee", self.employee, "user_id", cache=True)
		hrms.refetch_resource("hrms:my_leaves", employee_user)

	def update_status(self):
		if(not hasattr(self, "workflow_state")): return
		frappe.db.set_value('Leave Application', self.name, 'status', 'Cancelled')
		frappe.db.set_value('Leave Application', self.name, 'workflow_state', 'Cancelled')
		self.reload()

	# Leave Type applicable after working days commented by Mubashir on 14-01-2025 requested by AKFP HR in error sheet		
	# def validate_applicable_after(self):
		# from akf_hrms.patches.skip_validations import skip
		# if(skip()): 
		# 	return
	# 	if self.leave_type:
	# 		leave_type = frappe.get_doc("Leave Type", self.leave_type)
	# 		if leave_type.applicable_after > 0:
	# 			date_of_joining = frappe.db.get_value("Employee", self.employee, "date_of_joining")
	# 			leave_days = get_approved_leaves_for_period(
	# 				self.employee, False, date_of_joining, self.from_date
	# 			)
	# 			number_of_days = date_diff(getdate(self.from_date), date_of_joining)
	# 			if number_of_days >= 0:
	# 				holidays = 0
	# 				if not frappe.db.get_value("Leave Type", self.leave_type, "include_holiday"):
	# 					holidays = get_holidays(self.employee, date_of_joining, self.from_date)
	# 				number_of_days = number_of_days - leave_days - holidays
	# 				if number_of_days < leave_type.applicable_after:
	# 					frappe.throw(
	# 						_("{0} applicable after {1} working days").format(
	# 							self.leave_type, leave_type.applicable_after
	# 						)
	# 					)

	#Leave Type applicable after normal days done by Mubashir on 14-01-2025 requeted by AKFP HR in error sheet	 
	def validate_applicable_after(self):
		from akf_hrms.patches.skip_validations import skip		
		if skip():
			return		
		if self.leave_type:
			leave_type = frappe.get_doc("Leave Type", self.leave_type)
			applicable_after_days = int(leave_type.custom_applicable_after_days or 0)
			
			if applicable_after_days > 0:
				date_of_joining = frappe.db.get_value("Employee", self.employee, "date_of_joining")
				number_of_days = date_diff(getdate(self.from_date), date_of_joining)
				
				if number_of_days < applicable_after_days:
					frappe.throw(
						_("{0} applicable after {1} days after joining date").format(
							self.leave_type, leave_type.custom_applicable_after_days
						)
					)



	def validate_dates(self):
		if frappe.db.get_single_value("HR Settings", "restrict_backdated_leave_application"):
			if self.from_date and getdate(self.from_date) < getdate():
				allowed_role = frappe.db.get_single_value(
					"HR Settings", "role_allowed_to_create_backdated_leave_application"
				)
				user = frappe.get_doc("User", frappe.session.user)
				user_roles = [d.role for d in user.roles]
				if not allowed_role:
					frappe.throw(
						_("Backdated Leave Application is restricted. Please set the {} in {}").format(
							frappe.bold(_("Role Allowed to Create Backdated Leave Application")),
							get_link_to_form("HR Settings", "HR Settings", _("HR Settings")),
						)
					)

				if allowed_role and allowed_role not in user_roles:
					frappe.throw(
						_("Only users with the {0} role can create backdated leave applications").format(
							_(allowed_role)
						)
					)

		if self.from_date and self.to_date and (getdate(self.to_date) < getdate(self.from_date)):
			frappe.throw(_("To date cannot be before from date"))

		if (
			self.half_day
			and self.half_day_date
			and (
				getdate(self.half_day_date) < getdate(self.from_date)
				or getdate(self.half_day_date) > getdate(self.to_date)
			)
		):

			frappe.throw(_("Half Day Date should be between From Date and To Date"))

		if not is_lwp(self.leave_type):
			self.validate_dates_across_allocation()
			self.validate_back_dated_application()

	def validate_dates_across_allocation(self):
		if frappe.db.get_value("Leave Type", self.leave_type, "allow_negative"):
			return

		alloc_on_from_date, alloc_on_to_date = self.get_allocation_based_on_application_dates()

		if not (alloc_on_from_date or alloc_on_to_date):
			frappe.throw(_("Application period cannot be outside leave allocation period"))
		elif self.is_separate_ledger_entry_required(alloc_on_from_date, alloc_on_to_date):
			frappe.throw(
				_("Application period cannot be across two allocation records"),
				exc=LeaveAcrossAllocationsError,
			)

	def get_allocation_based_on_application_dates(self) -> Tuple[Dict, Dict]:
		"""Returns allocation name, from and to dates for application dates"""

		def _get_leave_allocation_record(date):
			LeaveAllocation = frappe.qb.DocType("Leave Allocation")
			allocation = (
				frappe.qb.from_(LeaveAllocation)
				.select(LeaveAllocation.name, LeaveAllocation.from_date, LeaveAllocation.to_date)
				.where(
					(LeaveAllocation.employee == self.employee)
					& (LeaveAllocation.leave_type == self.leave_type)
					& (LeaveAllocation.docstatus == 1)
					& ((date >= LeaveAllocation.from_date) & (date <= LeaveAllocation.to_date))
				)
			).run(as_dict=True)

			return allocation and allocation[0]

		allocation_based_on_from_date = _get_leave_allocation_record(self.from_date)
		allocation_based_on_to_date = _get_leave_allocation_record(self.to_date)

		return allocation_based_on_from_date, allocation_based_on_to_date

	def validate_back_dated_application(self):
		future_allocation = frappe.db.sql(
			"""select name, from_date from `tabLeave Allocation`
			where employee=%s and leave_type=%s and docstatus=1 and from_date > %s
			and carry_forward=1""",
			(self.employee, self.leave_type, self.to_date),
			as_dict=1,
		)

		if future_allocation:
			frappe.throw(
				_(
					"Leave cannot be applied/cancelled before {0}, as leave balance has already been carry-forwarded in the future leave allocation record {1}"
				).format(formatdate(future_allocation[0].from_date), future_allocation[0].name)
			)

	""" HR Leave Policy """
	
	""" HR Policy for Casual, Short, and Half day leaves Implemented By Mubashir """
	""" --------------------------------START----------------------------------- """
	# Implemented by Mubashir 1-1-2025
	def get_payroll_period_dates(self, date):
		"""Returns start and end dates for payroll period containing the given date
		
		For dates 1-20: Period is 21st of previous month to 20th of current month
		For dates 21-31: Period is 21st of current month to 20th of next month
		"""
		date = getdate(date)
		
		if date.day <= 20:
			# For dates 1-20
			# Start: 21st of previous month
			period_start = getdate(date).replace(day=21)
			period_start = frappe.utils.add_months(period_start, -1)
			
			# End: 20th of current month
			period_end = getdate(date).replace(day=20)
			
		else:
			# For dates 21-31
			# Start: 21st of current month
			period_start = getdate(date).replace(day=21)
			
			# End: 20th of next month
			period_end = getdate(date).replace(day=20)
			period_end = frappe.utils.add_months(period_end, 1)
		
		# frappe.msgprint(f'Payroll Dates: {period_start} - {period_end} - {date} - {date.day}')
			
		return period_start, period_end
	
	# Implemented by Mubashir 1-1-2025
	def get_period_name(self, start_date):
		"""Returns a formatted name for the payroll period
		Format: 'January 21 - February 20' for each period
		"""
		start_date = getdate(start_date)
		end_date = getdate(start_date).replace(day=20)		
		if start_date.day == 21:
			end_date = frappe.utils.add_months(end_date, 1)		
		period_name = f"{start_date.strftime('%B %d')} - {end_date.strftime('%B %d')}"
		# frappe.msgprint(f"Period Name: {period_name}")		
		return period_name
	
	# Implemented by Mubashir 1-1-2025
	def verify_leave_count(self, start_date, end_date, period_name, max_leaves, leave_type):
		"""Generic helper function to verify leave count for a date range"""
		try:
			# First get existing leaves in the period
			result = frappe.db.sql("""
				SELECT 
					DATEDIFF(to_date, from_date) + 1 as days
				FROM `tabLeave Application`
				WHERE 
					docstatus != 2
					AND workflow_state != 'Rejected'
					AND workflow_state != 'Rejected by Line Manager'
					AND workflow_state != 'Rejected by Head of Department'
					AND workflow_state != 'Rejected by Chief Executive Officer'
					AND employee = %s
					AND company = %s
					AND leave_type = %s
					AND from_date >= %s 
					AND to_date <= %s
					AND name != %s
			""", (
				self.employee,
				self.company,
				leave_type,
				start_date,
				end_date,
				self.name
			), as_dict=1)

			# Calculate total days from existing applications
			existing_days = sum(r.days for r in result)
			# Calculate days in current application
			current_days = date_diff(self.to_date, self.from_date) + 1
			# Total days including current application
			total_days = existing_days + current_days

			if total_days > max_leaves:
				frappe.throw(
					msg=f"Only {max_leaves} {leave_type} {'day' if max_leaves == 1 else 'days'} allowed in payroll period "
						f"({period_name}). This would be {total_days} days.",
					title=f"Maximum {leave_type} Days Exceeded"
				)
		except Exception as e:
			frappe.log_error(
				message=f"Error checking {leave_type} for period {period_name}: {str(e)}",
				title=f"{leave_type} Validation Error"
			)
			raise

	# Implemented by Mubashir 17-07-2025			
	def validate_three_consecutive_casual_leaves_in_period(self):
		"""Validates that an employee doesn't exceed 3 consecutive casual leaves in a payroll period"""
		from akf_hrms.patches.skip_validations import skip
		if skip() or self.leave_type != "Casual Leave":
			return

		try:
			# Get payroll periods for from_date and to_date
			from_date_period_start, from_date_period_end = self.get_payroll_period_dates(self.from_date)
			to_date_period_start, to_date_period_end = self.get_payroll_period_dates(self.to_date)

			# For each period spanned by the application
			periods = set()
			periods.add((from_date_period_start, from_date_period_end))
			periods.add((to_date_period_start, to_date_period_end))

			for period_start, period_end in periods:
				# Get all existing casual leave applications in this period (excluding current)
				existing_leaves = frappe.db.sql("""
					SELECT from_date, to_date
					FROM `tabLeave Application`
					WHERE 
						docstatus != 2
						AND workflow_state NOT IN ('Rejected', 'Rejected by Line Manager', 'Rejected by Head of Department', 'Rejected by Chief Executive Officer')
						AND employee = %s
						AND company = %s
						AND leave_type = %s
						AND from_date >= %s 
						AND to_date <= %s
						AND name != %s
				""", (
					self.employee,
					self.company,
					"Casual Leave",
					period_start,
					period_end,
					self.name
				), as_dict=1)

				# Add current application
				all_leaves = list(existing_leaves)
				all_leaves.append({"from_date": self.from_date, "to_date": self.to_date})

				# Collect all leave dates in this period
				leave_dates = set()
				for leave in all_leaves:
					start = getdate(leave["from_date"])
					end = getdate(leave["to_date"])
					for d in range((end - start).days + 1):
						leave_dates.add(start + datetime.timedelta(days=d))

				# Only consider dates within the period
				period_dates = set()
				p_start = getdate(period_start)
				p_end = getdate(period_end)
				for d in range((p_end - p_start).days + 1):
					period_dates.add(p_start + datetime.timedelta(days=d))
				leave_dates = leave_dates & period_dates

				# Check for more than 3 consecutive days
				if leave_dates:
					sorted_dates = sorted(leave_dates)
					max_consec = 1
					current_consec = 1
					for i in range(1, len(sorted_dates)):
						if (sorted_dates[i] - sorted_dates[i-1]).days == 1:
							current_consec += 1
							max_consec = max(max_consec, current_consec)
						else:
							current_consec = 1
					if max_consec > 3:
						frappe.throw(
							msg=f"You cannot apply for more than 3 consecutive Casual Leave days in a payroll period. Found {max_consec} consecutive days.",
							title="Maximum Consecutive Casual Leave Days Exceeded"
						)
		except Exception as e:
			frappe.log_error(
				message=f"Error in consecutive casual leave validation: {str(e)}",
				title="Consecutive Casual Leave Validation Error"
			)
			raise

	# Implemented by Mubashir 1-1-2025
	def short_leave_one_in_a_month(self):
		"""Validates that an employee doesn't exceed 1 short leave in a payroll period"""
		from akf_hrms.patches.skip_validations import skip
		if skip() or self.leave_type != "Short Leave":
			return

		try:
			# Ensure short leave is for single day
			if getdate(self.from_date) != getdate(self.to_date):
				frappe.throw(
					msg="Short Leave must be for a single day only.",
					title="Invalid Short Leave Duration"
				)

			# Get payroll period and verify
			period_start, period_end = self.get_payroll_period_dates(self.from_date)
			self.verify_leave_count(				
				period_start,
				period_end,
				self.get_period_name(period_start),
				1,
				"Short Leave"
			)

		except Exception as e:
			frappe.log_error(
				message=f"Error in short leave validation: {str(e)}",
				title="Short Leave Validation Error"
			)
			raise
			# frappe.throw(
			# 	msg="Error validating short leaves. Please contact system administrator.",
			# 	title="Validation Error"
			# )

	# Implemented by Mubashir 1-1-2025
	def half_day_leave_one_in_a_month(self):
		"""Validates that an employee doesn't exceed 1 half day leave in a payroll period"""
		from akf_hrms.patches.skip_validations import skip
		if skip() or self.leave_type != "Half Day Leave":
			return
		if self.leave_type != "Half Day Leave":
			return

		try:
			# Ensure half day leave is for single day
			if getdate(self.from_date) != getdate(self.to_date):
				frappe.throw(
					msg="Half Day Leave must be for a single day only.",
					title="Invalid Half Day Leave Duration"
				)

			# Get payroll period and verify
			period_start, period_end = self.get_payroll_period_dates(self.from_date)
			self.verify_leave_count(				
				period_start,
				period_end,
				self.get_period_name(period_start),
				1,
				"Half Day Leave"
			)

		except Exception as e:
			frappe.log_error(
				message=f"Error in half day leave validation: {str(e)}",
				title="Half Day Leave Validation Error"
			)
			raise
			# frappe.throw(
			# 	msg="Error validating half day leaves. Please contact system administrator.",
			# 	title="Validation Error"
			# )

	# Implemented by Mubashir 1-1-2025
	def short_leave_cannot_exceed_3_hours(self):
		"""Validates that short leave duration doesn't exceed 3 hours"""
		if self.custom_from_time and self.custom_to_time:
			hours = frappe.utils.time_diff_in_hours(self.custom_to_time, self.custom_from_time)
			if self.leave_type == 'Short Leave' and hours > 3:
				frappe.throw(
					msg='Short Leave cannot exceed 3 hours. Please adjust the duration accordingly.',
					title='Invalid Short Leave Duration'
				)

	# Implemented by Mubashir 1-1-2025
	def half_day_leave_cannot_exceed_4_hours(self):
		"""Validates that half day leave duration doesn't exceed 4 hours"""
		if self.custom_from_time and self.custom_to_time:
			hours = frappe.utils.time_diff_in_hours(self.custom_to_time, self.custom_from_time)
			if self.leave_type == 'Half Day Leave' and hours > 4:
				frappe.throw(
					msg='Half Day Leave cannot exceed 4 hours. Please adjust the duration accordingly.',
					title='Invalid Half Day Duration'
				)

	""" HR Policy for Casual, Short, and Half day leaves Implemented By Mubashir """
	""" --------------------------------END------------------------------------- """

	@frappe.whitelist()
	def validate_half_day_leave(self):  	
		from akf_hrms.utils.leave_policy import verify_half_day_leave
		verify_half_day_leave(self)
	
	# Nabeel Saleem, 18-12-2024
	# @frappe.whitelist()
	# def set_next_workflow_approver(self):
	# 	if(not hasattr(self, 'workflow_state')): return		
	# 	if(self.status!='Open'): return
	# 	data = frappe.db.sql(f""" 
	# 		Select 
	# 			w.name, wt.state, wt.action, wt.next_state, wt.allowed, wt.allow_self_approval
	# 		From 
	# 			`tabWorkflow` w inner join `tabWorkflow Transition` wt on (w.name=wt.parent)
	# 		Where 
	# 			w.document_type='Leave Application'
	# 			and w.is_active = 1
	# 			and wt.action='Approve'
	# 			and wt.state='{self.workflow_state}'
	# 		Order by
	# 			wt.idx asc
	# 		limit 1
	# 	""", as_dict=1)
	# 	# => find approver
	# 	def set_approver_detail(user_id, next_state):
	# 		self.leave_approver = user_id
	# 		self.leave_approver_name = get_fullname(user_id)
	# 		self.custom_next_workflow_state = next_state

	# 	for d in data:
	# 		if(d.allowed == "Line Manager"):
	# 			reports_to = frappe.db.get_value('Employee', {'name': self.employee}, 'reports_to')
	# 			if(reports_to):
	# 				user_id = frappe.db.get_value('Employee', {'name': reports_to}, 'user_id')
	# 				if(frappe.db.exists('Has Role', {'parent': user_id, 'role': 'Line Manager'})):
	# 					set_approver_detail(user_id, d.next_state)
	# 			else:
	# 				frappe.throw(f"Please set a `reports to` of this employee", title="Line Manager")
						
	# 		elif(d.allowed == "Head of Department"):
	# 			user_id = frappe.db.get_value('Employee', {'department': self.department , 'custom_hod': 1}, 'user_id')
	# 			if(user_id):
	# 				set_approver_detail(user_id, d.next_state)
	# 			else:
	# 				frappe.throw(f"Please set a `head of department` of department {self.department}", title="Head of Department")
			
	# 		elif(d.allowed == 'CEO'):
	# 			user_list = frappe.db.sql(""" 
	# 					Select 
	# 						u.name 
	# 					From 
	# 						`tabUser` u inner join `tabHas Role` h on (u.name=h.parent) 
	# 					Where 
	# 						h.role in ('CEO')
	# 					Group by
	# 						u.name 
	# 			""")
	# 			if(user_list):
	# 				set_approver_detail(user_list[0][0], d.next_state)
	# 			else:
	# 				frappe.throw(f"Please set a `CEO` of {self.company}", title="CEO")

	# Mubashir Bashir 03-03-2025 Start
	@frappe.whitelist()
	def set_next_workflow_approver(self):
		if(not hasattr(self, 'workflow_state')): return		
		if(self.status!='Open'): return

		# => find approver
		def set_approver_detail(user_id):
			self.leave_approver = user_id
			self.leave_approver_name = get_fullname(user_id)

		if (self.custom_next_workflow_state == 'Recommended by Line Manager'):
			reports_to = frappe.db.get_value('Employee', {'name': self.employee}, 'reports_to')
			if(reports_to):
				user_id = frappe.db.get_value('Employee', {'name': reports_to}, 'user_id')
				if(frappe.db.exists('Has Role', {'parent': user_id, 'role': 'Line Manager'})):
					set_approver_detail(user_id)
			else:
				frappe.throw(f"Please set a `reports to` of this employee", title="Line Manager")
					
		elif(self.custom_next_workflow_state == 'Recommended by Head of Department'):
			user_id = frappe.db.get_value('Employee', {'department': self.department , 'custom_hod': 1}, 'user_id')
			if(user_id):
				set_approver_detail(user_id)
			else:
				frappe.throw(f"Please set a `head of department` of department {self.department}", title="Head of Department")
		
		elif(self.custom_next_workflow_state == 'Approved'):
			user_list = frappe.db.sql(""" 
					Select 
						u.name 
					From 
						`tabUser` u inner join `tabHas Role` h on (u.name=h.parent) 
					Where 
						h.role in ('CEO')
					Group by
						u.name 
			""")
			if(user_list):
				set_approver_detail(user_list[0][0])
			else:
				frappe.throw(f"Please set a `Chief Executive Officer` of {self.company}", title="Chief Executive Officer")
	# Mubashir Bashir 03-03-2025 End


	# Mubashir Bashir 19-02-2025 Start
	def set_next_workflow_state(self):
		employee_user_id = frappe.db.get_value("Employee", self.employee, "user_id")

		if not employee_user_id: return

		employee_roles = frappe.get_roles(employee_user_id)

		if (frappe.db.exists('Employee', {'name': self.employee, 'custom_directly_reports_to_hod': 0}) and 
			"Employee" in employee_roles and 
			not any(role in employee_roles for role in ["Line Manager", "Head of Department", "CEO"])):
			if (self.custom_next_workflow_state == 'Recommended by Line Manager'):
				self.custom_next_workflow_state = 'Recommended by Head of Department'
				self.custom_workflow_indication = 'Line Manager to Head of Department'
			elif (self.custom_next_workflow_state == 'Recommended by Head of Department'):
				self.custom_next_workflow_state = 'Approved'
				self.custom_workflow_indication = 'Head of Department to CEO'
			else:
				self.custom_next_workflow_state = 'Recommended by Line Manager'
				self.custom_workflow_indication = 'Applied to Line Manager'


		elif (frappe.db.exists('Employee', {'name': self.employee, 'custom_directly_reports_to_hod': 1}) and 
			"Employee" in employee_roles and 
			not any(role in employee_roles for role in ["Line Manager", "Head of Department", "CEO"])):
			if (self.custom_next_workflow_state == 'Recommended by Head of Department'):
				self.custom_next_workflow_state = 'Approved'
				self.custom_workflow_indication = 'Head of Department to CEO'
			else:
				self.custom_next_workflow_state = 'Recommended by Head of Department'
				self.custom_workflow_indication = 'Applied to HOD'


		elif "Line Manager" in employee_roles and not any(role in employee_roles for role in ["Head of Department", "CEO"]):
			if (self.custom_next_workflow_state == 'Recommended by Head of Department'):
				self.custom_next_workflow_state = 'Approved'
				self.custom_workflow_indication = 'Head of Department to CEO'
			else:
				self.custom_next_workflow_state = 'Recommended by Head of Department'
				self.custom_workflow_indication = 'Applied to HOD'
				

		elif "Head of Department" in employee_roles and "CEO" not in employee_roles:
			self.custom_next_workflow_state = 'Approved'
			self.custom_workflow_indication = 'Applied to CEO'
		
		# self.leave_approver_name = get_fullname(self.leave_approver)
	# Mubashir Bashir 19-02-2025 End


	# Nabeel Saleem, 29-11-2024
	def record_application_state(self):
		if(hasattr(self, 'workflow_state')):
			from frappe.utils import get_datetime
			state_dict = eval(self.custom_state_data) if(self.custom_state_data) else {}
			# if(self.workflow_state not in state_dict):
			state_dict.update({f"{self.workflow_state}": {
				"current_user": f"{self.workflow_state} (<b>{get_fullname(frappe.session.user)}</b>)",
				"next_state": f"{self.custom_next_workflow_state} (<b>{self.leave_approver_name}</b>)" if(self.status=='Open') else "",
				"modified_on": get_datetime(),
			}})
			self.custom_state_data =  frappe.as_json(state_dict)
	
	def update_attendance(self):
		if self.status != "Approved":
			return

		holiday_dates = []
		if not frappe.db.get_value("Leave Type", self.leave_type, "include_holiday"):
			holiday_dates = get_holiday_dates_for_employee(self.employee, self.from_date, self.to_date)

		for dt in daterange(getdate(self.from_date), getdate(self.to_date)):
			date = dt.strftime("%Y-%m-%d")
			attendance_name = frappe.db.exists(
				"Attendance", dict(employee=self.employee, attendance_date=date, docstatus=("!=", 2))
			)

			# don't mark attendance for holidays
			# if leave type does not include holidays within leaves as leaves
			if date in holiday_dates:
				""" if attendance_name:
					# cancel and delete existing attendance for holidays
					attendance = frappe.get_doc("Attendance", attendance_name)
					attendance.flags.ignore_permissions = True
					if attendance.docstatus == 1:
						attendance.cancel()
					frappe.delete_doc("Attendance", attendance_name, force=1) """
				continue

			self.create_or_update_attendance(attendance_name, date)

	def create_or_update_attendance(self, attendance_name, date):
		""" status = (
			"Half Day"
			if self.half_day_date and getdate(date) == getdate(self.half_day_date)
			else "On Leave"
		) """
		# start, nabeel saleem, [19-12-2024]
		status = (
			"Half Day"
			if (self.half_day_date and getdate(date) == getdate(self.half_day_date)) or (self.leave_type in ["Short Leave", "Half Day Leave"])
			else "On Leave"
		)
		# end, nabeel saleem, [19-12-2024]
		if attendance_name:
			# update existing attendance, change absent to on leave
			doc = frappe.get_doc("Attendance", attendance_name)
			doc.db_set({"status": status, "leave_type": self.leave_type, "leave_application": self.name})
		else:
			# make new attendance and submit it
			doc = frappe.new_doc("Attendance")
			doc.employee = self.employee
			doc.employee_name = self.employee_name
			doc.attendance_date = date
			doc.company = self.company
			doc.leave_type = self.leave_type
			doc.leave_application = self.name
			doc.status = status
			doc.flags.ignore_validate = True
			doc.insert(ignore_permissions=True)
			doc.submit()

	def cancel_attendance(self):
		if self.docstatus == 2:
			attendance = frappe.db.sql(
				"""select name from `tabAttendance` where employee = %s\
				and (attendance_date between %s and %s) and docstatus < 2 and status in ('On Leave', 'Half Day')""",
				(self.employee, self.from_date, self.to_date),
				as_dict=1,
			)
			for name in attendance:
				frappe.db.set_value("Attendance", name, "docstatus", 2)

	def validate_salary_processed_days(self):
		if not frappe.db.get_value("Leave Type", self.leave_type, "is_lwp"):
			return

		last_processed_pay_slip = frappe.db.sql(
			"""
			select start_date, end_date from `tabSalary Slip`
			where docstatus = 1 and employee = %s
			and ((%s between start_date and end_date) or (%s between start_date and end_date))
			order by modified desc limit 1
		""",
			(self.employee, self.to_date, self.from_date),
		)

		if last_processed_pay_slip:
			frappe.throw(
				_(
					"Salary already processed for period between {0} and {1}, Leave application period cannot be between this date range."
				).format(
					formatdate(last_processed_pay_slip[0][0]), formatdate(last_processed_pay_slip[0][1])
				)
			)

	def show_block_day_warning(self):
		block_dates = get_applicable_block_dates(
			self.from_date,
			self.to_date,
			self.employee,
			self.company,
			all_lists=True,
			leave_type=self.leave_type,
		)

		if block_dates:
			frappe.msgprint(_("Warning: Leave application contains following block dates") + ":")
			for d in block_dates:
				frappe.msgprint(formatdate(d.block_date) + ": " + d.reason)

	def validate_block_days(self):
		block_dates = get_applicable_block_dates(
			self.from_date, self.to_date, self.employee, self.company, leave_type=self.leave_type
		)

		if block_dates and self.status == "Approved":
			frappe.throw(_("You are not authorized to approve leaves on Block Dates"), LeaveDayBlockedError)

	def validate_balance_leaves(self):
		if self.from_date and self.to_date:
			self.total_leave_days = get_number_of_leave_days(
				self.employee, self.leave_type, self.from_date, self.to_date, self.half_day, self.half_day_date
			)

			if self.total_leave_days <= 0:
				frappe.throw(
					_(
						"The day(s) on which you are applying for leave are holidays. You need not apply for leave."
					)
				)

			if not is_lwp(self.leave_type):
				leave_balance = get_leave_balance_on(
					self.employee,
					self.leave_type,
					self.from_date,
					self.to_date,
					consider_all_leaves_in_the_allocation_period=True,
					for_consumption=True,
				)
				self.leave_balance = leave_balance.get("leave_balance")
				leave_balance_for_consumption = leave_balance.get("leave_balance_for_consumption")

				if self.status != "Rejected" and (
					leave_balance_for_consumption < self.total_leave_days or not leave_balance_for_consumption
				):
					self.show_insufficient_balance_message(leave_balance_for_consumption)

	def show_insufficient_balance_message(self, leave_balance_for_consumption: float) -> None:
		alloc_on_from_date, alloc_on_to_date = self.get_allocation_based_on_application_dates()

		if frappe.db.get_value("Leave Type", self.leave_type, "allow_negative"):
			if leave_balance_for_consumption != self.leave_balance:
				msg = _("Warning: Insufficient leave balance for Leave Type {0} in this allocation.").format(
					frappe.bold(self.leave_type)
				)
				msg += "<br><br>"
				msg += _(
					"Actual balances aren't available because the leave application spans over different leave allocations. You can still apply for leaves which would be compensated during the next allocation."
				)
			else:
				msg = _("Warning: Insufficient leave balance for Leave Type {0}.").format(
					frappe.bold(self.leave_type)
				)

			frappe.msgprint(msg, title=_("Warning"), indicator="orange")
		else:
			frappe.throw(
				_("Insufficient leave balance for Leave Type {0}").format(frappe.bold(self.leave_type)),
				exc=InsufficientLeaveBalanceError,
				title=_("Insufficient Balance"),
			)

	def validate_leave_overlap(self):
		if not self.name:
			# hack! if name is null, it could cause problems with !=
			self.name = "New Leave Application"

		for d in frappe.db.sql(
			"""
			select
				name, leave_type, posting_date, from_date, to_date, total_leave_days, half_day_date
			from `tabLeave Application`
			where employee = %(employee)s and docstatus < 2 and status in ('Open', 'Approved')
			and to_date >= %(from_date)s and from_date <= %(to_date)s
			and name != %(name)s""",
			{
				"employee": self.employee,
				"from_date": self.from_date,
				"to_date": self.to_date,
				"name": self.name,
			},
			as_dict=1,
		):

			if (
				cint(self.half_day) == 1
				and getdate(self.half_day_date) == getdate(d.half_day_date)
				and (
					flt(self.total_leave_days) == 0.5
					or getdate(self.from_date) == getdate(d.to_date)
					or getdate(self.to_date) == getdate(d.from_date)
				)
			):

				total_leaves_on_half_day = self.get_total_leaves_on_half_day()
				if total_leaves_on_half_day >= 1:
					self.throw_overlap_error(d)
			else:
				self.throw_overlap_error(d)

	def throw_overlap_error(self, d):
		form_link = get_link_to_form("Leave Application", d.name)
		msg = _("Employee {0} has already applied for {1} between {2} and {3} : {4}").format(
			self.employee, d["leave_type"], formatdate(d["from_date"]), formatdate(d["to_date"]), form_link
		)
		frappe.throw(msg, OverlapError)

	def get_total_leaves_on_half_day(self):
		leave_count_on_half_day_date = frappe.db.sql(
			"""select count(name) from `tabLeave Application`
			where employee = %(employee)s
			and docstatus < 2
			and status in ('Open', 'Approved')
			and half_day = 1
			and half_day_date = %(half_day_date)s
			and name != %(name)s""",
			{"employee": self.employee, "half_day_date": self.half_day_date, "name": self.name},
		)[0][0]

		return leave_count_on_half_day_date * 0.5

	def validate_max_days(self):
		max_days = frappe.db.get_value("Leave Type", self.leave_type, "max_continuous_days_allowed")
		if not max_days:
			return

		details = self.get_consecutive_leave_details()

		if details.total_consecutive_leaves > cint(max_days):
			msg = _("Leave of type {0} cannot be longer than {1}.").format(
				get_link_to_form("Leave Type", self.leave_type), max_days
			)
			if details.leave_applications:
				msg += "<br><br>" + _("Reference: {0}").format(
					", ".join(get_link_to_form("Leave Application", name) for name in details.leave_applications)
				)

			frappe.throw(msg, title=_("Maximum Consecutive Leaves Exceeded"))

	def get_consecutive_leave_details(self) -> dict:
		leave_applications = set()

		def _get_first_from_date(reference_date):
			"""gets `from_date` of first leave application from previous consecutive leave applications"""
			prev_date = add_days(reference_date, -1)
			application = frappe.db.get_value(
				"Leave Application",
				{
					"employee": self.employee,
					"leave_type": self.leave_type,
					"to_date": prev_date,
					"docstatus": ["!=", 2],
					"status": ["in", ["Open", "Approved"]],
				},
				["name", "from_date"],
				as_dict=True,
			)
			if application:
				leave_applications.add(application.name)
				return _get_first_from_date(application.from_date)
			return reference_date

		def _get_last_to_date(reference_date):
			"""gets `to_date` of last leave application from following consecutive leave applications"""
			next_date = add_days(reference_date, 1)
			application = frappe.db.get_value(
				"Leave Application",
				{
					"employee": self.employee,
					"leave_type": self.leave_type,
					"from_date": next_date,
					"docstatus": ["!=", 2],
					"status": ["in", ["Open", "Approved"]],
				},
				["name", "to_date"],
				as_dict=True,
			)
			if application:
				leave_applications.add(application.name)
				return _get_last_to_date(application.to_date)
			return reference_date

		first_from_date = _get_first_from_date(self.from_date)
		last_to_date = _get_last_to_date(self.to_date)

		total_consecutive_leaves = get_number_of_leave_days(
			self.employee, self.leave_type, first_from_date, last_to_date
		)

		return frappe._dict(
			{
				"total_consecutive_leaves": total_consecutive_leaves,
				"leave_applications": leave_applications,
			}
		)

	def validate_attendance(self):
		# changes
		attendance = frappe.db.sql(
			"""select name from `tabAttendance` where employee = %s and (attendance_date between %s and %s)
					and status = 'On Leave' and docstatus = 1""",
			(self.employee, self.from_date, self.to_date),
		)
		if attendance:
			frappe.throw(
				_("Attendance for employee {0} is already marked for this day").format(self.employee),
				AttendanceAlreadyMarkedError,
			)

	def validate_optional_leave(self):
		leave_period = get_leave_period(self.from_date, self.to_date, self.company)
		if not leave_period:
			frappe.throw(_("Cannot find active Leave Period"))
		optional_holiday_list = frappe.db.get_value(
			"Leave Period", leave_period[0]["name"], "optional_holiday_list"
		)
		if not optional_holiday_list:
			frappe.throw(
				_("Optional Holiday List not set for leave period {0}").format(leave_period[0]["name"])
			)
		day = getdate(self.from_date)
		while day <= getdate(self.to_date):
			if not frappe.db.exists(
				{"doctype": "Holiday", "parent": optional_holiday_list, "holiday_date": day}
			):
				frappe.throw(
					_("{0} is not in Optional Holiday List").format(formatdate(day)), NotAnOptionalHoliday
				)
			day = add_days(day, 1)

	def set_half_day_date(self):
		if self.from_date == self.to_date and self.half_day == 1:
			self.half_day_date = self.from_date

		if self.half_day == 0:
			self.half_day_date = None

	def notify_employee(self):
		employee_email = get_employee_email(self.employee)

		if not employee_email:
			return

		parent_doc = frappe.get_doc("Leave Application", self.name)
		args = parent_doc.as_dict()

		template = frappe.db.get_single_value("HR Settings", "leave_status_notification_template")
		if not template:
			frappe.msgprint(_("Please set default template for Leave Status Notification in HR Settings."))
			return
		email_template = frappe.get_doc("Email Template", template)
		message = frappe.render_template(email_template.response_, args)

		self.notify(
			{
				# for post in messages
				"message": message,
				"message_to": employee_email,
				# for email
				"subject": email_template.subject,
				"notify": "employee",
			}
		)

	def notify_leave_approver(self):
		if self.leave_approver:
			parent_doc = frappe.get_doc("Leave Application", self.name)
			args = parent_doc.as_dict()

			template = frappe.db.get_single_value("HR Settings", "leave_approval_notification_template")
			if not template:
				frappe.msgprint(
					_("Please set default template for Leave Approval Notification in HR Settings.")
				)
				return
			email_template = frappe.get_doc("Email Template", template)
			message = frappe.render_template(email_template.response_, args)

			self.notify(
				{
					# for post in messages
					"message": message,
					"message_to": self.leave_approver,
					# for email
					"subject": email_template.subject,
				}
			)

	def notify(self, args):
		args = frappe._dict(args)
		# args -> message, message_to, subject
		if cint(self.follow_via_email):
			contact = args.message_to
			if not isinstance(contact, list):
				if not args.notify == "employee":
					contact = frappe.get_doc("User", contact).email or contact

			sender = dict()
			sender["email"] = frappe.get_doc("User", frappe.session.user).email
			sender["full_name"] = get_fullname(sender["email"])

			try:
				frappe.sendmail(
					recipients=contact,
					sender=sender["email"],
					subject=args.subject,
					message=args.message,
				)
				frappe.msgprint(_("Email sent to {0}").format(contact))
			except frappe.OutgoingEmailError:
				pass

	def create_leave_ledger_entry(self, submit=True):
		if self.status != "Approved" and submit:
			return

		expiry_date = get_allocation_expiry_for_cf_leaves(
			self.employee, self.leave_type, self.to_date, self.from_date
		)
		lwp = frappe.db.get_value("Leave Type", self.leave_type, "is_lwp")

		if expiry_date:
			self.create_ledger_entry_for_intermediate_allocation_expiry(expiry_date, submit, lwp)
		else:
			alloc_on_from_date, alloc_on_to_date = self.get_allocation_based_on_application_dates()
			if self.is_separate_ledger_entry_required(alloc_on_from_date, alloc_on_to_date):
				# required only if negative balance is allowed for leave type
				# else will be stopped in validation itself
				self.create_separate_ledger_entries(alloc_on_from_date, alloc_on_to_date, submit, lwp)
			else:
				raise_exception = False if frappe.flags.in_patch else True
				args = dict(
					leaves=self.total_leave_days * -1,
					from_date=self.from_date,
					to_date=self.to_date,
					is_lwp=lwp,
					holiday_list=get_holiday_list_for_employee(self.employee, raise_exception=raise_exception)
					or "",
				)
				create_leave_ledger_entry(self, args, submit)

	def is_separate_ledger_entry_required(
		self, alloc_on_from_date: Optional[Dict] = None, alloc_on_to_date: Optional[Dict] = None
	) -> bool:
		"""Checks if application dates fall in separate allocations"""
		if (
			(alloc_on_from_date and not alloc_on_to_date)
			or (not alloc_on_from_date and alloc_on_to_date)
			or (
				alloc_on_from_date and alloc_on_to_date and alloc_on_from_date.name != alloc_on_to_date.name
			)
		):
			return True
		return False

	def create_separate_ledger_entries(self, alloc_on_from_date, alloc_on_to_date, submit, lwp):
		"""Creates separate ledger entries for application period falling into separate allocations"""
		# for creating separate ledger entries existing allocation periods should be consecutive
		if (
			submit
			and alloc_on_from_date
			and alloc_on_to_date
			and add_days(alloc_on_from_date.to_date, 1) != alloc_on_to_date.from_date
		):
			frappe.throw(
				_(
					"Leave Application period cannot be across two non-consecutive leave allocations {0} and {1}."
				).format(
					get_link_to_form("Leave Allocation", alloc_on_from_date.name),
					get_link_to_form("Leave Allocation", alloc_on_to_date),
				)
			)

		raise_exception = False if frappe.flags.in_patch else True

		if alloc_on_from_date:
			first_alloc_end = alloc_on_from_date.to_date
			second_alloc_start = add_days(alloc_on_from_date.to_date, 1)
		else:
			first_alloc_end = add_days(alloc_on_to_date.from_date, -1)
			second_alloc_start = alloc_on_to_date.from_date

		leaves_in_first_alloc = get_number_of_leave_days(
			self.employee,
			self.leave_type,
			self.from_date,
			first_alloc_end,
			self.half_day,
			self.half_day_date,
		)
		leaves_in_second_alloc = get_number_of_leave_days(
			self.employee,
			self.leave_type,
			second_alloc_start,
			self.to_date,
			self.half_day,
			self.half_day_date,
		)

		args = dict(
			is_lwp=lwp,
			holiday_list=get_holiday_list_for_employee(self.employee, raise_exception=raise_exception)
			or "",
		)

		if leaves_in_first_alloc:
			args.update(
				dict(from_date=self.from_date, to_date=first_alloc_end, leaves=leaves_in_first_alloc * -1)
			)
			create_leave_ledger_entry(self, args, submit)

		if leaves_in_second_alloc:
			args.update(
				dict(from_date=second_alloc_start, to_date=self.to_date, leaves=leaves_in_second_alloc * -1)
			)
			create_leave_ledger_entry(self, args, submit)

	def create_ledger_entry_for_intermediate_allocation_expiry(self, expiry_date, submit, lwp):
		"""Splits leave application into two ledger entries to consider expiry of allocation"""
		raise_exception = False if frappe.flags.in_patch else True

		leaves = get_number_of_leave_days(
			self.employee, self.leave_type, self.from_date, expiry_date, self.half_day, self.half_day_date
		)

		if leaves:
			args = dict(
				from_date=self.from_date,
				to_date=expiry_date,
				leaves=leaves * -1,
				is_lwp=lwp,
				holiday_list=get_holiday_list_for_employee(self.employee, raise_exception=raise_exception)
				or "",
			)
			create_leave_ledger_entry(self, args, submit)

		if getdate(expiry_date) != getdate(self.to_date):
			start_date = add_days(expiry_date, 1)
			leaves = get_number_of_leave_days(
				self.employee, self.leave_type, start_date, self.to_date, self.half_day, self.half_day_date
			)

			if leaves:
				args.update(dict(from_date=start_date, to_date=self.to_date, leaves=leaves * -1))
				create_leave_ledger_entry(self, args, submit)

	
def get_allocation_expiry_for_cf_leaves(
	employee: str, leave_type: str, to_date: datetime.date, from_date: datetime.date
) -> str:
	"""Returns expiry of carry forward allocation in leave ledger entry"""
	Ledger = frappe.qb.DocType("Leave Ledger Entry")
	expiry = (
		frappe.qb.from_(Ledger)
		.select(Ledger.to_date)
		.where(
			(Ledger.employee == employee)
			& (Ledger.leave_type == leave_type)
			& (Ledger.is_carry_forward == 1)
			& (Ledger.transaction_type == "Leave Allocation")
			& (Ledger.to_date.between(from_date, to_date))
			& (Ledger.docstatus == 1)
		)
		.limit(1)
	).run()

	return expiry[0][0] if expiry else ""


@frappe.whitelist()
def get_number_of_leave_days(
	employee: str,
	leave_type: str,
	from_date: datetime.date,
	to_date: datetime.date,
	half_day: Union[int, str, None] = None,
	half_day_date: Union[datetime.date, str, None] = None,
	holiday_list: Optional[str] = None,
) -> float:
	"""Returns number of leave days between 2 dates after considering half day and holidays
	(Based on the include_holiday setting in Leave Type)"""
	number_of_days = 0
	if cint(half_day) == 1:
		if getdate(from_date) == getdate(to_date):
			number_of_days = 0.5
		elif half_day_date and getdate(from_date) <= getdate(half_day_date) <= getdate(to_date):
			number_of_days = date_diff(to_date, from_date) + 0.5
		else:
			number_of_days = date_diff(to_date, from_date) + 1
	else:
		number_of_days = date_diff(to_date, from_date) + 1

	if not frappe.db.get_value("Leave Type", leave_type, "include_holiday"):
		number_of_days = flt(number_of_days) - flt(
			get_holidays(employee, from_date, to_date, holiday_list=holiday_list)
		)
	return number_of_days


@frappe.whitelist()
def get_leave_details(employee, date):
	allocation_records = get_leave_allocation_records(employee, date)
	leave_allocation = {}
	precision = cint(frappe.db.get_single_value("System Settings", "float_precision", cache=True))

	for d in allocation_records:
		allocation = allocation_records.get(d, frappe._dict())
		remaining_leaves = get_leave_balance_on(
			employee, d, date, to_date=allocation.to_date, consider_all_leaves_in_the_allocation_period=True
		)

		end_date = allocation.to_date
		leaves_taken = get_leaves_for_period(employee, d, allocation.from_date, end_date) * -1
		leaves_pending = get_leaves_pending_approval_for_period(
			employee, d, allocation.from_date, end_date
		)
		expired_leaves = allocation.total_leaves_allocated - (remaining_leaves + leaves_taken)

		leave_allocation[d] = {
			"total_leaves": flt(allocation.total_leaves_allocated, precision),
			"expired_leaves": flt(expired_leaves, precision) if expired_leaves > 0 else 0,
			"leaves_taken": flt(leaves_taken, precision),
			"leaves_pending_approval": flt(leaves_pending, precision),
			"remaining_leaves": flt(remaining_leaves, precision),
		}
	
	# is used in set query
	lwp = frappe.get_list("Leave Type", filters={"is_lwp": 1}, pluck="name")

	return {
		"leave_allocation": leave_allocation,
		"leave_approver": get_leave_approver(employee),
		"lwps": lwp,
	}


@frappe.whitelist()
def get_leave_balance_on(
	employee: str,
	leave_type: str,
	date: datetime.date,
	to_date: Union[datetime.date, None] = None,
	consider_all_leaves_in_the_allocation_period: bool = False,
	for_consumption: bool = False,
):
	"""
	Returns leave balance till date
	:param employee: employee name
	:param leave_type: leave type
	:param date: date to check balance on
	:param to_date: future date to check for allocation expiry
	:param consider_all_leaves_in_the_allocation_period: consider all leaves taken till the allocation end date
	:param for_consumption: flag to check if leave balance is required for consumption or display
			eg: employee has leave balance = 10 but allocation is expiring in 1 day so employee can only consume 1 leave
			in this case leave_balance = 10 but leave_balance_for_consumption = 1
			if True, returns a dict eg: {'leave_balance': 10, 'leave_balance_for_consumption': 1}
			else, returns leave_balance (in this case 10)
	"""
	if not to_date:
		to_date = nowdate()

	allocation_records = get_leave_allocation_records(employee, date, leave_type)
	allocation = allocation_records.get(leave_type, frappe._dict())

	end_date = allocation.to_date if cint(consider_all_leaves_in_the_allocation_period) else date
	cf_expiry = get_allocation_expiry_for_cf_leaves(
		employee, leave_type, to_date, allocation.from_date
	)

	leaves_taken = get_leaves_for_period(employee, leave_type, allocation.from_date, end_date)

	remaining_leaves = get_remaining_leaves(allocation, leaves_taken, date, cf_expiry)

	if for_consumption:
     
		return remaining_leaves
	else:
		return remaining_leaves.get("leave_balance")

  


def get_leave_allocation_records(employee, date, leave_type=None):
	"""Returns the total allocated leaves and carry forwarded leaves based on ledger entries"""
	Ledger = frappe.qb.DocType("Leave Ledger Entry")
	LeaveAllocation = frappe.qb.DocType("Leave Allocation")

	cf_leave_case = (
		frappe.qb.terms.Case().when(Ledger.is_carry_forward == "1", Ledger.leaves).else_(0)
	)
	sum_cf_leaves = Sum(cf_leave_case).as_("cf_leaves")

	new_leaves_case = (
		frappe.qb.terms.Case().when(Ledger.is_carry_forward == "0", Ledger.leaves).else_(0)
	)
	sum_new_leaves = Sum(new_leaves_case).as_("new_leaves")

	query = (
		frappe.qb.from_(Ledger)
		.inner_join(LeaveAllocation)
		.on(Ledger.transaction_name == LeaveAllocation.name)
		.select(
			sum_cf_leaves,
			sum_new_leaves,
			Min(Ledger.from_date).as_("from_date"),
			Max(Ledger.to_date).as_("to_date"),
			Ledger.leave_type,
			Ledger.employee,
		)
		.where(
			(Ledger.from_date <= date)
			& (Ledger.docstatus == 1)
			& (Ledger.transaction_type == "Leave Allocation")
			& (Ledger.employee == employee)
			& (Ledger.is_expired == 0)
			& (Ledger.is_lwp == 0)
			& (
				# newly allocated leave's end date is same as the leave allocation's to date
				((Ledger.is_carry_forward == 0) & (Ledger.to_date >= date))
				# carry forwarded leave's end date won't be same as the leave allocation's to date
				# it's between the leave allocation's from and to date
				| (
					(Ledger.is_carry_forward == 1)
					& (Ledger.to_date.between(LeaveAllocation.from_date, LeaveAllocation.to_date))
					# only consider cf leaves from current allocation
					& (LeaveAllocation.from_date <= date)
					& (date <= LeaveAllocation.to_date)
				)
			)
		)
	)

	if leave_type:
		query = query.where((Ledger.leave_type == leave_type))
	query = query.groupby(Ledger.employee, Ledger.leave_type)

	allocation_details = query.run(as_dict=True)
	
	allocated_leaves = frappe._dict()
	for d in allocation_details:
		allocated_leaves.setdefault(
			d.leave_type,
			frappe._dict(
				{
					"from_date": d.from_date,
					"to_date": d.to_date,
					"total_leaves_allocated": flt(d.cf_leaves) + flt(d.new_leaves),
					"unused_leaves": d.cf_leaves,
					"new_leaves_allocated": d.new_leaves,
					"leave_type": d.leave_type,
					"employee": d.employee,
				}
			),
		)
	
	return allocated_leaves

# nabeel saleem, 19-12-2024
def get_leaves_pending_approval_for_period(
	employee: str, leave_type: str, from_date: datetime.date, to_date: datetime.date
) -> float:
	"""Returns leaves that are pending for approval"""
	leaves = frappe.get_all(
		"Leave Application",
		filters={"employee": employee, "leave_type": leave_type, "status": "Open"},
		or_filters={
			"from_date": ["between", (from_date, to_date)],
			"to_date": ["between", (from_date, to_date)],
		},
		fields=["SUM(total_leave_days) as leaves"],
	)[0]
	return leaves["leaves"] if leaves["leaves"] else 0.0


def get_remaining_leaves(
	allocation: Dict, leaves_taken: float, date: str, cf_expiry: str
) -> Dict[str, float]:
	"""Returns a dict of leave_balance and leave_balance_for_consumption
	leave_balance returns the available leave balance
	leave_balance_for_consumption returns the minimum leaves remaining after comparing with remaining days for allocation expiry
	"""

	def _get_remaining_leaves(remaining_leaves, end_date):
		"""Returns minimum leaves remaining after comparing with remaining days for allocation expiry"""
		if remaining_leaves > 0:
			remaining_days = date_diff(end_date, date) + 1
			remaining_leaves = min(remaining_days, remaining_leaves)

		return remaining_leaves

	if cf_expiry and allocation.unused_leaves:
		# allocation contains both carry forwarded and new leaves
		new_leaves_taken, cf_leaves_taken = get_new_and_cf_leaves_taken(allocation, cf_expiry)

		if getdate(date) > getdate(cf_expiry):
			# carry forwarded leaves have expired
			cf_leaves = remaining_cf_leaves = 0
		else:
			cf_leaves = flt(allocation.unused_leaves) + flt(cf_leaves_taken)
			remaining_cf_leaves = _get_remaining_leaves(cf_leaves, cf_expiry)

		# new leaves allocated - new leaves taken + cf leave balance
		# Note: `new_leaves_taken` is added here because its already a -ve number in the ledger
		leave_balance = (flt(allocation.new_leaves_allocated) + flt(new_leaves_taken)) + flt(cf_leaves)
		leave_balance_for_consumption = (
			flt(allocation.new_leaves_allocated) + flt(new_leaves_taken)
		) + flt(remaining_cf_leaves)
	else:
		# allocation only contains newly allocated leaves
		leave_balance = leave_balance_for_consumption = flt(allocation.total_leaves_allocated) + flt(
			leaves_taken
		)

	remaining_leaves = _get_remaining_leaves(leave_balance_for_consumption, allocation.to_date)
	return frappe._dict(leave_balance=leave_balance, leave_balance_for_consumption=remaining_leaves)


def get_new_and_cf_leaves_taken(allocation: Dict, cf_expiry: str) -> Tuple[float, float]:
	"""returns new leaves taken and carry forwarded leaves taken within an allocation period based on cf leave expiry"""
	cf_leaves_taken = get_leaves_for_period(
		allocation.employee, allocation.leave_type, allocation.from_date, cf_expiry
	)
	new_leaves_taken = get_leaves_for_period(
		allocation.employee, allocation.leave_type, add_days(cf_expiry, 1), allocation.to_date
	)

	# using abs because leaves taken is a -ve number in the ledger
	if abs(cf_leaves_taken) > allocation.unused_leaves:
		# adjust the excess leaves in new_leaves_taken
		new_leaves_taken += -(abs(cf_leaves_taken) - allocation.unused_leaves)
		cf_leaves_taken = -allocation.unused_leaves

	return new_leaves_taken, cf_leaves_taken


def get_leaves_for_period(
	employee: str,
	leave_type: str,
	from_date: datetime.date,
	to_date: datetime.date,
	skip_expired_leaves: bool = True,
) -> float:
	leave_entries = get_leave_entries(employee, leave_type, from_date, to_date)
	leave_days = 0
	
	for leave_entry in leave_entries:
		inclusive_period = leave_entry.from_date >= getdate(
			from_date
		) and leave_entry.to_date <= getdate(to_date)
		
		if inclusive_period and leave_entry.transaction_type == "Leave Encashment":
			leave_days += leave_entry.leaves
		
		elif (
			inclusive_period
			and leave_entry.transaction_type == "Leave Allocation"
			and leave_entry.is_expired
			and not skip_expired_leaves
		):
			leave_days += leave_entry.leaves
		# nabeel updated
		elif leave_entry.transaction_type in ["Leave Application", "Salary Slip"]:
			
			if leave_entry.from_date < getdate(from_date):
				leave_entry.from_date = from_date
			if leave_entry.to_date > getdate(to_date):
				leave_entry.to_date = to_date

			half_day = 0
			half_day_date = None
			# fetch half day date for leaves with half days
			if leave_entry.leaves % 1:
				half_day = 1
				half_day_date = frappe.db.get_value(
					"Leave Application", leave_entry.transaction_name, "half_day_date"
				) if(leave_entry.transaction_type == "Leave Application") else leave_entry.from_date
				
			leave_days += (
				get_number_of_leave_days(
					employee,
					leave_type,
					leave_entry.from_date,
					leave_entry.to_date,
					half_day,
					half_day_date,
					holiday_list=leave_entry.holiday_list,
				)
				* -1
			)
			# frappe.msgprint(f'{leave_type} {leave_days}')
	
	return leave_days

# nabeel saleem, [19-12-2024]
def get_leave_entries(employee, leave_type, from_date, to_date):
	"""Returns leave entries between from_date and to_date."""
	return frappe.db.sql(
		"""
		SELECT
			employee, leave_type, from_date, to_date, leaves, transaction_name, transaction_type, holiday_list,
			is_carry_forward, is_expired
		FROM `tabLeave Ledger Entry`
		WHERE employee=%(employee)s AND leave_type=%(leave_type)s
			AND docstatus=1
			AND (leaves<0
				OR is_expired=1)
			AND (from_date between %(from_date)s AND %(to_date)s
				OR to_date between %(from_date)s AND %(to_date)s
				OR (from_date < %(from_date)s AND to_date > %(to_date)s))
	""",
		{"from_date": from_date, "to_date": to_date, "employee": employee, "leave_type": leave_type},
		as_dict=1,
	)


@frappe.whitelist()
def get_holidays(employee, from_date, to_date, holiday_list=None):
	"""get holidays between two dates for the given employee"""
	if not holiday_list:
		holiday_list = get_holiday_list_for_employee(employee)

	holidays = frappe.db.sql(
		"""select count(distinct holiday_date) from `tabHoliday` h1, `tabHoliday List` h2
		where h1.parent = h2.name and h1.holiday_date between %s and %s
		and h2.name = %s""",
		(from_date, to_date, holiday_list),
	)[0][0]

	return holidays


def is_lwp(leave_type):
	lwp = frappe.db.sql("select is_lwp from `tabLeave Type` where name = %s", leave_type)
	return lwp and cint(lwp[0][0]) or 0


@frappe.whitelist()
def get_events(start, end, filters=None):
	from frappe.desk.reportview import get_filters_cond

	events = []

	employee = frappe.db.get_value(
		"Employee", filters={"user_id": frappe.session.user}, fieldname=["name", "company"], as_dict=True
	)

	if employee:
		employee, company = employee.name, employee.company
	else:
		employee = ""
		company = frappe.db.get_value("Global Defaults", None, "default_company")

	conditions = get_filters_cond("Leave Application", filters, [])
	# show department leaves for employee
	if "Employee" in frappe.get_roles():
		add_department_leaves(events, start, end, employee, company)

	add_leaves(events, start, end, conditions)
	add_block_dates(events, start, end, employee, company)
	add_holidays(events, start, end, employee, company)

	return events


def add_department_leaves(events, start, end, employee, company):
	department = frappe.db.get_value("Employee", employee, "department")

	if not department:
		return

	# department leaves
	department_employees = frappe.db.sql_list(
		"""select name from tabEmployee where department=%s
		and company=%s""",
		(department, company),
	)

	filter_conditions = ' and employee in ("%s")' % '", "'.join(department_employees)
	add_leaves(events, start, end, filter_conditions=filter_conditions)


def add_leaves(events, start, end, filter_conditions=None):
	from frappe.desk.reportview import build_match_conditions

	conditions = []

	if not cint(
		frappe.db.get_value("HR Settings", None, "show_leaves_of_all_department_members_in_calendar")
	):
		match_conditions = build_match_conditions("Leave Application")

		if match_conditions:
			conditions.append(match_conditions)

	query = """SELECT
		docstatus,
		name,
		employee,
		employee_name,
		leave_type,
		from_date,
		to_date,
		half_day,
		status,
		color
	FROM `tabLeave Application`
	WHERE
		from_date <= %(end)s AND to_date >= %(start)s <= to_date
		AND docstatus < 2
		AND status in ('Approved', 'Open')
	"""

	if conditions:
		query += " AND " + " AND ".join(conditions)

	if filter_conditions:
		query += filter_conditions

	for d in frappe.db.sql(query, {"start": start, "end": end}, as_dict=True):
		e = {
			"name": d.name,
			"doctype": "Leave Application",
			"from_date": d.from_date,
			"to_date": d.to_date,
			"docstatus": d.docstatus,
			"color": d.color,
			"all_day": int(not d.half_day),
			"title": cstr(d.employee_name)
			+ f" ({cstr(d.leave_type)})"
			+ (" " + _("(Half Day)") if d.half_day else ""),
		}
		if e not in events:
			events.append(e)


def add_block_dates(events, start, end, employee, company):
	# block days
	cnt = 0
	block_dates = get_applicable_block_dates(start, end, employee, company, all_lists=True)

	for block_date in block_dates:
		events.append(
			{
				"doctype": "Leave Block List Date",
				"from_date": block_date.block_date,
				"to_date": block_date.block_date,
				"title": _("Leave Blocked") + ": " + block_date.reason,
				"name": "_" + str(cnt),
			}
		)
		cnt += 1


def add_holidays(events, start, end, employee, company):
	applicable_holiday_list = get_holiday_list_for_employee(employee, company)
	if not applicable_holiday_list:
		return

	for holiday in frappe.db.sql(
		"""select name, holiday_date, description
		from `tabHoliday` where parent=%s and holiday_date between %s and %s""",
		(applicable_holiday_list, start, end),
		as_dict=True,
	):
		events.append(
			{
				"doctype": "Holiday",
				"from_date": holiday.holiday_date,
				"to_date": holiday.holiday_date,
				"title": _("Holiday") + ": " + cstr(holiday.description),
				"name": holiday.name,
			}
		)


@frappe.whitelist()
def get_mandatory_approval(doctype):
	mandatory = ""
	if doctype == "Leave Application":
		mandatory = frappe.db.get_single_value(
			"HR Settings", "leave_approver_mandatory_in_leave_application"
		)
	else:
		mandatory = frappe.db.get_single_value(
			"HR Settings", "expense_approver_mandatory_in_expense_claim"
		)

	return mandatory


def get_approved_leaves_for_period(employee, leave_type, from_date, to_date):
	LeaveApplication = frappe.qb.DocType("Leave Application")
	query = (
		frappe.qb.from_(LeaveApplication)
		.select(
			LeaveApplication.employee,
			LeaveApplication.leave_type,
			LeaveApplication.from_date,
			LeaveApplication.to_date,
			LeaveApplication.total_leave_days,
		)
		.where(
			(LeaveApplication.employee == employee)
			& (LeaveApplication.docstatus == 1)
			& (LeaveApplication.status == "Approved")
			& (
				(LeaveApplication.from_date.between(from_date, to_date))
				| (LeaveApplication.to_date.between(from_date, to_date))
				| ((LeaveApplication.from_date < from_date) & (LeaveApplication.to_date > to_date))
			)
		)
	)

	if leave_type:
		query = query.where(LeaveApplication.leave_type == leave_type)

	leave_applications = query.run(as_dict=True)

	leave_days = 0
	for leave_app in leave_applications:
		if leave_app.from_date >= getdate(from_date) and leave_app.to_date <= getdate(to_date):
			leave_days += leave_app.total_leave_days
		else:
			if leave_app.from_date < getdate(from_date):
				leave_app.from_date = from_date
			if leave_app.to_date > getdate(to_date):
				leave_app.to_date = to_date

			leave_days += get_number_of_leave_days(
				employee, leave_type, leave_app.from_date, leave_app.to_date
			)

	return leave_days


@frappe.whitelist()
def get_leave_approver(employee):
	leave_approver, department = frappe.db.get_value(
		"Employee", employee, ["leave_approver", "department"]
	)
	
	if not leave_approver and department:
		leave_approver = frappe.db.get_value(
			"Department Approver",
			{"parent": department, "parentfield": "leave_approvers", "idx": 1},
			"approver",
		)

	return leave_approver


def on_doctype_update():
	frappe.db.add_index("Leave Application", ["employee", "from_date", "to_date"])


def setter_next_workflow_approver(self):
	if(self.custom_next_workflow_approver in ["", None]) or (self.is_new()):
		self.custom_next_workflow_approver = self.employee

def record_workflow_approver_states(self):
	if(hasattr(self, 'workflow_state')):
		from frappe.utils import get_datetime
		
		# if(self.docstatus==1): return

		approversList = eval(self.custom_state_data) if(self.custom_state_data) else {}

		if(self.workflow_state in approversList): return
		# if(self.employee != self.custom_next_workflow_approver): return 
		prev = frappe.db.get_value("Employee", self.custom_next_workflow_approver, ["name", "reports_to", "employee_name", "designation"], as_dict=1)
		
		if(prev):
			if(not prev.reports_to):
				_link_ = get_link_to_form('Employee', prev.name, prev.employee_name)
				frappe.throw(f"`Reports to` is not set for {_link_}", title="Missing Info")

		nxt = frappe.db.get_value("Employee", prev.reports_to, ["name", "employee_name", "designation", "custom_current_role"], as_dict=1)
		if(self.custom_directly_reports_to_hod) and (self.workflow_state=="Applied"):
			nxt = frappe.db.get_value("Employee", {"custom_hod": 1,"department": self.department}, ["name", "employee_name", "designation", "custom_current_role"], as_dict=1)
		
		self.custom_next_workflow_approver = prev.reports_to
		
		approversList.update({
			f"{self.workflow_state}": {
				"employee_name": prev.employee_name,
				"current_state": self.workflow_state,
				"modified_on": get_datetime(),				
				"next_state": f"{nxt.employee_name}, (<b>{nxt.custom_current_role}</b>)" if((self.docstatus==0) and ("Rejected" not in self.workflow_state)) else "",
			}
		})
		self.custom_state_data =  frappe.as_json(approversList)

def set_next_workflow_approver_details(self):
	if self.workflow_state in ['Recommended By Line Manager', 'Recommended By Head Of Department'] :
		next_leave_approver = frappe.get_value("Employee", {"user_id":self.leave_approver}, 'leave_approver')
		self.leave_approver = next_leave_approver
		self.leave_approver_name = get_fullname(next_leave_approver) 


# # bench --site erp.alkhidmat.org execute akf_hrms.overrides.leave_application.leave_application._set_next_workflow_approver
# def _set_next_workflow_approver():
# 	from frappe.utils import get_datetime
# 	def get_state(workflow_state):
# 		return frappe.db.sql(f""" 
# 				Select 
# 					w.name, wt.state, wt.action, wt.next_state, wt.allowed, wt.allow_self_approval
# 				From 
# 					`tabWorkflow` w inner join `tabWorkflow Transition` wt on (w.name=wt.parent)
# 				Where 
# 					w.document_type='Leave Application'
# 					and w.is_active = 1
# 					and wt.action='Approve'
# 					and wt.state='{workflow_state}'
# 				Order by
# 					wt.idx asc
# 				limit 1
# 			""", as_dict=1)
	
# 	def set_approver_detail(user_id, next_state):
# 		self.leave_approver = user_id
# 		self.leave_approver_name = get_fullname(user_id)
# 		self.custom_next_workflow_state = next_state
	
# 	workflow_list  = ["Applied", "Approved by the Line Manager", "Approved by the Head of Department", "Approved"]
# 	state_dict = {}
# 	count=1
# 	for self in frappe.db.sql("""select * from `tabLeave Application` where docstatus =1 and modified_by="Administrator" and cast(modified as date)=curdate() """, as_dict=1):
# 		employee_name = None
# 		for state in workflow_list:
# 			statelist = get_state(state)
# 			# print(f"statelist: {statelist}")
# 			for d in statelist:
# 				if(d.allowed == "Line Manager"):
# 					reports_to = frappe.db.get_value('Employee', {'name': self.employee}, 'reports_to')
# 					employee_name = frappe.db.get_value('Employee', reports_to, 'employee_name')
# 					if(reports_to):
# 						user_id = frappe.db.get_value('Employee', {'name': reports_to}, 'user_id')

# 						if(frappe.db.exists('Has Role', {'parent': user_id, 'role': 'Line Manager'})):
# 							set_approver_detail(user_id, d.next_state)

# 							state_dict.update({f"{state}": {
# 											"current_user": f"{state} (<b>{self.employee_name}</b>)",
# 											"next_state": f"{d.next_state} (<b>{employee_name}</b>)",
# 											"modified_on": self.creation,
# 										}})
				
# 				elif(d.allowed == "Head of Department"):
# 						hod_data = frappe.db.get_value('Employee', {'department': self.department , 'custom_hod': 1}, ['user_id', 'employee_name'], as_dict=1)
# 						# print(hod_data, '=========')
# 						if(hod_data):
# 							state_dict.update({f"{state}": {
# 											"current_user": f"{state} (<b>{employee_name}</b>)",
# 											"next_state": f"{d.next_state} (<b>{hod_data.employee_name}</b>)",
# 											"modified_on": get_datetime(),
# 										}})
# 							employee_name = hod_data.employee_name
# 				elif(d.allowed == 'CEO'):
# 					user_list = frappe.db.sql(""" 
# 							Select 
# 								u.name , u.full_name
# 							From 
# 								`tabUser` u inner join `tabHas Role` h on (u.name=h.parent) 
# 							Where 
# 								h.role in ('CEO')
# 							Group by
# 								u.name 
# 					""")
# 					print(user_list)
# 					if(user_list):
# 						full_name = user_list[0][1]
# 						state_dict.update({f"{state}": {
# 											"current_user": f"{state} (<b>{employee_name}</b>)",
# 											"next_state": f"{d.next_state}",
# 											"modified_on": get_datetime(),
# 										}})

		
# 		frappe.db.set_value("Leave Application", self.name, "workflow_state", "Approved")
# 		frappe.db.set_value("Leave Application", self.name, "custom_state_data", frappe.as_json(state_dict))
# 		print(f"state_dict: {state_dict}")
# 


# /////////////////////////////////////
# /////////////////////////////////////
# /////////////////////////////////////
import frappe
import json

@frappe.whitelist()
def update_all_leave_approver_states():
    leave_apps = frappe.get_all(
        "Leave Application",
        filters={"workflow_state": "Applied"},
        fields=["name", "employee", "custom_state_data"]
    )

    for app in leave_apps:
        leave_app_id = app.name

        if not app.custom_state_data:
            print(f"[SKIP] No custom_state_data for {leave_app_id}")
            continue

        try:
            state_data = json.loads(app.custom_state_data)
        except json.JSONDecodeError:
            print(f"[ERROR] Invalid JSON in custom_state_data for {leave_app_id}")
            continue

        applied_state = state_data.get("Applied")
        if not applied_state:
            print(f"[SKIP] 'Applied' state not found in custom_state_data for {leave_app_id}")
            continue

        # previous_leave_approver = frappe.db.get_value("Employee", app.employee, "reports_to")
        leave_approver = frappe.db.get_value("Employee", app.employee, "leave_approver")
        if not leave_approver:
            print(f"[SKIP] No leave approver for employee {app.employee}")
            continue

        leave_approver_role = frappe.db.get_value("Employee", {"user_id": leave_approver}, "custom_current_role")
        leave_approver_name = frappe.db.get_value("Employee", {"user_id": leave_approver}, "employee_name")

        new_next_state = f"{leave_approver_name}, (<b>{leave_approver_role}</b>)"
        applied_state["next_state"] = new_next_state
        state_data["Applied"] = applied_state

        frappe.db.set_value("Leave Application", leave_app_id, "custom_state_data", json.dumps(state_data))
        print(f"[UPDATED] {leave_app_id} → {new_next_state}")

    frappe.db.commit()
    print("All applicable Leave Applications updated.")


def update_leave_approvers_for_applied():
    leave_apps = frappe.get_all(
        "Leave Application",
        filters={"workflow_state": "Recommended By Line Manager"},
        fields=["name", "employee"]
    )

    for app in leave_apps:
        previous_leave_approver = frappe.db.get_value("Employee", app.employee, "reports_to")
        leave_approver = frappe.db.get_value("Employee", previous_leave_approver, "leave_approver")

        if leave_approver:
            leave_approver_name = frappe.db.get_value("User", leave_approver, "full_name")

            update_fields = {
                "leave_approver": leave_approver,
                "leave_approver_name": leave_approver_name
            }

            frappe.db.set_value("Leave Application", app.name, update_fields)

    frappe.db.commit()

@frappe.whitelist()
def update_employee_details_in_leave_applications():
    valid_states = ["Applied", "Recommended By Line Manager", "Recommended By Head Of Department"]

    # Get all matching Leave Applications
    leave_apps = frappe.get_all(
        "Leave Application",
        filters={"workflow_state": ["in", valid_states]},
        fields=["name", "employee"]
    )

    total = len(leave_apps)
    updated = 0
    skipped = 0
    skipped_records = []

    for app in leave_apps:
        try:
            employee = frappe.get_doc("Employee", app.employee)

            leave_doc = frappe.get_doc("Leave Application", app.name)

            leave_doc.custom_current_role = employee.custom_current_role
            leave_doc.custom_directly_reports_to_hod = employee.reports_to
            leave_doc.department = employee.department

            leave_doc.save(ignore_permissions=True)
            updated += 1

        except Exception as e:
            skipped += 1
            skipped_records.append({
                "leave_application": app.name,
                "error": str(e)
            })
            frappe.logger().error(f"Skipping Leave Application {app.name}: {e}")

    frappe.db.commit()

    print(json.dumps({
        "total_leave_applications": total,
        "updated": updated,
        "skipped": skipped,
        "skipped_records": skipped_records
    }, indent=2))


@frappe.whitelist()
def update_approve_leave_open_status_to_approve():

    # Get all matching Leave Applications
    leave_apps = frappe.get_all(
        "Leave Application",
        filters={"workflow_state": "Approved", "status": "Open"},
        fields=["name", "employee"]
    )
    count = 0
    for app in leave_apps:
		# Update the status to "Approved"
        frappe.db.set_value("Leave Application", app.name, "status", "Approved")
        count += 1
        print(f"[{count}] Updating Leave Application: {app.name} for Employee: {app.employee}")


# bench --site erp.alkhidmat.org execute akf_hrms.overrides.leave_application.leave_application.update_leave_approvers_for_applied
# bench --site erp.alkhidmat.org execute akf_hrms.overrides.leave_application.leave_application.update_all_leave_approver_states
# bench --site erp.alkhidmat.org execute akf_hrms.overrides.leave_application.leave_application.update_employee_details_in_leave_applications
# bench --site erp.alkhidmat.org execute akf_hrms.overrides.leave_application.leave_application.update_approve_leave_open_status_to_approve