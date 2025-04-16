import frappe
from lending.loan_management.doctype.loan_repayment_schedule.loan_repayment_schedule import (
	add_single_month,
)
from frappe.utils import get_link_to_form

@frappe.whitelist()
def update_schedule(docname, row_number):
	count = 0
	doc = frappe.get_doc("Loan Repayment Schedule", docname)
 
	data = frappe.db.get_value("Repayment Schedule", 
                    {"parent": docname, "idx": row_number}, ["name", "payment_date"], as_dict=1)

	filters = frappe._dict({
		"company": doc.company,
		"loan": doc.loan,
		"payment_date": data.payment_date
	})
	
	validate_loan_interest_accrual(filters)

	check = False
	for row in doc.get("repayment_schedule"):
		if int(row.idx) == int(row_number) and row.custom_skipped_loan_installment:
			frappe.msgprint(f"This installment-{row_number} has been already skipped!", alert=1)
			
		if int(row.idx) == int(row_number) and not row.custom_skipped_loan_installment:
			payment_date = row.payment_date
			next_payment_date = add_single_month(payment_date)
			row.custom_skipped_loan_installment = 1
			row.custom_skipped_date = row.payment_date
			row.payment_date = next_payment_date
			check = True
		elif int(row.idx) > int(row_number) and check:
			payment_date = row.payment_date
			next_payment_date = add_single_month(payment_date)
			row.payment_date = next_payment_date
		count += 1
	doc.save()
	return f"Funcationality Perfomed! row-count: {count}"

def validate_loan_interest_accrual(filters):
	result = frappe.db.sql("""
		Select 
  			name
		From 
  			`tabLoan Interest Accrual`
		Where
			docstatus=1
			and company = %(company)s
			and loan= %(loan)s
			and due_date = %(payment_date)s
	""", filters, as_dict=0)
	
	if(result):
		link = get_link_to_form("Loan Interest Accrual", result[0][0], "Loan Interest Accrual")
		frappe.throw(f"You're not able to skip installment. Because, it's already processed. {link}", title="Not Allowed")
