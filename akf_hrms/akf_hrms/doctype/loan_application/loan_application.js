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
    // Mubashir Bashir 16-01-2025 START
    applicant: function (frm) {
        frm.set_value("loan_product", ""); 
        frm.set_value("custom_guarantor_of_loan_application", "");
        frm.set_value("custom_guarantor_2_of_loan_application", "");

        validatePermanentEmployee(frm);
    },

    custom_guarantor_of_loan_application: function (frm) {
        debouncedValidateGuaranters(frm);
    },

    custom_guarantor_2_of_loan_application: function (frm) {
        debouncedValidateGuaranters(frm);
    },
    // Mubashir Bashir 16-01-2025 END
		
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
            validate_eligibility_on_the_basis_of_grade(frm);    // <-- Mubashir 15-01-25

            get_latest_vehicle_loan_limit(frm, frm.doc.loan_product)
                .then(latest_limit => {
                    console.log("latest_limit: ", latest_limit);
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

function get_latest_vehicle_loan_limit(frm, loan_product) {     // Mubashir 15-01-2025 Start
    // Get employee grade first
    frappe.db.get_value("Employee", {"name": frm.doc.applicant}, ["grade", "date_of_joining"])
        .then(r => {
            frm.set_value("repayment_method", "Repay Over Number of Periods");
            frm.set_df_property("repayment_method", "read_only", 1);
            let grade = r.message.grade;
            let date_of_joining = r.message.date_of_joining;

            // Get Employee Grade doc with child table
            frappe.db.get_doc("Employee Grade", grade)
                .then(grade_doc => {
                    // Find matching entitlement based on loan product and experience
                    let today = new Date();
                    let joining_date = new Date(date_of_joining);
                    let experience_days = Math.floor((today - joining_date) / (1000 * 60 * 60 * 24));
                    let experience_years = experience_days / 365.0;

                    let matching_entitlement = grade_doc.custom_loan_entitlement.find(entitlement => 
                        entitlement.loan_entitlement === loan_product && 
                        experience_years >= entitlement.services_in_years
                    );

                    if (matching_entitlement) {
                        frm.set_value("repayment_periods", matching_entitlement.repayment_period);
                        frm.refresh_field("repayment_periods");
                    }
                });
        });  // Mubashir 15-01-2025 END

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
                                    latest_limit = row.max_loan_per_emp;
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

// Mubashir Bashir 15-01-2025 START
function validate_eligibility_on_the_basis_of_grade(frm) {
    if (!['Vehicle Loan', 'Bike Loan'].includes(frm.doc.loan_product)) {
        return;
    }

    // Get Employee details
    frappe.db.get_doc("Employee", frm.doc.applicant)
        .then(employee => {
            if (!employee.grade) {
                frappe.throw("Grade is not set for the employee");
                return;
            }
            if (!employee.date_of_joining) {
                frappe.throw("Date of Joining is not set for the employee");
                return;
            }
            // Get Employee Grade doc
            frappe.db.get_doc("Employee Grade", employee.grade)
                .then(grade_doc => {
                    // Calculate experience in years
                    let today = new Date();
                    let joining_date = new Date(employee.date_of_joining);
                    let experience_days = Math.floor((today - joining_date) / (1000 * 60 * 60 * 24));
                    let experience_years = experience_days / 365.0;

                    // Find matching entitlement
                    let matching_entitlement = grade_doc.custom_loan_entitlement.find(entitlement => 
                        entitlement.loan_entitlement === frm.doc.loan_product && 
                        experience_years >= entitlement.services_in_years
                    );
                    if (!matching_entitlement) {
                        frappe.throw(`Employee is not eligible for ${frm.doc.loan_product} based on grade ${employee.grade}`);
                        frm.set_value('loan_product', '');
                        return;
                    }
                    // Set and validate repayment periods
                    if (frm.doc.repayment_method === 'Repay Over Number of Periods') {
                        if (frm.doc.repayment_periods > matching_entitlement.repayment_period) {
                            frappe.throw(`Repayment periods cannot exceed ${matching_entitlement.repayment_period} months for ${frm.doc.loan_product}`);
                            frm.set_value('repayment_periods', matching_entitlement.repayment_period);
                        }
                    }
                });
        });
}
// Mubashir Bashir 15-01-2025 END

// Mubashir Bashir 16-01-2025 START
function validatePermanentEmployee(frm) {
    
    frappe.db.get_value('Employee', { name: frm.doc.applicant }, 'employment_type')
        .then(r => {
            const employmentType = r.message.employment_type;
            if (employmentType !== 'Permanent') {
                frappe.throw(__("Only Permanent Employees are eligible for Loan"));
            }
        });
}

const debounce = (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
};

async function validateGuaranters(frm) {
    try {
        const guarantor1 = frm.doc.custom_guarantor_of_loan_application;
        const guarantor2 = frm.doc.custom_guarantor_2_of_loan_application;

        // Basic validation checks
        if (!guarantor1 && !guarantor2) return;
        
        // Check if applicant is their own guarantor
        if (frm.doc.applicant === guarantor1 || frm.doc.applicant === guarantor2) {
            frappe.show_alert({
                message: __("Applicant can not be their own guarantor."),
                indicator: 'red'
            });
            return;
        }

        // Check if both guarantors are the same
        if (guarantor1 && guarantor2 && guarantor1 === guarantor2) {
            frappe.show_alert({
                message: __("Both guarantors cannot be the same person."),
                indicator: 'red'
            });
            return;
        }

        // Only proceed with full validation if both guarantors are set
        if (!(guarantor1 && guarantor2)) {
            frappe.show_alert({
                message: __("Please select both guarantors."),
                indicator: 'orange'
            });
            return;
        }

        const today = new Date();
        const requiredExperienceDays = 730;

        // Get employee details for both guarantors
        const [emp1, emp2] = await Promise.all([
            frappe.db.get_doc('Employee', guarantor1),
            frappe.db.get_doc('Employee', guarantor2)
        ]);

        // Validate employment types
        if (emp1.employment_type !== 'Permanent' || emp2.employment_type !== 'Permanent') {
            frappe.show_alert({
                message: __("Only permanent employees can be guarantor."),
                indicator: 'red'
            });
            return;
        }

        // Check for existing loans and guarantor roles
        const [
            hasLoan1,
            hasLoan2,
            isGuarantor1A,
            isGuarantor1B,
            isGuarantor2A,
            isGuarantor2B
        ] = await Promise.all([
            frappe.db.count('Loan Application', {
                filters: {
                    applicant: guarantor1,
                    docstatus: 1,
                    name: ['!=', frm.doc.name] // Exclude current document
                }
            }),
            frappe.db.count('Loan Application', {
                filters: {
                    applicant: guarantor2,
                    docstatus: 1,
                    name: ['!=', frm.doc.name]
                }
            }),
            frappe.db.count('Loan Application', {
                filters: {
                    custom_guarantor_of_loan_application: guarantor1,
                    docstatus: 1,
                    name: ['!=', frm.doc.name]
                }
            }),
            frappe.db.count('Loan Application', {
                filters: {
                    custom_guarantor_2_of_loan_application: guarantor1,
                    docstatus: 1,
                    name: ['!=', frm.doc.name]
                }
            }),
            frappe.db.count('Loan Application', {
                filters: {
                    custom_guarantor_of_loan_application: guarantor2,
                    docstatus: 1,
                    name: ['!=', frm.doc.name]
                }
            }),
            frappe.db.count('Loan Application', {
                filters: {
                    custom_guarantor_2_of_loan_application: guarantor2,
                    docstatus: 1,
                    name: ['!=', frm.doc.name]
                }
            })
        ]);

        if (hasLoan1 > 0) {
            frappe.show_alert({
                message: __(`Guarantor ${guarantor1} already has an active loan application.`),
                indicator: 'red'
            });
            return;
        }
        if (hasLoan2 > 0) {
            frappe.show_alert({
                message: __(`Guarantor ${guarantor2} already has an active loan application.`),
                indicator: 'red'
            });
            return;
        }
        if (isGuarantor1A > 0 || isGuarantor1B > 0) {
            frappe.show_alert({
                message: __(`Guarantor ${guarantor1} is already acting as a guarantor for another loan application.`),
                indicator: 'red'
            });
            return;
        }
        if (isGuarantor2A > 0 || isGuarantor2B > 0) {
            frappe.show_alert({
                message: __(`Guarantor ${guarantor2} is already acting as a guarantor for another loan application.`),
                indicator: 'red'
            });
            return;
        }

        // Experience validation
        for (const [emp, guarantor] of [[emp1, guarantor1], [emp2, guarantor2]]) {
            if (!emp.date_of_joining) {
                frappe.show_alert({
                    message: __(`Guarantor ${guarantor} does not have a valid date of joining.`),
                    indicator: 'red'
                });
                return;
            }

            const joining = new Date(emp.date_of_joining);
            const experience = Math.floor((today - joining) / (1000 * 60 * 60 * 24));

            if (experience < requiredExperienceDays) {
                frappe.show_alert({
                    message: __(`Guarantor ${guarantor} should have at least 2 years of experience.`),
                    indicator: 'red'
                });
                return;
            }
        }

        // If all validations pass
        frappe.show_alert({
            message: __("Guarantor validation successful"),
            indicator: 'green'
        }, 5);

    } catch (error) {
        console.error("Error in validateGuaranters:", error);
        frappe.show_alert({
            message: __("Error validating guarantors. Please try again."),
            indicator: 'red'
        });
    }
}

// Debounced version of the validation function
const debouncedValidateGuaranters = debounce(validateGuaranters, 300);

// Mubashir Bashir 16-01-2025 END




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
