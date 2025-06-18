import frappe
from frappe import _
from frappe.utils import (
	get_datetime, 
	get_link_to_form
)
from akf_hrms.utils.workflow_transitions_utils import get_transitions
import time

def set_next_workflow_approver(self):
	if(hasattr(self, 'workflow_state')):
		if(self.workflow_state):
			if(not self.current_role):
				frappe.throw(f"Current role is not set in employee profile.", title="Missing Information")

			if(self.next_workflow_approver in ["", None]) or (self.is_new()):
				self.next_workflow_approver = self.employee
			record_workflow_approver_states(self)

def record_workflow_approver_states(self, publish_progress=True):
	
	approversList = eval(self.custom_state_data) if(self.custom_state_data) else []
	
	workflowStateExist = False
	
	for state in approversList:
		if(self.workflow_state == state["current_state"]):
			workflowStateExist = True
			return

	if(workflowStateExist): 
		return

	doc = frappe.get_doc("Expense Claim", self.name)
	
	transitions = get_transitions(doc)
	
	wf = frappe._dict()
	
	for row in transitions:
		if(row["action"].lower()!='reject'): wf.update(row) 
	
	current_approver = self.next_workflow_approver
	
	nxt_employee_name = ""

	for d in get_next_role_employee(wf.allowed, self.department):
		if(not d.custom_current_role):
			link = get_link_to_form("Employee", d.name, d.employee_name)
			frappe.throw(f"Please set current role in {link}")
		frappe.db.set_value("Expense Claim", self.name, 'next_workflow_approver', d.name)
		nxt_employee_name = d.name
	cur_employee_name = frappe.db.get_value("Employee", current_approver, "employee_name")
	if(nxt_employee_name!=""): 
		nxt_employee_name = frappe.db.get_value("Employee", nxt_employee_name, "employee_name")
	
	approversList.append({
		# f"{self.workflow_state}": {
			"cur_employee": current_approver,
			"employee_name": cur_employee_name,
			"current_state": self.workflow_state,
			"modified_on": get_datetime(),	
			"next_employee": self.next_workflow_approver if(self.docstatus==0) else "",			
			"next_state": f"{nxt_employee_name}, (<b>{wf.allowed}</b>)" if((self.docstatus==0) and ("Rejected" not in self.workflow_state)) else "",
		# }
	})
	frappe.db.set_value("Expense Claim", self.name, 'custom_state_data', frappe.as_json(approversList))
	frappe.publish_realtime('event_name', {'key': 'value'}, user=frappe.session.user)
	self.reload()
	
def get_next_role_employee(allowed, department):
	if(not allowed): 
		return []
	query = f"""
		Select name, employee_name, custom_current_role
		From `tabEmployee` e
		Where 
			status='Active'
			-- and custom_current_role= '{allowed}'
			and user_id in (select u.name from `tabUser` u inner join `tabHas Role` h on (u.name=h.parent)
				where h.role='{allowed}')
	"""
		
	if(allowed.lower() in ['line manager', 'head of department']): 
		query += f" and department= '{department}'"
	elif(allowed.lower() in ['ceo', 'finance', 'secretary general', 'president']): 
		pass

	result = frappe.db.sql(query, as_dict=1)
	
	if(not result):
		frappe.throw(
			f"Next approver with role `{allowed}` not found. Please set it first in `User Profile`.", title="Missing Information"
		)

	return result