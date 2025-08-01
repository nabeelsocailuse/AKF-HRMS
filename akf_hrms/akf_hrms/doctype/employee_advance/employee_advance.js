frappe.ui.form.on('Employee Advance', {
	setup: function(frm) {
		frm.set_query("employee", function() {
			return {
				filters: {
					"status": "Active"
				}
			};
		});

		frm.set_query("advance_account", function() {
			if (!frm.doc.employee) {
				frappe.msgprint(__("Please select employee first"));
			}
			let company_currency = erpnext.get_currency(frm.doc.company);
			let currencies = [company_currency];
			if (frm.doc.currency && (frm.doc.currency != company_currency)) {
				currencies.push(frm.doc.currency);
			}

			return {
				filters: {
					"root_type": "Asset",
					"is_group": 0,
					"company": frm.doc.company,
					"account_currency": ["in", currencies],
				}
			};
		});

		frm.set_query('salary_component', function() {
			return {
				filters: {
					"type": "Deduction"
				}
			};
		});
	},

	refresh: function(frm) {
		if (frm.doc.docstatus === 1 &&
			(flt(frm.doc.paid_amount) < flt(frm.doc.advance_amount)) &&
			frappe.model.can_create("Payment Entry")) {
			frm.add_custom_button(__('Payment'),
				function () {
					frm.events.make_payment_entry(frm);
				}, __('Create'));
		} else if (
			frm.doc.docstatus === 1 &&
			flt(frm.doc.claimed_amount) < flt(frm.doc.paid_amount) - flt(frm.doc.return_amount) &&
			frappe.model.can_create("Expense Claim")
		) {
			frm.add_custom_button(
				__("Expense Claim"),
				function () {
					frm.events.make_expense_claim(frm);
				},
				__('Create')
			);
		}

		if (
			frm.doc.docstatus === 1
			&& (flt(frm.doc.claimed_amount) < flt(frm.doc.paid_amount) - flt(frm.doc.return_amount))
		) {
			if (frm.doc.repay_unclaimed_amount_from_salary == 0 && frappe.model.can_create("Journal Entry")) {
				frm.add_custom_button(__("Return"), function() {
					frm.trigger('make_return_entry');
				}, __('Create'));
			} else if (frm.doc.repay_unclaimed_amount_from_salary == 1 && frappe.model.can_create("Additional Salary")) {
				frm.add_custom_button(__("Deduction from Salary"), function() {
					frm.events.make_deduction_via_additional_salary(frm);
				}, __('Create'));
			}
		}

        frm.trigger("showWorkFlowState"); // Mubashir Bashir 19-06-2025
	},

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
				"Approved",
				"Rejected By Finance"
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

	make_deduction_via_additional_salary: function(frm) {
		frappe.call({
			method: "akf_hrms.akf_hrms.doctype.employee_advance.employee_advance.create_return_through_additional_salary",
			args: {
				doc: frm.doc
			},
			callback: function(r) {
				var doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			}
		});
	},

	make_payment_entry: function(frm) {
		let method = "hrms.overrides.employee_payment_entry.get_payment_entry_for_employee";
		if (frm.doc.__onload && frm.doc.__onload.make_payment_via_journal_entry) {
			method = "akf_hrms.akf_hrms.doctype.employee_advance.employee_advance.make_bank_entry";
		}
		return frappe.call({
			method: method,
			args: {
				"dt": frm.doc.doctype,
				"dn": frm.doc.name
			},
			callback: function(r) {
				var doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			}
		});
	},

	make_expense_claim: function(frm) {
		return frappe.call({
			method: "hrms.hr.doctype.expense_claim.expense_claim.get_expense_claim",
			args: {
				"employee_name": frm.doc.employee,
				"company": frm.doc.company,
				"employee_advance_name": frm.doc.name,
				"posting_date": frm.doc.posting_date,
				"paid_amount": frm.doc.paid_amount,
				"claimed_amount": frm.doc.claimed_amount
			},
			callback: function(r) {
				const doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			}
		});
	},

	make_return_entry: function(frm) {
		frappe.call({
			method: 'akf_hrms.akf_hrms.doctype.employee_advance.employee_advance.make_return_entry',
			args: {
				'employee': frm.doc.employee,
				'company': frm.doc.company,
				'employee_advance_name': frm.doc.name,
				'return_amount': flt(frm.doc.paid_amount - frm.doc.claimed_amount),
				'advance_account': frm.doc.advance_account,
				'mode_of_payment': frm.doc.mode_of_payment,
				'currency': frm.doc.currency,
				'exchange_rate': frm.doc.exchange_rate
			},
			callback: function(r) {
				const doclist = frappe.model.sync(r.message);
				frappe.set_route('Form', doclist[0].doctype, doclist[0].name);
			}
		});
	},

	employee: function(frm) {
		if (frm.doc.employee) {
			frappe.run_serially([
				() => frm.trigger('get_employee_currency'),
				() => frm.trigger('get_pending_amount')
			]);
		}
	},

	get_pending_amount: function(frm) {
		frappe.call({
			method: "akf_hrms.akf_hrms.doctype.employee_advance.employee_advance.get_pending_amount",
			args: {
				"employee": frm.doc.employee,
				"posting_date": frm.doc.posting_date
			},
			callback: function(r) {
				frm.set_value("pending_amount", r.message);
			}
		});
	},

	get_employee_currency: function(frm) {
		frappe.call({
			method: "hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment.get_employee_currency",
			args: {
				employee: frm.doc.employee,
			},
			callback: function(r) {
				if (r.message) {
					frm.set_value('currency', r.message);
					frm.refresh_fields();
				}
			}
		});
	},

	currency: function(frm) {
		if (frm.doc.currency) {
			var from_currency = frm.doc.currency;
			var company_currency;
			if (!frm.doc.company) {
				company_currency = erpnext.get_currency(frappe.defaults.get_default("Company"));
			} else {
				company_currency = erpnext.get_currency(frm.doc.company);
			}
			if (from_currency != company_currency) {
				frm.events.set_exchange_rate(frm, from_currency, company_currency);
			} else {
				frm.set_value("exchange_rate", 1.0);
				frm.set_df_property('exchange_rate', 'hidden', 1);
				frm.set_df_property("exchange_rate", "description", "");
			}
			frm.refresh_fields();
		}
	},

	set_exchange_rate: function(frm, from_currency, company_currency) {
		frappe.call({
			method: "erpnext.setup.utils.get_exchange_rate",
			args: {
				from_currency: from_currency,
				to_currency: company_currency,
			},
			callback: function(r) {
				frm.set_value("exchange_rate", flt(r.message));
				frm.set_df_property('exchange_rate', 'hidden', 0);
				frm.set_df_property("exchange_rate", "description", "1 " + frm.doc.currency +
					" = [?] " + company_currency);
			}
		});
	}
});
