// Copyright (c) 2024, Nabeel Saleem and contributors
// For license information, please see license.txt
let msg = ``;
frappe.ui.form.on("ZK Tool", {
    refresh(frm) {
        customButtons(frm);
        customQuery(frm);
        loadEmployeeDetails(frm);
        loadLogDetails(frm);
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

function loadEmployeeDetails(frm) {
    frm.call("get_employee_details").then(r => {
        let data = r.message;
        let rows = ``;
        let idx = 1
        data.forEach(element => {
            // console.log(element)
            rows += `
                <tr>
                    <th scope="row">${idx}</th>
                    <td class="">${element.employee}</td>
                    <td class="">${element.attendance_device_id!=null?element.attendance_device_id:"-"}</td>
                    <td>${element.default_shift!=null?element.default_shift:"-"}</td>
                    
                </tr>`;
            idx += 1;
        });
        let _html_ = `
                    <table class="table">
                        <thead class="thead-dark">
                            <tr>
                                <th scope="col">#</th>
                                <th class="" scope="col">Employee ID</th>
                                <th class="" scope="col">Biometric ID</th>
                                <th scope="col">Shift</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${rows}
                        </tbody>
                    </table>`;
        frm.set_df_property("employee_html", "options", _html_);
    });
}

function loadLogDetails(frm){
    frm.call("get_log_details").then(r => {
        let data = r.message;
        // console.log(data)
        let div = ``;
        let idx = 1

        for (const [key1, main_dict] of Object.entries(data)) {
            div +=`
                <div class="row"> 
                    <div class="col-md-12">
                        <b>Biometric ID</b>: ${key1} 
                    </div> 
                </div>`;
            if (typeof(main_dict)=='object'){
                for (const [key2, child_values] of Object.entries(main_dict)) {
                    div +=`
                        <div class="row"> 
                            <div class="col-md-12">
                                <b>Year</b>: ${key2} 
                            </div> 
                        </div>`;
                    if(Array.isArray(child_values)){
                        let ordered_list = [];
                        frappe.call({
                            method: "akf_hrms.zk_device.doctype.zk_tool.zk_tool.get_sorted_list",
                            async: false,
                            args:{
                                unordered_list: child_values
                            },
                            callback: function(r){
                                ordered_list = r.message;
                                // console.log(ordered_list)
                            }
                        });
                        let rows = ``;
                        for(let i in ordered_list){
                            let log = moment(ordered_list[i]).format("DD-MM-YYYY hh:mm:ss a")
                            rows += `
                                <tr>
                                    <!-- th scope="row">${key1}</th -->
                                    <td scope="row">${key2}</td>
                                    <td class="text-right" scope="row">${log}</td> 
                                </tr>`;
                        }
                        div += `
                        <div class="row"> 
                            <div class="col-md-12">
                                <table class="table">
                                    <thead class="thead-dark">
                                        <tr>
                                            <!-- th scope="col">Biometric ID</th -->
                                            <th scope="col">Year</th>
                                            <th class="text-right" scope="col">Log</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${rows}
                                    </tbody>
                                </table>
                            </div> 
                        </div>
                        `;
                    }
                }
                frm.set_df_property("logs_table", "options", div);
            }
        }
    });
}

function get_employees(frm) {
    frm.set_intro('');
    frm.set_intro('Fetching employees...');
    frm.call('get_employees')
        .then(r => {
            frm.set_intro(r.message);
            frm.save()
            // frm.refresh();
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

function fetch_attendance(frm) {
    frm.set_intro('');
    frm.set_intro('Fetching attendance...');
    frm.call('fetch_attendance')
        .then(r => {
            frm.set_intro(r.message);
            frm.save()
        });
}

function mark_attendance(frm) {
    // frm.set_intro('');
    // frm.set_intro('Marking attendance...', 'blue');
    // frm.set_value("progress_message", "Marking attendance...")
    frm.call('mark_attendance')
        .then(r => {
            // console.log(r.message)
            // frm.set_intro('');
            // frm.set_intro(r.message, 'green');
            // frm.save()
        });
}

frappe.realtime.on('event_name', (data) => {
    console.log(data)
})