import frappe
from frappe import _
from hrms.hr.doctype.leave_application.leave_application import LeaveApplication

class XLeaveApplication(LeaveApplication):
    def validate(self):
        super(XLeaveApplication, self).validate()
        self.update_pending_status()
        self.update_approval_status()
        self.update_rejected_status()

    def update_pending_status(self):
        if self.workflow_state == "Pending":
            self.custom_approval_status = 'Pending'
            
    def update_approval_status(self):
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

    def update_rejected_status(self):
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
