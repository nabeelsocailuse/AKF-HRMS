import frappe
from frappe import _
from hrms.hr.doctype.job_requisition.job_requisition import JobRequisition

class XJobRequisition(JobRequisition):
    def validate(self):
        super(XJobRequisition, self).validate()
        self.validate_custom_employee_grade()
        self.update_pending_status()
        self.update_approval_status()
        self.update_rejected_status()

    def validate_custom_employee_grade(self):
        # List of allowed grades
        allowed_grades = [
            "C", "D", "DM", "DH", "F", "FD", "FH", "FP", "FS",
            "P", "PD", "PS", "PP-1", "PP-2", "PP-3",
            "SS-1", "SS-2", "SS-3"
        ]
        
        custom_employee_grade = self.custom_employee_grade

        if custom_employee_grade not in allowed_grades:
            frappe.throw(_(f"Approval Flow for the grade <b>\"{custom_employee_grade}\"</b> is not defined. Please contact the HR department for further guidance."))
    def update_pending_status(self):
        if self.workflow_state == "Pending":
            self.custom_approval_status = 'Pending'

    def update_approval_status(self):
            current_roles = frappe.get_roles()

            # For Approved Statuses
            if 'Secretary General' in current_roles and self.docstatus == 0:
                if self.custom_employee_grade in ["C", "D", "DM", "DH", "F", "FD"]:
                    self.custom_approval_status = 'Approved by the Secretary General'

            if 'CEO' in current_roles and self.docstatus == 0:
                if self.custom_employee_grade in ["FH", "FP", "FS", "P", "PD", "PS", "PP-1", "PP-2", "PP-3"]:
                    self.custom_approval_status = 'Approved by the CEO'

            if 'HR Manager' in current_roles and self.docstatus == 0:
                if self.custom_employee_grade in ["SS-1", "SS-2", "SS-3"]:
                    self.custom_approval_status = 'Approved by the HR Manager'

            # Check if the document status is draft (docstatus == 0)
    def update_rejected_status(self):
        if self.workflow_state == "Rejected":
            current_roles = frappe.get_roles()
            if 'CEO' in current_roles and self.docstatus == 0 and self.custom_employee_grade in ["FH", "FP", "FS", "P", "PD", "PS", "PP-1", "PP-2", "PP-3"]:
                self.custom_approval_status = 'Rejected by the CEO'
            elif 'Secretary General' in current_roles and self.docstatus == 0 and self.custom_employee_grade in ["C", "D", "DM", "DH", "F", "FD"]:
                self.custom_approval_status = 'Rejected by the Secretary General'
            elif 'HR Manager' in current_roles and self.docstatus == 0 and self.custom_employee_grade in ["SS-1", "SS-2", "SS-3"]:
                self.custom_approval_status = 'Rejected by the HR Manager'
            
        elif self.workflow_state == 'Rejected by the CEO':
            current_roles = frappe.get_roles() 
            if 'CEO' in current_roles and self.docstatus == 0 and self.custom_employee_grade in ["DM", "DH", "F", "FD"]:
                self.custom_approval_status = 'Rejected by the CEO'
        elif self.workflow_state == 'Rejected by the Head of Department':
            current_roles = frappe.get_roles() 
            if 'CEO' in current_roles and self.docstatus == 0 and self.custom_employee_grade in ["FH", "FP", "FS", "P", "PD", "PS", "PP-1", "PP-2", "PP-3"]:
                self.custom_approval_status = 'Rejected by the Head of Department'
       
                
