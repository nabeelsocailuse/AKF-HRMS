// Copyright (c) 2024, Nabeel Saleem and contributors
// For license information, please see license.txt

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
    },

    on_submit: function(frm) {
        if (frm.doc.custom_status_of_approval === 'Open') {
            // Ensure we have the name of the Training Event
            const trainingEvent = frm.doc.custom_topictraining_event;
            if (!trainingEvent) {
                frappe.throw('Training Event is required.');
                return;
            }
            // Fetch employee details from the Training Request
            const attendees = frm.doc.custom_attendees;
            console.log(attendees)
            attendees.forEach(row => {
                frappe.call({
                    method: 'frappe.client.insert',
                    async: false,
                    args: {
                        doc: {
                            doctype: 'Training Event Employee',
                            parent: trainingEvent,
                            parenttype: 'Training Event',
                            parentfield: 'employees',
                            employee: row.participant_id,
                            employee_name: row.participant_name
                            // Add other relevant fields as needed
                        }
                    },
                    callback: function(response) {
                        if (response.message) {
                            frappe.set_route(`training-event/${trainingEvent}`)
                        }
                    }
                });
            });
            // Fetch Training Event name from the form
            // Get the Training Event document
            // Update child table (Training Event Employee) in the associated Training Event
            
        }
    }
});
