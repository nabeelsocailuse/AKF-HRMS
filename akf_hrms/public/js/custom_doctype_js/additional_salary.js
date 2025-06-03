// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Additional Salary', {
    refresh: function(frm){
        frm.trigger("showWorkFlowState");
    },
	salary_component: function(frm) {
        if(frm.doc.salary_component === 'Marriage Allowance'){
            let employee_id = frm.doc.employee
            if (employee_id) {
                frappe.call({
                    method: 'frappe.client.get_list',
                    args:{
                        doctype: 'Salary Structure Assignment',
                        filters: {
                            employee: employee_id
                        },
                        fields: ['base', 'from_date'],
                        order_by: 'from_date desc',
                        limit_page_length: 1 
                    },
                    callback: function(response) {
                        if (response && response.message && response.message.length > 0){
                            let salary_assignment = response.message[0];
                            let gross_salary = salary_assignment.base;
                            frm.set_value('amount', gross_salary);
                        } else {
                            frappe.msgprint("No Salary Structure Assignmen found for this employee.")
                        }
                    }
                });
            } else {
                frappe.msgprint("Please select an employee.")
                frm.set_value('salary_component', '')
            }
        }
	},
    showWorkFlowState: function(frm){
		if(frm.doc.custom_tracking_information==undefined) {
			frm.set_df_property('custom_tracking_html', 'options', '<p></p>')
		}else{
			const stateObj = JSON.parse(frm.doc.custom_tracking_information)
			let rows = ``;
			let idx = 1
			// for (const data of orderedStates) {
            for (const data of stateObj) {
				const dt = moment(data.modified_on).format("DD-MM-YYYY hh:mm:ss a");
				rows += `
				<tr>
					<th scope="row">${idx}</th>	
					<td scope="row">${data.employee_name}</td>
					<td scope="row">${data.current_state}</td>
					<td class="">${dt}</td>
					<td class="">${data.next_state}</td>
					
				</tr>`;
				idx += 1;
			}
			let _html_ = `
			<table class="table">
				<thead class="thead-dark">
					<tr>
					<th scope="col">#</th>
					<th class="text-left" scope="col">Employee Name</th>
					<th class="text-left" scope="col">Current State</th>
					<th class="text-left" scope="col">DateTime</th>
					<th scope="col">Next State(Employee Name, Role)</th>
					</tr>
				</thead>
				<tbody>
					${rows}
				</tbody>
			</table>`;
			frm.set_df_property('custom_tracking_html', 'options', _html_)
		}
	},
});
