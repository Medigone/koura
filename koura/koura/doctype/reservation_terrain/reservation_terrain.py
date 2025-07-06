# Copyright (c) 2025, IntraPro and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_to_date, get_datetime, get_weekday, flt
from datetime import timedelta


class ReservationTerrain(Document):
	"""DocType pour la gestion des réservations de terrain."""
	
	def validate(self):
		"""Validation des données de réservation."""
		self.calculate_end_time()
		self.validate_availability()
		self.calculate_pricing()
	
	def calculate_end_time(self):
		"""Calcule l'heure de fin basée sur la durée."""
		if self.date_heure_debut and self.duree_heures:
			debut = get_datetime(self.date_heure_debut)
			fin = debut + timedelta(hours=self.duree_heures)
			self.date_heure_fin = fin
	
	def validate_availability(self):
		"""Valide la disponibilité du terrain."""
		if not self.terrain or not self.date_heure_debut or not self.date_heure_fin:
			return
		
		# Vérifier si le terrain existe et est disponible
		terrain_doc = frappe.get_doc("Terrain", self.terrain)
		if not terrain_doc.disponible or terrain_doc.statut_terrain != "Disponible":
			frappe.throw(
				frappe._("Le terrain {0} n'est pas disponible.").format(self.terrain)
			)
		
		# Vérifier les horaires d'ouverture
		self.validate_opening_hours(terrain_doc)
		
		# Vérifier les conflits avec d'autres réservations
		self.validate_conflicts()
	
	def validate_opening_hours(self, terrain_doc):
		"""Valide que la réservation respecte les horaires d'ouverture."""
		if not terrain_doc.horaires_ouverture or not terrain_doc.horaires_fermeture:
			return
		
		debut = get_datetime(self.date_heure_debut)
		fin = get_datetime(self.date_heure_fin)
		
		# Vérifier pour chaque jour de la réservation
		current_date = debut.date()
		end_date = fin.date()
		
		while current_date <= end_date:
			# Calculer les heures pour ce jour
			day_start = max(debut, get_datetime(f"{current_date} {terrain_doc.horaires_ouverture}"))
			day_end = min(fin, get_datetime(f"{current_date} {terrain_doc.horaires_fermeture}"))
			
			if day_start.time() < get_datetime(f"{current_date} {terrain_doc.horaires_ouverture}").time():
				frappe.throw(
					frappe._("La réservation commence avant l'heure d'ouverture du terrain ({0}).").format(terrain_doc.horaires_ouverture)
				)
			
			if day_end.time() > get_datetime(f"{current_date} {terrain_doc.horaires_fermeture}").time():
				frappe.throw(
					frappe._("La réservation se termine après l'heure de fermeture du terrain ({0}).").format(terrain_doc.horaires_fermeture)
				)
			
			current_date = current_date + timedelta(days=1)
	
	def validate_conflicts(self):
		"""Valide qu'il n'y a pas de conflit avec d'autres réservations."""
		filters = {
			"terrain": self.terrain,
			"statut": ["in", ["Confirmée", "En cours"]],
			"date_heure_debut": ["<", self.date_heure_fin],
			"date_heure_fin": [">", self.date_heure_debut]
		}
		
		# Exclure la réservation actuelle si c'est une modification
		if not self.is_new():
			filters["name"] = ["!=", self.name]
		
		conflicting_reservations = frappe.get_list(
			"Reservation Terrain",
			filters=filters,
			fields=["name", "date_heure_debut", "date_heure_fin"]
		)
		
		if conflicting_reservations:
			conflict = conflicting_reservations[0]
			frappe.throw(
				frappe._("Conflit avec la réservation {0} ({1} - {2}).").format(
					conflict.name,
					conflict.date_heure_debut,
					conflict.date_heure_fin
				)
			)
	
	def calculate_pricing(self):
		"""Calcule le prix de la réservation."""
		if not self.terrain or not self.date_heure_debut or not self.duree_heures:
			return
		
		terrain_doc = frappe.get_doc("Terrain", self.terrain)
		debut = get_datetime(self.date_heure_debut)
		
		# Obtenir le jour de la semaine
		jour_semaine = get_weekday(debut.date())
		jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
		jour_nom = jours[jour_semaine]
		
		# Obtenir le prix pour ce créneau
		prix_unitaire = terrain_doc.get_prix_creneau(
			jour_nom,
			debut.time().strftime("%H:%M:%S"),
			"Normal"  # TODO: Détecter automatiquement le type d'événement
		)
		
		self.prix_unitaire = prix_unitaire
		self.montant_total = flt(prix_unitaire * self.duree_heures, 0)
	
	def on_submit(self):
		"""Actions à effectuer lors de la soumission."""
		self.statut = "Confirmée"
		self.create_sales_invoice()
	
	def create_sales_invoice(self):
		"""Crée une facture de vente dans ERPNext."""
		if self.sales_invoice:
			return
		
		try:
			# Créer la facture de vente
			sales_invoice = frappe.get_doc({
				"doctype": "Sales Invoice",
				"customer": self.client,
				"posting_date": self.date_reservation,
				"due_date": self.date_reservation,
				"items": [{
					"item_code": "RESERVATION_TERRAIN",  # Item à créer dans ERPNext
					"item_name": f"Réservation Terrain {self.terrain}",
					"description": f"Réservation du terrain {self.terrain} le {self.date_reservation} de {self.date_heure_debut} à {self.date_heure_fin}",
					"qty": self.duree_heures,
					"rate": self.prix_unitaire,
					"amount": self.montant_total
				}],
				"custom_reservation_terrain": self.name
			})
			
			sales_invoice.insert()
			self.sales_invoice = sales_invoice.name
			self.save()
			
		except Exception as e:
			frappe.log_error(f"Erreur lors de la création de la facture: {str(e)}")
	
	def on_cancel(self):
		"""Actions à effectuer lors de l'annulation."""
		self.statut = "Annulée"
		
		# Annuler la facture si elle existe
		if self.sales_invoice:
			try:
				sales_invoice = frappe.get_doc("Sales Invoice", self.sales_invoice)
				if sales_invoice.docstatus == 1:
					sales_invoice.cancel()
			except Exception as e:
				frappe.log_error(f"Erreur lors de l'annulation de la facture: {str(e)}")