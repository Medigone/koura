# Copyright (c) 2025, IntraPro and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, get_time, get_datetime


class Article(Document):
	"""DocType pour gérer les articles/services du stade."""
	
	def validate(self):
		"""Validation des données de l'article."""
		self.validate_prix()
		self.validate_stock()
		self.validate_tva()
		self.generate_code_if_missing()
	
	def validate_prix(self):
		"""Valide que le prix est positif."""
		if self.prix_unitaire and self.prix_unitaire < 0:
			frappe.throw(_("Le prix unitaire ne peut pas être négatif."))
	
	def validate_stock(self):
		"""Valide les données de stock."""
		if self.gestion_stock:
			if self.stock_actuel is None:
				self.stock_actuel = 0
			
			if self.stock_minimum and self.stock_minimum < 0:
				frappe.throw(_("Le stock minimum ne peut pas être négatif."))
			
			if self.stock_maximum and self.stock_maximum < 0:
				frappe.throw(_("Le stock maximum ne peut pas être négatif."))
			
			if (self.stock_minimum and self.stock_maximum and 
				self.stock_minimum > self.stock_maximum):
				frappe.throw(_("Le stock minimum ne peut pas être supérieur au stock maximum."))
	
	def validate_tva(self):
		"""Valide les données de TVA."""
		if self.tva_applicable and not self.taux_tva:
			self.taux_tva = 19  # Taux par défaut en Algérie
		
		if self.taux_tva and (self.taux_tva < 0 or self.taux_tva > 100):
			frappe.throw(_("Le taux de TVA doit être entre 0% et 100%."))
	
	def generate_code_if_missing(self):
		"""Génère un code article s'il n'est pas fourni."""
		if not self.code_article:
			# Générer un code basé sur le nom et le type
			prefix = {
				"Service": "SRV",
				"Produit": "PRD",
				"Location": "LOC",
				"Abonnement": "ABO",
				"Événement": "EVT"
			}.get(self.type_article, "ART")
			
			# Prendre les 3 premières lettres du nom
			nom_clean = ''.join(c for c in self.nom_article if c.isalnum())[:3].upper()
			
			# Générer un numéro séquentiel
			count = frappe.db.count("Article", {"type_article": self.type_article}) + 1
			
			self.code_article = f"{prefix}-{nom_clean}-{count:03d}"
	
	def get_prix_avec_tva(self):
		"""Calcule le prix TTC.
		
		Returns:
			float: Prix TTC
		"""
		prix_ht = flt(self.prix_unitaire)
		
		if self.tva_applicable and self.taux_tva:
			tva = prix_ht * flt(self.taux_tva) / 100
			return prix_ht + tva
		
		return prix_ht
	
	def get_montant_tva(self, quantite=1):
		"""Calcule le montant de TVA.
		
		Args:
			quantite (float): Quantité
			
		Returns:
			float: Montant TVA
		"""
		if self.tva_applicable and self.taux_tva:
			prix_ht = flt(self.prix_unitaire) * flt(quantite)
			return prix_ht * flt(self.taux_tva) / 100
		
		return 0
	
	def is_disponible(self, quantite=1, date_heure=None):
		"""Vérifie la disponibilité de l'article.
		
		Args:
			quantite (float): Quantité demandée
			date_heure (datetime): Date et heure de la demande
			
		Returns:
			bool: True si disponible
		"""
		# Vérifier si l'article est actif
		if not self.actif:
			return False
		
		# Vérifier le stock si géré
		if self.gestion_stock:
			if flt(self.stock_actuel) < flt(quantite):
				return False
		
		# Vérifier les horaires de disponibilité
		if not self.disponible_24h and date_heure:
			return self.is_disponible_horaire(date_heure)
		
		return True
	
	def is_disponible_horaire(self, date_heure):
		"""Vérifie si l'article est disponible à une heure donnée.
		
		Args:
			date_heure (datetime): Date et heure
			
		Returns:
			bool: True si disponible
		"""
		if self.disponible_24h:
			return True
		
		if not self.heures_disponibilite:
			return False
		
		dt = get_datetime(date_heure)
		jour_semaine = dt.strftime("%A")
		jour_fr = {
			"Monday": "Lundi", "Tuesday": "Mardi", "Wednesday": "Mercredi",
			"Thursday": "Jeudi", "Friday": "Vendredi", "Saturday": "Samedi", "Sunday": "Dimanche"
		}.get(jour_semaine, jour_semaine)
		
		heure_actuelle = dt.time()
		
		for horaire in self.heures_disponibilite:
			if (horaire.jour_semaine == jour_fr or horaire.jour_semaine == "Tous les jours"):
				if (get_time(horaire.heure_debut) <= heure_actuelle <= get_time(horaire.heure_fin)):
					return True
		
		return False
	
	def reduire_stock(self, quantite):
		"""Réduit le stock de l'article.
		
		Args:
			quantite (float): Quantité à déduire
		"""
		if self.gestion_stock:
			if flt(self.stock_actuel) < flt(quantite):
				frappe.throw(_("Stock insuffisant pour l'article {0}").format(self.nom_article))
			
			self.stock_actuel = flt(self.stock_actuel) - flt(quantite)
			self.save()
	
	def augmenter_stock(self, quantite):
		"""Augmente le stock de l'article.
		
		Args:
			quantite (float): Quantité à ajouter
		"""
		if self.gestion_stock:
			self.stock_actuel = flt(self.stock_actuel) + flt(quantite)
			self.save()
	
	def is_stock_faible(self):
		"""Vérifie si le stock est faible.
		
		Returns:
			bool: True si stock faible
		"""
		if self.gestion_stock and self.stock_minimum:
			return flt(self.stock_actuel) <= flt(self.stock_minimum)
		
		return False
	
	def get_articles_similaires(self, limit=5):
		"""Retourne des articles similaires.
		
		Args:
			limit (int): Nombre maximum d'articles
			
		Returns:
			list: Liste d'articles similaires
		"""
		return frappe.get_all(
			"Article",
			filters={
				"name": ["!=", self.name],
				"type_article": self.type_article,
				"categorie": self.categorie,
				"actif": 1
			},
			fields=["name", "nom_article", "prix_unitaire", "unite_mesure"],
			limit=limit,
			order_by="prix_unitaire"
		)
	
	def get_statistiques_ventes(self, periode_mois=12):
		"""Retourne les statistiques de vente de l'article.
		
		Args:
			periode_mois (int): Période en mois
			
		Returns:
			dict: Statistiques de vente
		"""
		from frappe.utils import add_months, today
		
		date_debut = add_months(today(), -periode_mois)
		
		# TODO: Implémenter quand les DocTypes de vente seront créés
		return {
			"quantite_vendue": 0,
			"chiffre_affaires": 0,
			"nombre_commandes": 0
		}