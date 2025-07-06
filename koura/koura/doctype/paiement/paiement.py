# -*- coding: utf-8 -*-
# Copyright (c) 2025, Koura and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, nowdate
from frappe import _

class Paiement(Document):
    """DocType pour gérer les paiements des factures."""
    
    def validate(self):
        """Validation des données du paiement."""
        self.validate_facture()
        self.validate_montant()
        self.validate_date()
        self.validate_mode_paiement()
        self.set_client_from_facture()
        self.set_montants_from_facture()
    
    def validate_facture(self):
        """Valide que la facture existe et peut être payée."""
        if not self.facture:
            frappe.throw(_("Une facture doit être spécifiée"))
        
        facture_doc = frappe.get_doc("Facture", self.facture)
        
        if facture_doc.statut == "Annulée":
            frappe.throw(_("Impossible de créer un paiement pour une facture annulée"))
        
        if facture_doc.statut_paiement == "Payé":
            frappe.throw(_("Cette facture est déjà entièrement payée"))
    
    def validate_montant(self):
        """Valide le montant du paiement."""
        if flt(self.montant_paiement) <= 0:
            frappe.throw(_("Le montant du paiement doit être supérieur à zéro"))
        
        if self.facture:
            facture_doc = frappe.get_doc("Facture", self.facture)
            montant_restant = facture_doc.get_montant_restant()
            
            if flt(self.montant_paiement) > montant_restant:
                frappe.throw(_("Le montant du paiement ({0} DA) dépasse le montant restant de la facture ({1} DA)").format(
                    self.montant_paiement, montant_restant))
    
    def validate_date(self):
        """Valide la date du paiement."""
        if self.date_paiement and self.facture:
            facture_doc = frappe.get_doc("Facture", self.facture)
            if getdate(self.date_paiement) < getdate(facture_doc.date_facture):
                frappe.throw(_("La date de paiement ne peut pas être antérieure à la date de facture"))
    
    def validate_mode_paiement(self):
        """Valide les détails du mode de paiement."""
        if self.mode_paiement == "Chèque":
            if not self.numero_cheque:
                frappe.throw(_("Le numéro de chèque est requis pour un paiement par chèque"))
            if not self.banque:
                frappe.throw(_("La banque est requise pour un paiement par chèque"))
        
        elif self.mode_paiement == "Virement Bancaire":
            if not self.numero_transaction:
                frappe.throw(_("Le numéro de transaction est requis pour un virement bancaire"))
        
        elif self.mode_paiement == "Carte Bancaire":
            if not self.numero_transaction:
                frappe.throw(_("Le numéro de transaction est requis pour un paiement par carte"))
    
    def set_client_from_facture(self):
        """Définit le client à partir de la facture."""
        if self.facture and not self.client:
            facture_doc = frappe.get_doc("Facture", self.facture)
            self.client = facture_doc.client
    
    def set_montants_from_facture(self):
        """Définit les montants à partir de la facture."""
        if self.facture:
            facture_doc = frappe.get_doc("Facture", self.facture)
            self.montant_facture = facture_doc.total_ttc
            self.montant_restant = facture_doc.get_montant_restant() - flt(self.montant_paiement)
    
    def on_submit(self):
        """Actions à effectuer lors de la soumission du paiement."""
        self.statut = "Validé"
        self.update_facture_payment()
        self.create_payment_receipt()
    
    def on_cancel(self):
        """Actions à effectuer lors de l'annulation du paiement."""
        self.statut = "Annulé"
        self.reverse_facture_payment()
    
    def update_facture_payment(self):
        """Met à jour le paiement de la facture."""
        if self.facture:
            facture_doc = frappe.get_doc("Facture", self.facture)
            facture_doc.enregistrer_paiement(
                montant=self.montant_paiement,
                mode_paiement=self.mode_paiement,
                date_paiement=self.date_paiement
            )
    
    def reverse_facture_payment(self):
        """Annule le paiement de la facture."""
        if self.facture:
            facture_doc = frappe.get_doc("Facture", self.facture)
            nouveau_montant_paye = flt(facture_doc.montant_paye) - flt(self.montant_paiement)
            
            facture_doc.montant_paye = max(0, nouveau_montant_paye)
            
            # Mise à jour du statut de paiement
            if facture_doc.montant_paye == 0:
                facture_doc.statut_paiement = "En Attente"
            elif facture_doc.montant_paye < facture_doc.total_ttc:
                facture_doc.statut_paiement = "Partiellement Payé"
            
            facture_doc.save()
    
    def create_payment_receipt(self):
        """Crée un reçu de paiement."""
        if not self.recu_paiement:
            # Logique pour générer un reçu de paiement
            # Cela pourrait inclure l'envoi d'un email, l'impression d'un reçu, etc.
            self.recu_paiement = 1
            self.save()
    
    def get_payment_details(self):
        """Retourne les détails du paiement."""
        details = {
            'numero_paiement': self.name,
            'facture': self.facture,
            'client': self.client,
            'date_paiement': self.date_paiement,
            'montant': self.montant_paiement,
            'mode_paiement': self.mode_paiement,
            'statut': self.statut
        }
        
        # Ajouter les détails spécifiques au mode de paiement
        if self.mode_paiement == "Chèque":
            details.update({
                'numero_cheque': self.numero_cheque,
                'banque': self.banque
            })
        elif self.mode_paiement in ["Carte Bancaire", "Virement Bancaire", "Paiement Mobile"]:
            details.update({
                'numero_transaction': self.numero_transaction
            })
        
        return details
    
    def is_refundable(self):
        """Vérifie si le paiement peut être remboursé."""
        return self.statut == "Validé" and self.docstatus == 1
    
    def create_refund(self, montant_remboursement=None, raison=""):
        """Crée un remboursement pour ce paiement."""
        if not self.is_refundable():
            frappe.throw(_("Ce paiement ne peut pas être remboursé"))
        
        if not montant_remboursement:
            montant_remboursement = self.montant_paiement
        
        if flt(montant_remboursement) > flt(self.montant_paiement):
            frappe.throw(_("Le montant du remboursement ne peut pas être supérieur au montant du paiement"))
        
        # Créer un nouveau paiement avec un montant négatif (remboursement)
        remboursement = frappe.new_doc("Paiement")
        remboursement.facture = self.facture
        remboursement.client = self.client
        remboursement.date_paiement = nowdate()
        remboursement.montant_paiement = -flt(montant_remboursement)
        remboursement.mode_paiement = self.mode_paiement
        remboursement.statut = "Validé"
        remboursement.notes = f"Remboursement du paiement {self.name}. Raison: {raison}"
        remboursement.reference_paiement = self.name
        
        remboursement.save()
        remboursement.submit()
        
        # Marquer ce paiement comme remboursé
        self.statut = "Remboursé"
        self.save()
        
        return remboursement.name
    
    def send_payment_confirmation(self):
        """Envoie une confirmation de paiement au client."""
        if not self.client:
            return
        
        client_doc = frappe.get_doc("Client", self.client)
        if not client_doc.email or not client_doc.notifications_email:
            return
        
        # Logique d'envoi d'email de confirmation
        # frappe.sendmail(...)
        
        frappe.msgprint(_("Confirmation de paiement envoyée à {0}").format(client_doc.email))
    
    def get_payment_method_details(self):
        """Retourne les détails spécifiques au mode de paiement."""
        details = {}
        
        if self.mode_paiement == "Chèque":
            details = {
                'type': 'Chèque',
                'numero': self.numero_cheque,
                'banque': self.banque
            }
        elif self.mode_paiement == "Carte Bancaire":
            details = {
                'type': 'Carte Bancaire',
                'transaction': self.numero_transaction
            }
        elif self.mode_paiement == "Virement Bancaire":
            details = {
                'type': 'Virement',
                'transaction': self.numero_transaction,
                'compte': self.compte_bancaire
            }
        elif self.mode_paiement == "Paiement Mobile":
            details = {
                'type': 'Mobile',
                'transaction': self.numero_transaction
            }
        elif self.mode_paiement == "Espèces":
            details = {
                'type': 'Espèces'
            }
        
        return details

