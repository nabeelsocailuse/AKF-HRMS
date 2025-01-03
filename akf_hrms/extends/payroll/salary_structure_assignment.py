# import frappe
from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import (
    SalaryStructureAssignment
)
from akf_hrms.utils.hr_policy import (submit_employee_additional_salary_arrears)

class XSalaryStructureAssignment(SalaryStructureAssignment):
    def validate(self):
        super(XSalaryStructureAssignment, self).validate()
        self.calculate_hours_base()
        self.calculate_per_day()
        # submit_employee_additional_salary_arrears(self)
        
    def calculate_hours_base(self):
        # (base/30)/8
        self.custom_hourly_base = (self.base/30.0)/8.0

    def calculate_per_day(self): # Mubarrim
        self.custom_per_day = (self.base/30.0)
    
    def on_submit(self):
        submit_employee_additional_salary_arrears(self)


