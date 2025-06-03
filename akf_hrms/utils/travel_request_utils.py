import frappe
from frappe.utils import (
	get_datetime, 
	get_link_to_form
)

def setting_next_workflow_approver(self):
	if(hasattr(self, 'workflow_state')):
		if(self.next_workflow_approver in ["", None]) or (self.is_new()):
			self.next_workflow_approver = self.employee

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
			
			nxt = frappe.db.get_value("Employee", {"custom_hod": 1,"department": self.department}, ["name", "employee_name", "designation", "custom_current_role"], as_dict=1)
			
			if(not nxt): 
				link = get_link_to_form("Employee", prev.name, prev.employee_name)
				frappe.throw(
						f"`Head of Department` is not set for department <b>{self.department}</b> of employee {link} ", title="Missing Information"
					)
		
		if(not nxt.custom_current_role):
			link = get_link_to_form("Employee", nxt.name, nxt.employee_name)
			frappe.throw(
					f"Current role is not set in employee profile {link}.", title="Missing Information"
				)

		self.next_workflow_approver = prev.reports_to

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