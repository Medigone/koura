# Copyright (c) 2025, IntraPro and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import get_time


class HoraireDisponibiliteArticle(Document):
	"""DocType pour gérer les horaires de disponibilité des articles."""
	
	def validate(self):
		"""Validation des données d'horaire."""
		self.validate_time_range()
	
	def validate_time_range(self):
		"""Valide que l'heure de fin est après l'heure de début."""
		if self.heure_debut and self.heure_fin:
			if get_time(self.heure_debut) >= get_time(self.heure_fin):
				frappe.throw(_("L'heure de fin doit être après l'heure de début."))