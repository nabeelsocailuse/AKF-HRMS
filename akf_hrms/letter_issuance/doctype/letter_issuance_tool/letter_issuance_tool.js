// Copyright (c) 2020, publisher and contributors
// For license information, please see license.txt
/*
@media screen {
.print-format {
	min-height: 0.0in;
	padding-top: 0.0in;
  	padding-left: 0.4in;
  	padding-right: 0.4in;
	padding-bottom: 0.0in;
	margin-top: 0mm;
  	margin-left: 1mm;
  	margin-right: 1mm;
	margin-bottom: 0mm;
}
}
@media print {
   .print-format {
	min-height: 0.0in;
	padding-top: 0.0in;
  	padding-left: 0.4in;
  	padding-right: 0.4in;
	padding-bottom: 0.0in;
	margin-top: 0mm;
  	margin-left: 1mm;
  	margin-right: 1mm;
	margin-bottom: 0mm;
}
*/
frappe.ui.form.on('Letter Issuance Tool', {
	onload: function(frm) {
		$(".primary-action").hide();
		const doctype = frm.doc.reference_doctype;
		if (doctype) {
			frappe.model.with_doctype(doctype, () => set_field_options(frm));
		} else {
			reset_filter_and_field(frm);
		}
		cur_frm.set_value('reference_doctype', 'Employee');
		refresh_field('reference_doctype');
	},

	reference_doctype: frm => {
		const doctype = frm.doc.reference_doctype;
		if (doctype) {
			frappe.model.with_doctype(doctype, () => set_field_options(frm));
		} else {
			reset_filter_and_field(frm);
		}
	},

	refresh: function(frm) {
		frm.fields_dict.get_employees.$input.addClass(' btn btn-primary');
		frm.fields_dict.send_email.$input.addClass(' btn btn-primary');
	},
	get_employees:(frm)=>{
		erpnext.get_employees.get_employees_data(frm);
	},
	send_email:(frm)=>{
		erpnext.issuance_tool.issuance_tool_email_function(frm);
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
});

erpnext.issuance_tool = {
	issuance_tool_email_function: function (frm) {
		if (frm.doc.employees && frm.doc.letter_template && frm.doc.print_format && frm.doc.type && frm.doc.series)
		{
			frappe.call({
				method: "akf_hrms.letter_issuance.doctype.letter_issuance_tool.letter_issuance_tool.issuance_tool_function",
				async: false,
				args:{
					"series": frm.doc.series,
					"employees": frm.doc.employees,
					"letter_template": frm.doc.letter_template,
					"letter_head": frm.doc.letter_head,
					"attach_to_employee" : frm.doc.attach_to_employee,
					"print_format" : frm.doc.print_format,
					"type_" : frm.doc.type,
					"bulk_download" : frm.doc.bulk_download
				},
				callback: function (r) {
					if (frm.doc.type == 'PDF' || frm.doc.type == 'Email and PDF'){
						for (var a=0; a< r.message.length; a++){
							var url = String(window.location.origin) +`/api/method/frappe.utils.print_format.download_multi_pdf?doctype=Employee Letter&name=[`
							for (var x=0; x < r.message[a].length; x++){
								url+= `"` + r.message[a][x] + `"`
								if (x+1 != r.message[a].length){
									url+= `,`
								}
							}
							url += `]&format=` + String(frm.doc.print_format) + `&`
							if (frm.doc.letter_head){
								url += `no_letterhead=0`
							}
							else{
								url += `no_letterhead=1`	
							}
							console.log(url);
							window.open(url);
						}
					}
				}
			});
		}
	}
},

erpnext.get_employees = {
	get_employees_data: function (frm) {
		//console.log(frm.filter_list);
		console.log(frm.filter_list.get_filters().map(filter => filter.slice(1, 4)));
		var filter_list_arr = frm.filter_list.get_filters().map(filter => filter.slice(1, 4))

		frm.set_value("employees" ,"");
		frappe.call({
			method: "akf_hrms.letter_issuance.doctype.letter_issuance_tool.letter_issuance_tool.get_employees_data",
			async: false,
			args:{
				"company":frm.doc.company,
				"branch":frm.doc.branch,
				"designation":frm.doc.designation,
				"department":frm.doc.department,
				"args_value":filter_list_arr
			},
			callback: function (response) {
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


const can_export = frm => {
	const doctype = frm.doc.reference_doctype;
	let is_valid_form = false;
	if (!doctype) {
		frappe.msgprint(__('Please select the Document Type.'));
	} else if (!parent_multicheck_options.length) {
		frappe.msgprint(__('Atleast one field of Parent Document Type is mandatory'));
	} else {
		is_valid_form = true;
	}
	return is_valid_form;
};

const export_data = frm => {
	let get_template_url = '/api/method/frappe.core.doctype.data_export.exporter.export_data';
	var export_params = () => {
		let columns = {};
		return {
			doctype: frm.doc.reference_doctype,
			select_columns: JSON.stringify(columns),
			filters: frm.filter_list.get_filters().map(filter => filter.slice(1, 4)),
			file_type: frm.doc.file_type,
			template: true,
			with_data: 1
		};
	};

	open_url_post(get_template_url, export_params());
};

const reset_filter_and_field = (frm) => {
	const filter_wrapper = frm.fields_dict.filter_list.$wrapper;
	filter_wrapper.empty();
	frm.filter_list = [];
};

const set_field_options = (frm) => {
	const filter_wrapper = frm.fields_dict.filter_list.$wrapper;
	const doctype = frm.doc.reference_doctype;
	const related_doctypes = get_doctypes(doctype);

	filter_wrapper.empty();

	frm.filter_list = new frappe.ui.FilterGroup({
		parent: filter_wrapper,
		doctype: doctype,
		on_change: () => { },
	});
	frm.refresh();
};
const get_doctypes = parentdt => {
	return [parentdt].concat(
		frappe.meta.get_table_fields(parentdt).map(df => df.options)
	);
};
