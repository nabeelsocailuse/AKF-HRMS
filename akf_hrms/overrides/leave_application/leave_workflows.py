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


# bench --site erp.alkhidmat.org execute akf_hrms.overrides.leave_application.leave_workflows.set_next_workflow_approver
# Nabeel Saleem, 18-12-2024
@frappe.whitelist()
def set_next_workflow_approver():
	state = []
	for d in frappe.db.get_list("Leave Application", filters={"name": "HR-LAP-2025-00609"}, fields=["*"]):
		employee = frappe.db.get_value("Employee", d.employee, 
				["name", "reports_to", "user_id", "custom_current_role"], as_dict=1)
		
		reports_to = frappe.db.get_value("Employee",  employee.reports_to, 
				["name", "reports_to", "user_id", "custom_current_role"], as_dict=1)
		
		# reports_to = frappe.db.get_value("Employee", {"reports_to": reports_to.name}, ["name", "user_id", "custom_current_role"], as_dict=1)
		# print(f"reports_to3: {reports_to}")
		# data = frappe.db.sql(f""" 
		# 	Select 
		# 		wt.state, wt.action, wt.next_state, wt.allowed
		# 	From 
		# 		`tabWorkflow` w inner join `tabWorkflow Transition` wt on (w.name=wt.parent)
		# 	Where 
		# 		w.document_type='Leave Application'
		# 		and w.is_active = 1
		# 		and wt.action='Approve'
		# 		and wt.state='{row.workflow_state}'
		# 	Order by
		# 		wt.idx asc
		# 	-- limit 1
		# """, as_dict=1)
		# print(data)
		# state.append([
		# 	{
		# 		"userId": "frappe.session.user",
		# 		"workflow_state": row.workflow_state,
		# 		"next_workflow_state": row.custom_next_workflow_state,
		# 		"leave_approver": row.leave_approver,
		# 	}
		# ])
		# print(state)
		# # => find approver
		# def set_approver_detail(user_id, next_state):
		# 	self.leave_approver = user_id
		# 	self.leave_approver_name = get_fullname(user_id)
		# 	self.custom_next_workflow_state = next_state

		# for d in data:
		# 	if(d.allowed == "Line Manager"):
		# 		reports_to = frappe.db.get_value('Employee', {'name': self.employee}, 'reports_to')
		# 		if(reports_to):
		# 			user_id = frappe.db.get_value('Employee', {'name': reports_to}, 'user_id')
		# 			if(frappe.db.exists('Has Role', {'parent': user_id, 'role': 'Line Manager'})):
		# 				set_approver_detail(user_id, d.next_state)
		# 		else:
		# 			frappe.throw(f"Please set a `reports to` of this employee", title="Line Manager")
						
		# 	elif(d.allowed == "Head of Department"):
		# 		user_id = frappe.db.get_value('Employee', {'department': self.department , 'custom_hod': 1}, 'user_id')
		# 		if(user_id):
		# 			set_approver_detail(user_id, d.next_state)
		# 		else:
		# 			frappe.throw(f"Please set a `head of department` of department {self.department}", title="Head of Department")
			
		# 	elif(d.allowed == 'CEO'):
		# 		user_list = frappe.db.sql(""" 
		# 				Select 
		# 					u.name 
		# 				From 
		# 					`tabUser` u inner join `tabHas Role` h on (u.name=h.parent) 
		# 				Where 
		# 					h.role in ('CEO')
		# 				Group by
		# 					u.name 
		# 		""")
		# 		if(user_list):
		# 			set_approver_detail(user_list[0][0], d.next_state)
		# 		else:
		# 			frappe.throw(f"Please set a `CEO` of {self.company}", title="CEO")
