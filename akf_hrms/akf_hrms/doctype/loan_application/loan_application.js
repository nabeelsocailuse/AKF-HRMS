// Module Overriden by Mubashir Bashir

lending.common.setup_filters("Loan Application");

frappe.ui.form.on('Loan Application', {

	setup: function(frm) {
		frm.make_methods = {
			'Loan': function() { frm.trigger('create_loan') },
			'Loan Security Pledge': function() { frm.trigger('create_loan_security_pledge') },
		}
	},
	refresh: function(frm) {
	
		frm.trigger("toggle_fields");
		frm.trigger("add_toolbar_buttons");
		frm.set_query('loan_product', () => {
			return {
				filters: {
					company: frm.doc.company
				}
			};
		});
	},
	repayment_method: function(frm) {
		frm.doc.repayment_amount = frm.doc.repayment_periods = "";
		frm.trigger("toggle_fields");
		frm.trigger("toggle_required");
	},
	toggle_fields: function(frm) {
		frm.toggle_enable("repayment_amount", frm.doc.repayment_method=="Repay Fixed Amount per Period");
		frm.toggle_enable("repayment_periods", frm.doc.repayment_method=="Repay Over Number of Periods");
	},
	toggle_required: function(frm){
		frm.toggle_reqd("repayment_amount", cint(frm.doc.repayment_method=='Repay Fixed Amount per Period'));
		frm.toggle_reqd("repayment_periods", cint(frm.doc.repayment_method=='Repay Over Number of Periods'));
	},
	add_toolbar_buttons: function(frm) {
		if (frm.doc.status == "Approved") {

			if (frm.doc.is_secured_loan) {
				frappe.db.get_value("Loan Security Pledge", {"loan_application": frm.doc.name, "docstatus": 1}, "name", (r) => {
					if (Object.keys(r).length === 0) {
						frm.add_custom_button(__('Loan Security Pledge'), function() {
							frm.trigger('create_loan_security_pledge');
						},__('Create'))
					}
				});
			}

			frappe.db.get_value("Loan", {"loan_application": frm.doc.name, "docstatus": 1}, "name", (r) => {
				if (Object.keys(r).length === 0) {
					frm.add_custom_button(__('Loan'), function() {
						frm.trigger('create_loan');
					},__('Create'))
				} else {
					frm.set_df_property('status', 'read_only', 1);
				}
			});
		}
	},
	create_loan: function(frm) {
		if (frm.doc.status != "Approved") {
			frappe.throw(__("Cannot create loan until application is approved"));
		}

		frappe.model.open_mapped_doc({
			method: 'akf_hrms.akf_hrms.doctype.loan_application.loan_application.create_loan',
			frm: frm
		});
	},
	create_loan_security_pledge: function(frm) {

		if(!frm.doc.is_secured_loan) {
			frappe.throw(__("Loan Security Pledge can only be created for secured loans"));
		}

		frappe.call({
			method: "akf_hrms.akf_hrms.doctype.loan_application.loan_application.create_pledge",
			args: {
				loan_application: frm.doc.name
			},
			callback: function(r) {
				frappe.set_route("Form", "Loan Security Pledge", r.message);
			}
		})
	},
	is_term_loan: function(frm) {
		frm.set_df_property('repayment_method', 'hidden', 1 - frm.doc.is_term_loan);
		frm.set_df_property('repayment_method', 'reqd', frm.doc.is_term_loan);
	},
	is_secured_loan: function(frm) {
		frm.set_df_property('proposed_pledges', 'reqd', frm.doc.is_secured_loan);
	},

	calculate_amounts: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.qty) {
			frappe.model.set_value(cdt, cdn, 'amount', row.qty * row.loan_security_price);
			frappe.model.set_value(cdt, cdn, 'post_haircut_amount', cint(row.amount - (row.amount * row.haircut/100)));
		} else if (row.amount) {
			frappe.model.set_value(cdt, cdn, 'qty', cint(row.amount / row.loan_security_price));
			frappe.model.set_value(cdt, cdn, 'amount', row.qty * row.loan_security_price);
			frappe.model.set_value(cdt, cdn, 'post_haircut_amount', cint(row.amount - (row.amount * row.haircut/100)));
		}

		let maximum_amount = 0;

		$.each(frm.doc.proposed_pledges || [], function(i, item){
			maximum_amount += item.post_haircut_amount;
		});

		if (flt(maximum_amount)) {
			frm.set_value('maximum_loan_amount', flt(maximum_amount));
		}
	},

    // loan_product: function (frm) {
    //     if (frm.doc.loan_product == "Advance Salary") {
    //       frm.set_value("repayment_method", "Repay Fixed Amount per Period");
    //       frappe.call({
    //         method: "frappe.client.get_list",
    //         args: {
    //           doctype: "Salary Structure Assignment",
    //           fields: ["base"],
    //           filters: {
    //             employee: frm.doc.applicant,
    //             docstatus: 1,
    //             from_date: ["<", new Date()],
    //           },
    //           order_by: "from_date DESC",
    //           limit_page_length: 1,
    //         },
    //         callback: function (r) {
    //           if (r.message[0]) {
    //             frm.set_value("custom_maximum_allowed_loan", r.message[0].base / 2);
    //             frm.set_value("loan_amount", frm.doc.custom_maximum_allowed_loan);
    //             frm.set_value(
    //               "repayment_amount",
    //               frm.doc.custom_maximum_allowed_loan
    //             );
    //             frm.set_value("repay_from_salary", 1);
    //             // frm.set_df_property("custom_maximum_allowed_loan", "read_only", 1);
    //             frm.set_df_property("applicant", "read_only", 1);
    //             frm.set_df_property("repay_from_salary", "read_only", 1);
    //           } else {
    //             frm.set_value("loan_product", "");
    //             frappe.msgprint(
    //               __(
    //                 "Not authorized to apply for the loan as there is no Salary Structure Assignment currently active."
    //               )
    //             );
    //           }
    //         },
    //       });
    //     } else {
    //     //   frm.set_df_property("custom_maximum_allowed_loan", "read_only", 0);
    //       frm.set_df_property("applicant", "read_only", 0);
    //       frm.set_df_property("repay_from_salary", "read_only", 0);
    //     }

	// 	// Mubashir Bashir Start 11-13-2024
	// 	if (frm.doc.loan_product == "Vehicle Loan") {
	// 		frm.set_value("repayment_method", "Repay Over Number of Periods");

    //         frappe.db.get_doc('Loan Product', frm.doc.loan_product)
    //             .then(doc => {
    //                 if (doc.custom_loan_limit && doc.custom_loan_limit.length > 0) {
    //                     let latest_limit = null;
    //                     let latest_date = null;

    //                     doc.custom_loan_limit.forEach(row => {
    //                         frappe.db.get_doc('Fiscal Year', row.fiscal_year)
    //                             .then(fiscal_year => {
    //                                 let to_date = new Date(fiscal_year.to_date);

    //                                 if (!latest_date || to_date > latest_date) {
    //                                     latest_date = to_date;
    //                                     latest_limit = row.per_vehicle_loan_limit;
    //                                 }

    //                                 if (latest_limit) {
    //                                     frm.set_value("custom_maximum_allowed_loan", latest_limit);
    //                                 }
    //                             });
    //                     });
    //                 }
    //             });
    //     }   // Mubashir Bashir End 11-13-2024
    //   },
    applicant: function (frm) {
        frm.set_value("loan_product", "");
    },
		
	loan_product: function (frm) {
        frm.set_value("loan_amount", 0);
        frm.set_value("repayment_method", "");
        frm.set_value("repayment_periods", "");
        frm.set_value("total_payable_amount", 0);


        
        if (frm.doc.loan_product == "Advance Salary") {
            frm.set_value("repayment_method", "Repay Fixed Amount per Period");
            frappe.call({
                method: "frappe.client.get_list",
                args: {
                    doctype: "Salary Structure Assignment",
                    fields: ["base"],
                    filters: {
                        employee: frm.doc.applicant,
                        docstatus: 1,
                        from_date: ["<", new Date()],
                    },
                    order_by: "from_date DESC",
                    limit_page_length: 1,
                },
                callback: function (r) {
                    console.log(r.message);
                    if (r.message[0]) {
                        frm.set_value("custom_maximum_allowed_loan", r.message[0].base / 2);
                        frm.set_value("loan_amount", frm.doc.custom_maximum_allowed_loan);
                        frm.set_value("repayment_amount", frm.doc.custom_maximum_allowed_loan);
                        frm.set_value("repay_from_salary", 1);
                        frm.set_df_property("applicant", "read_only", 1);
                        frm.set_df_property("repay_from_salary", "read_only", 1);
                    } else {
                        frm.set_value("loan_product", "");
                        frappe.msgprint(
                            __("Not authorized to apply for the loan as there is no Salary Structure Assignment currently active.")
                        );
                    }
                },
            });
        } else {
            frm.set_df_property("applicant", "read_only", 0);
            frm.set_df_property("repay_from_salary", "read_only", 0);
        }

							// Mubashir Bashir Start 14-11-2024
        // For Vehicle Loan
        if (frm.doc.loan_product == "Vehicle Loan" || frm.doc.loan_product == "Bike Loan") {
            
            get_latest_vehicle_loan_limit(frm, frm.doc.loan_product)
                .then(latest_limit => {
                    console.log(latest_limit);
                    if (latest_limit) {
                        frm.set_value("custom_maximum_allowed_loan", latest_limit);
                        frm.set_df_property("custom_maximum_allowed_loan", "read_only", 1);
                    } else {
                        frappe.msgprint(
                            __("No loan limit found for the latest fiscal year.")
                        );
                    }
                })
                .catch(error => {
                    frappe.msgprint(__("Error fetching loan limit: ") + error);
                });
        }		// Mubashir Bashir End 14-11-2024
        else {
            // frm.set_df_property("custom_maximum_allowed_loan", "read_only", 0);
            frm.set_df_property("repayment_method", "read_only", 0);
            // frm.set_df_property("repayment_periods", "read_only", 0);
        }
    },

    loan_amount: function (frm) {
        if (frm.doc.loan_product == "Advance Salary") {
            if (frm.doc.custom_loan_category == "Term Loan(Salary Advance)") {
                frm.set_value("repayment_method", "Repay Fixed Amount per Period");
                frm.set_value("repayment_amount", frm.doc.loan_amount);
                frm.set_df_property("repayment_method", "read_only", 1);
                frm.set_df_property("repayment_amount", "read_only", 1);
    
                if (frm.doc.loan_amount > frm.doc.custom_maximum_allowed_loan) {
                    frappe.msgprint(
                        __("You cannot apply for a loan more than " + frm.doc.custom_maximum_allowed_loan)
                    );
                    frm.set_value("loan_amount", frm.doc.custom_maximum_allowed_loan);
                    return;
                }
            } else {
                frm.set_df_property("repayment_method", "read_only", 0);
                frm.set_df_property("repayment_amount", "read_only", 0);
            }
        } 
        
		// Mubashir Bashir Start 11-13-2024
        if (frm.doc.loan_product == "Vehicle Loan" || frm.doc.loan_product == "Bike Loan") {
            if (frm.doc.loan_amount > frm.doc.custom_maximum_allowed_loan)
              frappe.msgprint(__("Loan amount cannot exceed the limit of PKR " + frm.doc.custom_maximum_allowed_loan));
        }  // Mubashir Bashir End 11-13-2024
    },
    
    company: function (frm) {
    frm.trigger("set_reports_to_query");
    if (!frm.doc.company) {
        frm.set_value("custom_guarantor_of_loan_application", "");
    }
    },
    set_reports_to_query: function (frm) {
    var company = frm.doc.company;
    frm.set_query("custom_guarantor_of_loan_application", function () {
        return {
        filters: {
            company: company,
        },
        };
    });
    },
});

