// This doctype is included from hr to akf_hrms by Mubashir on 27-01-2025

frappe.ui.form.on('Staffing Plan', {
	setup: function(frm) {
		frm.set_query("designation", "staffing_details", function() {
			let designations = [];
			(frm.doc.staffing_details || []).forEach(function(staff_detail) {
				if(staff_detail.designation){
					designations.push(staff_detail.designation)
				}
			})
			// Filter out designations already selected in Staffing Plan Detail
			return {
				filters: [
					['Designation', 'name', 'not in', designations],
				]
			}
		});

		frm.set_query("department", function() {
			return {
				"filters": {
					"company": frm.doc.company,
				}
			};
		});
	},

	// Mubashir 29-01-25 Start
	onload: function(frm) {
		// Run set_number_of_positions for each row in staffing_details on load
        if (!frm.is_new() && frm.doc.staffing_details && frm.doc.staffing_details.length > 0) {
			frm.doc.staffing_details.forEach(function(child) {
				set_number_of_positions(frm, child.doctype, child.name);
				frm.save();
            });
        }
    },
	// Mubashir 29-01-25 End

	get_job_requisitions: function(frm) {
		new frappe.ui.form.MultiSelectDialog({
			doctype: "Job Requisition",
			target: frm,
			date_field: "posting_date",
			add_filters_group: 1,
			setters: {
				designation: null,
				requested_by: null,
			},
			get_query() {
				let filters = {
					company: frm.doc.company,
					status: ["in", ["Pending", "Open & Approved"]],
				}

				if (frm.doc.department)
					filters.department = frm.doc.department;

				return {
					filters: filters
				};
			},
			action(selections) {
				const plan_name = frm.doc.__newname;
				frappe.call({
					method: "set_job_requisitions",
					doc: frm.doc,
					args: selections,
				}).then(() => {
					// hack to retain prompt name that gets lost on frappe.call
					frm.doc.__newname = plan_name;
					refresh_field("staffing_details");
				});

				cur_dialog.hide();
			}
		});
	}
});

frappe.ui.form.on('Staffing Plan Detail', {
	designation: function(frm, cdt, cdn) {
		let child = locals[cdt][cdn];
		if(frm.doc.company && child.designation) {
			set_number_of_positions(frm, cdt, cdn);
		}
	},

	vacancies: function(frm, cdt, cdn) {
		let child = locals[cdt][cdn];
		if(child.vacancies < child.current_openings) {
			frappe.throw(__("Vacancies cannot be lower than the current openings"));
		}
		set_number_of_positions(frm, cdt, cdn);
	},

	current_count: function(frm, cdt, cdn) {
		set_number_of_positions(frm, cdt, cdn);
	},

	estimated_cost_per_position: function(frm, cdt, cdn) {
		set_total_estimated_cost(frm, cdt, cdn);
	}
});

var set_number_of_positions = function(frm, cdt, cdn) {
	console.log("set number of positions running...");
	
	let child = locals[cdt][cdn];
	if (!child.designation) frappe.throw(__("Please enter the designation"));
	frappe.call({
		"method": "akf_hrms.akf_hrms.doctype.staffing_plan.staffing_plan.get_designation_counts",
		args: {
			designation: child.designation,
			company: frm.doc.company,
			department: frm.doc.department
		},
		callback: function (data) {
			if(data.message){
				frappe.model.set_value(cdt, cdn, 'current_count', data.message.employee_count);
				frappe.model.set_value(cdt, cdn, 'current_openings', data.message.job_openings);
				let total_positions = cint(data.message.employee_count) + cint(child.vacancies);
				if (cint(child.number_of_positions) < total_positions){
					frappe.model.set_value(cdt, cdn, 'number_of_positions', total_positions);
				}
			}
			else{ // No employees for this designation
				frappe.model.set_value(cdt, cdn, 'current_count', 0);
				frappe.model.set_value(cdt, cdn, 'current_openings', 0);
			}
		}
	});
	refresh_field("staffing_details");
	set_total_estimated_cost(frm, cdt, cdn);
}

// Note: Estimated Cost is calculated on number of Vacancies
var set_total_estimated_cost = function(frm, cdt, cdn) {
	let child = locals[cdt][cdn]
	if(child.vacancies > 0 && child.estimated_cost_per_position) {
		frappe.model.set_value(cdt, cdn, 'total_estimated_cost', child.vacancies * child.estimated_cost_per_position);
	}
	else {
		frappe.model.set_value(cdt, cdn, 'total_estimated_cost', 0);
	}
	set_total_estimated_budget(frm);
};

var set_total_estimated_budget = function(frm) {
	let estimated_budget = 0.0
	if(frm.doc.staffing_details) {
		(frm.doc.staffing_details || []).forEach(function(staff_detail) {
			if(staff_detail.total_estimated_cost){
				estimated_budget += staff_detail.total_estimated_cost
			}
		})
		frm.set_value('total_estimated_budget', estimated_budget);
	}
};
