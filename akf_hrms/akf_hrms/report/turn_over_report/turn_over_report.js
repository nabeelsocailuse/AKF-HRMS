// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

// Mubashir Bashir

frappe.query_reports["Turn over report"] = {
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
			"fieldname":"duration",
			"label": __("Duration"),
			"fieldtype": "Select",
			"options": ["Monthly", "Biannually", "Annually"],
			"reqd": 1,
			on_change: function() {
				var start_date = frappe.datetime.month_start(frappe.datetime.nowdate()); 
				var end_date = frappe.datetime.month_end(frappe.datetime.nowdate());
				var duration_value = frappe.query_report.get_filter_value('duration')
				if (duration_value == "Monthly"){
					frappe.query_report.set_filter_value('from_date',start_date);
				}
				else if (duration_value == "Biannually"){
					var sub_months = frappe.datetime.add_months(start_date, -5); 
					frappe.query_report.set_filter_value('from_date',sub_months);
				}
				else{
					var sub_months = frappe.datetime.add_months(start_date, -11); 
					frappe.query_report.set_filter_value('from_date',sub_months);
				}
				frappe.query_report.set_filter_value('to_date',end_date);
			}
		},
		{
			"fieldname":"department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department"
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"reqd": 1,
			"hidden": 1
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"reqd": 1,
			"hidden": 1
		},
		{
			"fieldname":"status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": ["","Active", "Left"]
		}
	]
}
