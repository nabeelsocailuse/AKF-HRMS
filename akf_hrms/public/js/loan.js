frappe.ui.form.on("Loan", {
  loan_category: function (frm) {
    if (frm.doc.loan_category == "Term Loan(Salary Advance)") {
      frm.set_value("repay_from_salary", 1);
      frm.set_df_property("repay_from_salary", "read_only", 1);
      frm.set_value("repayment_start_date", frappe.datetime.month_start());
      frm.set_df_property("repayment_start_date", "read_only", 1);
      frm.set_value("repayment_method", "Repay Fixed Amount per Period");
      frm.set_df_property("monthly_repayment_amount", "read_only", 1);
      frm.set_df_property("repayment_method", "read_only", 1);
    } else {
      frm.set_df_property("repay_from_salary", "read_only", 0);
      frm.set_df_property("monthly_repayment_amount", "read_only", 0);
      frm.set_df_property("repayment_method", "read_only", 0);
      frm.set_df_property("repayment_start_date", "read_only", 0);
    }
  },

  loan_amount: function (frm) {
    if (frm.doc.loan_category == "Term Loan(Salary Advance)") {
      frm.set_value("monthly_repayment_amount", frm.doc.loan_amount);
      frm.set_value("repayment_start_date", frappe.datetime.month_start());
      frm.set_df_property("repayment_method", "read_only", 1);
      frm.set_df_property("monthly_repayment_amount", "read_only", 1);
      frm.set_df_property("repayment_start_date", "read_only", 1);
    } else {
      frm.set_df_property("repayment_method", "read_only", 0);
      frm.set_df_property("monthly_repayment_amount", "read_only", 0);
      frm.set_df_property("repayment_start_date", "read_only", 0);
    }
  },
});
