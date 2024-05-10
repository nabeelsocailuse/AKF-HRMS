frappe.ui.form.on("Loan Repayment Schedule", {
  refresh(frm) {
    if (frm.doc.docstatus == 1) {
      frm.add_custom_button(__("Change Payment Schedule"), function () {
        frappe.prompt(
          [
            { fieldname: "row_number", fieldtype: "Int", label: "Row Number" },
            {
              fieldname: "new_date",
              fieldtype: "Date",
              label: "New Payment Date",
            },
          ],
          function (values) {
            // Handle the input values here
            var idx_value = values.row_number;
            var newDate_value = values.new_date;
            console.log(idx_value);
            console.log(newDate_value);

            // You can perform further actions here
            frappe.call({
              method:
                "akf_hrms.button_triggers.loan_repayment_schedule.update_schedule",
              args: {
                docname: frm.docname,
                row_number: idx_value,
                date: newDate_value,
              },
              callback: function (r) {
                let data = r.message;
                console.log("returned from py file : " + data);
              },
            });
          },
          __("Enter the Row and New date for your Loan Payment"),
          __("Submit")
        );
      });
    }
  },
});

// frappe.prompt(
//     [
//       { fieldname: "idx", fieldtype: "Int", label: "ID" },
//       {
//         fieldname: "new_date",
//         fieldtype: "Date",
//         label: "New Payment Date",
//       },
//     ],
//     function (values) {
//       // Handle the input values here
//       var idx_value = values.idx;
//       var newDate_value = values.new_date;
//       console.log(idx_value);
//       console.log(newDate_value);

//       // You can perform further actions here
//       frappe.call({
//         method:
//           "akf_hrms.button_triggers.loan_repayment_schedule.update_schedule",
//         args: {
//           docname: frm.docname,
//           idx: idx_value,
//           date: newDate_value,
//         },
//         callback: function (r) {
//           let data = r.message;
//           console.log("returned from py file : " + data);
//         },
//       });
//     },
//     __("Enter Values"),
//     __("Submit")
//   );
