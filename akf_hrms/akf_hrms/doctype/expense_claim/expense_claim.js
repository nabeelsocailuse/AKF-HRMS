// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.provide("hrms.hr");
frappe.provide("erpnext.accounts.dimensions");

frappe.ui.form.on('Expense Claim', {
    onload: function (frm) {
        erpnext.accounts.dimensions.setup_dimension_filters(frm, frm.doctype);

        // if (!frm.doc.employee && !frm.doc.expense_approver) {
        //     frappe.throw(__('Please select Employee and Approver first'));
        //     return;
        // }
    },

    company: function (frm) {
        erpnext.accounts.dimensions.update_dimension(frm, frm.doctype);
        var expenses = frm.doc.expenses;
        for (var i = 0; i < expenses.length; i++) {
            var expense = expenses[i];
            if (!expense.expense_type) {
                continue;
            }

            frappe.call({
                method: "hrms.hr.doctype.expense_claim.expense_claim.get_expense_claim_account_and_cost_center",
                args: {
                    "expense_claim_type": expense.expense_type,
                    "company": frm.doc.company
                },
                callback: function (r) {
                    if (r.message) {
                        expense.default_account = r.message.account;
                        expense.cost_center = r.message.cost_center;
                    }
                }
            });
        }
    },
    employee: function (frm) {

        if (!frm.doc.grade) {
            frappe.throw(__('Grade is not set. Please provide a valid grade to proceed with the validation.'));
            return;
        }
    },
    // nabeel saleem, 19-12-2024 > start
    ownership: function(frm){
        if(!frm.doc.ownership){
            frm.set_value('vehicle', null);
            frm.set_value('expense_rate', 0);
            frm.set_value('kilometers', 0);

            // Mubashir Bashir 24-12-2024 Start    
            // Remove Vehicle Expense row from child expense if any         
            const rows_to_remove = frm.doc.expenses.filter(row => row.expense_type === 'Vehicle Expense');
            rows_to_remove.forEach(row => {frm.get_field('expenses').grid.grid_rows_by_docname[row.name].remove();});
            frm.refresh_field('expenses');

            // frm.set_df_property('kilometers', 'hidden', 1);
            // frm.set_df_property('kilometers', 'reqd', 0);
            // Mubashir Bashir 24-12-2024 End
        }
    },
    // nabeel saleem, 19-12-2024 > end

    // Mubashir Bashir 24-12-2024 Start
    kilometers: function (frm) {
        if (frm.doc.kilometers) {            
            const expense_rate = frm.doc.expense_rate || 0;
            const kilometers = frm.doc.kilometers;
            const amount = expense_rate * kilometers;

            // Remove empty rows or Vehicle Expense rows
            if (frm.doc.expenses && frm.doc.expenses.length) {
                // Get all rows that need to be removed
                let rows_to_remove = frm.doc.expenses.filter(row => 
                    !row.expense_type || row.expense_type === 'Vehicle Expense'
                );                
                for (let i = frm.doc.expenses.length - 1; i >= 0; i--) {
                    if (!frm.doc.expenses[i].expense_type || 
                        frm.doc.expenses[i].expense_type === 'Vehicle Expense') {
                        frm.get_field('expenses').grid.grid_rows[i].remove();
                    }
                }
                
                frm.refresh_field('expenses');
            }
            // Add a row to the 'expenses' child table
            const row = frm.add_child('expenses', {
                expense_date: frappe.datetime.get_today(), 
                expense_type: 'Vehicle Expense',         
                amount: amount,
                sanctioned_amount: amount                        
            });
            frm.refresh_field('expenses');
        }
    },
    // Mubashir Bashir 24-12-2024 End
}
);


// nabeel saleem, 19-12-2024
function set_query_vehicle_expense(frm) {
    frm.fields_dict['expenses'].grid.get_field('expense_type').get_query = function (doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        let ffilters = frm.doc.ownership === 0
            ? {name: ["!=", "Vehicle Expense"]}: {}

        return {
            filters: ffilters
        };
    };
}

