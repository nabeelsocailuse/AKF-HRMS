import frappe
from frappe.utils import (
	get_datetime, 
	get_link_to_form
)

""" 
current_roles = ["Employee", "Line Manager", "Head Of Department", "CEO"]
document_states = ["Applied", "Recommended By Line Manager", "Recommended By Head Of Department", "Approved"]

def record_workflow_approver_state(self):
	if(hasattr(self, "workflow_state")):
		current_role = self.current_role
		state = self.workflow_state
		if(current_role == "Employee")
			if(state == "Applied"):
					
			elif(state == "Recommended By Line Manager"):
				# Next approver Head Of Department
				pass
			elif(state == "Recommended By Head Of Department"):
				# Next approver CEO
				pass
			elif(state == "Approved"):
				# Next approver nothing
				pass

def get_reports_to(employee):
	# Next approver Line Manager
	reports_to = frappe.db.get_value("Employee", employee, ["reports_to", "custom_reports_to_line_manager_name"], as_dict=1)
	
	if(not reports_to): 
		link = get_link_to_form("Employee", self.employee, self.employee_name)
		frappe.throw(
				f"Reports to is not set for employee {link}", title="Missing Information"
			)
	
	reports_to_info = frappe.db.get_value("Employee", 
						{"name": reports_to, "custom_current_role": "Line Manager"}, 
						["employee_name", "designation", "custom_current_role"]
					)
	if(not reports_to_info): 
		link = get_link_to_form("Employee", reports_to.reports_to, reports_to.custom_reports_to_line_manager_name)
		frappe.throw(
				f"Reports to: {link} has no role 'Line Manager' ", title="Missing Information"
			)
	return reports_to_info

def recording(self):
	
	approversList = eval(self.custom_state_data) if(self.custom_state_data) else {}

	approversList.update({
			f"{self.workflow_state}": {
				"cur_employee": 
				"cur_employee_name": prev.employee_name,
				"current_state": self.workflow_state,
				"modified_on": get_datetime(),
				"nxt_employee": nxt.name,
				"nxt_employee_name": nxt.employee_name,
				"nxt_current_role": nxt.custom_current_role,
			}
		})
"""
 
def setting_next_workflow_approver(self):
	if(hasattr(self, 'workflow_state')):
		if(self.next_workflow_approver in ["", None]) or (self.is_new()):
			self.next_workflow_approver = self.employee
			self.approver = get_approver_id(self.employee)
			self.approver_name = get_approver_name(self.employee)

def record_workflow_approver_states(self):
	if(hasattr(self, 'workflow_state')):
		# if(self.docstatus==1): return
		if(not self.current_role):
			frappe.throw(
					f"Current role is not set in employee profile {link}.", title="Missing Information"
				)

		approversList = eval(self.custom_state_data) if(self.custom_state_data) else {}
		
		if(self.workflow_state in approversList): return
		# if(self.employee != self.next_workflow_approver): return 
		prev = frappe.db.get_value("Employee", self.next_workflow_approver, ["name", "reports_to", "employee_name", "designation"], as_dict=1)
		
		if(not prev.reports_to): 
			link = get_link_to_form("Employee", self.employee, self.employee_name)
			frappe.throw(
					f"Reports to is not set for employee {link}", title="Missing Information"
				)
		
		nxt = frappe.db.get_value("Employee", prev.reports_to, ["name", "employee_name", "designation", "custom_current_role"], as_dict=1)
		
		if(self.directly_reports_to_hod) and (self.workflow_state=="Applied"):
			
			# nxt = frappe.db.get_value("Employee", {"custom_hod": 1,"department": self.department}, ["name", "employee_name", "designation", "custom_current_role"], as_dict=1)
			reports_to = frappe.db.get_value("Employee", {"name": self.employee}, ["reports_to"], as_dict=1)
			nxt = frappe.db.get_value("Employee", {"custom_hod": 1,"name": reports_to.reports_to}, ["name", "employee_name", "designation", "custom_current_role"], as_dict=1)
			# f"`Head of Department` is not set for department <b>{self.department}</b> of employee {link} ", title="Missing Information"
			if(not nxt): 
				link = get_link_to_form("Employee", prev.name, prev.employee_name)
				frappe.throw(
						f"`Head of Department` is not set for employee {link} ", title="Missing Information"
					)
		
		if(not nxt.custom_current_role):
			link = get_link_to_form("Employee", nxt.name, nxt.employee_name)
			frappe.throw(
					f"Current role is not set in employee profile {link}.", title="Missing Information"
				)

		self.next_workflow_approver = prev.reports_to
		self.approver = get_approver_id(prev.reports_to)
		self.approver_name = get_approver_name(prev.reports_to)

		approversList.update({
			f"{self.workflow_state}": {
				"cur_employee": prev.name,
				"employee_name": prev.employee_name,
				"current_state": self.workflow_state,
				"modified_on": get_datetime(),	
				"next_employee": nxt.name if(self.docstatus==0) else "",			
				"next_state": f"{nxt.employee_name}, (<b>{nxt.custom_current_role}</b>)" if((self.docstatus==0) and ("Rejected" not in self.workflow_state)) else "",
			}
		})
		self.custom_state_data =  frappe.as_json(approversList)


# Mubashir Bashir 19-June-2025
def get_approver_id(employee_id):		
	return frappe.db.get_value("Employee", employee_id, ["user_id"])
def get_approver_name(employee_id):	
	return frappe.db.get_value("Employee", employee_id, ["employee_name"])