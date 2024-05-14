// Copyright (c) 2020, publisher and contributors
// For license information, please see license.txt

frappe.ui.form.on('Letter Issuance Tool', {
	onload: function(frm) {
		$(".primary-action").hide();
	},
	refresh: function(frm) {
		frm.fields_dict.get_employees.$input.addClass(' btn btn-primary');
		frm.fields_dict.send_email.$input.addClass(' btn btn-primary');
		frm.fields_dict.print.$input.addClass(' btn btn-primary');
	},
	get_employees:(frm)=>{
		erpnext.get_employees.get_employees_data(frm);
		//$('.indicator').addClass('hide');
	},
	send_email:(frm)=>{
		erpnext.issuance_tool.issuance_tool_email_function(frm);
		//$('.indicator').addClass('hide');
	},
	print:(frm)=>{
		erpnext.issuance_tool.issuance_tool_print_function(frm);
		//$('.indicator').addClass('hide');
	},
	setup: function(frm) {
		frm.set_query("print_format", function() {
			return {
				filters: [
					['doc_type', '=', 'Employee Letter'],
				]
			}
		});
	}
});

erpnext.issuance_tool = {
	issuance_tool_email_function: function (frm) {
		if (frm.doc.series) { var series = frm.doc.series; } else { var series = '' }
		if (frm.doc.employees) { var employees = frm.doc.employees; } else { var employees = [] }
		if (frm.doc.letter_template) { var letter_template = frm.doc.letter_template; } else { var letter_template = "" }
		if (frm.doc.letter_head) { var letter_head = frm.doc.letter_head; } else { var letter_head = "" }
		if (frm.doc.attach_to_employee) { var attach_to_employee = frm.doc.attach_to_employee; } else { var attach_to_employee = "" }
		if (frm.doc.print_format) { var print_format = frm.doc.print_format; } else { var print_format = '' }
		
		frappe.call({
			method: "letter_issuance.letter_issuance.doctype.letter_issuance_tool.letter_issuance_tool.issuance_tool_function",
			async: false,
			args:{
				"series":series,
				"employees":employees,
				"letter_template":letter_template,
				"letter_head":letter_head,
				"send_email" : 1,
				"attach_to_employee" : attach_to_employee,
				"print_format" : print_format
			},
			callback: function (response) {
				console.log(response);
				if (response.message) {
					console.log(response.message);
					/* var response_arr = JSON.parse(response.message);
					console.log(response_arr);
					var i;
					for (i = 0; i < response_arr.length; i++) {
						console.log(response_arr[i]['employee']);
						//http://localhost/files/letters/GTR-00008-HR-EMP-00004.pdf
						//window.open('http://localhost/files/letters/GTR-00008-HR-EMP-00004.pdf')
					} */
				}
			}
		});
	},
	issuance_tool_print_function: function (frm) {
		if (frm.doc.series) { var series = frm.doc.series; } else { var series = '' }
		if (frm.doc.employees) { var employees = frm.doc.employees; } else { var employees = [] }
		if (frm.doc.letter_template) { var letter_template = frm.doc.letter_template; } else { var letter_template = "" }
		if (frm.doc.letter_head) { var letter_head = frm.doc.letter_head; } else { var letter_head = "" }
		if (frm.doc.attach_to_employee) { var attach_to_employee = frm.doc.attach_to_employee; } else { var attach_to_employee = "" }
		if (frm.doc.print_format) { var print_format = frm.doc.print_format; } else { var print_format = '' }
		frappe.call({
			method: "letter_issuance.letter_issuance.doctype.letter_issuance_tool.letter_issuance_tool.issuance_tool_function",
			async: false,
			args:{
				"series":series,
				"employees":employees,
				"letter_template":letter_template,
				"letter_head":letter_head,
				"send_email" : 0,
				"attach_to_employee" : attach_to_employee,
				"print_format" : print_format
			},
			callback: function (response) {
				console.log(response);
				if (response.message) {

				}
			}
		});
	}
},

erpnext.get_employees = {
	get_employees_data: function (frm) {
		//console.log("Department changed");
		if (frm.doc.company) { var company = frm.doc.company; } else { var company = "" }
		if (frm.doc.branch) { var branch = frm.doc.branch; } else { var branch = "" }
		if (frm.doc.designation) { var designation = frm.doc.designation; } else { var designation = "" }
		if (frm.doc.department) { var department = frm.doc.department; } else { var department = "" }
		if (frm.doc.employment_status) { var employment_status = frm.doc.employment_status; } else { var employment_status = "" }
		if (frm.doc.gender) { var gender = frm.doc.gender; } else { var gender = "" }


		if (frm.doc.joining_date_from) { var joining_date_from = frm.doc.joining_date_from; } else { var joining_date_from = "" }
		if (frm.doc.joining_date_to) { var joining_date_to = frm.doc.joining_date_to; } else { var joining_date_to = "" }
		if (frm.doc.relieving_date_from) { var relieving_date_from = frm.doc.relieving_date_from; } else { var relieving_date_from = "" }
		if (frm.doc.relieving_date_to) { var relieving_date_to = frm.doc.relieving_date_to; } else { var relieving_date_to = "" }
		if (frm.doc.date_of_birth_from) { var date_of_birth_from = frm.doc.date_of_birth_from; } else { var date_of_birth_from = "" }
		if (frm.doc.date_of_birth_to) { var date_of_birth_to = frm.doc.date_of_birth_to; } else { var date_of_birth_to = "" }

		frm.set_value("employees" ,"");
		frappe.call({
			method: "letter_issuance.letter_issuance.doctype.letter_issuance_tool.letter_issuance_tool.get_employees_data",
			async: false,
			args:{
				"company":company,
				"branch":branch,
				"designation":designation,
				"department":department,
				"employment_status":employment_status,
				"gender":gender,
				"joining_date_from":joining_date_from,
				"joining_date_to":joining_date_to,
				"relieving_date_from":relieving_date_from,
				"relieving_date_to":relieving_date_to,
				"date_of_birth_from":date_of_birth_from,
				"date_of_birth_to":date_of_birth_to,
			},
			callback: function (response) {
				console.log(response);
				if (response.message) {
					$.each(response.message, function(i, d) {
						var row = frappe.model.add_child(frm.doc, "Employee Letter Issuance Table", "employees");
						row.employee = d[0];
						row.full_name = d[1];
						row.user_id = d[2];
						row.designation = d[3];
						row.date_of_joining = d[4];
					});
				}
				refresh_field("employees");
			}
		});
	}
}
