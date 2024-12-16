import frappe
import json
from erpnext.accounts.utils import get_fiscal_year
from hrms.payroll.doctype.additional_salary.additional_salary import AdditionalSalary

class XAdditionalSalary(AdditionalSalary):
    def on_submit(self):
        super().on_submit()
        pass

    def validate(self):
        super().validate()
        
        if(self.salary_component == "Marriage Allowance"):
            marital_status = frappe.db.get_value('Employee', self.employee, 'marital_status')
            if(marital_status != 'Single'):
                frappe.throw("Unmarried individuals are eligible to claim the Marriage Allowance!")

            if frappe.db.exists("Additional Salary", {
                "salary_component": "Marriage Allowance", 
                "employee": self.employee,
                "docstatus": 1
            }):
                frappe.throw("You have already applied for the Marriage Allowance and cannot apply again.")

        employee_type = frappe.db.get_value("Employee", {"name": self.employee, "status": "Active"}, "employment_type")
        
        if employee_type:
            if employee_type == "Permanent":
                gross_salary = frappe.db.get_value(
                        "Salary Structure Assignment",
                        {"employee": ["like", f"{self.employee}%"], "docstatus": 1},
                        "base"
                    )

                if gross_salary:
                    if float(gross_salary) < float(self.amount):
                        frappe.throw(f"The requested amount exceeds the gross salary PKR: {gross_salary}")
                    else:
                        pass
                else:
                    frappe.throw("No salary structure found for this employee. Please ensure the employee has a valid salary structure.")
            elif(self.salary_component == "Marriage Allowance"):
                frappe.throw("You are not eligible to apply for the Marriage Allowance as you are not a permanent employee.")
                
        else:
            frappe.throw("Employee type could not be determined. Please check the employee record.")