import frappe


@frappe.whitelist()
def update_schedule(docname, row_number, date):
    count = 0
    frappe.msgprint(f"Worked! - docname: {docname}")

    doc = frappe.get_doc("Loan Repayment Schedule", docname)
    child_doc = frappe.new_doc("Repayment Schedule")
    frappe.msgprint(f"child doc : {child_doc}")
    # child_doc.payment_date = date
    # child_doc.principal_amount = 100
    # doc.append("repayment_schedule", child_doc)

    for row in doc.get("repayment_schedule"):
        if row.idx == row_number:
            row.custom_skipped_loan_installment = 1
            frappe.msgprint(f"skipped: {row.custom_skipped_loan_installment}")
        count += 1
    doc.save()
    frappe.msgprint(f"after loop - child doc : {child_doc}")
    return f"Funcationality Perfomed! row-count: {count}"


# def add_repayment_schedule_row(
#     doc,
#     payment_date,
#     principal_amount,
#     interest_amount,
#     total_payment,
#     balance_loan_amount,
#     days,
# ):
#     frappe.msgprint(
#         f"{payment_date},{principal_amount},{interest_amount},{total_payment},{balance_loan_amount},{days}"
#     )
#     doc.append(
#         "repayment_schedule",
#         {
#             "number_of_days": days,
#             "payment_date": payment_date,
#             "principal_amount": principal_amount,
#             "interest_amount": interest_amount,
#             "total_payment": total_payment,
#             "balance_loan_amount": balance_loan_amount,
#         },
#     )


# doc = frappe.get_doc("Loan Repayment Schedule", docname)
#     for row in doc.get("repayment_schedule"):
#         if row.idx == idx:
#             row.idx = idx
#             row.payment_date = date
#     doc.save()
