# Copyright (c) 2025, IntraPro and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_months, getdate, flt


class Membre(Document):
	"""DocType pour la gestion des membres du stade."""
	
	def validate(self):
		"""Validation des données du membre."""
		self.calculate_expiration_date()
		self.update_loyalty_level()
		self.update_member_status()
	
	def calculate_expiration_date(self):
		"""Calcule la date d'expiration basée sur le type d'adhésion."""
		if not self.date_adhesion or not self.type_adhesion:
			return
		
		date_adhesion = getdate(self.date_adhesion)
		
		if self.type_adhesion == "Mensuelle":
			self.date_expiration = add_months(date_adhesion, 1)
		elif self.type_adhesion == "Trimestrielle":
			self.date_expiration = add_months(date_adhesion, 3)
		elif self.type_adhesion == "Semestrielle":
			self.date_expiration = add_months(date_adhesion, 6)
		elif self.type_adhesion == "Annuelle":
			self.date_expiration = add_months(date_adhesion, 12)
	
	def update_member_status(self):
		"""Met à jour le statut du membre basé sur la date d'expiration."""
		if self.date_expiration and getdate() > getdate(self.date_expiration):
			if self.statut_membre not in ["Suspendu", "Inactif"]:
				self.statut_membre = "Expiré"
	
	def update_loyalty_level(self):
		"""Met à jour le niveau de fidélité basé sur les dépenses totales."""
		if not self.total_depenses:
			self.total_depenses = 0
		
		# Définir les seuils de fidélité (en DZD)
		if self.total_depenses >= 100000:  # 100,000 DZD
			self.niveau_fidelite = "Platine"
			self.reduction_applicable = 15
		elif self.total_depenses >= 50000:  # 50,000 DZD
			self.niveau_fidelite = "Or"
			self.reduction_applicable = 10
		elif self.total_depenses >= 20000:  # 20,000 DZD
			self.niveau_fidelite = "Argent"
			self.reduction_applicable = 5
		else:
			self.niveau_fidelite = "Bronze"
			self.reduction_applicable = 0
	
	def after_insert(self):
		"""Actions après l'insertion du membre."""
		pass
	

	

	
	def add_loyalty_points(self, points):
		"""Ajoute des points de fidélité au membre.
		
		Args:
			points (int): Nombre de points à ajouter
		"""
		self.points_fidelite = (self.points_fidelite or 0) + points
		self.save()
	
	def add_expense(self, amount):
		"""Ajoute une dépense au total du membre.
		
		Args:
			amount (float): Montant de la dépense
		"""
		self.total_depenses = (self.total_depenses or 0) + amount
		
		# Ajouter des points de fidélité (1 point par 100 DZD dépensés)
		points_to_add = int(amount / 100)
		if points_to_add > 0:
			self.add_loyalty_points(points_to_add)
		
		self.update_loyalty_level()
		self.save()
	
	def get_discount_percentage(self):
		"""Retourne le pourcentage de réduction applicable.
		
		Returns:
			float: Pourcentage de réduction
		"""
		return self.reduction_applicable or 0
	
	def is_active(self):
		"""Vérifie si le membre est actif.
		
		Returns:
			bool: True si actif, False sinon
		"""
		return self.statut_membre == "Actif" and getdate() <= getdate(self.date_expiration)
	
	def renew_membership(self, new_type=None):
		"""Renouvelle l'adhésion du membre.
		
		Args:
			new_type (str): Nouveau type d'adhésion (optionnel)
		"""
		if new_type:
			self.type_adhesion = new_type
		
		self.date_adhesion = getdate()
		self.calculate_expiration_date()
		self.statut_membre = "Actif"
		self.save()
	
	@frappe.whitelist()
	def get_member_stats(self):
		"""Retourne les statistiques du membre.
		
		Returns:
			dict: Statistiques du membre
		"""
		# Chercher un client Koura avec le même nom et email
		client_koura = None
		if self.email:
			client_koura = frappe.db.get_value("Client", {"email": self.email}, "name")
		
		# Compter les réservations
		reservations_count = frappe.db.count(
			"Reservation Terrain",
			filters={"client": client_koura}
		) if client_koura else 0
		
		# Calculer le montant total des réservations
		total_reservations = frappe.db.sql("""
			SELECT SUM(montant_total)
			FROM `tabReservation Terrain`
			WHERE client = %s AND docstatus = 1
		""", (client_koura,))[0][0] or 0 if client_koura else 0
		
		return {
			"reservations_count": reservations_count,
			"total_reservations_amount": total_reservations,
			"loyalty_points": self.points_fidelite,
			"loyalty_level": self.niveau_fidelite,
			"discount_percentage": self.reduction_applicable,
			"is_active": self.is_active(),
			"days_until_expiration": (getdate(self.date_expiration) - getdate()).days if self.date_expiration else 0
		}