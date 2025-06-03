// Mubahsir Bashir 29-05-25

frappe.ui.form.on("Expense Claim Type", {
	refresh: function(frm) {
		frm.fields_dict["accounts"].grid.get_field("default_account").get_query = function(doc, cdt, cdn) {
			var d = locals[cdt][cdn];
			return {
				filters: {
					"is_group": 0,
					"root_type": frm.doc.deferred_expense_account ? "Asset" : "Expense",
					'company': d.company
				}
			}
		}
	},
    onload: function (frm) {
        loadEmployeeGrades(frm);
    }
});

function loadEmployeeGrades(frm) {
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Employee Grade',
            fields: ['name'],
            limit_page_length: 1000
        },
        callback: function (res) {
            if (res.message) {
                const existing_grades = frm.doc.expense_amounts.map(row => row.grade);
                
                const sorted_grades = res.message.sort((a, b) => a.name.localeCompare(b.name));

                sorted_grades.forEach(grade_doc => {
                    if (!existing_grades.includes(grade_doc.name)) {
                        let row = frm.add_child('expense_amounts');
                        row.grade = grade_doc.name;
                        row.amount = 0;
                    }
                });
                // Manually sorting all rows by grade after adding
                frm.doc.expense_amounts.sort((a, b) => a.grade.localeCompare(b.grade));
                frm.refresh_field('expense_amounts');
            }
        }
    });
}




