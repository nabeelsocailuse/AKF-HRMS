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
/////////////////////////////////////////////////////////////////
		frm.chart_filters = null;
		frm.set_value('filters_json', '{}');
		frm.trigger('update_options');
/////////////////////////////////////////////////////////////////
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
	},
///////////////////////////////////////////////////////////////////

	update_options: function(frm) {
		let doctype = "Employee";
		let date_fields = [
			{label: __('Created On'), value: 'creation'},
			{label: __('Last Modified On'), value: 'modified'}
		];
		let value_fields = [];
		let group_by_fields = [];
		let aggregate_function_fields = [];
		let update_form = function() {
			frm.trigger("show_filters");
		}


		if (doctype) {
			frappe.model.with_doctype(doctype, () => {
				// get all date and datetime fields
				frappe.get_meta(doctype).fields.map(df => {
					if (['Date', 'Datetime'].includes(df.fieldtype)) {
						date_fields.push({label: df.label, value: df.fieldname});
					}
					if (['Int', 'Float', 'Currency', 'Percent'].includes(df.fieldtype)) {
						value_fields.push({label: df.label, value: df.fieldname});
						aggregate_function_fields.push({label: df.label, value: df.fieldname});
					}
					if (['Link', 'Select'].includes(df.fieldtype)) {
						group_by_fields.push({label: df.label, value: df.fieldname});
					}
				});
				update_form();
			});
		} else {
			// update select options
			update_form();
		}

	},

	show_filters: function(frm) {
		if (frm.chart_filters && frm.chart_filters.length) {
			frm.trigger('render_filters_table');
		} else {
			// standard filters
			frappe.model.with_doctype("Employee", () => {
				frm.chart_filters = [];
				frappe.get_meta("Employee").fields.map(df => {
					if (['Link', 'Select'].includes(df.fieldtype)) {
						let _df = copy_dict(df);

						// nothing is mandatory
						_df.reqd = 0;
						_df.default = null;
						_df.depends_on = null;
						_df.read_only = 0;
						_df.permlevel = 1;
						_df.hidden = 0;

						frm.chart_filters.push(_df);
					}
				});
				frm.trigger('render_filters_table');
			});
		}
	},

	render_filters_table: function(frm) {
		frm.set_df_property("filters_section", "hidden", 0);
		let fields = frm.chart_filters;

		let wrapper = $(frm.get_field('filters_json').wrapper).empty();
		let table = $(`<table class="table table-bordered" style="cursor:pointer; margin:0px;">
			<thead>
				<tr>
					<th style="width: 50%">${__('Filter')}</th>
					<th>${__('Value')}</th>
				</tr>
			</thead>
			<tbody></tbody>
		</table>`).appendTo(wrapper);
		$(`<p class="text-muted small">${__("Click table to edit")}</p>`).appendTo(wrapper);

		let filters = JSON.parse(frm.doc.filters_json || '{}');
		var filters_set = false;
		fields.map(f => {
			if (filters[f.fieldname]) {
				const filter_row = $(`<tr><td>${f.label}</td><td>${filters[f.fieldname] || ""}</td></tr>`);
				table.find('tbody').append(filter_row);
				filters_set = true;
			}
		});

		if (!filters_set) {
			const filter_row = $(`<tr><td colspan="2" class="text-muted text-center">
				${__("Click to Set Filters")}</td></tr>`);
			table.find('tbody').append(filter_row);
		}

		table.on('click', () => {
			let dialog = new frappe.ui.Dialog({
				title: __('Set Filters'),
				fields: fields,
				primary_action: function() {
					let values = this.get_values();
					if(values) {
						this.hide();
						frm.set_value('filters_json', JSON.stringify(values));
						frm.trigger('show_filters');
					}
				},
				primary_action_label: "Set"
			});
			dialog.show();
			dialog.set_values(filters);
			frappe.dashboards.filters_dialog = dialog;
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

		console.log(frm.doc.filters_json);

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
