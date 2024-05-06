frappe.ui.form.on("Employee Separation", {
  refresh: function (frm) {
    if (frm.doc.docstatus == 1) {
      frm.add_custom_button(__("Create Full and Final Statement"), function () {
        frappe.set_route("List", "Full and Final Statement", {
          employee: frm.doc.employee,
        });
      });
    }
  },
});
