// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Work From Home Request', {
	setup: function(frm) {
		frm.set_query("leave_approver", function() {
			return {
				query: "hrms.setup.doctype.department_approver.department_approver.get_approvers",
				filters: {
					employee: frm.doc.employee,
					doctype: frm.doc.doctype
				}
			};
		});
	},
	refresh: function(frm) {
		/*if(frm.doc.docstatus==1) {
			frm.add_custom_button(__('Attendance Request'), function() {
				frappe.call({
					method: "mm_app.mm_hr.doctype.work_from_home_request.work_from_home_request.chk_dublication",
					args: {doc_name: frm.doc.name,
						employee: frm.doc.employee},
					callback: function(r){
						if (r.message == ""){
							frappe.set_route("/app/attendance-request/new-attendance-request-",{"employee": frm.doc.employee,"work_from_home_request": frm.doc.name, "reason": "Work From Home"});
						}
						else{
							frappe.throw("Attendance Request Already Created")
						}
					}
				});
			});
		}*/
		frm.set_query("employee", function() {
			return {
				"filters": {
					"status": 'Active',
				}
			};
		});
	},
	onload: function(frm) {
		/*if(frm.doc.docstatus==1) {
			frm.add_custom_button(__('Attendance Request'), function() {
				frappe.call({
					method: "mm_app.mm_hr.doctype.work_from_home_request.work_from_home_request.chk_dublication",
					args: {doc_name: frm.doc.name,
						employee: frm.doc.employee},
					callback: function(r){
						if (r.message == ""){
							frappe.set_route("/app/attendance-request/new-attendance-request-",{"employee": frm.doc.employee,"work_from_home_request": frm.doc.name, "reason": "Work From Home"});
						}
						else{
							frappe.throw("Attendance Request Already Created")
						}
					}
				});
			});
		}*/
		frm.set_query("employee", function() {
			return {
				"filters": {
					"status": 'Active',
				}
			};
		});
	},
	leave_approver: function(frm) {
		if(frm.doc.leave_approver){
			frm.set_value("leave_approver_name", frappe.user.full_name(frm.doc.leave_approver));
		}
	},
	employee: function(frm) {
		frm.trigger("set_leave_approver");
	},
	from_date: function(frm) {
		frm.trigger("calculate_total_days");
	},

	to_date: function(frm) {
		frm.trigger("calculate_total_days");
	},
	calculate_total_days: function(frm) {
		if(frm.doc.from_date && frm.doc.to_date && frm.doc.employee) {

			var from_date = Date.parse(frm.doc.from_date);
			var to_date = Date.parse(frm.doc.to_date);

			if(to_date < from_date){
				frappe.msgprint(__("To Date cannot be less than From Date"));
				frm.set_value('to_date', '');
				return;
			}
		}
	},
	set_leave_approver: function(frm) {
		if(frm.doc.employee) {
				// server call is done to include holidays in leave days calculations
			return frappe.call({
				method: 'hrms.hr.doctype.leave_application.leave_application.get_leave_approver',
				args: {
					"employee": frm.doc.employee,
				},
				callback: function(r) {
					if (r && r.message) {
						frm.set_value('approver', r.message);
					}
				}
			});
		}
	}
});
