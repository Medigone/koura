# -*- coding: utf-8 -*-
# Copyright (c) 2025, Koura and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, add_days, nowdate
from frappe import _

class Facture(Document):
    """DocType pour gérer les factures du stade."""
    
    def validate(self):
        """Validation des données de la facture."""
        self.validate_dates()
        self.validate_articles()
        self.calculate_totals()
        self.set_adresse_facturation()
        self.validate_paiement()
    
    def validate_dates(self):
        """Valide les dates de la facture."""
        if self.date_echeance and getdate(self.date_echeance) < getdate(self.date_facture):
            frappe.throw(_("La date d'échéance ne peut pas être antérieure à la date de facture"))
    
    def validate_articles(self):
        """Valide les articles de la facture."""
        if not self.articles:
            frappe.throw(_("Au moins un article doit être ajouté à la facture"))
        
        for article in self.articles:
            if flt(article.quantite) <= 0:
                frappe.throw(_("La quantité doit être supérieure à zéro pour l'article {0}").format(article.article))
            if flt(article.prix_unitaire) < 0:
                frappe.throw(_("Le prix unitaire ne peut pas être négatif pour l'article {0}").format(article.article))
    
    def calculate_totals(self):
        """Calcule les totaux de la facture."""
        self.sous_total_ht = 0
        self.total_tva = 0
        self.total_remise = 0
        
        for article in self.articles:
            # Calcul du montant HT
            montant_ht = flt(article.quantite) * flt(article.prix_unitaire)
            
            # Calcul de la remise
            remise = 0
            if article.pourcentage_remise:
                remise = montant_ht * flt(article.pourcentage_remise) / 100
            elif article.montant_remise:
                remise = flt(article.montant_remise)
            
            montant_ht_apres_remise = montant_ht - remise
            
            # Calcul de la TVA
            tva = 0
            if article.taux_tva:
                tva = montant_ht_apres_remise * flt(article.taux_tva) / 100
            
            # Mise à jour des champs de l'article
            article.montant_ht = montant_ht
            article.montant_remise = remise
            article.montant_tva = tva
            article.montant_ttc = montant_ht_apres_remise + tva
            
            # Cumul des totaux
            self.sous_total_ht += montant_ht
            self.total_remise += remise
            self.total_tva += tva
        
        self.total_ttc = self.sous_total_ht - self.total_remise + self.total_tva
    
    def set_adresse_facturation(self):
        """Définit l'adresse de facturation à partir du client."""
        if self.client and not self.adresse_facturation:
            client_doc = frappe.get_doc("Client", self.client)
            adresse_parts = []
            
            if client_doc.adresse_ligne_1:
                adresse_parts.append(client_doc.adresse_ligne_1)
            if client_doc.adresse_ligne_2:
                adresse_parts.append(client_doc.adresse_ligne_2)
            if client_doc.ville:
                adresse_parts.append(client_doc.ville)
            if client_doc.code_postal:
                adresse_parts.append(client_doc.code_postal)
            if client_doc.wilaya:
                adresse_parts.append(client_doc.wilaya)
            
            self.adresse_facturation = "\n".join(adresse_parts)
    
    def validate_paiement(self):
        """Valide les informations de paiement."""
        if flt(self.montant_paye) > flt(self.total_ttc):
            frappe.throw(_("Le montant payé ne peut pas être supérieur au total de la facture"))
        
        # Mise à jour automatique du statut de paiement
        if flt(self.montant_paye) == 0:
            self.statut_paiement = "En Attente"
        elif flt(self.montant_paye) >= flt(self.total_ttc):
            self.statut_paiement = "Payé"
        else:
            self.statut_paiement = "Partiellement Payé"
    
    def on_submit(self):
        """Actions à effectuer lors de la soumission."""
        self.statut = "Émise"
        self.update_reservation_status()
    
    def on_cancel(self):
        """Actions à effectuer lors de l'annulation."""
        self.statut = "Annulée"
        self.statut_paiement = "Annulé"
    
    def update_reservation_status(self):
        """Met à jour le statut de la réservation liée."""
        if self.reservation_terrain:
            reservation = frappe.get_doc("Reservation Terrain", self.reservation_terrain)
            if reservation.statut == "Confirmée":
                reservation.statut = "Facturée"
                reservation.save()
    
    def add_reservation_to_invoice(self, reservation_name):
        """Ajoute une réservation à la facture."""
        reservation = frappe.get_doc("Reservation Terrain", reservation_name)
        
        # Ajouter la ligne de réservation
        self.append("articles", {
            "article": "Réservation Terrain",
            "description": f"Réservation {reservation.terrain} - {reservation.date_debut} à {reservation.heure_debut}",
            "quantite": 1,
            "prix_unitaire": reservation.prix_total,
            "taux_tva": 19  # TVA standard en Algérie
        })
        
        self.reservation_terrain = reservation_name
    
    def add_article_to_invoice(self, article_code, quantite, prix_unitaire=None, remise=0):
        """Ajoute un article à la facture."""
        article_doc = frappe.get_doc("Article", article_code)
        
        if not prix_unitaire:
            prix_unitaire = article_doc.get_prix_avec_tva()
        
        self.append("articles", {
            "article": article_code,
            "description": article_doc.description,
            "quantite": quantite,
            "prix_unitaire": prix_unitaire,
            "pourcentage_remise": remise,
            "taux_tva": article_doc.taux_tva if article_doc.tva_applicable else 0
        })
    
    def enregistrer_paiement(self, montant, mode_paiement, date_paiement=None):
        """Enregistre un paiement pour la facture."""
        if not date_paiement:
            date_paiement = nowdate()
        
        montant_restant = flt(self.total_ttc) - flt(self.montant_paye)
        
        if flt(montant) > montant_restant:
            frappe.throw(_("Le montant du paiement ({0} DA) dépasse le montant restant ({1} DA)").format(
                montant, montant_restant))
        
        self.montant_paye = flt(self.montant_paye) + flt(montant)
        self.mode_paiement = mode_paiement
        
        # Mise à jour du statut de paiement
        if flt(self.montant_paye) >= flt(self.total_ttc):
            self.statut_paiement = "Payé"
            self.statut = "Payée"
        else:
            self.statut_paiement = "Partiellement Payé"
        
        self.save()
        
        # Créer un enregistrement de paiement (optionnel)
        # self.create_payment_entry(montant, mode_paiement, date_paiement)
    
    def get_montant_restant(self):
        """Retourne le montant restant à payer."""
        return flt(self.total_ttc) - flt(self.montant_paye)
    
    def is_overdue(self):
        """Vérifie si la facture est en retard."""
        if self.date_echeance and self.statut_paiement not in ["Payé", "Annulé"]:
            return getdate(self.date_echeance) < getdate(nowdate())
        return False
    
    def get_days_overdue(self):
        """Retourne le nombre de jours de retard."""
        if self.is_overdue():
            from frappe.utils import date_diff
            return date_diff(nowdate(), self.date_echeance)
        return 0
    
    def send_invoice_email(self):
        """Envoie la facture par email au client."""
        if not self.client:
            frappe.throw(_("Aucun client spécifié pour l'envoi de la facture"))
        
        client_doc = frappe.get_doc("Client", self.client)
        if not client_doc.email:
            frappe.throw(_("Aucune adresse email trouvée pour le client {0}").format(self.client))
        
        # Logique d'envoi d'email (à implémenter selon les besoins)
        # frappe.sendmail(...)
        
        self.statut = "Envoyée"
        self.save()
        
        frappe.msgprint(_("Facture envoyée par email à {0}").format(client_doc.email))
    
    @frappe.whitelist()
    def duplicate_invoice(self):
        """Duplique la facture actuelle."""
        new_invoice = frappe.copy_doc(self)
        new_invoice.statut = "Brouillon"
        new_invoice.statut_paiement = "En Attente"
        new_invoice.montant_paye = 0
        new_invoice.date_facture = nowdate()
        new_invoice.reservation_terrain = None
        
        return new_invoice

