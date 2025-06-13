import frappe
from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import (
    SalaryStructureAssignment
)

class XSalaryStructureAssignment(SalaryStructureAssignment):
    def validate(self):
        super(XSalaryStructureAssignment, self).validate()
        self.calculate_hours_base()
        self.calculate_per_day()
    
    def on_submit(self):
        self.validate_social_security_applicable()

    def calculate_hours_base(self):
        # (base/30)/8
        self.custom_hourly_base = (self.base/30.0)/8.0
        
    def calculate_per_day(self): # Mubarrim
        self.custom_per_day = (self.base/30.0)

    def validate_social_security_applicable(self):  # Mubashir Bashir 12-June-2025
        social_security_amount = frappe.db.get_value("AKF Payroll Settings", None, "social_security_amount")
        if social_security_amount is not None:
            social_security_amount = float(social_security_amount)
        else:
            return

        is_applicable = False

        if self.base <= social_security_amount:
            is_applicable = True
        else:
            existing_assignments = frappe.get_all(
                "Salary Structure Assignment",
                filters={
                    "employee": self.employee,
                    "docstatus": 1,
                    "name": ["!=", self.name],
                    "base": ["<=", social_security_amount]
                },
                limit=1
            )
            if existing_assignments:
                is_applicable = True

        if is_applicable:
            frappe.db.set_value("Employee", self.employee, "custom_social_security_applicable", 1)



