from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import (
    SalaryStructureAssignment
)

class XSalaryStructureAssignment(SalaryStructureAssignment):
    def validate(self):
        super(XSalaryStructureAssignment, self).validate()
        self.calculate_hours_base()

    def calculate_hours_base(self):
        # (base/30)/8
        self.custom_hourly_base = (self.base/30.0)/8.0

