frappe.ui.form.on("Loan Application", {
  loan_product: function (frm) {
    if (frm.doc.loan_product == "Advance Salary") {
      frm.set_value("repayment_method", "Repay Fixed Amount per Period");
      frm.set_value("repayment_amount", frm.doc.loan_amount);
      frm.set_df_property("repayment_method", "read_only", 1);
      frm.set_df_property("repayment_amount", "read_only", 1);
    } else {
      frm.set_df_property("repayment_method", "read_only", 0);
      frm.set_df_property("repayment_amount", "read_only", 0);
    }
  },
});
