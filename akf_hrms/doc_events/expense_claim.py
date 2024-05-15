import frappe


@frappe.whitelist()
def create_additional_salary_for_expense_claim(self):
    if self.approval_status == "Approved":
        additional_salary = frappe.new_doc("Additional Salary")
        additional_salary.employee = self.employee
        additional_salary.company = self.company
        additional_salary.payroll_date = self.posting_date
        additional_salary.amount = self.grand_total
        additional_salary.salary_component = "Expense Claim"
        additional_salary.overwrite_salary_structure_amount = 0
        additional_salary.insert()
        additional_salary.submit()
