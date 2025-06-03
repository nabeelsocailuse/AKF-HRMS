// Copyright (c) 2024, Nabeel Saleem and contributors
// For license information, please see license.txt

frappe.ui.form.on("Travel Request", {
    onload(frm) {
        clearFieldsOnLoad(frm); // Mubashir Bashir 13-03-2025
    },
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

        frm.trigger("showWorkFlowState"); // Mubashir Bashir 13-03-2025
    },
    showWorkFlowState: function(frm){
		if(frm.doc.custom_state_data==undefined) {
			frm.set_df_property('custom_state_html', 'options', '<p></p>')
		}else{
			const stateObj = JSON.parse(frm.doc.custom_state_data)
			
			const desiredOrder = [
				"Applied",
				"Recommended By Line Manager",
				"Rejected By Line Manager",
				"Recommended By Head Of Department",
				"Rejected By Head Of Department",
				"Recommended by Chief Executive Officer",
				"Rejected by Chief Executive Officer",
				"Approved",
				"Rejected By Secretary General"
			];

			const orderedStates = desiredOrder
				.filter(state => stateObj.hasOwnProperty(state)) 
				.map(state => ({ key: state, ...stateObj[state] })); 
			

			let rows = ``;
			let idx = 1
			for (const data of orderedStates) {
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
	// Start, Mubashir Bashir, 13-03-2025
	/*showWorkFlowState: function(frm){
		if(frm.doc.custom_state_data==undefined) {
			frm.set_df_property('custom_state_html', 'options', '<p></p>')
		}else{
			const stateObj = JSON.parse(frm.doc.custom_state_data)
			
			const desiredOrder = [
				"Applied",
				"Recommended By Line Manager",
				"Rejected by the Line Manager",
				"Recommended By Head Of Department",
				"Rejected By Head Of Department",
				"Approved",
				"Rejected by Chief Executive Officer"
			];

			const orderedStates = desiredOrder
				.filter(state => stateObj.hasOwnProperty(state)) 
				.map(state => ({ key: state, ...stateObj[state] })); 
			

			let rows = ``;
			let idx = 1
			for (const data of orderedStates) {
				const dt = moment(data.modified_on).format("DD-MM-YYYY hh:mm:ss a");

				rows += `
				<tr>
					<th scope="row">${idx}</th>	
					<td scope="row">${data.current_user}</td>
					<td class="">${data.next_state}</td>
					<td class="">${dt}</td>
				</tr>`;
				idx += 1;
			}
			let _html_ = `
			<table class="table">
				<thead class="thead-dark">
					<tr>
					<th scope="col">#</th>
					<th class="text-left" scope="col">Current State (User)</th>
					<th class="text-left" scope="col">Next State (User)</th>
					<th scope="col">DateTime</th>
					</tr>
				</thead>
				<tbody>
					${rows}
				</tbody>
			</table>`;
			frm.set_df_property('custom_state_html', 'options', _html_)
		}
	},*/
	// End, Mubashir Bashir, 13-03-2025

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
        let today = new Date();
        
        // Zero out the time part for proper date comparison
        today.setHours(0, 0, 0, 0);

        if (departure > arrival) {
            frappe.msgprint({
                title: __('Validation Error'),
                message: __('Departure Date cannot be greater than Arrival Date.'),
                indicator: 'red'
            });

            frappe.model.set_value(cdt, cdn, 'arrival_date', null);
            return;
        }

        // if (departure < today || arrival < today) {
        //     frappe.msgprint({
        //         title: __('Validation Error'),
        //         message: __('Departure Date and Arrival Date cannot be earlier than today.'),
        //         indicator: 'red'
        //     });

        //     if (departure < today) {
        //         frappe.model.set_value(cdt, cdn, 'departure_date', null);
        //     }
        //     if (arrival < today) {
        //         frappe.model.set_value(cdt, cdn, 'arrival_date', null);
        //     }
        // }
    }
}
// Mubashir Bashir 07-02-2025 End


// Mubashir Bashir 13-03-2025 Start
function clearFieldsOnLoad(frm) {
    if (frm.is_new()) {
        frm.set_value('custom_next_workflow_state', '');
        frm.set_value('custom_workflow_indication', '');
        frm.set_value('custom_state_data', '');
        frm.set_value('custom_state_html', '');
    }
}
// Mubashir Bashir 13-03-2025 End