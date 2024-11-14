# import frappe
from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import (
    SalaryStructureAssignment
)

class XSalaryStructureAssignment(SalaryStructureAssignment):
    def validate(self):
        super(XSalaryStructureAssignment, self).validate()
        self.calculate_hours_base()
        self.calculate_per_day()

    def calculate_hours_base(self):
        # (base/30)/8
        self.custom_hourly_base = (self.base/30.0)/8.0

    def calculate_per_day(self): # Mubarrim
        self.custom_per_day = (self.base/30.0)

