# Mubashir Bashir 2-July-2025

import frappe
from frappe import _
from lending.loan_management.doctype.loan_product.loan_product import LoanProduct


class XLoanProduct(LoanProduct):

    def validate(self):
        super().validate()
        self.validate_loan_limits()

    def validate_loan_limits(self):
        
        for row in self.custom_loan_limit:
            if row.max_loan_per_emp > row.total_loan_budget:
                frappe.throw(
                    f"Max Loan per Employee ({row.max_loan_per_emp}) cannot exceed Total Loan Budget ({row.total_loan_budget}) in row {row.idx}."
                )

