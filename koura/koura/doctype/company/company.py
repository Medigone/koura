# Copyright (c) 2025, IntraPro and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import validate_email_address
import re


class Company(Document):
	"""DocType pour gérer les sociétés dans le système multi-tenant."""
	
	def validate(self):
		"""Validation des données de la société."""
		self.validate_email()
		self.validate_telephone()
		self.validate_code_societe()
	
	def validate_email(self):
		"""Valide le format de l'email."""
		if self.email:
			try:
				validate_email_address(self.email, throw=True)
			except frappe.InvalidEmailAddressError:
				frappe.throw(_("Format d'email invalide"))
	
	def validate_telephone(self):
		"""Valide le format du numéro de téléphone."""
		if self.telephone:
			# Pattern pour numéros algériens (+213 ou 0) suivi de 9 chiffres
			pattern = r'^(\+213|0)[5-7][0-9]{8}$'
			if not re.match(pattern, self.telephone.replace(' ', '').replace('-', '')):
				frappe.throw(_("Format de téléphone invalide. Utilisez le format algérien (+213XXXXXXXXX ou 0XXXXXXXXX)"))
	
	def validate_code_societe(self):
		"""Valide le code société (alphanumerique, 2-10 caractères)."""
		if self.code_societe:
			pattern = r'^[A-Z0-9]{2,10}$'
			if not re.match(pattern, self.code_societe.upper()):
				frappe.throw(_("Le code société doit contenir uniquement des lettres et chiffres (2-10 caractères)"))
			# Convertir en majuscules
			self.code_societe = self.code_societe.upper()
	
	def before_save(self):
		"""Actions avant sauvegarde."""
		if self.code_societe:
			self.code_societe = self.code_societe.upper()


# Fonction get_user_company() supprimée car le DocType 'User Company' n'existe plus
# Utilisez maintenant les 'User Permissions' natives de Frappe pour gérer l'accès aux sociétés


@frappe.whitelist()
def get_active_companies():
	"""Retourne la liste des sociétés actives."""
	return frappe.get_all("Company", 
						 filters={"actif": 1}, 
						 fields=["name", "nom_societe", "code_societe"],
						 order_by="nom_societe")