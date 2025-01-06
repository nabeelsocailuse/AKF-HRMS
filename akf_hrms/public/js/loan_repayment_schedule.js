frappe.ui.form.on("Loan Repayment Schedule", {
  refresh(frm) {
    if (frm.doc.docstatus == 1) {
      frm.add_custom_button(__("Skip Installment"), function () {
        frappe.prompt(
          [{ fieldname: "row_number", fieldtype: "Int", label: "Row Number" }],
          function (values) {
            var idx_value = values.row_number;
            frappe.call({
              method:
                "akf_hrms.button_triggers.loan_repayment_schedule.update_schedule",
              args: {
                docname: frm.docname,
                row_number: idx_value,
              },
              callback: function (r) {},
            });
          },
          __("Enter the serial number of Installment to be skipped!"),
          __("Submit")
        );
      });
    }

    // var check = false;
    // frappe.call({
    //   method: "akf_hrms.button_triggers.loan_repayment_schedule.skip_status",
    //   args: {
    //     docname: frm.docname,
    //   },
    //   async: false,
    //   callback: function (r) {
    //     check = r.message;
    //   },
    // });

    // if (frm.doc.docstatus == 1 && check) {
    //   frm.add_custom_button(__("Revert All Changes"), function () {
    //     frappe.call({
    //       method: "akf_hrms.button_triggers.loan_repayment_schedule.revert",
    //       args: {
    //         docname: frm.docname,
    //       },
    //       async: false,
    //       callback: function (r) {},
    //     });
    //   });
    // }
  },
});
