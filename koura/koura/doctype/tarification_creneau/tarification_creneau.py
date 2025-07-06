# Copyright (c) 2025, IntraPro and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import get_time, get_datetime


class TarificationCreneau(Document):
	"""DocType pour gérer la tarification et la disponibilité des créneaux."""
	
	def validate(self):
		"""Validation des données du créneau."""
		self.validate_time_range()
		self.validate_price()
	
	def validate_time_range(self):
		"""Valide que l'heure de fin est après l'heure de début."""
		if self.heure_debut and self.heure_fin:
			if get_time(self.heure_debut) >= get_time(self.heure_fin):
				frappe.throw(_("L'heure de fin doit être après l'heure de début."))
	
	def validate_price(self):
		"""Valide que le prix est positif."""
		if self.prix_creneau and self.prix_creneau < 0:
			frappe.throw(_("Le prix du créneau ne peut pas être négatif."))
	
	def set_statut_reserve(self):
		"""Marque le créneau comme réservé."""
		self.statut_creneau = "Réservé"
		self.disponible = 0
		self.save()
	
	def set_statut_disponible(self):
		"""Marque le créneau comme disponible."""
		self.statut_creneau = "Disponible"
		self.disponible = 1
		self.save()
	
	def set_statut_maintenance(self):
		"""Marque le créneau en maintenance."""
		self.statut_creneau = "Maintenance"
		self.disponible = 0
		self.save()
	
	def is_available_for_booking(self):
		"""Vérifie si le créneau est disponible pour réservation.
		
		Returns:
			bool: True si disponible, False sinon
		"""
		return self.disponible and self.statut_creneau == "Disponible"
	
	def get_duration_hours(self):
		"""Calcule la durée du créneau en heures.
		
		Returns:
			float: Durée en heures
		"""
		if self.heure_debut and self.heure_fin:
			debut = get_time(self.heure_debut)
			fin = get_time(self.heure_fin)
			
			# Convertir en secondes puis en heures
			debut_seconds = debut.hour * 3600 + debut.minute * 60 + debut.second
			fin_seconds = fin.hour * 3600 + fin.minute * 60 + fin.second
			
			# Gérer le cas où le créneau traverse minuit
			if fin_seconds < debut_seconds:
				fin_seconds += 24 * 3600
			
			return (fin_seconds - debut_seconds) / 3600
		
		return 0