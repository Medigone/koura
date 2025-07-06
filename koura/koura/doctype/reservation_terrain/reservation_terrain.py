# Copyright (c) 2025, IntraPro and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_to_date, get_datetime, get_weekday, flt, today
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
		
		# Vérifier la disponibilité du terrain et du créneau
		terrain_doc = frappe.get_doc("Terrain", self.terrain)
		
		# Vérifier la disponibilité générale du terrain
		if not terrain_doc.is_disponible(self.date_heure_debut, self.date_heure_fin):
			frappe.throw(frappe._("Le terrain n'est pas disponible pour cette période."))
		
		# Vérifier la disponibilité du créneau spécifique
		jour_semaine = get_datetime(self.date_heure_debut).strftime("%A")
		jour_fr = {
			"Monday": "Lundi", "Tuesday": "Mardi", "Wednesday": "Mercredi",
			"Thursday": "Jeudi", "Friday": "Vendredi", "Saturday": "Samedi", "Sunday": "Dimanche"
		}.get(jour_semaine, jour_semaine)
		
		heure_debut = get_datetime(self.date_heure_debut).time().strftime("%H:%M:%S")
		heure_fin = get_datetime(self.date_heure_fin).time().strftime("%H:%M:%S")
		
		if not terrain_doc.is_creneau_disponible(jour_fr, heure_debut, heure_fin, self.type_evenement or "Normal"):
			frappe.throw(frappe._("Aucun créneau disponible pour cette période et ce type d'événement."))
		
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
		self.create_facture()
	
	def create_facture(self):
		"""Crée une facture dans le système Koura."""
		if self.facture:
			return
		
		try:
			# Créer la facture Koura
			facture = frappe.get_doc({
				"doctype": "Facture",
				"client": self.client,
				"date_facture": self.date_reservation,
				"type_facture": "Réservation",
				"reservation": self.name,
				"statut": "Brouillon",
				"lignes_facture": [{
					"article": "RESERVATION_TERRAIN",
					"description": f"Réservation du terrain {self.terrain} - {self.type_evenement}",
					"quantite": self.duree_heures,
					"prix_unitaire": self.prix_unitaire,
					"montant_ht": self.montant_total
				}]
			})
			
			facture.insert()
			self.facture = facture.name
			self.save()
			
		except Exception as e:
			frappe.log_error(f"Erreur lors de la création de la facture Koura: {str(e)}")
	

	
	def create_paiement(self, montant_paye, mode_paiement="Espèces"):
		"""Crée un paiement pour la réservation.
		
		Args:
			montant_paye (float): Montant payé
			mode_paiement (str): Mode de paiement
		"""
		if not self.facture:
			frappe.throw("Aucune facture associée à cette réservation.")
		
		try:
			paiement = frappe.get_doc({
				"doctype": "Paiement",
				"facture": self.facture,
				"client": self.client,
				"date_paiement": frappe.utils.today(),
				"montant_paiement": montant_paye,
				"mode_paiement": mode_paiement,
				"statut": "Validé"
			})
			
			paiement.insert()
			paiement.submit()
			
			self.paiement = paiement.name
			self.statut_paiement = "Payé" if montant_paye >= self.montant_total else "Partiellement Payé"
			self.save()
			
			return paiement.name
			
		except Exception as e:
			frappe.log_error(f"Erreur lors de la création du paiement: {str(e)}")
			frappe.throw(f"Erreur lors de la création du paiement: {str(e)}")
	
	def on_cancel(self):
		"""Actions à effectuer lors de l'annulation."""
		self.statut = "Annulée"
		
		# Annuler la facture Koura si elle existe
		if self.facture:
			try:
				facture = frappe.get_doc("Facture", self.facture)
				if facture.docstatus == 1:
					facture.cancel()
			except Exception as e:
				frappe.log_error(f"Erreur lors de l'annulation de la facture Koura: {str(e)}")
		
		# Annuler le paiement si il existe
		if self.paiement:
			try:
				paiement = frappe.get_doc("Paiement", self.paiement)
				if paiement.docstatus == 1:
					paiement.cancel()
			except Exception as e:
				frappe.log_error(f"Erreur lors de l'annulation du paiement: {str(e)}")
		



# Méthodes utilitaires
@frappe.whitelist()
def get_terrain_availability(terrain, date_debut, date_fin):
	"""Retourne la disponibilité d'un terrain pour une période donnée.
	
	Args:
		terrain (str): Nom du terrain
		date_debut (str): Date et heure de début
		date_fin (str): Date et heure de fin
		
	Returns:
		dict: Informations sur la disponibilité
	"""
	terrain_doc = frappe.get_doc("Terrain", terrain)
	return {
		"disponible": terrain_doc.is_disponible(date_debut, date_fin),
		"prix_estime": terrain_doc.get_prix_creneau(
			get_datetime(date_debut).strftime("%A"),
			get_datetime(date_debut).time().strftime("%H:%M:%S"),
			"Normal"
		)
	}

@frappe.whitelist()
def create_reservation_with_payment(terrain, client, date_debut, duree_heures, 
									 type_evenement="Normal", mode_paiement="Espèces"):
	"""Crée une réservation avec paiement immédiat.
	
	Args:
		terrain (str): Nom du terrain
		client (str): Nom du client
		date_debut (str): Date et heure de début
		duree_heures (float): Durée en heures
		type_evenement (str): Type d'événement
		mode_paiement (str): Mode de paiement
		
	Returns:
		dict: Informations sur la réservation créée
	"""
	try:
		# Créer la réservation
		reservation = frappe.get_doc({
			"doctype": "Reservation Terrain",
			"terrain": terrain,
			"client": client,
			"date_reservation": today(),
			"date_heure_debut": date_debut,
			"duree_heures": duree_heures,
			"type_evenement": type_evenement,
			"mode_paiement": mode_paiement
		})
		
		reservation.insert()
		reservation.submit()
		
		# Créer le paiement
		paiement_name = reservation.create_paiement(reservation.montant_total, mode_paiement)
		
		return {
			"success": True,
			"reservation": reservation.name,
			"facture": reservation.facture,
			"paiement": paiement_name,
			"montant_total": reservation.montant_total
		}
		
	except Exception as e:
		frappe.log_error(f"Erreur lors de la création de la réservation avec paiement: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}

@frappe.whitelist()
def get_client_reservations(client, limit=10):
	"""Retourne les réservations d'un client.
	
	Args:
		client (str): Nom du client
		limit (int): Nombre maximum de réservations
		
	Returns:
		list: Liste des réservations
	"""
	return frappe.get_list(
		"Reservation Terrain",
		filters={"client": client},
		fields=["name", "terrain", "date_reservation", "date_heure_debut", 
				"duree_heures", "montant_total", "statut", "statut_paiement"],
		order_by="date_reservation desc",
		limit=limit
	)