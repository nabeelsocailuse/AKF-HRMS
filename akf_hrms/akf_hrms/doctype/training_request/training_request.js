frappe.ui.form.on('Training Request', {
    custom_workshoptraining_program: function(frm) {
        // When the custom_workshoptraining_program field changes
        frm.trigger('set_custom_training_event_query');
        // Clear the selected training event if the training program is removed
        if (!frm.doc.custom_workshoptraining_program) {
            frm.set_value('custom_topictraining_event', '');
        }
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

    // Function to add custom buttons on refreshing the Training Request form
    refresh: function(frm) {
        frm.add_custom_button(__('Training Programs'), function() {
            frappe.set_route('List', 'Training Program');
        });

        frm.add_custom_button(__('Training Events'), function() {
            frappe.set_route('List', 'Training Event');
        });
    }
});