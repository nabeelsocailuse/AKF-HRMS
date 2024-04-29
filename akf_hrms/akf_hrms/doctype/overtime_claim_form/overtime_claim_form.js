// Copyright (c) 2024, Nabeel Saleem and contributors
// For license information, please see license.txt

frappe.ui.form.on("Overtime Claim Form", {
	refresh(frm) {
		acf.set_queries(frm);
		acf.employee_info(frm);
	},
	employee_id: function(frm){
		acf.employee_info(frm);
	}
});
// COMMENTS
acf = {
	set_queries: function(frm){
		frm.set_query("employee_id", function(){
			return {
				filters: {
					"custom_overtime_allowed": 1,
				}
			}
		})
	},
	employee_info: function(frm){
		let employee_id = frm.doc.employee_id;
		if(employee_id==undefined || employee_id=="") return
		
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Employee",
				filters: { name: frm.doc.employee_id },
				fieldname: [
					"employee_name",
					"company",
					"designation",
					"department"
				]
			},
			callback: function(r){
				// console.log(r.message);
				let acf_employee_info = frappe.render_template("acf_employee_info", r.message);
				frm.set_df_property("employee_info_html", "options", acf_employee_info);
			}
		});
		
	}
}
