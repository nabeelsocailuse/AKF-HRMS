import frappe
from frappe import _
from frappe.utils import (
	get_datetime, 
	get_link_to_form
)
from akf_hrms.utils.workflow_transitions_utils import get_transitions

def validate_guarantors(self):
	if(self.custom_guarantor_of_loan_application):
		employee_id = frappe.db.get_value("Employee", {"name": self.custom_guarantor_of_loan_application, "user_id": frappe.session.user}, "name")
		if(not employee_id) and (self.workflow_state in ["Applied", "Pending"]): 
			frappe.throw("You are not the assigned Guarantor for this loan application.", title="Guarantor 1")
	
	if(self.custom_guarantor_2_of_loan_application):
		employee_id = frappe.db.get_value("Employee", {"name": self.custom_guarantor_2_of_loan_application, "user_id": frappe.session.user}, "name")
		if(not employee_id) and (self.workflow_state in ["Recommended By Guarantor 1", "Approved By Guarantor 1", "Acknowledged By Guarantor 1"]): 
			frappe.throw("You are not the assigned Guarantor for this loan application.", title="Guarantor 2")

def set_employee_defaults(self):
	if(self.applicant_type=="Employee"):
		if(self.applicant):
			data = frappe.db.get_value(self.applicant_type, self.applicant, 
						["department", "custom_current_role", "custom_directly_reports_to_hod"], as_dict=1)
			self.department = data.department
			self.custom_current_role = data.custom_current_role
			self.directly_reports_to_hod = data.custom_directly_reports_to_hod
	else:
		self.department = ''
		self.custom_current_role = ''
		self.directly_reports_to_hod = 0

def set_next_workflow_approver(doc, method=None):
	self = doc
	if hasattr(self, 'workflow_state') and self.workflow_state:
		transitions = get_transitions(self)
		if not transitions:
			record_terminal_workflow_state(self)
			return
		if self.applicant_type == "Employee":
			if not self.custom_current_role:
				frappe.throw(f"Current role is not set in employee profile.", title="Missing Information")
			if (self.custom_next_workflow_approver in ["", None]) or (self.is_new()):
				self.custom_next_workflow_approver = self.applicant
			record_workflow_approver_states(self)

def record_workflow_approver_states(self, publish_progress=True):
	current_user = frappe.session.user
	current_employee = frappe.db.get_value("Employee", {"user_id": current_user}, "name")

	# previous doc to compare states bcz we're calling this function on_update
	previous = self.get_doc_before_save()
	previous_state = previous.workflow_state if previous else None

	# Only validate when a transition is happening (action button is pressed)
	if previous_state and previous_state != self.workflow_state:
		_validate_transition(self, previous_state, current_employee, current_user)

	approvers_list = frappe.parse_json(self.custom_tracking_information) if self.custom_tracking_information else []
	if any(self.workflow_state == state["current_state"] for state in approvers_list):
		return

	doc = frappe.get_doc(self.doctype, self.name)
	transitions = get_transitions(doc)
	matched_transition = _find_matched_transition(self, transitions, state=None)

	if not matched_transition:
		frappe.throw("No valid workflow transition found from current state.")

	wf = frappe._dict(matched_transition)
	current_approver = self.custom_next_workflow_approver

	# Handle Guarantor 1
	if self.workflow_state == "Applied" and has_required_guarantors(self):
		_set_next_approver_and_track(
			self,
			approvers_list, wf, current_approver,
			next_employee=self.custom_guarantor_of_loan_application,
			next_state_label="Guarantor 1"
		)
		return

	# Handle Guarantor 2
	if self.workflow_state == "Recommended By Guarantor 1" and has_required_guarantors(self):
		_set_next_approver_and_track(
			self,
			approvers_list, wf, current_approver,
			next_employee=self.custom_guarantor_2_of_loan_application,
			next_state_label="Guarantor 2"
		)
		return

	# After guarantors, proceed with role-based workflow
	next_employees = get_next_role_employee(wf.allowed, self.department)
	for d in next_employees:
		if not d.get("custom_current_role"):
			link = get_link_to_form("Employee", d["name"], d["employee_name"])
			frappe.throw(f"Please set current role in {link}")
		frappe.db.set_value(self.doctype, self.name, 'custom_next_workflow_approver', d["name"])
		nxt_employee_name = frappe.db.get_value("Employee", d["name"], "employee_name")

	cur_employee_name = frappe.db.get_value("Employee", current_approver, "employee_name")
	wf.update({
		"cur_employee": current_approver,
		"employee_name": cur_employee_name,
		"current_state": self.workflow_state,
		"modified_on": get_datetime(),
		"next_employee": self.custom_next_workflow_approver if self.docstatus == 0 else "",
		"next_state": f"{nxt_employee_name}, (<b>{wf.allowed}</b>)" if self.docstatus == 0 and "Rejected" not in self.workflow_state else "",
	})

	approvers_list.append(wf)
	frappe.db.set_value(self.doctype, self.name, 'custom_tracking_information', frappe.as_json(approvers_list))
	self.reload()

