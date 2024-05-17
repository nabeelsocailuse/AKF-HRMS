// frappe.ui.form.off("Salary Slip",employee)
frappe.ui.form.on("Salary Slip", {
    employee: function (frm){
        frm.events.get_eobi_pf_social_security_details(frm);
    },


    get_eobi_pf_social_security_details: function (frm) {
		if (frm.doc.employee) {
			return frappe.call({
				method: "get_eobi_pf_social_security_details",
				doc: frm.doc,
				callback: function (r) {
					// frm.refresh();
				},
			});
		}
	},
})