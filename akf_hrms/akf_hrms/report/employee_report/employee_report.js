// Mubashir Bashir

frappe.query_reports["Employee Report"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1
		},
		// {
		// 	"fieldname":"from_date",
		// 	"label": __("From Date"),
		// 	"fieldtype": "Date",
		// 	"reqd": 1
		// },
		// {
		// 	"fieldname":"to_date",
		// 	"label": __("To Date"),
		// 	"fieldtype": "Date",
		// 	"reqd": 1
		// },
		{
			"fieldname":"region",
			"label": __("Region"),
			"fieldtype": "Link",
			"options": "Region"
		},
		{
			"fieldname":"branch",
			"label": __("Branch"),
			"fieldtype": "Link",
			"options": "Branch"
		},
		{
			"fieldname":"department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department"
		},
		{
			"fieldname":"employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee"
		},
		{
			"fieldname":"status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "Active\nInactive\nSuspended\nLeft"
		}
	],
};