def _validate_transition(self, previous_state, current_employee, current_user):
	if not has_required_guarantors(self): return
	# Validation for Guarantor 1
	if previous_state == "Applied":
		expected = self.custom_guarantor_of_loan_application
		if current_employee != expected and current_user != self.owner:
			frappe.throw("Only the assigned Guarantor 1 can take action at this stage.")

	# Validation for Guarantor 2
	elif previous_state == "Recommended By Guarantor 1":
		expected = self.custom_guarantor_2_of_loan_application
		if current_employee != expected:
			frappe.throw("Only the assigned Guarantor 2 can take action at this stage.")

def _find_matched_transition(self, transitions, state=None):
	for row in transitions:
		if (not state or row["state"] == state) and row["action"].lower() != "reject":
			condition = row.get("condition")
			try:
				if not condition or frappe.safe_eval(condition, {"doc": self}):
					return row
			except Exception as e:
				frappe.throw(f"Error in evaluating transition condition: {e}")
	return None

def has_required_guarantors(self):
	return bool(self.custom_guarantor_of_loan_application and self.custom_guarantor_2_of_loan_application)

def _set_next_approver_and_track(self, approvers_list, wf, current_approver, next_employee, next_state_label):
	if next_employee:
		frappe.db.set_value(self.doctype, self.name, 'custom_next_workflow_approver', next_employee)
		nxt_employee_name = frappe.db.get_value("Employee", next_employee, "employee_name")
		wf.update({
			"cur_employee": current_approver,
			"employee_name": frappe.db.get_value("Employee", current_approver, "employee_name"),
			"current_state": self.workflow_state,
			"modified_on": get_datetime(),
			"next_employee": next_employee,
			"next_state": f"{nxt_employee_name}, (<b>{next_state_label}</b>)"
		})
		approvers_list.append(wf)
		frappe.db.set_value(self.doctype, self.name, 'custom_tracking_information', frappe.as_json(approvers_list))
		self.reload()

def get_next_role_employee(allowed, department):
	if not allowed:
		return []
	query = f"""
		SELECT name, employee_name, custom_current_role
		FROM `tabEmployee` e
		WHERE status='Active'
			AND custom_current_role= '{allowed}'
			AND user_id IN (
				SELECT u.name FROM `tabUser` u
				INNER JOIN `tabHas Role` h ON (u.name=h.parent)
				WHERE h.role='{allowed}'
			)
	"""
	if allowed.lower() in ['line manager', 'head of department']:
		query += f" AND department= '{department}'"
	# For CEO, Finance, Secretary General, President: no department filter

	result = frappe.db.sql(query, as_dict=1)
	if not result:
		frappe.throw(
			f"Next approver with role `{allowed}` not found. Please set it first in `User Profile`.",
			title="Missing Information"
		)
	return result

def record_terminal_workflow_state(self):
	current_user = frappe.session.user
	current_employee = frappe.db.get_value("Employee", {"user_id": current_user}, "name")
	approvers_list = frappe.parse_json(self.custom_tracking_information) if self.custom_tracking_information else []
	cur_employee_name = frappe.db.get_value("Employee", current_employee, "employee_name")
	wf = {
		"cur_employee": current_employee,
		"employee_name": cur_employee_name,
		"current_state": self.workflow_state,
		"modified_on": get_datetime(),
		"next_employee": "",
		"next_state": "",
	}
	approvers_list.append(wf)
	frappe.db.set_value(self.doctype, self.name, 'custom_tracking_information', frappe.as_json(approvers_list))
	self.reload()


# http://192.168.10.137/api/method/frappe.desk.form.linked_with.get_submitted_linked_docs
# bench --site al-khidmat.com execute akf_hrms.utils.loan_utils.remove_loan
def remove_loan():
	from frappe.desk.form.linked_with import get_submitted_linked_docs, get_linked_doctypes, get_child_tables_of_doctypes, get_dynamic_linked_fields
	# links = get_submitted_linked_docs('Loan', 'ACC-LOAN-2025-00110')
	# if(links): links = links['docs']
	# # print(links)
	# for d in links:
	# 	print(d['doctype'], d['name'])
	# 	frappe.db.sql(f"delete from `tab{d['doctype']}` where name='{d['name']}' ")
	# loan_name = 'ACC-LOAN-2025-00132'
	for ln in frappe.db.sql("select name from `tabLoan` order by creation desc limit 10 ", as_dict=1):
		loan_name = ln.name
		# print(doctypes)	
		dynamic = get_dynamic_linked_fields('Loan')
		# print(dynamic)	
		for d in dynamic:
			doctype = d
	
			if(doctype != 'Full and Final Statement'):
				fname = dynamic[d]['fieldname'][0]
				print(doctype, ' ', fname)
				frappe.db.sql(f"delete from `tab{doctype}` where {fname}='{loan_name}' ")
		
		doctypes = get_linked_doctypes('Loan', loan_name)
		for doctype in doctypes:
			fieldname = doctypes[doctype]['fieldname'][0]
			fieldnamelist = frappe.db.get_list(doctype, filters={fieldname: loan_name})
			for row in fieldnamelist:  
				print(doctype)
				print(fieldname)
				print(row)
				# childs = get_child_tables_of_doctypes(doctype)
				# print('childs: ',childs)
				frappe.db.sql(f"delete from `tab{doctype}` where name='{row.name}' ")
		frappe.db.sql(f"delete from `tabLoan` where name='{loan_name}' ")
		# childs = get_child_tables_of_doctypes('Loan')
		# print(childs)
	
	