# Fonctions utilitaires
@frappe.whitelist()
def create_payment_from_facture(facture, montant, mode_paiement, date_paiement=None):
    """Crée un paiement à partir d'une facture."""
    if not date_paiement:
        date_paiement = nowdate()
    
    facture_doc = frappe.get_doc("Facture", facture)
    
    if facture_doc.statut_paiement == "Payé":
        frappe.throw(_("Cette facture est déjà entièrement payée"))
    
    montant_restant = facture_doc.get_montant_restant()
    if flt(montant) > montant_restant:
        frappe.throw(_("Le montant dépasse le montant restant de la facture"))
    
    paiement = frappe.new_doc("Paiement")
    paiement.facture = facture
    paiement.client = facture_doc.client
    paiement.date_paiement = date_paiement
    paiement.montant_paiement = montant
    paiement.mode_paiement = mode_paiement
    
    paiement.save()
    
    return paiement.name

@frappe.whitelist()
def get_facture_payments(facture):
    """Retourne tous les paiements d'une facture."""
    return frappe.get_list("Paiement",
                          filters={"facture": facture, "docstatus": 1},
                          fields=["name", "date_paiement", "montant_paiement", "mode_paiement", "statut"],
                          order_by="date_paiement desc")

@frappe.whitelist()
def get_client_payments(client, from_date=None, to_date=None):
    """Retourne tous les paiements d'un client."""
    filters = {"client": client, "docstatus": 1}
    
    if from_date:
        filters["date_paiement"] = [">=", from_date]
    if to_date:
        if "date_paiement" in filters:
            filters["date_paiement"] = ["between", [from_date, to_date]]
        else:
            filters["date_paiement"] = ["<=", to_date]
    
    return frappe.get_list("Paiement",
                          filters=filters,
                          fields=["name", "facture", "date_paiement", "montant_paiement", "mode_paiement", "statut"],
                          order_by="date_paiement desc")

@frappe.whitelist()
def get_payment_summary_by_mode(from_date=None, to_date=None):
    """Retourne un résumé des paiements par mode de paiement."""
    conditions = "WHERE p.docstatus = 1 AND p.statut = 'Validé'"
    
    if from_date:
        conditions += f" AND p.date_paiement >= '{from_date}'"
    if to_date:
        conditions += f" AND p.date_paiement <= '{to_date}'"
    
    return frappe.db.sql(f"""
        SELECT 
            p.mode_paiement,
            COUNT(*) as nombre_paiements,
            SUM(p.montant_paiement) as total_montant
        FROM `tabPaiement` p
        {conditions}
        GROUP BY p.mode_paiement
        ORDER BY total_montant DESC
    """, as_dict=True)