// Mubashir Bashir Start 14-11-2024

// function getRepaymentPeriods(grade) {
//     let repayment_periods;
//     if (["M-4", "M-5", "M-6", "O-1", "O-2", "O-3", "O-4", "PC-1", "S-3", "X-1"].includes(grade)) {
//         repayment_periods = 36; // 36 months for 3 years of experience
//     } else if (["A-1", "A-3", "A-4", "A-5", "A-6", "B-1", "B-2", "B-3", "C-1", "C-2", "Contractual - Part time", "D-1", "D-2", "D-3", "Data Management Officer", "F-1", "F-2", "F-3", "G-1", "G-2", "G-3", "G-4", "G-5", "G-8", "M-3", "M-2", "M-1"].includes(grade)) {
//         repayment_periods = 24; // 24 months for 2 years of experience
//     }
//     return repayment_periods;
// }

function get_latest_vehicle_loan_limit(frm, loan_product) { // updated by mubarrim for Grade
	
    frappe.db.get_value("Employee", {"name": frm.doc.applicant}, "grade")
        .then(r => {
            frm.set_value("repayment_method", "Repay Over Number of Periods");
            frm.set_df_property("repayment_method", "read_only", 1);
            let grade = r.message.grade;
            // let repayment_periods = getRepaymentPeriods(grade);
            frappe.db.get_value("Employee Grade", {"name": grade}, "custom_repayment_period").then(r =>{
                console.log("period: " + r.message.custom_repayment_period)
                frm.set_value("repayment_periods", r.message.custom_repayment_period);
                frm.refresh_field("repayment_periods");
            })
            
            // frm.set_df_property("repayment_periods", "read_only", 1);

        }); // End by mubarrim

    return new Promise((resolve, reject) => {
        frappe.db.get_doc('Loan Product', loan_product)
            .then(doc => {
                console.log(doc);
                if (doc.custom_loan_limit && doc.custom_loan_limit.length > 0) {
                    let latest_limit = null;
                    let latest_date = null;

                    let promises = doc.custom_loan_limit.map(row => {
                        return frappe.db.get_doc('Fiscal Year', row.fiscal_year)
                            .then(fiscal_year => {
                                let to_date = new Date(fiscal_year.to_date);
                                
                                if (!latest_date || to_date > latest_date) {
                                    latest_date = to_date;
                                    latest_limit = row.per_vehicle_loan_limit;
                                }
                            });
                    });

                    Promise.all(promises).then(() => resolve(latest_limit));
                } else {
                    resolve(null);  // No loan limits found
                }
            })
            .catch(error => reject(error));
    });
}  // Mubashir Bashir End 14-11-2024


frappe.ui.form.on("Proposed Pledge", {
	loan_security: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];

		if (row.loan_security) {
			frappe.call({
				method: "lending.loan_management.doctype.loan_security_price.loan_security_price.get_loan_security_price",
				args: {
					loan_security: row.loan_security
				},
				callback: function(r) {
					frappe.model.set_value(cdt, cdn, 'loan_security_price', r.message);
					frm.events.calculate_amounts(frm, cdt, cdn);
				}
			})
		}
	},

	amount: function(frm, cdt, cdn) {
		frm.events.calculate_amounts(frm, cdt, cdn);
	},

	qty: function(frm, cdt, cdn) {
		frm.events.calculate_amounts(frm, cdt, cdn);
	},
})
