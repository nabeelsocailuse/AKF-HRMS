// Developer Mubashir Bashir

frappe.query_reports["Retention Rate"] = {
    "filters": [
        {
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_default("company"),
			reqd: 1
		},
        {
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Branch",
		},
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_days(frappe.datetime.nowdate(), -30),
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.nowdate(),
            "reqd": 1
        },
    ],
    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (data.is_bold) {
            // Apply bold styling to the row marked as is_bold
            value = `<b>${value}</b>`;
        }

        return value;
    }
};

