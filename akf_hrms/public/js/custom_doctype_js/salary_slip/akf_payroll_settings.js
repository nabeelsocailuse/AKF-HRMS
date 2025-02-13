// frappe.ui.form.off("Salary Slip",employee)
frappe.ui.form.on("Salary Slip", {
	onload: function(frm){
		// Ignore cancellation of doctype on cancel all.
		frm.ignore_doctypes_on_cancel_all = ["Leave Ledger Entry", "Leave Application", "Attendance"];
	},
	custom_leaves_without_pay: function(frm) {
		// console.log('working')
		if (frm.doc.employee && frm.doc.start_date && frm.doc.end_date) {
			return frappe.call({
				method: 'process_salary_based_on_working_days',
				doc: frm.doc,
				callback: function() {
					frm.refresh();
				}
			});
		}
	},
	custom_apply_deductions: function(frm) {
		if (frm.doc.employee && frm.doc.start_date && frm.doc.end_date) {
			return frappe.call({
				method: 'process_salary_based_on_working_days',
				doc: frm.doc,
				callback: function() {
					frm.refresh();
				}
			});
		}
	},
   /*  employee: function (frm){
        frm.events.get_eobi_pf_social_security_details(frm);
		frm.events.set_deduction_ledger(frm);
    },
	start_date: function(frm){
		frappe.call({
			method: "akf_hrms.utils.hr_policy.get_no_attendance",
			doc: frm.doc,
			callback: function (r) {
				// frm.refresh();
			},
		});

		frm.events.set_deduction_ledger(frm);
	},
	end_date: function(frm){
		frm.events.set_deduction_ledger(frm);
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
	set_deduction_ledger: function(frm){
		if (frm.doc.employee!=undefined && frm.doc.start_date!=undefined && frm.doc.end_date!=undefined) {
			return frappe.call({
				method: "akf_hrms.utils.hr_policy.get_deduction_ledger",
				args: {
					employee: frm.doc.employee,
					start_date: frm.doc.start_date,
					end_date: frm.doc.end_date,
				},
				callback: function (r) {
					let data = r.message;
					if(data.length>0){
						data.forEach(d => {
							frm.set_value('custom_casual_leaves', d.leave_type == "Casual Leave"? d.total: 0);
							frm.set_value('custom_medical_leaves', d.leave_type == "Medical Leave"? d.total: 0);
							frm.set_value('custom_earned_leaves', d.leave_type == "Earned Leave"? d.total: 0);
							frm.set_value('custom_leaves_without_pay', d.leave_type == "Leave Without Pay"? d.total: 0);
						});
					}else{
						frm.set_value('custom_casual_leaves', 0);
						frm.set_value('custom_medical_leaves', 0);
						frm.set_value('custom_earned_leaves', 0);
						frm.set_value('custom_leaves_without_pay', 0);
					}
				},
			});
		}
	} */
})