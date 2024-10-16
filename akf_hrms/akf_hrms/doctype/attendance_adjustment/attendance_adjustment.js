frappe.ui.form.on('Attendance Adjustment', {
    refresh: function (frm) {
        if(!frm.is_new()){
            loadSevenDaysStats(frm);
            loadCompensateOnStats(frm);
        }
    },
    employee: function (frm) {
        loadSevenDaysStats(frm);
        // frm.set_value('custom_adjustment_date', '');
        // frm.set_value('custom_adjustment_hours', '');
    },
    custom_adjustment_date: function (frm) {
        // frm.set_value('custom_adjustment_hours', '');
        // validate_custom_adjustment_date(frm);
    },
    adjustment_date: function(frm){
        if(frm.doc.adjustment_date!=undefined){
            frm.call('get_adjustment_for').then(r=>{
                frm.set_value('adjustment_for', r.message);
            });
        }else{
            frm.set_value('adjustment_for', null);
        }
    },
    compensation_date: function (frm) {
        // validateAttendanceExistence(frm);
        if(frm.doc.compensation_date!=undefined){
            frm.call('get_compensation_for').then(r=>{
                frm.set_value('compensation_for', r.message);
            });
        }else{
            frm.set_value('compensation_for', null);
        }
        loadCompensateOnStats(frm);
    },
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
            callback: function (response) {
                if (response.message) {
                    frm.set_value('custom_adjustment_hours', response.message);
                }
            },
            error: function (response) {
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
            callback: function (response) {
            },
            error: function (response) {
                // Clear the compensation_date field if validation fails
                frm.set_value('compensation_date', '');
                frappe.msgprint(response.message);
            }
        });
    }
}

function loadSevenDaysStats(frm) {
    frm.call('get_attendance_stats').then(r => {
        let data = r.message;
        let rows = ``;
        let idx = 1
        data.forEach(row => {
            let attendance_date = moment(row.attendance_date).format("DD-MM-YYYY")
            rows += `
                <tr>
                    <th scope="row">${idx}</th>
                    <td class=""><a href="/app/attendance/${row.name}">${row.name}</a></td>
                    <td class="">${attendance_date}</td>
                    <td>${row.custom_total_working_hours}</td>
                    <td>${row.custom_hours_worked}</td>
                    <td>${row.custom_overtime_hours}</td>
                </tr>`;
            idx += 1;
        });
        if(rows==''){
            rows = `
                <tr>
                    <td class="text-center" style="color:lightgray;" colspan="6">No records found.</td>
                </tr>`;
        }
        let _html_ = `
            <h3 style="">Attendance Stats (7 Days)</h3>
            <table class="table">
                <thead class="thead-dark" >
                    <tr>
                    <th scope="col">#</th>
                    <th class="" scope="col">Attendance ID</th>
                    <th class="" scope="col">Date</th>
                    <th scope="col">Working Hours</th>
                    <th scope="col">Hours Worked</th>
                    <th scope="col">Extra Hours</th>
                    </tr>
                </thead>
                <tbody  style="font-size: 13px;">
                    ${rows}
                </tbody>
            </table>`;
        frm.set_df_property("seven_days_stats", "options", _html_);
    });
}

function loadCompensateOnStats(frm) {
    if(frm.doc.compensation_date==undefined) return;
    frm.call('get_compensation_date_stats').then(r => {
        let data = r.message;
        let rows = ``;
        data.forEach(row => {
            // let attendance_date = moment(row.attendance_date).format("DD-MM-YYYY")
            rows += `
                <tr>
                    <td class=""><a href="/app/attendance/${row.name}">${row.name}</a></td>
                    <td class="">${row.in_time}</td>
                    <td class="">${row.out_time}</td>
                    <td>${row.custom_hours_worked}</td>
                    <td>${row.custom_total_working_hours}</td>
                    <td>${row.custom_overtime_hours}</td>
                </tr>`;
        });
        if(rows==''){
            rows = `
                <tr>
                    <td class="text-center" style="color:lightgray;" colspan="6">No records found.</td>
                </tr>`;
        }
        let _html_ = `
            <h3 style="">Compensation Stats</h3>
            <table class="table">
                <thead class="thead-dark" style="font-size: 11px;">
                    <tr>
                    <th class="" scope="col">Attendance ID</th>
                    <th class="" scope="col">In Time</th>
                    <th class="" scope="col">Out Time</th>
                    <th scope="col">Hours Worked</th>
                    <th scope="col">Working Hours</th>
                    <th scope="col">Extra Hours</th>
                    

                    </tr>
                </thead>
                <tbody style="font-size: 11px;">
                    ${rows}
                </tbody>
            </table>`;
        frm.set_df_property("compensation_on_stats", "options", _html_);
    });
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
