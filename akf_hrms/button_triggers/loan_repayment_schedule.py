import frappe

# import datetime


@frappe.whitelist()
def update_schedule(docname, row_number):
    count = 0
    frappe.msgprint(f"Worked! - docname: {docname}")

    doc = frappe.get_doc("Loan Repayment Schedule", docname)
    # last_entry = frappe.get_list(
    #     "Repayment Schedule",
    #     filters={"parent": docname},
    #     fields=["payment_date", "payment_date"],
    #     order_by="payment_date desc",
    #     limit_page_length=1,
    # )
    # last_payment_date = frappe.db.get_value(
    #     "Repayment Schedule",
    #     {"parent": docname, "idx": last_entry},
    #     "payment_date",
    # )
    # data = """select payment_date from `tabRepayment Schedule` where parent in
    # (select name from `tabLoan Repayment Schedule` where name = '%s') order by payment_date desc limit 1""" % (
    #     docname
    # )
    # data = frappe.db.sql(data)
    # frappe.throw(f"last entry : {last_entry}")
    # frappe.throw(frappe.as_json(data[0]))
    child_doc = frappe.new_doc("Repayment Schedule")
    # frappe.msgprint(f"child doc : {child_doc}")

    # size = len(doc.get(doc.repayment_schedule))
    # frappe.msgprint(f"{size}")
    for row in doc.get("repayment_schedule"):
        # check=False
        # frappe.throw(f"{size}")
        # existing_date = frappe.utils.formatdate(row.payment_date, "dd-MM-YYYY")
        # new_date = frappe.utils.formatdate(date, "dd-MM-YYYY")
        # frappe.msgprint(str(row.idx == row_number))
        # frappe.throw(f"payemt date: {existing_date} , new Date: {new_date}")
        if int(row.idx) == int(row_number) and not row.custom_skipped_loan_installment:
            # frappe.throw(f"entered if condition for row: {row_number}, ID: {row.idx}")
            row.custom_skipped_loan_installment = 1
            # frappe.utils.formatdate(frappe.utils.today(), 'dd-MM-YYYY') == frappe.utils.formatdate(data.modified, 'dd-MM-YYYY')
            # frappe.db.set_value(
            #     "Repayment Schedule",
            #     row.name,
            #     "payment_date",
            #     frappe.utils.getdate("2024-09-01"),
            # )
            # frappe.throw(f"New date cannot be less than old Payment Date")

            # check = True

            child_doc.payment_date = row.payment_date
            child_doc.principal_amount = row.principal_amount
            row.principal_amount = 0
            frappe.db.set_value("Repayment Schedule", row.name, "principal_amount", 0)
            child_doc.total_payment = row.total_payment
            # row.total_payment = 0
            # frappe.db.set_value("Repayment Schedule", row.name, "total_payment", 0)
            child_doc.number_of_days = row.number_of_days
            child_doc.balance_loan_amount = row.balance_loan_amount
            doc.append("repayment_schedule", child_doc)
            frappe.msgprint(f"skipping worked!")
        count += 1

        # if check:
        #     frappe.db.set_value("Repayment Schedule", row.name, "payment_date", "2025-10-1")

    doc.save()
    # doc.save
    # frappe.msgprint(f"after loop - child doc : {child_doc}")
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
