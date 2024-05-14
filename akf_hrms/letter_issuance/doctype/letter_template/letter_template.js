// Copyright (c) 2020, publisher and contributors
// For license information, please see license.txt

frappe.ui.form.on('Letter Template', {
	// refresh: function(frm) {

	// }
	refresh: function(frm) {
		//frm.trigger("make_dashboard");
	},
	onload: function(frm) {
		$('div[data-fieldname="html_2"]').attr('title',''); 
		$("[data-fieldname='html_2']").html(`<style>
table, th, td {
  border: 1px solid black;
  border-collapse: collapse;
}
</style>Note: Use short codes to add values from Employee form. e.g. For "Date of Joining" short code will be {{date_of_joining}} and for Designation short code will be {{designation}}.<br><h4>Some shortcut Keys</h4>
	<table width=100%>
		<tr>
			<th>employee_code</th>
			<td>{{employee_code}}</td>
		</tr>
		<tr>
			<th>Series</th>
			<td>{{series}}</td>
		</tr>
		<tr>
			<th>Today Date</th>
			<td>{{today_date}}</td>
		</tr>
		<tr>
			<th>Salary</th>
			<td>{{salary}}</td>
		</tr>
	</table>`);
	},
	make_dashboard: function(frm) {
		$("div").remove(".form-dashboard-section");
		frm.dashboard.add_section(
			frappe.render_template('letter_template_dashboard', {
			})
		);
		frm.dashboard.show();
	},
});
