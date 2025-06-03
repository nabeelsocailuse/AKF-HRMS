// Mubashir Bashir, 14-05-2025

frappe.query_reports["Department Wise Salary Register"] = {
	"filters": [
		{
			"fieldname":"from_date",
			"label": __("From"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(),-1),
			"reqd": 1,
			"width": "100px"
		},
		{
			"fieldname":"to_date",
			"label": __("To"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1,
			"width": "100px"
		},
		{
			"fieldname": "currency",
			"fieldtype": "Link",
			"options": "Currency",
			"label": __("Currency"),
			"default": erpnext.get_currency(frappe.defaults.get_default("Company")),
			"width": "50px"
		},
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"width": "100px",
			"reqd": 1
		},
		{
			"fieldname":"branch",
			"label": __("Branch"),
			"fieldtype": "Link",
			"options": "Branch",
			"default": "",
			"width": "100px",
			"reqd": 0
		},
		{
			"fieldname":"department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department",
			"default": "",
			"width": "100px",
			"reqd": 0
		},
		{
			"fieldname":"designation",
			"label": __("Designation"),
			"fieldtype": "Link",
			"options": "Designation",
			"default": "",
			"width": "100px",
			"reqd": 0
		},
		{
			"fieldname":"employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": "100px"
		},
		{
			"fieldname":"docstatus",
			"label":__("Document Status"),
			"fieldtype":"Select",
			"options":["Draft", "Submitted", "Cancelled"],
			"default": "Submitted",
			"width": "100px"
		},
		// {
		// 	"fieldname":"non_taxable_component",
		// 	"label": __("Non Taxable Component"),
		// 	"fieldtype": "Check",
		// 	"width": "100px",
		// },
	]
}
