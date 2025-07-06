# Copyright (c) 2025, IntraPro and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class GroupeClient(Document):
	"""DocType pour gérer les groupes de clients et leurs tarifications."""
	
	def validate(self):
		"""Validation des données du groupe client."""
		self.validate_remise()
		self.validate_limites()
	
	def validate_remise(self):
		"""Valide que la remise est dans une plage acceptable."""
		if self.remise_pourcentage and (self.remise_pourcentage < 0 or self.remise_pourcentage > 100):
			frappe.throw(_("La remise doit être entre 0% et 100%."))
	
	def validate_limites(self):
		"""Valide les limites de réservation."""
		if self.limite_reservations_jour and self.limite_reservations_jour < 0:
			frappe.throw(_("La limite de réservations par jour ne peut pas être négative."))
		
		if self.limite_reservations_mois and self.limite_reservations_mois < 0:
			frappe.throw(_("La limite de réservations par mois ne peut pas être négative."))
		
		if self.duree_max_reservation and self.duree_max_reservation < 1:
			frappe.throw(_("La durée maximale de réservation doit être d'au moins 1 heure."))
		
		if self.avance_max_reservation and self.avance_max_reservation < 1:
			frappe.throw(_("L'avance maximale de réservation doit être d'au moins 1 jour."))
	
	def get_prix_avec_remise(self, prix_base):
		"""Calcule le prix avec remise appliquée.
		
		Args:
			prix_base (float): Prix de base
			
		Returns:
			float: Prix avec remise
		"""
		# Si un prix spécial est défini, l'utiliser
		if self.prix_special_heure:
			return flt(self.prix_special_heure)
		
		# Sinon appliquer la remise sur le prix de base
		if self.remise_pourcentage:
			remise = flt(prix_base) * flt(self.remise_pourcentage) / 100
			return flt(prix_base) - remise
		
		return flt(prix_base)
	
	def get_nombre_clients(self):
		"""Retourne le nombre de clients dans ce groupe.
		
		Returns:
			int: Nombre de clients
		"""
		return frappe.db.count("Client", {"groupe_client": self.name, "statut": "Actif"})
	
	def get_clients_actifs(self):
		"""Retourne la liste des clients actifs du groupe.
		
		Returns:
			list: Liste des clients actifs
		"""
		return frappe.get_all(
			"Client",
			filters={"groupe_client": self.name, "statut": "Actif"},
			fields=["name", "nom_complet", "telephone", "email"],
			order_by="nom_complet"
		)
	
	def can_client_reserve(self, client_name, date_reservation, duree_heures):
		"""Vérifie si un client peut faire une réservation selon les limites du groupe.
		
		Args:
			client_name (str): Nom du client
			date_reservation (date): Date de la réservation
			duree_heures (float): Durée en heures
			
		Returns:
			dict: {"can_reserve": bool, "message": str}
		"""
		from frappe.utils import today, add_days, get_first_day, get_last_day
		
		# Vérifier la durée maximale
		if self.duree_max_reservation and duree_heures > self.duree_max_reservation:
			return {
				"can_reserve": False,
				"message": f"Durée maximale autorisée : {self.duree_max_reservation} heures"
			}
		
		# Vérifier l'avance maximale
		if self.avance_max_reservation:
			max_date = add_days(today(), self.avance_max_reservation)
			if date_reservation > max_date:
				return {
					"can_reserve": False,
					"message": f"Réservation possible jusqu'à {self.avance_max_reservation} jours à l'avance"
				}
		
		# Vérifier les limites quotidiennes
		if self.limite_reservations_jour:
			reservations_jour = frappe.db.count(
				"Reservation Terrain",
				{
					"client": client_name,
					"date_heure_debut": ["between", [date_reservation, date_reservation]],
					"statut": ["in", ["Confirmée", "En cours"]]
				}
			)
			
			if reservations_jour >= self.limite_reservations_jour:
				return {
					"can_reserve": False,
					"message": f"Limite quotidienne atteinte : {self.limite_reservations_jour} réservations/jour"
				}
		
		# Vérifier les limites mensuelles
		if self.limite_reservations_mois:
			first_day = get_first_day(date_reservation)
			last_day = get_last_day(date_reservation)
			
			reservations_mois = frappe.db.count(
				"Reservation Terrain",
				{
					"client": client_name,
					"date_heure_debut": ["between", [first_day, last_day]],
					"statut": ["in", ["Confirmée", "En cours"]]
				}
			)
			
			if reservations_mois >= self.limite_reservations_mois:
				return {
					"can_reserve": False,
					"message": f"Limite mensuelle atteinte : {self.limite_reservations_mois} réservations/mois"
				}
		
		return {"can_reserve": True, "message": "Réservation autorisée"}
	
	def get_statistiques(self):
		"""Retourne les statistiques du groupe.
		
		Returns:
			dict: Statistiques du groupe
		"""
		from frappe.utils import today, add_months
		
		date_debut = add_months(today(), -12)
		
		# Nombre de clients
		nb_clients = self.get_nombre_clients()
		
		# Revenus générés
		revenus = frappe.db.sql("""
			SELECT COALESCE(SUM(rt.prix_total), 0) as total
			FROM `tabReservation Terrain` rt
			INNER JOIN `tabClient` c ON rt.client = c.name
			WHERE c.groupe_client = %s
			AND rt.statut IN ('Confirmée', 'Terminée')
			AND rt.date_heure_debut >= %s
		""", (self.name, date_debut), as_dict=True)
		
		# Nombre de réservations
		nb_reservations = frappe.db.sql("""
			SELECT COUNT(*) as total
			FROM `tabReservation Terrain` rt
			INNER JOIN `tabClient` c ON rt.client = c.name
			WHERE c.groupe_client = %s
			AND rt.statut IN ('Confirmée', 'Terminée')
			AND rt.date_heure_debut >= %s
		""", (self.name, date_debut), as_dict=True)
		
		return {
			"nombre_clients": nb_clients,
			"revenus_12_mois": revenus[0].total if revenus else 0,
			"reservations_12_mois": nb_reservations[0].total if nb_reservations else 0,
			"revenu_moyen_client": (revenus[0].total / nb_clients) if revenus and nb_clients > 0 else 0
		}