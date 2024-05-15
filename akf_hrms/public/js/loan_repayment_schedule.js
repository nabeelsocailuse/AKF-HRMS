frappe.ui.form.on("Loan Repayment Schedule", {
  refresh(frm) {
    if (frm.doc.docstatus == 1) {
      frm.add_custom_button(__("Skip Installment"), function () {
        frappe.prompt(
          [
            { fieldname: "row_number", fieldtype: "Int", label: "Row Number" },
          ],
          function (values) {
            var idx_value = values.row_number;
            frappe.call({
              method:
                "akf_hrms.button_triggers.loan_repayment_schedule.update_schedule",
              args: {
                docname: frm.docname,
                row_number: idx_value,
              },
              callback: function (r) {
              },
            });
          },
          __("Enter the serial number of Installment to be skipped!"),
          __("Submit")
        );
      });
    }
  },
});