frappe.ui.form.on('Expense Claim Detail', {
    expense_type: function (frm, cdt, cdn) {
        // nabeel saleem, 19-12-2024
        if (!frm.doc.employee && !frm.doc.expense_approver) {
            frappe.throw(__('Please select Employee and Approver first'));
            return;
        }
        var d = locals[cdt][cdn];
        if (d.expense_type === "Daily Allowance") {
            frm.toggle_reqd("travel_request", true);
            frm.set_df_property("travel_request", "read_only", 0);
        }
        else {
            frm.toggle_reqd("travel_request", false);
            frm.set_df_property("travel_request", "read_only", 1);
            // frm.set_value("custom_travel_request","");
        }

        if (!frm.doc.company) {
            d.expense_type = "";
            frappe.msgprint(__("Please set the Company"));
            this.frm.refresh_fields();
            return;
        }

        if (!d.expense_type) {
            return;
        }

        if(d.expense_type=="Vehicle Expense"){
            frm.call('validate_and_set_vehicle_expense');
        }else{
            frm.call('get_travel_expense_amount', { "expense_type": d.expense_type }).then(r => {
                console.log(r.message)
                if (r.message.amount) {
                    d.amount = r.message.amount || 0;
                    d.sanctioned_amount = r.message.amount || 0;
                    frm.refresh_field('expenses');
                } else {
                    frappe.msgprint(__("No amount defined for the selected expense type."));
                    frm.refresh_field('expenses');
                }
            });

            frm.call('validate_expenses_table').then(r => {
            });

            return frappe.call({
                method: "hrms.hr.doctype.expense_claim.expense_claim.get_expense_claim_account_and_cost_center",
                args: {
                    "expense_claim_type": d.expense_type,
                    "company": frm.doc.company
                },
                callback: function (r) {
                    if (r.message) {
                        d.default_account = r.message.account;
                        d.cost_center = r.message.cost_center;
                    }
                }
            });
        }


    },
    expense_date: function (frm, cdt, cdn) {
        frm.call('validate_expenses_table').then(r => {
        });
    }
});

cur_frm.add_fetch('employee', 'company', 'company');
cur_frm.add_fetch('employee', 'employee_name', 'employee_name');
cur_frm.add_fetch('expense_type', 'description', 'description');

cur_frm.cscript.refresh = function (doc) {
    cur_frm.cscript.set_help(doc);

    if (!doc.__islocal) {

        if (doc.docstatus === 1) {
            /* eslint-disable */
            // no idea how `me` works here
            var entry_doctype, entry_reference_doctype, entry_reference_name;
            if (doc.__onload.make_payment_via_journal_entry) {
                entry_doctype = "Journal Entry";
                entry_reference_doctype = "Journal Entry Account.reference_type";
                entry_reference_name = "Journal Entry.reference_name";
            } else {
                entry_doctype = "Payment Entry";
                entry_reference_doctype = "Payment Entry Reference.reference_doctype";
                entry_reference_name = "Payment Entry Reference.reference_name";
            }

            if (cint(doc.total_amount_reimbursed) > 0 && frappe.model.can_read(entry_doctype)) {
                cur_frm.add_custom_button(__('Bank Entries'), function () {
                    frappe.route_options = {
                        party_type: "Employee",
                        party: doc.employee,
                        company: doc.company
                    };
                    frappe.set_route("List", entry_doctype);
                }, __("View"));
            }
            /* eslint-enable */
        }
    }
};

cur_frm.cscript.set_help = function (doc) {
    cur_frm.set_intro("");
    if (doc.__islocal && !in_list(frappe.user_roles, "HR User")) {
        cur_frm.set_intro(__("Fill the form and save it"));
    }
};

cur_frm.cscript.validate = function (doc) {
    cur_frm.cscript.calculate_total(doc);
};

cur_frm.cscript.calculate_total = function (doc) {
    doc.total_claimed_amount = 0;
    doc.total_sanctioned_amount = 0;
    $.each((doc.expenses || []), function (i, d) {
        doc.total_claimed_amount += d.amount;
        doc.total_sanctioned_amount += d.sanctioned_amount;
    });
};

cur_frm.cscript.calculate_total_amount = function (doc, cdt, cdn) {
    cur_frm.cscript.calculate_total(doc, cdt, cdn);
};

cur_frm.fields_dict['cost_center'].get_query = function (doc) {
    return {
        filters: {
            "company": doc.company
        }
    }
};

