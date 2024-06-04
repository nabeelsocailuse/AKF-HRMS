// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Employment History Report"] = {
	filters: [
	  {
		fieldname: "company",
		label: __("Company"),
		fieldtype: "Link",
		options: "Company",
		reqd:1,  //Make the company filter mandatory
	  },
	  {
		fieldname: "employee",
		label: __("Employee"),
		fieldtype: "Link",
		options: "Employee",
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
		fieldname: "status",
		label: __("Status"),
		fieldtype: "Select",
		options: ["","Active","Inactive","Suspended","Left"],
	  },
	],
  };
  