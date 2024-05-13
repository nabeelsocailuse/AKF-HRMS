frappe.ui.form.on("Loan Repayment Schedule", {
  refresh(frm) {
    if (frm.doc.docstatus == 1) {
      frm.add_custom_button(__("Skip Installment"), function () {
        frappe.prompt(
          [
            { fieldname: "row_number", fieldtype: "Int", label: "Row Number" },
            // {
            //   fieldname: "new_date",
            //   fieldtype: "Date",
            //   label: "New Payment Date",
            // },
          ],
          function (values) {
            // Handle the input values here
            var idx_value = values.row_number;
            // var newDate_value = values.new_date;
            console.log(idx_value);
            // console.log(newDate_value);

            // You can perform further actions here
            frappe.call({
              method:
                "akf_hrms.button_triggers.loan_repayment_schedule.update_schedule",
              args: {
                docname: frm.docname,
                row_number: idx_value,
              },
              callback: function (r) {
                let data = r.message;
                console.log("returned from py file : " + data);
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
