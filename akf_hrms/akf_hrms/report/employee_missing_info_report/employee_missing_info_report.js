// Mubashir Bashir 29-05-2025

frappe.query_reports["Employee Missing Info Report"] = {
	"filters": [
		{
			"label": __("Company"),
			"fieldtype": "Link",
			"fieldname": "company",
			"options": "Company",
			"width": 150,
			"reqd": 1,
			default: frappe.defaults.get_user_default("Company")			
		},		
		{
			"label": __("Branch"),
			"fieldtype": "Link",
			"fieldname": "branch",
			"options": "Branch",
			"width": 150,
		},
		{
			"label": __("Department"),
			"fieldtype": "Link",
			"fieldname": "department",
			"options": "Department",
			"width": 150,
		},
		{
			"label": __("Designation"),
			"fieldtype": "Link",
			"fieldname": "designation",
			"options": "Designation",
			"width": 150,
		},
		{
			"label": __("Employment Type"),
			"fieldtype": "Link",
			"fieldname": "employment_type",
			"options": "Employment Type",
			"width": 150,
		},	
		{
			"label": __("Employee"),
			"fieldtype": "Link",
			"fieldname": "employee",
			"options": "Employee",
			"width": 150,
		},	
	]
};