# Fonctions utilitaires
@frappe.whitelist()
def create_invoice_from_reservation(reservation_name):
    """Crée une facture à partir d'une réservation."""
    reservation = frappe.get_doc("Reservation Terrain", reservation_name)
    
    if reservation.statut not in ["Confirmée", "En Cours"]:
        frappe.throw(_("Seules les réservations confirmées ou en cours peuvent être facturées"))
    
    # Vérifier s'il existe déjà une facture pour cette réservation
    existing_invoice = frappe.db.exists("Facture", {"reservation_terrain": reservation_name})
    if existing_invoice:
        frappe.throw(_("Une facture existe déjà pour cette réservation: {0}").format(existing_invoice))
    
    # Créer la nouvelle facture
    invoice = frappe.new_doc("Facture")
    invoice.client = reservation.client
    invoice.date_facture = nowdate()
    invoice.date_echeance = add_days(nowdate(), 30)  # Échéance à 30 jours
    
    # Ajouter la réservation
    invoice.add_reservation_to_invoice(reservation_name)
    
    invoice.save()
    
    return invoice.name

@frappe.whitelist()
def get_client_invoices(client, statut=None):
    """Retourne les factures d'un client."""
    filters = {"client": client}
    if statut:
        filters["statut"] = statut
    
    return frappe.get_list("Facture", 
                          filters=filters,
                          fields=["name", "date_facture", "total_ttc", "statut", "statut_paiement"],
                          order_by="date_facture desc")

@frappe.whitelist()
def get_overdue_invoices():
    """Retourne les factures en retard."""
    return frappe.db.sql("""
        SELECT name, client, date_facture, date_echeance, total_ttc, montant_paye,
               DATEDIFF(CURDATE(), date_echeance) as jours_retard
        FROM `tabFacture`
        WHERE date_echeance < CURDATE()
        AND statut_paiement NOT IN ('Payé', 'Annulé')
        AND docstatus = 1
        ORDER BY date_echeance ASC
    """, as_dict=True)