// Copyright (c) 2024, Nabeel Saleem and contributors
// For license information, please see license.txt

frappe.ui.form.on("Travel Request", {
    refresh(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Expense Claim'), function () {
                frappe.route_options = {
                    employee: frm.doc.employee,
                    travel_request: frm.doc.name,
                };
                frappe.set_route('Form', 'Expense Claim', 'new-expense-claim');
            }, __("Create"));

            frm.add_custom_button(__('Compensatory Leave'), function () {
                frappe.route_options = {
                    employee: frm.doc.employee,
                    against: "Travel",
                    travel_request: frm.doc.name,
                };
                frappe.set_route('Form', 'Compensatory Leave Request', 'new-compensatory-leave-request');
            }, __("Create"));
        }
    },
});
