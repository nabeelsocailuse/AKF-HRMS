import frappe


@frappe.whitelist()
def on_submit(self, doc, method=None):
    if doc.custom_status_of_approval == 'Open':
        training_event = doc.custom_topictraining_event
        if not training_event:
            frappe.throw(_("Training Event is required."))
        attendees = doc.custom_attendees
        for row in attendees:
            filters = {
                'parent': training_event,
                'employee': row.participant_id,
            }
            response = frappe.get_doc('Training Event Employee', filters)