frappe.ui.form.on("Expense Claim", {
    setup: function (frm) {
        frm.add_fetch("company", "cost_center", "cost_center");
        frm.add_fetch("company", "default_expense_claim_payable_account", "payable_account");

        frm.set_query("employee_advance", "advances", function () {
            return {
                filters: [
                    ['docstatus', '=', 1],
                    ['employee', '=', frm.doc.employee],
                    ['paid_amount', '>', 0],
                    ['status', 'not in', ['Claimed', 'Returned', 'Partly Claimed and Returned']]
                ]
            };
        });

        frm.set_query("expense_approver", function () {
            return {
                query: "hrms.hr.doctype.department_approver.department_approver.get_approvers",
                filters: {
                    employee: frm.doc.employee,
                    doctype: frm.doc.doctype
                }
            };
        });

        frm.set_query("account_head", "taxes", function () {
            return {
                filters: [
                    ['company', '=', frm.doc.company],
                    ['account_type', 'in', ["Tax", "Chargeable", "Income Account", "Expenses Included In Valuation"]]
                ]
            };
        });

        frm.set_query("payable_account", function () {
            return {
                filters: {
                    "report_type": "Balance Sheet",
                    "account_type": "Payable",
                    "company": frm.doc.company,
                    "is_group": 0
                }
            };
        });

        frm.set_query("task", function () {
            return {
                filters: {
                    'project': frm.doc.project
                }
            };
        });

        frm.set_query("employee", function () {
            return {
                query: "erpnext.controllers.queries.employee_query"
            };
        });
    },

    onload: function (frm) {
        if (frm.doc.docstatus == 0) {
            return frappe.call({
                method: "hrms.hr.doctype.leave_application.leave_application.get_mandatory_approval",
                args: {
                    doctype: frm.doc.doctype,
                },
                callback: function (r) {
                    if (!r.exc && r.message) {
                        frm.toggle_reqd("expense_approver", true);
                    }
                }
            });
        }
    },

    refresh: function (frm) {
        frm.trigger("toggle_fields");

        if (frm.doc.docstatus > 0 && frm.doc.approval_status !== "Rejected") {
            frm.add_custom_button(__('Accounting Ledger'), function () {
                frappe.route_options = {
                    voucher_no: frm.doc.name,
                    company: frm.doc.company,
                    from_date: frm.doc.posting_date,
                    to_date: moment(frm.doc.modified).format('YYYY-MM-DD'),
                    group_by: '',
                    show_cancelled_entries: frm.doc.docstatus === 2
                };
                frappe.set_route("query-report", "General Ledger");
            }, __("View"));
        }

        if (
            frm.doc.docstatus === 1
            && frm.doc.status !== "Paid"
            && frappe.model.can_create("Payment Entry")
        ) {
            frm.add_custom_button(__('Payment'),
                function () { frm.events.make_payment_entry(frm); }, __('Create'));
        }
        // nabeel saleem, 19-12-2024
        set_query_vehicle_expense(frm);
    },

    calculate_grand_total: function (frm) {
        var grand_total = flt(frm.doc.total_sanctioned_amount) + flt(frm.doc.total_taxes_and_charges) - flt(frm.doc.total_advance_amount);
        frm.set_value("grand_total", grand_total);
        frm.refresh_fields();
    },

    grand_total: function (frm) {
        frm.trigger("update_employee_advance_claimed_amount");
    },

    update_employee_advance_claimed_amount: function (frm) {
        let amount_to_be_allocated = frm.doc.grand_total;
        $.each(frm.doc.advances || [], function (i, advance) {
            if (amount_to_be_allocated >= advance.unclaimed_amount) {
                advance.allocated_amount = frm.doc.advances[i].unclaimed_amount;
                amount_to_be_allocated -= advance.allocated_amount;
            } else {
                advance.allocated_amount = amount_to_be_allocated;
                amount_to_be_allocated = 0;
            }
            frm.refresh_field("advances");
        });
    },

    make_payment_entry: function (frm) {
        let method = "hrms.overrides.employee_payment_entry.get_payment_entry_for_employee";
        if (frm.doc.__onload && frm.doc.__onload.make_payment_via_journal_entry) {
            method = "hrms.hr.doctype.expense_claim.expense_claim.make_bank_entry";
        }
        return frappe.call({
            method: method,
            args: {
                "dt": frm.doc.doctype,
                "dn": frm.doc.name
            },
            callback: function (r) {
                var doclist = frappe.model.sync(r.message);
                frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
            }
        });
    },

    is_paid: function (frm) {
        frm.trigger("toggle_fields");
    },

    toggle_fields: function (frm) {
        frm.toggle_reqd("mode_of_payment", frm.doc.is_paid);
    },

    employee: function (frm) {
        frm.events.get_advances(frm);
    },

    cost_center: function (frm) {
        frm.events.set_child_cost_center(frm);
    },

    validate: function (frm) {
        frm.events.set_child_cost_center(frm);
    },

    set_child_cost_center: function (frm) {
        (frm.doc.expenses || []).forEach(function (d) {
            if (!d.cost_center) {
                d.cost_center = frm.doc.cost_center;
            }
        });
    },
    get_taxes: function (frm) {
        if (frm.doc.taxes) {
            frappe.call({
                method: "calculate_taxes",
                doc: frm.doc,
                callback: () => {
                    refresh_field("taxes");
                    frm.trigger("update_employee_advance_claimed_amount");
                }
            });
        }
    },

    get_advances: function (frm) {
        frappe.model.clear_table(frm.doc, "advances");
        if (frm.doc.employee) {
            return frappe.call({
                method: "hrms.hr.doctype.expense_claim.expense_claim.get_advances",
                args: {
                    employee: frm.doc.employee
                },
                callback: function (r, rt) {

                    if (r.message) {
                        $.each(r.message, function (i, d) {
                            var row = frappe.model.add_child(frm.doc, "Expense Claim Advance", "advances");
                            row.employee_advance = d.name;
                            row.posting_date = d.posting_date;
                            row.advance_account = d.advance_account;
                            row.advance_paid = d.paid_amount;
                            row.unclaimed_amount = flt(d.paid_amount) - flt(d.claimed_amount);
                            row.allocated_amount = 0;
                        });
                        refresh_field("advances");
                    }
                }
            });
        }
    }
});

