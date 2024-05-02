frappe.ui.form.on("Staffing Plan", {
  //   onload: function (frm) {
  //     frm.get_field("get_job_requisitions").$input.off("click");

  //     frm.get_field("get_job_requisitions").$input.on("click", function (e) {
  //       e.stopImmediatePropagation();

  //       frappe.msgprint({
  //         title: __("Custom Handler"),
  //         indicator: "green",
  //         message: __(
  //           "The original modal will not be shown, this is the custom behavior."
  //         ),
  //       });
  //     });
  //   },
  get_job_requisitions: function (frm) {
    new frappe.ui.form.MultiSelectDialog({
      doctype: "Job Requisition",
      target: frm,
      date_field: "posting_date",
      add_filters_group: 1,
      setters: {
        designation: null,
        requested_by: null,
      },
      get_query() {
        let filters = {
          company: frm.doc.company,
          status: ["in", ["Open & Approved"]],
        };

        if (frm.doc.department) filters.department = frm.doc.department;

        return {
          filters: filters,
        };
      },
      action(selections) {
        const plan_name = frm.doc.__newname;
        frappe
          .call({
            method: "set_job_requisitions",
            doc: frm.doc,
            args: selections,
          })
          .then(() => {
            // hack to retain prompt name that gets lost on frappe.call
            frm.doc.__newname = plan_name;
            refresh_field("staffing_details");
          });

        cur_dialog.hide();
      },
    });
  },
});
