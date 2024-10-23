
// Mubashir Bashir

frappe.query_reports["Manual Attendance Report"] = {
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
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"reqd": 1
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"reqd": 1
		},
		{
			"fieldname":"from_time",
			"label": __("From Time"),
			"fieldtype": "Time"
		},
		{
			"fieldname":"to_time",
			"label": __("To Time"),
			"fieldtype": "Time"
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
			"options": "\nPending\nApproved by the Line Manager\nRejected by the Line Manager\nApproved by the Head of Department\nRejected by the Head of Department\nApproved by the Executive Director\nRejected by the Executive Director"
		}
	],
};









