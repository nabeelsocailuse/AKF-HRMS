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
        frappe.msgprint("Extended Additional Salary Triggered")
        
        