frappe.ui.form.on("Expense Claim Detail", {
    // Mubashir Bashir 14-01-2025 Start
    
    // 80% sanctioned amount in case of medical expense 100% in other cases. 
    // Make sanctioned amount field readonly in case of medical expnese.
    amount: function (frm, cdt, cdn) {
        var child = locals[cdt][cdn];
        if (child.expense_type == 'Medical'){
            // 80% sanctioned amount in case of medical expense
            frappe.model.set_value(cdt, cdn, 'sanctioned_amount', child.amount*0.8);
            frm.get_field('expenses').grid.grid_rows_by_docname[cdn].toggle_editable('sanctioned_amount', false);
        }
        else {
            frappe.model.set_value(cdt, cdn, 'sanctioned_amount', child.amount);
            frm.get_field('expenses').grid.grid_rows_by_docname[cdn].toggle_editable('sanctioned_amount', true);
        }
    },
    // Mubashir Bashir 14-01-2025 End


    sanctioned_amount: function (frm, cdt, cdn) {
        cur_frm.cscript.calculate_total(frm.doc, cdt, cdn);
        frm.trigger("get_taxes");
        frm.trigger("calculate_grand_total");
    },

    cost_center: function (frm, cdt, cdn) {
        erpnext.utils.copy_value_in_all_rows(frm.doc, cdt, cdn, "expenses", "cost_center");
    }
});

frappe.ui.form.on("Expense Claim Advance", {
    employee_advance: function (frm, cdt, cdn) {
        var child = locals[cdt][cdn];
        if (!frm.doc.employee) {
            frappe.msgprint(__('Select an employee to get the employee advance.'));
            frm.doc.advances = [];
            refresh_field("advances");
        }
        else {
            return frappe.call({
                method: "hrms.hr.doctype.expense_claim.expense_claim.get_advances",
                args: {
                    employee: frm.doc.employee,
                    advance_id: child.employee_advance
                },
                callback: function (r, rt) {
                    if (r.message) {
                        child.employee_advance = r.message[0].name;
                        child.posting_date = r.message[0].posting_date;
                        child.advance_account = r.message[0].advance_account;
                        child.advance_paid = r.message[0].paid_amount;
                        child.unclaimed_amount = flt(r.message[0].paid_amount) - flt(r.message[0].claimed_amount);
                        child.allocated_amount = flt(r.message[0].paid_amount) - flt(r.message[0].claimed_amount);
                        frm.trigger('calculate_grand_total');
                        refresh_field("advances");
                    }
                }
            });
        }
    }
});

frappe.ui.form.on("Expense Taxes and Charges", {
    account_head: function (frm, cdt, cdn) {
        var child = locals[cdt][cdn];
        if (child.account_head && !child.description) {
            // set description from account head
            child.description = child.account_head.split(' - ').slice(0, -1).join(' - ');
            refresh_field("taxes");
        }
    },

    calculate_total_tax: function (frm, cdt, cdn) {
        var child = locals[cdt][cdn];
        child.total = flt(frm.doc.total_sanctioned_amount) + flt(child.tax_amount);
        frm.trigger("calculate_tax_amount", cdt, cdn);
    },

    calculate_tax_amount: function (frm) {
        frm.doc.total_taxes_and_charges = 0;
        (frm.doc.taxes || []).forEach(function (d) {
            frm.doc.total_taxes_and_charges += d.tax_amount;
        });
        frm.trigger("calculate_grand_total");
    },

    rate: function (frm, cdt, cdn) {
        var child = locals[cdt][cdn];
        if (!child.amount) {
            child.tax_amount = flt(frm.doc.total_sanctioned_amount) * (flt(child.rate) / 100);
        }
        frm.trigger("calculate_total_tax", cdt, cdn);
    },

    tax_amount: function (frm, cdt, cdn) {
        frm.trigger("calculate_total_tax", cdt, cdn);
    }
});
