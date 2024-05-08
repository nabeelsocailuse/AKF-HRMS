frappe.ui.form.on("Employee", {
  refresh: function(frm) {
      frm.cscript.date_of_joining = function(doc, cdt, cdn) {
          var date_of_joining = doc.date_of_joining;
          if (date_of_joining) {
              var now = new Date();
              var join_date = new Date(date_of_joining);
              var diffInMonths = (now.getFullYear() - join_date.getFullYear()) * 12 + (now.getMonth() - join_date.getMonth());

              var years = Math.floor(diffInMonths / 12);
              var months = diffInMonths % 12;

              var total_duration = years + ' Yr ' + months + ' Months';
              frm.set_value('custom_total_duration', total_duration);
          } else {
              frm.set_value('custom_total_duration', '');
          }
      };
  }
});
