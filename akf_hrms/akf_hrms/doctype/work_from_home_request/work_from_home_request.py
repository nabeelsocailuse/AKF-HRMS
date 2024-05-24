# -*- coding: utf-8 -*-
# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import (
    date_diff,
    getdate,
    formatdate
)
from frappe import _


class WorkFromHomeRequest(Document):
    def validate(self):
        self.validate_dates()
        self.wfh_for_samedates()
        self.count_total_days()

    def wfh_for_samedates(self):
        get_previos_data = frappe.db.sql(
            """ select name from `tabWork From Home Request` 
                where docstatus<2
                    and (%s between from_date and to_date) and (%s between from_date and to_date) 
                    and employee=%s 
                    and name!=%s """,
            (
                str(self.from_date),
                str(self.to_date),
                self.employee,
                self.name
            ),
            as_dict=1,
        )
        if (get_previos_data):
            frappe.throw(_(f"`Work From Home Request` already exist b/w dates {formatdate(self.from_date)} and {formatdate(self.to_date)}"))

    def count_total_days(self):
        self.total_days = 0.0
        self.total_days += float(date_diff(self.to_date, self.from_date)) + 1.0
        holidays_count = self.get_holiday()
        self.total_days -= holidays_count
        year, month, date = str(self.from_date).split("-")
        self.year = year
        self.month = month

    def validate_dates(self):
        if (
            self.from_date
            and self.to_date
            and (getdate(self.to_date) < getdate(self.from_date))
        ):
            frappe.throw(_("To date cannot be less than from date"))

    def check_limit_per_month(self):
        month_first_date = frappe.utils.get_first_day(self.from_date)
        month_last_date = frappe.utils.get_last_day(self.from_date)
        total_ = 0.0
        get_previos_data = frappe.db.sql(
            """ select ifnull(sum(total_days),0) from `tabWork From Home Request` where docstatus=1
                and from_date between %s and %s and employee=%s """,
            (str(month_first_date), str(month_last_date), self.employee),
        )
        if get_previos_data:
            total_ = float(get_previos_data[0][0])
        total_days_ = float(total_) + float(self.total_days)
        get_total_days = frappe.db.get_value("HR Settings", None, "max_wfh_allowed")
        if not get_total_days:
            get_total_days = 0
        if total_days_ > float(get_total_days):
            frappe.throw(
                "Your monthly limit exceed for {0} days WFH, please coordinate with HR department".format(
                    get_total_days
                )
            )

    def get_holiday(self):
        holidays = 0
        if self.holiday_list:
            get_count = frappe.db.sql_list(
                """select day(holiday_date) from `tabHoliday` where parent=%s and holiday_date between %s and %s """,
                (self.holiday_list, self.from_date, self.to_date),
            )
            if get_count:
                holidays = len(get_count)
        return holidays
