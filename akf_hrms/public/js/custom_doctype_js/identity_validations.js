let NoArrays = ['custom_id_number'];
// Id number validations
var id_mask=null;
var id_mask_length=0;
var id_regex = null;
var custom_label = null;

frappe.ui.form.on('Employee', {
    refresh: function(frm) {
        // console.log('working.')
        if (!frm.doc.__islocal) {
            frm.set_query('referee_id', function(doc) {
                return {
                    filters: {
                        'name': ['!=', frm.doc.name]
                    }
                };
            });
        }
        custom_country_change(frm);
    },
    // validate: function(frm) {
    //     // Validate the ID number field
    //     if (frm.doc.custom_cnic) {
    //         const labelName = __(frm.fields_dict['custom_cnic'].df.label);
    //         frm.set_intro(``);
    //         if (!internationalIdNumberValidation(frm.doc.custom_cnic, labelName)) {
    //             // frm.set_value('custom_cnic', '');
    //             frm.set_intro(`Please enter valid ${labelName}`, 'red');
    //         }
    //     }
    // },
    custom_cnic: function(frm) {
        if (frm.doc.custom_cnic) {
            const labelName = __(frm.fields_dict['custom_cnic'].df.label);
            frm.set_df_property("custom_cnic", "description", "")
            if (!internationalIdNumberValidation(frm.doc.custom_cnic, labelName)) {
                // frm.set_value('custom_cnic', '');
                frm.set_df_property("custom_cnic", "description", `<p style="color:red">Please enter valid ${labelName}</p>`)
                // frm.set_intro(`Please enter valid ${labelName}`, 'red');
            }
        }
    },
    custom_country: function(frm) {
        frm.set_value("custom_cnic", "");
        custom_country_change(frm);
    }
});

function custom_country_change(frm) {
    var country = frm.doc.custom_country;
    
    if (country) {
        frappe.call({
            method: 'frappe.client.get_value',
            args: {
                doctype: 'Country',
                fieldname: ['custom_label', 'custom_id_mask', 'custom_id_regex'],
                filters: {'name': country}
            },
            callback: function(r) {
                let data = r.message;
                // console.log(data)
                if (data) {
                    id_mask=data.custom_id_mask;
                    id_mask_length=id_mask.length;
                    id_regex = data.custom_id_regex;
                    custom_label = data.custom_label;
                    change_label(frm);
                    apply_mask_on_id_number(frm);
                }
            }
        });
    }
}

function change_label(frm){
    
    frm.set_df_property("custom_cnic", "label", custom_label)
}

function apply_mask_on_id_number(frm) {
    frm.fields_dict["custom_cnic"].$input.mask(id_mask);
    frm.fields_dict["custom_cnic"].$input.attr("placeholder", id_mask);
}

function internationalIdNumberValidation(id_number, labelName) {
    var pattern = new RegExp(id_regex);
    if (!(id_number.match(pattern)) || id_number.length != id_mask.length) {
        // frappe.msgprint(`Please enter valid ${labelName}`);
        return false;
    } else {
        return true;
    }
}
