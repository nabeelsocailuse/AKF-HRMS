// Developer Mubashir Bashir

frappe.query_reports["Attendance Leave Summary Report"] = {
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
			"fieldname":"branch",
			"label": __("Branch"),
			"fieldtype": "Link",
			"options": "Branch",
			"default": "Central Office"
		},
		{
			"fieldname":"department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department"
		},
		{
			"fieldname":"designation",
			"label": __("Designation"),
			"fieldtype": "Link",
			"options": "Designation"
		},
		{
			"fieldname":"employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee"
		},
		{
			"fieldname":"employment_type",
			"label": __("Employment Type"),
			"fieldtype": "Link",
			"options": "Employment Type"
		},
		// {
		// 	"fieldname": "month",
		// 	"label": __("Month"),
		// 	"fieldtype": "Select",
		// 	"options": [
		// 		{ "value": "1", "label": "January" },
		// 		{ "value": "2", "label": "February" },
		// 		{ "value": "3", "label": "March" },
		// 		{ "value": "4", "label": "April" },
		// 		{ "value": "5", "label": "May" },
		// 		{ "value": "6", "label": "June" },
		// 		{ "value": "7", "label": "July" },
		// 		{ "value": "8", "label": "August" },
		// 		{ "value": "9", "label": "September" },
		// 		{ "value": "10", "label": "October" },
		// 		{ "value": "11", "label": "November" },
		// 		{ "value": "12", "label": "December" }
		// 	],
		// 	"default": moment().month() + 1,
		// 	"reqd": 1,
		// 	on_change: function() {
		// 		const month = parseInt(frappe.query_report.get_filter_value('month'));
		// 		const dates = get_dates_for_month(month);
		// 		frappe.query_report.set_filter_value('from_date', dates.from_date);
		// 		frappe.query_report.set_filter_value('to_date', dates.to_date);
		// 	}
		// },
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": get_default_from_date(),
			"reqd": 1,
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": get_default_to_date(),
			"reqd": 1,
		}
	],

	onload: function(report) {
		if (frappe.user.has_role("Employee")) {
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "Employee",
					fieldname: ["name", "designation", "department", "branch", "employment_type"],
					filters: { user_id: frappe.session.user }
				},
				callback: function(response) {
					if (response && response.message) {
						const employee_id = response.message.name;
						const designation = response.message.designation;
						const department = response.message.department;
						const branch = response.message.branch;
						const employment_type = response.message.employment_type;

						report.set_filter_value("employee", employee_id);
						if (designation) {
							report.set_filter_value("designation", designation);
						}
						if (department) {
							report.set_filter_value("department", department);
						}
						if (branch) {
							report.set_filter_value("branch", branch);
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


// function get_dates_for_month(month) {
// 	const today = new Date();
// 	const year = today.getFullYear();
// 	let from_date, to_date;

// 	// If selected month is January (1), we need previous year's December for from_date
// 	if (month === 1) {
// 		from_date = moment(`${year-1}-12-21`).format('YYYY-MM-DD');
// 		to_date = moment(`${year}-01-20`).format('YYYY-MM-DD');
// 	}
// 	// If selected month is December (12), we need next year for to_date
// 	else if (month === 12) {
// 		from_date = moment(`${year}-11-21`).format('YYYY-MM-DD');
// 		to_date = moment(`${year+1}-12-20`).format('YYYY-MM-DD');
// 	}
// 	// For all other months
// 	else {
// 		from_date = moment(`${year}-${month-1}-21`).format('YYYY-MM-DD');
// 		to_date = moment(`${year}-${month}-20`).format('YYYY-MM-DD');
// 	}

// 	return { from_date, to_date };
// }


function get_default_from_date() {
	const today = new Date();
	const day = today.getDate();
	const month = today.getMonth();
	const year = today.getFullYear();

	let from_date;

	if (day > 20) {
		from_date = new Date(year, month, 22).toISOString().split("T")[0];
	} else {
		from_date = new Date(year, month - 1, 22).toISOString().split("T")[0];
	}

	console.log("Calculated from_date:", from_date);
	return from_date;
}

function get_default_to_date() {
	const today = new Date();
	const day = today.getDate();
	const month = today.getMonth();
	const year = today.getFullYear();

	let to_date;

	if (day > 20) {
		to_date = new Date(year, month + 1, 21).toISOString().split("T")[0];
	} else {
		to_date = new Date(year, month, 21).toISOString().split("T")[0];
	}

	console.log("Calculated to_date:", to_date);
	return to_date;
}