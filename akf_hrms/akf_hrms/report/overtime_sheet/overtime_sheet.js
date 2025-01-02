// Copyright (c) 2024, Nabeel Saleem and contributors
// For license information, please see license.txt

frappe.query_reports["Overtime Sheet"] = {
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
			"fieldname":"month",
			"label": __("Period Covered"),
			"fieldtype": "Select",
			"options": [
                { value: "January", label: __("January") },
                { value: "February", label: __("February") },
                { value: "March", label: __("March") },
                { value: "April", label: __("April") },
                { value: "May", label: __("May") },
                { value: "June", label: __("June") },
                { value: "July", label: __("July") },
                { value: "August", label: __("August") },
                { value: "September", label: __("September") },
                { value: "October", label: __("October") },
                { value: "November", label: __("November") },
                { value: "December", label: __("December") }
            ],
			"reqd": 1
		},
	],
	onload: function (report) {
        // Get the current month name
        const currentMonth = new Date().toLocaleString('default', { month: 'long' });

        // Set the default value for the month filter
        frappe.query_report.set_filter_value("month", currentMonth);
    }
};
