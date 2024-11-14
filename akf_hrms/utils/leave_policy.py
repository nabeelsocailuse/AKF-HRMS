import frappe
from frappe.utils import (date_diff)
def verify_half_day_leave(self=None):
    if(self.leave_type in ['Half Leave', 'Half Day Leave'] and self.from_date and self.to_date):
        no_of_days = date_diff(self.to_date, self.from_date) + 1
        if(no_of_days>1):
            frappe.throw(f"You can avail only for '1-day'.", title=f'{self.leave_type}')
            