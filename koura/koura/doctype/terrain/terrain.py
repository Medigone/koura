# Copyright (c) 2025, IntraPro and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import get_time, time_diff_in_hours


class Terrain(Document):
	"""DocType pour la gestion des terrains de football."""
	
	def validate(self):
		"""Validation des données du terrain."""
		self.validate_horaires()
		self.validate_tarification()
	
	def validate_horaires(self):
		"""Valide que l'heure d'ouverture est antérieure à l'heure de fermeture."""
		if self.horaires_ouverture and self.horaires_fermeture:
			ouverture = get_time(self.horaires_ouverture)
			fermeture = get_time(self.horaires_fermeture)
			
			if ouverture >= fermeture:
				frappe.throw(
					frappe._("L'heure d'ouverture doit être antérieure à l'heure de fermeture.")
				)
	
	def validate_tarification(self):
		"""Valide les créneaux de tarification."""
		if not self.tarification_creneaux:
			return
		
		for creneau in self.tarification_creneaux:
			if creneau.heure_debut and creneau.heure_fin:
				debut = get_time(creneau.heure_debut)
				fin = get_time(creneau.heure_fin)
				
				if debut >= fin:
					frappe.throw(
						frappe._("Ligne {0}: L'heure de début doit être antérieure à l'heure de fin.").format(creneau.idx)
					)
	
	def get_prix_creneau(self, jour, heure, type_evenement="Normal"):
		"""Retourne le prix pour un créneau donné.
		
		Args:
			jour (str): Jour de la semaine
			heure (str): Heure au format HH:MM:SS
			type_evenement (str): Type d'événement
			
		Returns:
			float: Prix du créneau ou prix par heure par défaut
		"""
		heure_obj = get_time(heure)
		
		# Recherche d'un créneau spécifique
		for creneau in self.tarification_creneaux:
			if (
				(creneau.jour_semaine == jour or creneau.jour_semaine == "Tous les jours")
				and creneau.type_evenement == type_evenement
				and get_time(creneau.heure_debut) <= heure_obj <= get_time(creneau.heure_fin)
			):
				return creneau.prix_creneau
		
		# Retourne le prix par heure par défaut
		return self.prix_par_heure or 0
	
	def is_disponible(self, date_heure_debut, date_heure_fin):
		"""Vérifie si le terrain est disponible pour une période donnée.
		
		Args:
			date_heure_debut (datetime): Date et heure de début
			date_heure_fin (datetime): Date et heure de fin
			
		Returns:
			bool: True si disponible, False sinon
		"""
		if not self.disponible or self.statut_terrain != "Disponible":
			return False
		
		# Vérifier les réservations existantes
		reservations_conflictuelles = frappe.db.count(
			"Reservation Terrain",
			filters={
				"terrain": self.name,
				"statut": ["in", ["Confirmée", "En cours"]],
				"date_heure_debut": ["<", date_heure_fin],
				"date_heure_fin": [">", date_heure_debut]
			}
		)
		
		return reservations_conflictuelles == 0