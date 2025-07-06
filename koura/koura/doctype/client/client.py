# Copyright (c) 2025, IntraPro and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import validate_email_address, get_datetime
import re


class Client(Document):
	"""DocType pour gérer les clients du stade."""
	
	def validate(self):
		"""Validation des données du client."""
		self.validate_email()
		self.validate_telephone()
		self.validate_nom_complet()
		self.set_default_groupe_client()
	
	def validate_email(self):
		"""Valide le format de l'email."""
		if self.email:
			try:
				validate_email_address(self.email, True)
			except frappe.InvalidEmailAddressError:
				frappe.throw(_("Format d'email invalide : {0}").format(self.email))
	
	def validate_telephone(self):
		"""Valide le format du numéro de téléphone algérien."""
		if self.telephone:
			# Format algérien : 0XXXXXXXXX (10 chiffres) ou +213XXXXXXXXX
			phone_pattern = r'^(\+213|0)[5-7]\d{8}$'
			if not re.match(phone_pattern, self.telephone.replace(' ', '').replace('-', '')):
				frappe.throw(_("Format de téléphone invalide. Utilisez le format algérien : 0XXXXXXXXX ou +213XXXXXXXXX"))
	
	def validate_nom_complet(self):
		"""Génère le nom complet si les champs prénom et nom sont remplis."""
		if self.prenom and self.nom_famille and not self.nom_complet:
			self.nom_complet = f"{self.prenom} {self.nom_famille}"
		elif not self.nom_complet:
			frappe.throw(_("Le nom complet est requis."))
	
	def set_default_groupe_client(self):
		"""Définit le groupe client par défaut selon le type."""
		if not self.groupe_client:
			default_groups = {
				"Individuel": "Clients Individuels",
				"Entreprise": "Clients Entreprises",
				"Club Sportif": "Clubs Sportifs",
				"École": "Établissements Scolaires",
				"Association": "Associations"
			}
			
			default_group = default_groups.get(self.type_client)
			if default_group and frappe.db.exists("Groupe Client", default_group):
				self.groupe_client = default_group
	
	def before_save(self):
		"""Actions avant sauvegarde."""
		# Normaliser le téléphone
		if self.telephone:
			self.telephone = self.telephone.replace(' ', '').replace('-', '')
		
		# Normaliser l'email
		if self.email:
			self.email = self.email.lower().strip()
	
	def get_reservations_actives(self):
		"""Retourne les réservations actives du client.
		
		Returns:
			list: Liste des réservations actives
		"""
		return frappe.get_all(
			"Reservation Terrain",
			filters={
				"client": self.name,
				"statut": ["in", ["Confirmée", "En cours"]]
			},
			fields=["name", "terrain", "date_heure_debut", "date_heure_fin", "prix_total"],
			order_by="date_heure_debut desc"
		)
	
	def get_historique_reservations(self, limit=10):
		"""Retourne l'historique des réservations du client.
		
		Args:
			limit (int): Nombre maximum de réservations à retourner
			
		Returns:
			list: Liste des réservations
		"""
		return frappe.get_all(
			"Reservation Terrain",
			filters={"client": self.name},
			fields=["name", "terrain", "date_heure_debut", "date_heure_fin", "prix_total", "statut"],
			order_by="date_heure_debut desc",
			limit=limit
		)
	
	def get_total_depenses(self, periode_mois=12):
		"""Calcule le total des dépenses du client sur une période.
		
		Args:
			periode_mois (int): Période en mois
			
		Returns:
			float: Total des dépenses
		"""
		from frappe.utils import add_months, today
		
		date_debut = add_months(today(), -periode_mois)
		
		total = frappe.db.sql("""
			SELECT COALESCE(SUM(prix_total), 0) as total
			FROM `tabReservation Terrain`
			WHERE client = %s
			AND statut IN ('Confirmée', 'Terminée')
			AND date_heure_debut >= %s
		""", (self.name, date_debut), as_dict=True)
		
		return total[0].total if total else 0
	
	def can_make_reservation(self):
		"""Vérifie si le client peut faire une réservation.
		
		Returns:
			bool: True si le client peut réserver, False sinon
		"""
		return self.statut == "Actif"
	
	def get_display_name(self):
		"""Retourne le nom d'affichage du client.
		
		Returns:
			str: Nom d'affichage
		"""
		return self.nom_complet or self.name
	
	def send_notification(self, message, type_notification="info"):
		"""Envoie une notification au client.
		
		Args:
			message (str): Message à envoyer
			type_notification (str): Type de notification (info, success, warning, error)
		"""
		if self.notifications_email and self.email:
			# Envoyer par email
			frappe.sendmail(
				recipients=[self.email],
				subject=f"Notification - Stade Koura DZ",
				message=message
			)
		
		if self.notifications_sms and self.telephone:
			# TODO: Implémenter l'envoi de SMS
			pass