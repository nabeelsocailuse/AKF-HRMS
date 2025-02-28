// This module is overridden by Mubashir on 29-01-2025

frappe.ui.form.on("Job Requisition", {
    // Mubashir Bashir 29-01-2025 Start
    onload: function(frm) {
        if (frm.__islocal) {
            frm.set_value("posting_date", frappe.datetime.nowdate());
        }
    },
    // Mubashir Bashir 29-01-2025 End
	refresh: function(frm) {
		if (!frm.doc.__islocal && !["Filled", "On Hold", "Cancelled"].includes(frm.doc.status)) {
			frappe.db.get_list("Employee Referral", {
				filters: { for_designation: frm.doc.designation, status: "Pending" }
			}).then((data) => {
				if (data && data.length) {
					const link = data.length > 1
						? `<a id="referral_links" style="text-decoration: underline;">${__("Employee Referrals")}</a>`
						: `<a id="referral_links" style="text-decoration: underline;">${__("Employee Referral")}</a>`;

					const headline = __("{} {} open for this position.", [data.length, link]);
					frm.dashboard.clear_headline();
					frm.dashboard.set_headline(headline, "yellow");

					$("#referral_links").on("click", (e) => {
						e.preventDefault();
						frappe.set_route("List", "Employee Referral", {
							for_designation: frm.doc.designation,
							status: "Pending"
						});
					});
				}
			})
		}

		if (frm.doc.status === "Open & Approved") {
			frm.add_custom_button(__("Create Job Opening"), () => {
				frappe.model.open_mapped_doc({
					method: "akf_hrms.akf_hrms.doctype.job_requisition.job_requisition.make_job_opening",
					frm: frm
				});
			}, __("Actions"));

			frm.add_custom_button(__("Associate Job Opening"), () => {
				frappe.prompt({
					label: __("Job Opening"),
					fieldname: "job_opening",
					fieldtype: "Link",
					options: "Job Opening",
					reqd: 1,
					get_query: () => {
						const filters = {
							company: frm.doc.company,
							status: "Open",
							designation: frm.doc.designation,
						}

						if (frm.doc.department)
							filters.department = frm.doc.department;

						return { filters: filters };
					}
				}, (values) => {
					frm.call("associate_job_opening", { job_opening: values.job_opening });
				}, __("Associate Job Opening"), __("Submit"));
			}, __("Actions"));

			frm.page.set_inner_btn_group_as_primary(__("Actions"));
		}
	},

	// Mubashir Bashir 28-02-2025 Start
	designation: function(frm) {
		fetch_no_of_positions(frm);
	},

	no_of_positions: function(frm) {
        let remaining_vacancies = frm.doc.remaining_vacancies || 0; 
        if (frm.doc.no_of_positions > remaining_vacancies) {
            frappe.msgprint(__('You cannot enter more than the available vacancies.'));
            frm.set_value('no_of_positions', remaining_vacancies);
        }
    }
});

function fetch_no_of_positions(frm) {
    if (!frm.doc.company || !frm.doc.custom_branch || !frm.doc.department) {
        frappe.msgprint(__('Please select Company, Branch and Department first.'));
        return;
    }

    frappe.call({
        method: "akf_hrms.akf_hrms.doctype.job_requisition.job_requisition.get_vacancies_from_staffing_plan",
        args: {
            company: frm.doc.company,
			branch: frm.doc.custom_branch,
			department: frm.doc.department,
            designation: frm.doc.designation,
            posting_date: frm.doc.posting_date
        },
        callback: function(r) {
            if (r.message) {
                frm.set_value('staffing_plan', r.message.staffing_plan);
                frm.set_value('no_of_positions', r.message.remaining_vacancies);
                frm.set_value('current_count', r.message.current_count);
                frm.doc.remaining_vacancies = r.message.remaining_vacancies;  
            } else {
                frm.set_value('designation', '');
                frm.set_value('staffing_plan', '');
                frm.set_value('no_of_positions', 0);
                frm.set_value('current_count', '');
                frm.doc.remaining_vacancies = 0;
                frappe.msgprint(__('No matching staffing plan found for this designation.'));
            }
        }
    });
}

// Mubashir Bashir 28-02-2025 End