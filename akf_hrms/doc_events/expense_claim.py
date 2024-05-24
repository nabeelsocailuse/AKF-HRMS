import frappe


@frappe.whitelist()
def create_additional_salary_for_expense_claim(doc, method=""):
    if (doc.approval_status == "Approved"):
        additional_salary = frappe.new_doc("Additional Salary")
        additional_salary.employee = doc.employee
        additional_salary.company = doc.company
        additional_salary.payroll_date = doc.posting_date
        additional_salary.amount = doc.grand_total
        additional_salary.salary_component = "Expense Claim"
        additional_salary.overwrite_salary_structure_amount = 0
        additional_salary.insert()
        additional_salary.submit()
