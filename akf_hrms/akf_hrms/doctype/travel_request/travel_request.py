# Copyright (c) 2024, Nabeel Saleem and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
# Nabeel Saleem, May 16'2025
from akf_hrms.utils.travel_request_utils import (
	setting_next_workflow_approver,
	record_workflow_approver_states
)

class TravelRequest(Document):
	def validate(self):
		# self.set_next_workflow_state() # Mubashir Bashir 13-03-2025
		# self.set_next_workflow_approver() # Mubashir Bashir 13-03-2025
		# self.record_application_state() # Mubashir Bashir, 13-03-2025
		setting_next_workflow_approver(self)
		record_workflow_approver_states(self)

	# Mubashir Bashir 13-03-2025 Start
	@frappe.whitelist()
	def set_next_workflow_approver(self):
		if(not hasattr(self, 'workflow_state')): return		
		# if(self.status!='Open'): return

		# => find approver
		def set_approver_detail(user_id):
			self.approver = user_id
			self.approver_name = frappe.utils.get_fullname(user_id)

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
				frappe.throw(f"Please set a `CEO` of {self.company}", title="CEO")


	def set_next_workflow_state(self):
		employee_user_id = frappe.db.get_value("Employee", self.employee, "user_id")

		if not employee_user_id: return

		employee_roles = frappe.get_roles(employee_user_id)

		if (frappe.db.exists('Employee', {'name': self.employee, 'custom_directly_reports_to_hod': 0}) and 
			"Employee" in employee_roles and 
			not any(role in employee_roles for role in ["Line Manager", "Head of Department", "CEO", "Executive Director"])):
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
			not any(role in employee_roles for role in ["Line Manager", "Head of Department", "CEO", "Executive Director"])):
			if (self.custom_next_workflow_state == 'Recommended by Head of Department'):
				self.custom_next_workflow_state = 'Approved'
				self.custom_workflow_indication = 'Head of Department to CEO'
			else:
				self.custom_next_workflow_state = 'Recommended by Head of Department'
				self.custom_workflow_indication = 'Applied to HOD'


		elif "Line Manager" in employee_roles and not any(role in employee_roles for role in ["Head of Department", "CEO", "Executive Director"]):
			if (self.custom_next_workflow_state == 'Recommended by Head of Department'):
				self.custom_next_workflow_state = 'Approved'
				self.custom_workflow_indication = 'Head of Department to CEO'
			else:
				self.custom_next_workflow_state = 'Recommended by Head of Department'
				self.custom_workflow_indication = 'Applied to HOD'
				

		elif "Head of Department" in employee_roles and not any(role in employee_roles for role in ["CEO", "Executive Director"]):
			self.custom_next_workflow_state = 'Approved'
			self.custom_workflow_indication = 'Applied to CEO'

	def record_application_state(self):
		if(hasattr(self, 'workflow_state')):
			from frappe.utils import get_datetime
			state_dict = eval(self.custom_state_data) if(self.custom_state_data) else {}
			state_dict.update({f"{self.workflow_state}": {
				"current_user": f"{self.workflow_state} (<b>{frappe.utils.get_fullname(frappe.session.user)}</b>)",
				"next_state": f"{self.custom_next_workflow_state} (<b>{self.approver_name}</b>)" if "CEO" not in frappe.get_roles(frappe.session.user) and "Executive Director" not in frappe.get_roles(frappe.session.user) else "",
				"modified_on": get_datetime(),
			}})
			self.custom_state_data =  frappe.as_json(state_dict)

	# Mubashir Bashir 13-03-2025 End
