# -*- coding: utf-8 -*-
# Copyright (c) 2025, Koura and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt
from frappe import _

class LigneFacture(Document):
    """DocType pour gérer les lignes de facture."""
    
    def validate(self):
        """Validation des données de la ligne de facture."""
        self.validate_quantite()
        self.validate_prix()
        self.set_article_details()
        self.calculate_amounts()
    
    def validate_quantite(self):
        """Valide la quantité."""
        if flt(self.quantite) <= 0:
            frappe.throw(_("La quantité doit être supérieure à zéro"))
    
    def validate_prix(self):
        """Valide le prix unitaire."""
        if flt(self.prix_unitaire) < 0:
            frappe.throw(_("Le prix unitaire ne peut pas être négatif"))
    
    def set_article_details(self):
        """Définit les détails de l'article."""
        if self.article and frappe.db.exists("Article", self.article):
            article_doc = frappe.get_doc("Article", self.article)
            
            # Définir la description si elle n'est pas fournie
            if not self.description:
                self.description = article_doc.description or article_doc.nom_article
            
            # Définir l'unité de mesure
            self.unite_mesure = article_doc.unite_mesure
            
            # Définir le prix unitaire si il n'est pas fourni
            if not self.prix_unitaire:
                self.prix_unitaire = article_doc.prix_unitaire
            
            # Définir le taux de TVA
            if article_doc.tva_applicable and not self.taux_tva:
                self.taux_tva = article_doc.taux_tva or 19
            elif not article_doc.tva_applicable:
                self.taux_tva = 0
    
    def calculate_amounts(self):
        """Calcule les montants de la ligne."""
        # Calcul du montant HT
        self.montant_ht = flt(self.quantite) * flt(self.prix_unitaire)
        
        # Calcul de la remise
        if self.pourcentage_remise:
            self.montant_remise = self.montant_ht * flt(self.pourcentage_remise) / 100
        else:
            self.montant_remise = 0
        
        # Montant HT après remise
        montant_ht_apres_remise = self.montant_ht - self.montant_remise
        
        # Calcul de la TVA
        if self.taux_tva:
            self.montant_tva = montant_ht_apres_remise * flt(self.taux_tva) / 100
        else:
            self.montant_tva = 0
        
        # Calcul du montant TTC
        self.montant_ttc = montant_ht_apres_remise + self.montant_tva
    
    def get_montant_ht_net(self):
        """Retourne le montant HT après remise."""
        return self.montant_ht - self.montant_remise
    
    def get_taux_remise_effectif(self):
        """Retourne le taux de remise effectif."""
        if self.montant_ht > 0:
            return (self.montant_remise / self.montant_ht) * 100
        return 0
    
    def apply_discount_amount(self, discount_amount):
        """Applique une remise en montant."""
        if flt(discount_amount) > flt(self.montant_ht):
            frappe.throw(_("Le montant de la remise ne peut pas être supérieur au montant HT"))
        
        self.montant_remise = flt(discount_amount)
        self.pourcentage_remise = (self.montant_remise / self.montant_ht) * 100 if self.montant_ht > 0 else 0
        self.calculate_amounts()
    
    def apply_discount_percentage(self, discount_percentage):
        """Applique une remise en pourcentage."""
        if flt(discount_percentage) > 100:
            frappe.throw(_("Le pourcentage de remise ne peut pas être supérieur à 100%"))
        
        self.pourcentage_remise = flt(discount_percentage)
        self.calculate_amounts()
    
    def get_article_info(self):
        """Retourne les informations de l'article."""
        if self.article and frappe.db.exists("Article", self.article):
            return frappe.get_doc("Article", self.article)
        return None
    
    def check_stock_availability(self):
        """Vérifie la disponibilité du stock pour l'article."""
        article_doc = self.get_article_info()
        if article_doc and article_doc.type_article == "Produit":
            if article_doc.stock_actuel < self.quantite:
                frappe.msgprint(_("Stock insuffisant pour l'article {0}. Stock disponible: {1} {2}").format(
                    self.article, article_doc.stock_actuel, article_doc.unite_mesure
                ), alert=True)
                return False
        return True
    
    def reduce_stock(self):
        """Réduit le stock de l'article."""
        article_doc = self.get_article_info()
        if article_doc and article_doc.type_article == "Produit":
            article_doc.reduire_stock(self.quantite)
    
    def restore_stock(self):
        """Restaure le stock de l'article (en cas d'annulation)."""
        article_doc = self.get_article_info()
        if article_doc and article_doc.type_article == "Produit":
            article_doc.augmenter_stock(self.quantite)
    
    def get_profit_margin(self):
        """Calcule la marge bénéficiaire (si un prix de revient est défini)."""
        article_doc = self.get_article_info()
        if article_doc and hasattr(article_doc, 'prix_revient') and article_doc.prix_revient:
            cout_total = flt(article_doc.prix_revient) * flt(self.quantite)
            benefice = self.get_montant_ht_net() - cout_total
            if cout_total > 0:
                marge_pourcentage = (benefice / cout_total) * 100
                return {
                    'cout_total': cout_total,
                    'benefice': benefice,
                    'marge_pourcentage': marge_pourcentage
                }
        return None
    
    def is_service(self):
        """Vérifie si l'article est un service."""
        article_doc = self.get_article_info()
        return article_doc and article_doc.type_article == "Service"
    
    def is_product(self):
        """Vérifie si l'article est un produit."""
        article_doc = self.get_article_info()
        return article_doc and article_doc.type_article == "Produit"
    
    def get_line_summary(self):
        """Retourne un résumé de la ligne de facture."""
        return {
            'article': self.article,
            'description': self.description,
            'quantite': self.quantite,
            'prix_unitaire': self.prix_unitaire,
            'montant_ht': self.montant_ht,
            'montant_remise': self.montant_remise,
            'montant_tva': self.montant_tva,
            'montant_ttc': self.montant_ttc,
            'taux_tva': self.taux_tva,
            'pourcentage_remise': self.pourcentage_remise
        }

# Fonctions utilitaires pour les lignes de facture
@frappe.whitelist()
def get_article_price(article, client=None, date=None):
    """Retourne le prix d'un article pour un client donné."""
    if not frappe.db.exists("Article", article):
        return 0
    
    article_doc = frappe.get_doc("Article", article)
    prix = article_doc.prix_unitaire
    
    # Appliquer les remises du groupe client si applicable
    if client:
        client_doc = frappe.get_doc("Client", client)
        if client_doc.groupe_client:
            groupe_doc = frappe.get_doc("Groupe Client", client_doc.groupe_client)
            if groupe_doc.pourcentage_remise:
                prix = prix * (1 - flt(groupe_doc.pourcentage_remise) / 100)
            elif groupe_doc.prix_horaire_special and article_doc.type_article == "Service":
                prix = groupe_doc.prix_horaire_special
    
    return prix

@frappe.whitelist()
def get_article_details(article):
    """Retourne les détails d'un article pour la ligne de facture."""
    if not frappe.db.exists("Article", article):
        return {}
    
    article_doc = frappe.get_doc("Article", article)
    
    return {
        'description': article_doc.description or article_doc.nom_article,
        'unite_mesure': article_doc.unite_mesure,
        'prix_unitaire': article_doc.prix_unitaire,
        'taux_tva': article_doc.taux_tva if article_doc.tva_applicable else 0,
        'stock_disponible': article_doc.stock_actuel if article_doc.type_article == "Produit" else None,
        'type_article': article_doc.type_article
    }