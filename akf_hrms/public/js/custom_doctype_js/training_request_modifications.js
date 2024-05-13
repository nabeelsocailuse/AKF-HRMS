frappe.ui.form.on('Training Request', {
    custom_workshoptraining_program: function(frm) {
        // When the custom_workshoptraining_program field changes
        frm.trigger('set_custom_training_event_query');
    },

    set_custom_training_event_query: function(frm) {
        var trainingProgram = frm.doc.custom_workshoptraining_program;
        // Set the query for the custom_topictraining_event field
        frm.set_query('custom_topictraining_event', function() {
            return {
                filters: {
                    training_program: trainingProgram
                }
            };
        });
    },

    validate: function(frm) {
        var startTime = frm.doc.proposed_start_time;
        var endTime = frm.doc.proposed_end_time;
        if (startTime >= endTime) {
            frappe.throw(__("The Proposed Start Time must be less than the Proposed End Time."));
        }
    },

    addCustomButtons: function(frm) {
        frm.page.add_custom_button(__('Training Programs'), function() {
            frappe.set_route('List', 'Training Program');
        });

        frm.page.add_custom_button(__('Training Events'), function() {
            frappe.set_route('List', 'Training Event');
        });
    },

    on_load: function(frm) {
        this.addCustomButtons(frm);
    },

    custom_status_of_approval: function(frm) {
        if (frm.doc.status == 'Open') {
            frappe.call({
                method: 'akf_hrms.services.training_event_employees.append_employees_to_training_event',
                args: {
                    training_request_name: frm.doc.name
                },
                callback: function(response) {
                    if (response.message) {
                        frappe.msgprint('Employee added to Training Event.');
                        // Refresh the form to reflect changes
                        frm.refresh();
                    }
                }
            });
        }
    }
});
