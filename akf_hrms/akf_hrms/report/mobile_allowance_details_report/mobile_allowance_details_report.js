// Developer Mubashir Bashir

frappe.query_reports["Mobile Allowance Details Report"] = {
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
			"fieldname":"employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			// "reqd": 1
		},
		{
			"fieldname":"designation",
			"label": __("Designation"),
			"fieldtype": "Link",
			"options": "Designation"
		},
		{
			"fieldname":"department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department"
		},
		{
			"fieldname":"employment_type",
			"label": __("Employment Type"),
			"fieldtype": "Link",
			"options": "Employment Type"
		},
		{
			"fieldname":"grade",
			"label": __("Employee Grade"),
			"fieldtype": "Link",
			"options": "Employee Grade"
		},
		// {
		// 	"label": "Date",
		// 	"fieldtype": "Date",
		// 	"fieldname": "date",
		// 	"default": frappe.datetime.nowdate("dd-mm-yyyy"),
		// 	"reqd": 0,
		// },
	],	
	
	onload: function(report) {
		if (frappe.user.has_role("Employee")) {
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "Employee",
					fieldname: ["name", "designation", "department", "employment_type", "grade"],
					filters: { user_id: frappe.session.user }
				},
				callback: function(response) {
					if (response && response.message) {
						const employee_id = response.message.name;
						const designation = response.message.designation;
						const department = response.message.department;
						const grade = response.message.grade;
						const employment_type = response.message.employment_type;

						report.set_filter_value("employee", employee_id);
						if (designation) {
							report.set_filter_value("designation", designation);
						}
						if (department) {
							report.set_filter_value("department", department);
						}
						if (grade) {
							report.set_filter_value("grade", grade);
						}
						if (employment_type) {
							report.set_filter_value("employment_type", employment_type);
						}
					}
				}
			});
		}
	}
};

