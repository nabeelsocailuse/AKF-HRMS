// Copyright (c) 2024, Nabeel Saleem and contributors
// For license information, please see license.txt

frappe.ui.form.on("ZK Tool", {
    refresh(frm) {
        customButtons(frm);
        customQuery(frm);
    },
    company: function (frm) {
        get_company_details(frm);
    },
    log_type: function (frm) {
        get_company_details(frm);
    },
});

function customButtons(frm) {

    frm.add_custom_button(__('Get Employees'), function () {
        get_employees(frm);
    });
    frm.add_custom_button(__('Fetch Attendance'), function () {
        fetch_attendance(frm);
    });
    frm.add_custom_button(__('Mark Attendance'), function () {
       mark_attendance(frm);
    });

}

function customQuery(frm) {
    // frm.set_query('employee', 'employee_biometric', function () {
    //     return {
    //         filters: {
    //             'status': 'Active',
    //             'company': frm.doc.company
    //         }
    //     }
    // });
}

function get_employees(frm){
    frm.set_intro('');
    frm.set_intro('Fetching employees...');
    frm.call('get_employees')
        .then(r => {
            frm.set_intro(r.message);
            frm.save()
        });

}
function get_company_details(frm) {
    frm.call('get_company_details')
        .then(r => {
            // console.log(r.message);
            frm.set_intro('');
            frm.set_intro(r.message == undefined ? "Device detail not found." : "", 'red');
        });
}

function fetch_attendance(frm){
    frm.set_intro('');
    frm.set_intro('Fetching attendance...');
    frm.call('fetch_attendance')
        .then(r => {
            frm.set_intro(r.message);
            frm.save()
        });
}

function mark_attendance(frm){
    // frm.set_intro('');
    // frm.set_intro('Marking attendance...', 'blue');
    frm.set_value("progress_message", "Marking attendance...")
    frm.call('mark_attendance')
        .then(r => {
            // console.log(r.message)
            // frm.set_intro(r.message, 'green');
            // frm.save()
        });
}