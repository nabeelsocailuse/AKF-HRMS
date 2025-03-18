// Copyright (c) 2025, Nabeel Saleem and contributors
// For license information, please see license.txt

frappe.query_reports["EOBI Deduction Report"] = {
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
			"fieldname":"employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			get_query: () => {
				var company = frappe.query_report.get_filter_value("company");
				return {
					filters: {
						company: company,
					},
				};
			},
		},
		{
			"fieldname":"department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department",
			get_query: () => {
				var company = frappe.query_report.get_filter_value("company");
				return {
					filters: {
						company: company,
					},
				};
			},
		},
		{
			"fieldname":"fiscal_year",
			"label": __("Fiscal Year"),
			"fieldtype": "Link",
			"options": "Fiscal Year",
		},
	]
};
