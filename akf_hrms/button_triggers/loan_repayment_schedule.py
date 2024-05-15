import frappe
from lending.loan_management.doctype.loan_repayment_schedule.loan_repayment_schedule import (
    add_single_month,
)


@frappe.whitelist()
def update_schedule(docname, row_number):
    count = 0
    doc = frappe.get_doc("Loan Repayment Schedule", docname)
    check = False
    for row in doc.get("repayment_schedule"):
        if int(row.idx) == int(row_number) and not row.custom_skipped_loan_installment:
            payment_date = row.payment_date
            next_payment_date = add_single_month(payment_date)
            row.custom_skipped_loan_installment = 1
            row.payment_date = next_payment_date
            check = True
        elif int(row.idx) > int(row_number) and check:
            payment_date = row.payment_date
            next_payment_date = add_single_month(payment_date)
            row.payment_date = next_payment_date
        count += 1
    doc.save()
