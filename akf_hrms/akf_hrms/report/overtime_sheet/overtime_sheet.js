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
			"fieldname":"year",
			"label": __("Year"),
			"fieldtype": "Select",
			"options": [
                { value: "2024", label: __("2024") },
                { value: "2025", label: __("2025") },
                { value: "2026", label: __("2026") },
                { value: "2027", label: __("2027") },
                { value: "2028", label: __("2028") },
                { value: "2029", label: __("2029") },
                { value: "2030", label: __("2030") },
                { value: "2031", label: __("2031") },
                { value: "2032", label: __("2032") },
                { value: "2033", label: __("2033") },
                { value: "2034", label: __("2034") },
                { value: "2035", label: __("2035") }
            ],
			"default": "2025",
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
