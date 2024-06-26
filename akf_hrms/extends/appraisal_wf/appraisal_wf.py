import frappe
from frappe import _
from hrms.hr.doctype.appraisal.appraisal import Appraisal

class XAppraisal(Appraisal):
    def validate(self):
        super(XAppraisal, self).validate()
        self.update_pending_status()
        self.update_approval_status()
        self.update_rejected_status()

    def update_pending_status(self):
        if self.workflow_state == "Pending":
            self.custom_approval_status = 'Pending'

    def update_approval_status(self):
        current_roles = frappe.get_roles()
        workflow_state = self.workflow_state
        docstatus = self.docstatus

        if workflow_state == 'Pending':
            self.custom_approval_status = 'Pending'

        elif workflow_state == 'Approved':
            self.custom_approval_status = 'Approved by the CEO'

        elif workflow_state == 'Rejected by the Head of Department':
            if 'Head of Department' in current_roles and docstatus == 0:
                self.custom_approval_status = 'Rejected by the Head of Department'

    def update_rejected_status(self):
        current_roles = frappe.get_roles()
        workflow_state = self.workflow_state
        docstatus = self.docstatus

        if workflow_state == 'Rejected':
            self.custom_approval_status = 'Rejected by the CEO'

        elif workflow_state == 'Rejected by the Head of Department':
            if 'Head of Department' in current_roles and docstatus == 0:
                self.custom_approval_status = 'Rejected by the Head of Department'
