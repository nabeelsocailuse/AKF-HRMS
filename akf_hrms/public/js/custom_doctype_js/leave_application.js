// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on("Leave Application", {
	setup: function(frm) {
		frm.set_query("leave_approver", function() {
			return {
				query: "hrms.hr.doctype.department_approver.department_approver.get_approvers",
				filters: {
					employee: frm.doc.employee,
					doctype: frm.doc.doctype
				}
			};
		});

		frm.set_query("employee", erpnext.queries.employee);
	},

	onload: function(frm) {
		console.log('onload');
		
		// Ignore cancellation of doctype on cancel all.
		frm.ignore_doctypes_on_cancel_all = ["Leave Ledger Entry", "Attendance"];
		
		// Start, Nabeel Saleem, 02-12-2024
		frm.trigger("populateEmployeeIdBasedOnSelfService");
		// End, Nabeel Saleem, 02-12-2024
		if (!frm.doc.posting_date) {
			frm.set_value("posting_date", frappe.datetime.get_today());
		}
		if (frm.doc.docstatus == 0) {
			return frappe.call({
				method: "akf_hrms.overrides.leave_application.leave_application.get_mandatory_approval",
				args: {
					doctype: frm.doc.doctype,
				},
				callback: function(r) {
					if (!r.exc && r.message) {
						frm.toggle_reqd("leave_approver", true);
					}
				}
			});
		}

		clearFieldsOnLoad(frm); // Mubashir Bashir 13-03-2025
	},

	validate: function(frm) {
		if (frm.doc.from_date === frm.doc.to_date && cint(frm.doc.half_day)) {
			frm.doc.half_day_date = frm.doc.from_date;
		} else if (frm.doc.half_day === 0) {
			frm.doc.half_day_date = "";
		}
		frm.toggle_reqd("half_day_date", cint(frm.doc.half_day));
	},

	make_dashboard: function(frm) {
		let leave_details;
		let lwps;

		if (frm.doc.employee) {
			frappe.call({
				method: "akf_hrms.overrides.leave_application.leave_application.get_leave_details",
				async: false,
				
				args: {
					
					
					employee: frm.doc.employee,
					date: frm.doc.from_date || frm.doc.posting_date
				},
				callback: function(r) {
					if (!r.exc && r.message["leave_allocation"]) {
						leave_details = r.message["leave_allocation"];
					}
					// Nabeel Saleem, 18-12-2024
					// if (!r.exc && r.message["leave_approver"]) {}
					if (!r.exc && r.message["leave_approver"] && !("workflow_state" in frm.doc)) {
						frm.set_value("leave_approver", r.message["leave_approver"]);
					}
					lwps = r.message["lwps"];
				}
			});

			$("div").remove(".form-dashboard-section.custom");

			frm.dashboard.add_section(
				frappe.render_template("leave_application_dashboard", {
					data: leave_details
				}),
				__("Allocated Leaves")
			);
			frm.dashboard.show();

			let allowed_leave_types = Object.keys(leave_details);
			// lwps should be allowed for selection as they don't have any allocation
			allowed_leave_types = allowed_leave_types.concat(lwps);

			frm.set_query("leave_type", function() {
				return {
					filters: [
						["leave_type_name", "in", allowed_leave_types]
					]
				};
			});
		}
	},

	refresh: function(frm) {
		// start, nabeel saleem, 18-12-2024
		if("workflow_state" in frm.doc){
			frm.set_df_property('leave_approver', 'read_only', 1);
		}
		// end, nabeel saleem, 18-12-2024

		if (frm.is_new()) {
			frm.trigger("calculate_total_days");
			// nabeel saleem, 18-12-2024
			frm.set_value('custom_state_data', null);
		}

		frm.set_intro("");
		if (frm.doc.__islocal && !in_list(frappe.user_roles, "Employee")) {
			frm.set_intro(__("Fill the form and save it"));
		}

		frm.trigger("set_employee");
		frm.trigger("showWorkFlowState"); // Nabeel Saleem, 29-11-2024
	},

	async set_employee(frm) {
		if (frm.doc.employee) return;

		const employee = await hrms.get_current_employee(frm);
		if (employee) {
			frm.set_value("employee", employee);
		}
	},

	employee: function(frm) {		
		frm.trigger("make_dashboard");
		frm.trigger("get_leave_balance");
		//start, Nabeel Saleem, 29-11-2024
		if("workflow_state" in frm.doc){
			setTimeout(() => {
				frm.call("set_next_workflow_approver");
			}, 100);
		//end, Nabeel Saleem, 29-11-2024
		}else{
			frm.trigger("set_leave_approver");
		}
	},

	leave_approver: function(frm) {
		if (frm.doc.leave_approver) {
			frm.set_value("leave_approver_name", frappe.user.full_name(frm.doc.leave_approver));
		}
	},

	leave_type: function(frm) {
		short_half_leave_message(frm); // Mubashir Bashir 2-July-2025
		frm.trigger("get_leave_balance");
	},

	half_day: function(frm) {
		if (frm.doc.half_day) {
			if (frm.doc.from_date == frm.doc.to_date) {
				frm.set_value("half_day_date", frm.doc.from_date);
			} else {
				frm.trigger("half_day_datepicker");
			}
		} else {
			frm.set_value("half_day_date", "");
		}
		frm.trigger("calculate_total_days");
	},

	from_date: function(frm) {
		frm.trigger("make_dashboard");
		// frm.trigger("half_day_datepicker");
		// frm.trigger("calculate_total_days");
	},

	to_date: function(frm) {
		frm.trigger("make_dashboard");
		// frm.trigger("half_day_datepicker");
		// frm.trigger("calculate_total_days");
	},

	half_day_date(frm) {
		frm.trigger("calculate_total_days");
	},

	half_day_datepicker: function(frm) {
		frm.set_value("half_day_date", "");
		let half_day_datepicker = frm.fields_dict.half_day_date.datepicker;
		half_day_datepicker.update({
			minDate: frappe.datetime.str_to_obj(frm.doc.from_date),
			maxDate: frappe.datetime.str_to_obj(frm.doc.to_date)
		});
	},

	get_leave_balance: function(frm) {
		if (frm.doc.docstatus === 0 && frm.doc.employee && frm.doc.leave_type && frm.doc.from_date && frm.doc.to_date) {
			return frappe.call({
				method: "akf_hrms.overrides.leave_application.leave_application.get_leave_balance_on",
				args: {
					employee: frm.doc.employee,
					date: frm.doc.from_date,
					to_date: frm.doc.to_date,
					leave_type: frm.doc.leave_type,
					consider_all_leaves_in_the_allocation_period: 1
				},
				callback: function (r) {
					if (!r.exc && r.message) {
						frm.set_value("leave_balance", r.message);
					} else {
						frm.set_value("leave_balance", "0");
					}
				}
			});
		}
	},

	calculate_total_days: function(frm) {
		if (frm.doc.from_date && frm.doc.to_date && frm.doc.employee && frm.doc.leave_type) {
			let from_date = Date.parse(frm.doc.from_date);
			let to_date = Date.parse(frm.doc.to_date);

			if (to_date < from_date) {
				frappe.msgprint(__("To Date cannot be less than From Date"));
				frm.set_value("to_date", "");
				return;
			}
			// server call is done to include holidays in leave days calculations
			return frappe.call({
				method: "akf_hrms.overrides.leave_application.leave_application.get_number_of_leave_days",
				args: {
					"employee": frm.doc.employee,
					"leave_type": frm.doc.leave_type,
					"from_date": frm.doc.from_date,
					"to_date": frm.doc.to_date,
					"half_day": frm.doc.half_day,
					"half_day_date": frm.doc.half_day_date,
				},
				callback: function(r) {
					if (r && r.message) {
						frm.set_value("total_leave_days", r.message);
						frm.trigger("get_leave_balance");
					}
				}
			});
		}
	},

	set_leave_approver: function(frm) {
		if (frm.doc.employee) {
			return frappe.call({
				method: "akf_hrms.overrides.leave_application.leave_application.get_leave_approver",
				args: {
					"employee": frm.doc.employee,
				},
				callback: function(r) {
					if (r && r.message) {
						frm.set_value("leave_approver", r.message);
					}
				}
			});
		}
	},
	// Start, Mubashir Bashir, 11-02-2025
	showWorkFlowState: function(frm){
		if(frm.doc.custom_state_data==undefined) {
			frm.set_df_property('custom_state_html', 'options', '<p></p>')
		}else{
			const stateObj = JSON.parse(frm.doc.custom_state_data)
			
			const desiredOrder = [
				"Applied",
				"Recommended By Line Manager",
				"Rejected By Line Manager",
				"Recommended By Head Of Department",
				"Rejected By Head Of Department",
				"Recommended by Chief Executive Officer",
				"Rejected by Chief Executive Officer",
				"Approved",
				"Rejected By Secretary General"
			];

			const orderedStates = desiredOrder
				.filter(state => stateObj.hasOwnProperty(state)) 
				.map(state => ({ key: state, ...stateObj[state] })); 
			

			let rows = ``;
			let idx = 1
			for (const data of orderedStates) {
				const dt = moment(data.modified_on).format("DD-MM-YYYY hh:mm:ss a");

				rows += `
				<tr>
					<th scope="row">${idx}</th>	
					<td scope="row">${data.employee_name}</td>
					<td scope="row">${data.current_state}</td>
					<td class="">${dt}</td>
					<td class="">${data.next_state}</td>
					
				</tr>`;
				idx += 1;
			}
			let _html_ = `
			<table class="table">
				<thead class="thead-dark">
					<tr>
					<th scope="col">#</th>
					<th class="text-left" scope="col">Employee Name</th>
					<th class="text-left" scope="col">Current State</th>
					<th class="text-left" scope="col">DateTime</th>
					<th scope="col">Next State(Employee Name, Role)</th>
					</tr>
				</thead>
				<tbody>
					${rows}
				</tbody>
			</table>`;
			frm.set_df_property('custom_state_html', 'options', _html_)
		}
	},
	// End, Mubashir Bashir, 11-02-2025
	
	// Start, Nabeel Saleem, 02-12-2024
	populateEmployeeIdBasedOnSelfService: function(frm){
		if (frappe.user.has_role("Employee") && frm.doc.employee == undefined) {
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "Employee",
					fieldname: "name",
					filters: { user_id: frappe.session.user }
				},
				callback: function (response) {
					if (response && response.message) {
						const employee_id = response.message.name;
						frm.set_value("employee", employee_id);
						console.log("Employee field populated with ID:", employee_id);

						// After setting employee, check for shift assignment
						// frm.trigger("check_shift_assignment");
					} else {
						console.log("No employee found for the current user.");
					}
				}
			});
		}
	}
	// End, Nabeel Saleem, 02-12-2024
});

