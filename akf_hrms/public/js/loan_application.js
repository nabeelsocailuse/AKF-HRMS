frappe.ui.form.on("Loan Application", {
  loan_product: function (frm) {
    if (frm.doc.loan_product == "Advance Salary") {
      frm.set_value("repayment_method", "Repay Fixed Amount per Period");
      frappe.call({
        method: "frappe.client.get_value",
        args: {
          doctype: "Salary Structure Assignment",
          filters: { employee: frm.doc.applicant },
          fieldname: ["base"],
        },
        callback: function (r) {
          if (r.message) {
            frm.set_value("custom_maximum_allowed_loan", r.message.base / 2);
            frm.set_value("loan_amount", frm.doc.custom_maximum_allowed_loan);
            frm.set_value(
              "repayment_amount",
              frm.doc.custom_custom_maximum_allowed_loan
            );
            frm.set_df_property("custom_custom_maximum_allowed_loan", "read_only", 1);
          } else {
            frappe.msgprint(__("No Salary Structure Assignment found"));
          }
        },
      });
    } else {
      frm.set_df_property("custom_custom_maximum_allowed_loan", "read_only", 0);
    }
  },
  loan_amount: function (frm) {
    if (frm.doc.loan_product == "Advance Salary") {
      frm.set_value("repayment_method", "Repay Fixed Amount per Period");
      frm.set_value("repayment_amount", frm.doc.loan_amount);
      frm.set_df_property("repayment_method", "read_only", 1);
      frm.set_df_property("repayment_amount", "read_only", 1);

      if (frm.doc.loan_amount > frm.doc.custom_custom_maximum_allowed_loan) {
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
