frappe.ui.form.on('Attendance Adjustment', {
    employee: function(frm) {
        frm.set_value('custom_adjustment_date', '');
        frm.set_value('custom_adjustment_hours', '');
    },
    custom_adjustment_date: function(frm) {
        frm.set_value('custom_adjustment_hours', '');
        validate_custom_adjustment_date(frm);
    },
    compensation_date: function(frm) {
        validateAttendanceExistence(frm);
    }
});


function validate_custom_adjustment_date(frm) {
    const custom_adjustment_date = frm.doc.custom_adjustment_date;
    const employee = frm.doc.employee;

    if (custom_adjustment_date && employee) {
        frappe.call({
            method: 'akf_hrms.akf_hrms.doctype.attendance_adjustment.attendance_adjustment.validate_custom_adjustment_date',
            args: {
                custom_adjustment_date: custom_adjustment_date,
                employee: employee
            },
            callback: function(response) {
                if (response.message) {
                    frm.set_value('custom_adjustment_hours', response.message);
                }
            },
            error: function(response) {
                frappe.msgprint(response.message);
                frm.set_value('custom_adjustment_date', '');
            }
        });
    }
}
function validateAttendanceExistence(frm) {
    const compensation_date = frm.doc.compensation_date;
    const employee = frm.doc.employee;

    if (compensation_date && employee) {
        frappe.call({
            method: 'akf_hrms.akf_hrms.doctype.attendance_adjustment.attendance_adjustment.validate_compensation_date',
            args: {
                compensation_date: compensation_date,
                employee: employee
            },
            callback: function(response) {
            },
            error: function(response) {
                // Clear the compensation_date field if validation fails
                frm.set_value('compensation_date', '');
                frappe.msgprint(response.message);
            }
        });
    }
}




// frappe.ui.form.on("Attendance Adjustment", {
//     refresh(frm) {
//     },
//     start_time(frm) {
//         validate_time(frm);
//     },
//     end_time(frm) {
//         validate_time(frm);
//     },
//     custom_adjustment_date: function(frm) {
//         check_attendance_existence(frm);
//         check_overtime_claim(frm);
//         fill_custom_adjustment_hours(frm);
//     },
//     compensation_date: function(frm) {
//         check_attendance_existence(frm);
//     }
// });

// function validate_time(frm) {
//     var startTime = frm.doc.start_time;
//     var endTime = frm.doc.end_time;

//     if (startTime && endTime) {
//         if (startTime >= endTime) {
//             frappe.throw("The Start Time must be less than the End Time.");
//         } 
//     }
// }

// function fill_custom_adjustment_hours(frm) {
//     if(frm.doc.custom_adjustment_date){
//     frappe.call({
//         method: "akf_hrms.akf_hrms.doctype.attendance_adjustment.attendance_adjustment.get_custom_overtime_hours",
//         args: {
//             employee: frm.doc.employee,
//             custom_adjustment_date: custom_adjustment_date
//         },
//         callback: function(response) {
//             if (response.message) {
//                 frm.set_value('custom_adjustment_hours', response.message);
//             }
//         }
//     });
// }
// }
// function check_attendance_existence(frm) {
//     if (frm.doc.employee && frm.doc.custom_adjustment_date && frm.doc.compensation_date) {
//         frappe.call({
//             method: "akf_hrms.akf_hrms.doctype.attendance_adjustment.attendance_adjustment.check_attendance",
//             args: {
//                 employee: frm.doc.employee,
//                 custom_adjustment_date: frm.doc.custom_adjustment_date,
//                 compensation_date: frm.doc.compensation_date
//             },
//             callback: function(attendance_response) {
//                 frappe.msgprint(attendance_response.message);
//                 check_overtime_claim(frm); 
//             }
//         });
//     }
// }

// function check_overtime_claim(frm) {
//     if (frm.doc.custom_adjustment_date) {
//         frappe.call({
//             method: "akf_hrms.akf_hrms.doctype.attendance_adjustment.attendance_adjustment.check_overtime_claim",
//             args: {
//                 employee: frm.doc.employee,
//                 custom_adjustment_date: frm.doc.custom_adjustment_date
//             },
//             callback: function(overtime_response) {
//                 frappe.msgprint(overtime_response.message);
//             }
//         });
//     }
// }
