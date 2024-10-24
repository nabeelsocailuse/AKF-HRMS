frappe.ui.form.on('Attendance Adjustment', {
    refresh: function (frm) {
        if(!frm.is_new()){
            loadSevenDaysStats(frm);
            loadCompensateOnStats(frm);
            de_link(frm);
        }
    },
    employee: function (frm) {
        loadSevenDaysStats(frm);
        // frm.set_value('custom_adjustment_date', '');
        // frm.set_value('custom_adjustment_hours', '');
    },
    custom_adjustment_date: function (frm) {
       
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
        frm.trigger('set_compensation');
    },
    compensation_type: function (frm) {
        frm.trigger('set_compensation')
    },
    set_compensation: function(frm){
        if(frm.doc.compensation_date!=undefined && frm.doc.compensation_type!=""){
            frm.call('get_compensation_for').then(r=>{
                frm.set_value('compensation_for', r.message==undefined?null:r.message);
                loadCompensateOnStats(frm);
            });
        }else{
            frm.set_value('compensation_for', null);
        }
    }
});

function de_link(frm){
    if(frm.doc.docstatus!=1) return;
    
        frm.call('verify_linkages').then(r=>{
            if(r.message){
                frm.add_custom_button(__('De Link'), () => {
                    frappe.confirm('Are you sure you want to proceed?',
                    () => {
                        // action to perform if Yes is selected
                        frm.call('de_link').then(r=>{
                            // show_alert with indicator
                            frappe.show_alert({
                                message:__('All attendance linkages are reset!'),
                                indicator:'green'
                            }, 5);
                            frm.refresh();
                        });
                    },
                    () => {
                        // action to perform if No is selected
                    })
                });
            }
        });
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