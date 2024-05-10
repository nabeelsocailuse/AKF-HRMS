frappe.ui.form.on('Attendance', {
    refresh: function (frm) {
        frm.dashboard.hide();
        if(frm.doc.docstatus!=2){
        load_log_details(frm);
        }
    },
});

function load_log_details(frm) {
    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Attendance Log",
            filters: {
                "company": frm.doc.company,
                "employee": frm.doc.employee,
                "attendance_date": frm.doc.attendance_date
            },
            fields: ["device_id", "log", "log_type"],
            group_by: "log",
            order_by: "log asc"
        },
        callback: function (r) {
            let data = r.message;
            let rows = ``;
            let idx = 1
            data.forEach(element => {
                let log = moment(element.log).format("DD-MM-YYYY hh:mm:ss a")
                rows += `
                <tr>
                    <th scope="row">${idx}</th>
                    <td class="">${element.device_id}</td>
                    <td class="">${log}</td>
                    <td>${element.log_type}</td>
                    
                </tr>`;
                idx += 1;
            });
            let _html_ = `
            <table class="table">
                <thead class="thead-dark">
                    <tr>
                    <th scope="col">#</th>
                    <th class="" scope="col">Biometric ID</th>
                    <th class="" scope="col">Log</th>
                    <th scope="col">Log Type</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows}
                </tbody>
            </table>`;
            frm.set_df_property("custom_logs_table", "options", _html_);
        }
    })
}