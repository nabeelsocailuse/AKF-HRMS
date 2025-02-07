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

// Mubashir Bashir 07-02-2025 Start
frappe.ui.form.on("Travel Itinerary", {
    departure_date: function(frm, cdt, cdn){
        validate_dates(frm, cdt, cdn);
    },
    arrival_date: function(frm, cdt, cdn){
        validate_dates(frm, cdt, cdn);
    }
});

function validate_dates(frm, cdt, cdn){
    console.log('validate dates running...');
    
    let row = locals[cdt][cdn];

    if (row.departure_date && row.arrival_date){
        let departure = new Date(row.departure_date);
        let arrival = new Date(row.arrival_date);

        if (departure > arrival) {
            frappe.msgprint({
                title: __('Validation Error'),
                message: __('Departure Date cannot be greater than Arrival Date.'),
                indicator: __('red')
            });

            // frappe.model.set_value(cdt, cdn, 'departure_date', null);
            frappe.model.set_value(cdt, cdn, 'arrival_date', null);
        }
    }
}
// Mubashir Bashir 07-02-2025 End