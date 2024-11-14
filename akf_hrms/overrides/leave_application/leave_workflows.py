""" 
 MAARIJ SIDDIQUI

update_pending_status()
update_approval_status()
update_rejected_status()
validate_time_allowed()
validate_leave_count()
"""
import frappe
from frappe import _
from datetime import datetime, timedelta

# MAARIJ SIDDIQUI
def update_pending_status(self=None):
	if self.workflow_state == "Pending":
		self.custom_approval_status = 'Pending'

# MAARIJ SIDDIQUI
def update_approval_status(self=None):
	current_roles = frappe.get_roles()
	leave_type = self.leave_type
	status = self.status
	docstatus = self.docstatus

	special_leave_types = [
		'Official Duty (Out-Station)', 'Official Duty (In-Station)', 
		'Special Circumstances Leaves', 'Compensatory Leave', 'Study Leaves'
	]

	if status == 'Approved' and docstatus == 1:
		if 'Head of Department' in current_roles and leave_type not in special_leave_types:
			self.custom_approval_status = 'Approved by the Head of Department'
		elif 'CEO' in current_roles and leave_type in special_leave_types:
			self.custom_approval_status = 'Approved by the CEO'

# MAARIJ SIDDIQUI
def update_rejected_status(self=None):
	current_roles = frappe.get_roles()
	leave_type = self.leave_type
	workflow_state = self.workflow_state
	docstatus = self.docstatus

	special_leave_types = [
		'Official Duty (Out-Station)', 'Official Duty (In-Station)', 
		'Special Circumstances Leaves', 'Compensatory Leave', 'Study Leaves'
	]

	if workflow_state == "Rejected" and docstatus == 0:
		if 'Head of Department' in current_roles and leave_type not in special_leave_types:
			self.custom_approval_status = 'Rejected by the Head of Department'
		if 'CEO' in current_roles and leave_type in special_leave_types:
			self.custom_approval_status = 'Rejected by the CEO'

	elif workflow_state == 'Rejected by the Line Manager':
		if 'Line Manager' in current_roles and docstatus == 0:
			self.custom_approval_status = 'Rejected by the Line Manager'
	
	elif workflow_state == 'Rejected by the Head of Department':
		if 'Head of Department' in current_roles and docstatus == 0:
			self.custom_approval_status = 'Rejected by the Head of Department'

# MAARIJ SIDDIQUI
def validate_time_allowed(self=None):
	if self.leave_type not in ['Half Day Leave', 'Short Leave']:
		return        
	# Ensure the times are strings in the correct format
	if isinstance(self.custom_from_time, timedelta):
		from_time_str = (datetime.min + self.custom_from_time).time().strftime('%H:%M:%S')
	else:
		from_time_str = self.custom_from_time

	if isinstance(self.custom_to_time, timedelta):
		to_time_str = (datetime.min + self.custom_to_time).time().strftime('%H:%M:%S')
	else:
		to_time_str = self.custom_to_time

	from_time = datetime.strptime(from_time_str, '%H:%M:%S')
	to_time = datetime.strptime(to_time_str, '%H:%M:%S')
	time_difference = to_time - from_time

	if self.leave_type == "Half Day Leave":                        
		if time_difference < timedelta(0):
			frappe.throw(_("The 'To Time' must be later than 'From Time'"))
		
		if time_difference > timedelta(hours=4):
			frappe.throw(_("The time for Half Day Leave cannot be greater than 04 hours"))

	if self.leave_type == "Short Leave":
		if time_difference < timedelta(0):
			frappe.throw(_("The 'To Time' must be later than 'From Time'"))
		
		if time_difference > timedelta(hours=3):
			frappe.throw(_("The time for Short Leave cannot be greater than 03 hours"))

# MAARIJ SIDDIQUI
def validate_leave_count(self=None):
	if self.leave_type in ["Half Day Leave", "Short Leave"]:
		current_date = datetime.now()
		if current_date.day >= 21:
			start_date = current_date.replace(day=21)
			end_date = (start_date + timedelta(days=32)).replace(day=20)
		else:
			start_date = (current_date - timedelta(days=20)).replace(day=21)
			end_date = current_date.replace(day=20)
					
		start_date_str = start_date.strftime('%Y-%m-%d')
		end_date_str = end_date.strftime('%Y-%m-%d')
		
		short_leave_count = frappe.db.count('Leave Application', {
			'employee': self.employee,
			'leave_type': 'Short Leave',
			'status': ['in', ['Approved', 'Submitted']],
			'from_date': ['between', [start_date_str, end_date_str]]
		})

		if short_leave_count > 1:
			frappe.throw(_("You cannot avail more than 01 Short Leaves in a month"))

		half_leave_count = frappe.db.count('Leave Application', {
			'employee': self.employee,
			'leave_type': 'Half Day Leave',
			'status': ['in', ['Approved', 'Submitted']],
			'from_date': ['between', [start_date_str, end_date_str]]
		})

		if half_leave_count > 1:
			frappe.throw(_("You cannot avail more than 01 Half Day Leaves in a month"))
	if self.leave_type in ["Half Day Leave", "Short Leave"]:
		current_date = datetime.now()
		if current_date.day >= 21:
			start_date = current_date.replace(day=21)
			end_date = (start_date + timedelta(days=32)).replace(day=20)
		else:
			start_date = (current_date - timedelta(days=20)).replace(day=21)
			end_date = current_date.replace(day=20)
					
		start_date_str = start_date.strftime('%Y-%m-%d')
		end_date_str = end_date.strftime('%Y-%m-%d')
		
		short_leave_count = frappe.db.count('Leave Application', {
			'employee': self.employee,
			'leave_type': 'Short Leave',
			'status': ['in', ['Approved', 'Submitted']],
			'from_date': ['between', [start_date_str, end_date_str]]
		})

		if short_leave_count > 1:
			frappe.throw(_("You cannot avail more than 01 Short Leaves in a month"))

		half_leave_count = frappe.db.count('Leave Application', {
			'employee': self.employee,
			'leave_type': 'Half Day Leave',
			'status': ['in', ['Approved', 'Submitted']],
			'from_date': ['between', [start_date_str, end_date_str]]
		})

		if half_leave_count > 1:
			frappe.throw(_("You cannot avail more than 01 Half Day Leaves in a month"))

	
