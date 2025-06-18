// Copyright (c) 2024, Nabeel Saleem and contributors
// For license information, please see license.txt

frappe.ui.form.on('Compensatory Leave Request', {
    refresh: function (frm) {
        frm.set_query("leave_type", function () {
            return {
                filters: {
                    "is_compensatory": true
                }
            };
        });
    },
    onload: function (frm) {
        setEmployeeFromSession(frm);
        frm.set_query("employee", function () {
            return {
                filters: {
                    status: 'Active',
                },
            };
        });
    },
    half_day: function (frm) {
        if (frm.doc.half_day == 1) {
            frm.set_df_property('half_day_date', 'reqd', true);
        }
        else {
            frm.set_df_property('half_day_date', 'reqd', false);
        }
    }
});


// Mubashir Bashir 17-06-2025 Start
function setEmployeeFromSession(frm) {
	if (frm.is_new()) {
		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "Employee",
				filters: {
					user_id: frappe.session.user,
					status: "Active"
				},
				fields: ["name"]
			},
			callback: function (r) {
				if (r.message && r.message.length > 0) {
					frm.set_value("employee", r.message[0].name);
					frm.set_value("leave_type", 'Compensatory Leave');
				}
			}
		});
	}
}
// Mubashir Bashir 17-06-2025 End