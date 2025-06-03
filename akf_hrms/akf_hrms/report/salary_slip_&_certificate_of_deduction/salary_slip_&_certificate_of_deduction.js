// Mubashir Bashir 21-05-2025

frappe.query_reports["Salary Slip & Certificate of Deduction"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			fieldname: "employee_name",
			label: __("Employee Name"),
			fieldtype: "Data",
			hidden:1
		},
		{
			fieldname: "designation",
			label: __("Designation"),
			fieldtype: "Data",
			hidden:1
		},
		{
			fieldname: "cnic",
			label: __("CNIC"),
			fieldtype: "Data",
			hidden:1
		},
		{
			fieldname: "bank_name",
			label: __("Bank Name"),
			fieldtype: "Data",
			hidden:1
		},
		{
			fieldname: "bank_ac_no",
			label: __("Bank Ac No"),
			fieldtype: "Data",
			hidden:1
		},
		{
			fieldname: "hidden_year",
			label: __("Hidden Year"),
			fieldtype: "Data",
			hidden:1
		},
		{
			fieldname: "fiscal_year",
			label: __("Fiscal Year"),
			fieldtype: "Link",
			options: "Fiscal Year",
			reqd: 1,
			//default: frappe.sys_defaults.fiscal_year,
			on_change: function() {
				var a = String(frappe.query_report.get_filter_value('fiscal_year')).split("-")[0];
				var b = String(frappe.query_report.get_filter_value('fiscal_year')).split("-")[1];
				var c = String(a % 100) + "-" + String(b % 100);
				frappe.query_report.set_filter_value('hidden_year',c);
			}
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
			reqd: 1,
			get_query: function() {
				var company = frappe.query_report.get_filter_value('company');
				return {
					"doctype": "Employee",
					"filters": {
						"company": company,
					}
				}
			},
			on_change: function() {
				frappe.call({
					method: "akf_hrms.akf_hrms.report.salary_slip_&_certificate_of_deduction.employee_detail.emp_detail",
					args: {
						emp: frappe.query_report.get_filter_value('employee'),
					},
					callback: function(r) {
						frappe.query_report.set_filter_value('employee_name', r.message[0]);
						frappe.query_report.set_filter_value('designation', r.message[1]);
						frappe.query_report.set_filter_value('cnic', r.message[2]);
						frappe.query_report.set_filter_value('bank_name', r.message[3]);
						frappe.query_report.set_filter_value('bank_ac_no', r.message[4]);
					},
				});
			}
		}
	]
};
