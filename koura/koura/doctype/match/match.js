// Copyright (c) 2025, IntraPro and contributors
// For license information, please see license.txt

frappe.ui.form.on("Match", {
	refresh(frm) {

	},
	type: function(frm) {
		if (frm.doc.type === "6 Vs 6") {
			frm.set_value('nbr_jr_blanc', 6);
			frm.set_value('nbr_jr_noir', 6);
		} else if (frm.doc.type === "8 Vs 8") {
			frm.set_value('nbr_jr_blanc', 8);
			frm.set_value('nbr_jr_noir', 8);
		} else if (frm.doc.type === "11 Vs 11") {
			frm.set_value('nbr_jr_blanc', 11);
			frm.set_value('nbr_jr_noir', 11);
		}
	}
});
