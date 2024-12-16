// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Additional Salary', {
	
	salary_component: function(frm) {
		console.log("Mubashir Testing");

        if(frm.doc.salary_component === 'Marriage Allowance'){
            let employee_id = frm.doc.employee
            if (employee_id) {
                frappe.call({
                    method: 'frappe.client.get_list',
                    args:{
                        doctype: 'Salary Structure Assignment',
                        filters: {
                            employee: employee_id,
                            docstatus: 1
                        },
                        fields: ['base', 'from_date'],
                        order_by: 'from_date desc',
                        limit_page_length: 1 
                    },
                    callback: function(response) {
                        if (response && response.message && response.message.length > 0){
                            let salary_assignment = response.message[0];
                            let gross_salary = salary_assignment.base;
                            console.log('gross salary: ', gross_salary);
                            
                            
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
});
