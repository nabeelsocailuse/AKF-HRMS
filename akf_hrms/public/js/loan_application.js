frappe.ui.form.on("Loan Application", {
  loan_product: function (frm) {
    if (
      frm.doc.loan_product == "Advance Salary" ||
      frm.doc.loan_product == "Advance Salary - Endowment Fund Trust" ||
      frm.doc.loan_product ==
        "Advance Salary - Alkhidmat Islamic Microfinance" ||
      frm.doc.loan_product == "Advance Salary - Alkhidmat Health Foundation" ||
      frm.doc.loan_product == "Advance Salary - Alfalah Scholarship"
    ) {
      frm.set_value("repayment_method", "Repay Fixed Amount per Period");
      frappe.call({
        method: "frappe.client.get_list",
        args: {
          doctype: "Salary Structure Assignment",
          fields: ["base"],
          filters: {
            employee: frm.doc.applicant,
            docstatus: 1,
            from_date: ["<", new Date()],
          },
          order_by: "from_date DESC",
          limit_page_length: 1,
        },
        callback: function (r) {
          if (r.message[0]) {
            frm.set_value("custom_maximum_allowed_loan", r.message[0].base / 2);
            frm.set_value("loan_amount", frm.doc.custom_maximum_allowed_loan);
            frm.set_value(
              "repayment_amount",
              frm.doc.custom_maximum_allowed_loan
            );
            frm.set_df_property("custom_maximum_allowed_loan", "read_only", 1);
          } else {
            frm.set_value("loan_product", "");
            frappe.msgprint(
              __(
                "Not authorized to apply for the loan as there is no Salary Structure Assignment currently active."
              )
            );
          }
        },
      });
    } else {
      frm.set_df_property("custom_maximum_allowed_loan", "read_only", 0);
    }
  },
  loan_amount: function (frm) {
    if (
      frm.doc.loan_product == "Advance Salary" ||
      frm.doc.loan_product == "Advance Salary - Endowment Fund Trust" ||
      frm.doc.loan_product ==
        "Advance Salary - Alkhidmat Islamic Microfinance" ||
      frm.doc.loan_product == "Advance Salary - Alkhidmat Health Foundation" ||
      frm.doc.loan_product == "Advance Salary - Alfalah Scholarship"
    ) {
      frm.set_value("repayment_method", "Repay Fixed Amount per Period");
      frm.set_value("repayment_amount", frm.doc.loan_amount);
      frm.set_df_property("repayment_method", "read_only", 1);
      frm.set_df_property("repayment_amount", "read_only", 1);

      if (frm.doc.loan_amount > frm.doc.custom_maximum_allowed_loan) {
        frappe.msgprint(
          __(
            "You cannot apply Loan more than " +
              frm.doc.custom_maximum_allowed_loan
          )
        );

        frm.set_value("loan_amount", frm.doc.custom_maximum_allowed_loan);
        return;
      }
    } else {
      frm.set_df_property("repayment_method", "read_only", 0);
      frm.set_df_property("repayment_amount", "read_only", 0);
    }
  },
});
