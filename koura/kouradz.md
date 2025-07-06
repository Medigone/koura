# ⚽ Koura DZ - Application de Gestion des Terrains de Foot Amateurs

**Koura DZ** est une application personnalisée basée sur le Frappe Framework, destinée aux gestionnaires de stades de football amateur (foot à 5, foot à 7, mini-foot, etc.).  
Elle permet de centraliser les opérations quotidiennes : gestion des terrains, des réservations, des membres, des ventes de produits, de la maintenance, et bien plus.

---

## 🧱 Modules de l'Application

### 1. Terrains
- Gestion de la fiche terrain (nom, surface, capacité, éclairage…)
- Définition de la disponibilité (jours, horaires)
- Tarification personnalisée par créneau, jour ou type d'événement
- Statuts de terrain (disponible, maintenance, réservé)

### 2. Réservations
- Réservation de créneaux simples ou récurrents
- Paiement immédiat, partiel ou différé
- Notifications automatiques (email, SMS) de confirmation ou rappel
- Gestion des annulations, reprogrammations et historique complet

### 3. Membres
- Enregistrement des clients / joueurs
- Historique des réservations et consommations
- Système de fidélité (points, crédits, cartes)
- Création de groupes ou équipes de joueurs

### 4. Consommables / Boutique
- Gestion des produits à vendre (boissons, snacks, équipements…)
- Suivi des stocks et alertes de seuil critique
- Vente directe au comptoir via POS
- Rapports de ventes et inventaires

### 5. Maintenance & Incidents
- Déclaration d'incidents sur les terrains ou équipements
- Attribution des tickets à un employé
- Suivi du statut (Nouveau, En cours, Résolu)
- Historique des interventions

---

### Rôles et permissions

- **Gestionnaire de Stade** : accès complet aux modules de réservation, facturation, stock
- **Caissier** : accès au point de vente uniquement
- **Employé** : accès limité à la maintenance et présence
- **Administrateur** : contrôle total de l’application et des intégrations ERP

---

## 📊 Reporting et Tableaux de Bord

- Fréquentation par créneau, jour, semaine ou mois
- Revenus par terrain, par période ou par produit
- Classement des produits les plus vendus
- Taux d’occupation des terrains
- Suivi de l'utilisation des crédits fidélité

---

## 🧠 Fonctionnalités à venir (Roadmap)

- Intégration WhatsApp pour rappels et confirmations automatiques
- Générateur de tournois avec inscriptions et classement automatisé
- Système de matchmaking entre joueurs seuls
- Check-in via QR Code pour les joueurs et équipes

---

## 🛠️ Stack Technique

- **Framework** : Frappe Framework
- **ERP** : ERPNext
- **Backend** : Python (Frappe ORM)
- **Frontend** : React
- **Base de données** : MariaDB
- **Impression & Reporting** : Print Format Builder
- **Notifications** : Email, SMS, WhatsApp (futur)
