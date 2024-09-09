// Copyright (c) 2024, Nabeel Saleem and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["HR Details Report"] = {
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
			"fieldname":"employee_id",
			"label": __("Employee ID"),
			"fieldtype": "Link",
			"options": "Employee"
		},
		{
			"fieldname":"branch",
			"label": __("Branch"),
			"fieldtype": "Link",
			"options": "Branch"
		},
		{
			"fieldname":"employee_status",
			"label": __("Employee Status"),
			"fieldtype": "Select",
			"options": "\nActive\nInactive\nSuspended\nLeft"
		},
		{
			"fieldname":"ssa",
			"label": __("Salary Structure Assignment"),
			"fieldtype": "Select",
			"options": "\nAssigned\nNot Assigned"
		},
	]
};