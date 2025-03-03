// Copyright (c) 2025, Nabeel Saleem and contributors
// For license information, please see license.txt

frappe.query_reports["Non Taxable Earnings"] = {
	"filters": [

		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1
		},
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee"
		},
		{
			"fieldname": "start_date",
			"label": __("Start Date"),
			"fieldtype": "Date"
		},
		{
			"fieldname": "end_date",
			"label": __("End Date"),
			"fieldtype": "Date"
		}

	]
};
