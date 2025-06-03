frappe.ui.form.on('Employee Advance', {
    refresh: function(frm){
        frm.trigger("showWorkFlowState"); 
    },
    showWorkFlowState: function(frm){
		if(frm.doc.custom_state_data==undefined) {
			frm.set_df_property('custom_state_html', 'options', '<p></p>')
		}else{
			const stateObj = JSON.parse(frm.doc.custom_state_data)
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
			frm.set_df_property('custom_state_html', 'options', _html_)
		}
	},
});