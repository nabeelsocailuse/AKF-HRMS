import frappe
from hrms.hr.doctype.shift_type.shift_type import ShiftType
from frappe.utils import getdate, add_to_date, get_time, time_diff_in_hours

class XShiftType(ShiftType):
    def validate(self):
        self.calculate_working_hours()
        self.calculate_grace_period()

    def calculate_working_hours(self):
        self.custom_total_working_hours = time_diff_in_hours(self.end_time, self.start_time)

    def calculate_grace_period(self):
        if (not self.enable_auto_attendance): return
        self.custom_grace_in_time = self.get_grace_time(self.start_time, self.late_entry_grace_period, True) if(self.enable_late_entry_marking) else None
        self.custom_grace_out_time = self.get_grace_time(self.end_time, self.early_exit_grace_period) if(self.enable_early_exit_marking) else None
    
    def get_grace_time(self, _time_, grace_minutes, graceflag=False):
        stime = str(_time_).split(":")
        hours = int(stime[0])
        minutes = int(stime[1]) + int(grace_minutes) if (graceflag) else -int(grace_minutes)
        seconds = int(stime[2])
        return get_time(add_to_date(getdate(), hours=hours, minutes=minutes, seconds=seconds))
        
       