// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Late Arrival Report"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"reqd": 1
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"reqd": 1
		},
		{
			"fieldname":"employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee"
		},
		{
			"fieldname":"department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department"
		}
	],

	// "formatter": function(value, row, column, data, default_formatter) {
	// 	value = default_formatter(value, row, column, data);

	// 	let class_name = "";
	// 	if (value == "P") class_name = "span-present";
	// 	else if (value == "A") class_name = "span-absent";
	// 	else if (value == "L") class_name = "span-leave";
	// 	else if (value == "Late") class_name = "span-late";
	// 	else if (value == "Early") class_name = "span-early";
	// 	else if (value == "Extra") class_name = "span-extra";
	// 	else if (parseFloat(data["Total hours worked"]) > parseFloat(data["Total hours assigned"]) && column.id == "Total hours worked") class_name = "span-extratime";
	// 	else if (parseFloat(data["Total hours worked"]) < parseFloat(data["Total hours assigned"]) && column.id == "Total hours worked") class_name = "span-lessime";
	// 	else if (data["Check In"] > data["Shift Check In"] && column.id == "Check In") class_name = "span-chk_in";

	// 	value = $(`<span class="${class_name}">${value}</span>`);
	// 	return value.wrap("<p></p>").parent().html();
	// },

	// "onload": function(frm) {
	// 	console.log(frm.report_name);
	// 	frm.page.add_inner_button(__("Send Email"), function() {
	// 		frappe.call({
	// 			method: "erpnext.hr.report.api_send_email.send_email",
	// 			args: {
	// 				from_date: frm.get_values().from_date,
	// 				to_date: frm.get_values().to_date,
	// 				employee: frm.get_values().employee,
	// 				company: frm.get_values().company,
	// 				department: frm.get_values().department,
	// 				// sub_department: frm.get_values().sub_department,
	// 				report_name: frm.report_name
	// 			}/*,
	// 			callback: function(r) {
	// 				frappe.set_route("Form", "Budget Invoice", r.message)
	// 			},*/
	// 		});
	// 	});
	// }
}
