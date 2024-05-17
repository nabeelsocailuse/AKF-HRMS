import frappe
from frappe.model.document import Document

class TrainingRequest(Document):
    def validate(self):
        participants_in_event = []
        for row in self.custom_attendees:
            query = """
                SELECT employee 
                FROM `tabTraining Event Employee` 
                WHERE parent=%s 
                AND employee=%s
            """
            result = frappe.db.sql(query, (self.custom_topictraining_event, row.participant_id), as_dict=True)
        
            if result:
                participants_in_event.append(row.participant_id)
        
        if participants_in_event:
            participants_str = ", ".join(participants_in_event)
            frappe.throw(f"The employee {participants_str} are already in this training event.")
        
    def on_submit(self):
        if (self.custom_approval_status != 'Approved by the Head of Department'):
            frappe.throw('Training Request can only be submitted when status is "Approved by the Head of Department".')
        
        # Implementation of the existing employees 
        event_id = self.custom_topictraining_event
        for row in self.custom_attendees:
            query = f"""
                SELECT employee 
                FROM `tabTraining Event Employee` 
                WHERE parent='{event_id}' 
                AND employee='{row.participant_id}'
            """
            result = frappe.db.sql(query, as_dict=True)
            if not result:
                doc = frappe.get_doc("Training Event", event_id)
                doc.append('employees', {
                    'employee': row.participant_id,
                    'employee_name': row.participant_name
                })
                doc.save()
    
    def on_cancel(self):
        # Remove participants from the associated training event
        event_id = self.custom_topictraining_event
        for row in self.custom_attendees:
            frappe.db.sql("""
                DELETE FROM `tabTraining Event Employee`
                WHERE parent=%s AND employee=%s
            """, (event_id, row.participant_id))