// Mubashir Bashir 13-03-2025 Start
function clearFieldsOnLoad(frm) {
    if (frm.is_new()) {
        frm.set_value('custom_next_workflow_state', '');
        frm.set_value('custom_workflow_indication', '');
        frm.set_value('custom_state_data', '');
        frm.set_value('custom_state_html', '');
    }
}
// Mubashir Bashir 13-03-2025 End

// Mubashir Bashir 2-July-2025
function short_half_leave_message(frm) {
    if (['Short Leave', 'Half Day Leave'].includes(frm.doc.leave_type)) {
        frm.set_df_property('leave_type', 'description', '<span style="color: #0c5ebd;">Short Leave and Half Day Leave are allocated annually but can only be availed once per month.</span>');
    } else {
        frm.set_df_property('leave_type', 'description', '');
    }
}
  

frappe.tour["Leave Application"] = [
	{
		fieldname: "employee",
		title: "Employee",
		description: __("Select the Employee.")
	},
	{
		fieldname: "leave_type",
		title: "Leave Type",
		description: __("Select type of leave the employee wants to apply for, like Sick Leave, Privilege Leave, Casual Leave, etc.")
	},
	{
		fieldname: "from_date",
		title: "From Date",
		description: __("Select the start date for your Leave Application.")
	},
	{
		fieldname: "to_date",
		title: "To Date",
		description: __("Select the end date for your Leave Application.")
	},
	{
		fieldname: "half_day",
		title: "Half Day",
		description: __("To apply for a Half Day check 'Half Day' and select the Half Day Date")
	},
	{
		fieldname: "leave_approver",
		title: "Leave Approver",
		description: __("Select your Leave Approver i.e. the person who approves or rejects your leaves.")
	}
];
