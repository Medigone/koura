# Koura DZ - Gestion de Stades de Football Amateur

## Description

Koura DZ est une application Frappe Framework intégrée à ERPNext pour la gestion complète de stades de football amateur en Algérie. L'application permet de gérer les terrains, réservations, membres, et s'intègre parfaitement avec les modules ERPNext pour la comptabilité, stock, et CRM.

## Fonctionnalités Principales

### 🏟️ Gestion des Terrains
- Création et gestion des terrains avec photos
- Types de surface (Herbe naturelle, Gazon synthétique, Futsal, etc.)
- Tarification flexible par créneaux horaires
- Gestion des horaires d'ouverture/fermeture
- Statuts des terrains (Disponible, Maintenance, Hors service)

### 📅 Système de Réservation
- Réservations en temps réel avec vérification de disponibilité
- Calcul automatique des prix selon les créneaux
- Intégration avec ERPNext (Factures de vente automatiques)
- Gestion des statuts de paiement
- Validation des conflits de réservation

### 👥 Gestion des Membres
- Profils complets des membres avec photos
- Système d'adhésion (Mensuelle, Trimestrielle, Semestrielle, Annuelle)
- Programme de fidélité avec niveaux (Bronze, Argent, Or, Platine)
- Intégration automatique avec les Clients ERPNext
- Suivi des statistiques et performances

### 🎯 Programme de Fidélité
- Points de fidélité basés sur les dépenses
- Réductions automatiques selon le niveau
- Suivi des dépenses totales
- Niveaux de fidélité progressifs

## Architecture Technique

### DocTypes Principaux

1. **Terrain**
   - Gestion complète des terrains
   - Tarification par créneaux
   - Validation des horaires

2. **Reservation Terrain**
   - Système de réservation complet
   - Intégration ERPNext (Sales Invoice)
   - Validation de disponibilité

3. **Membre**
   - Gestion des membres
   - Programme de fidélité
   - Intégration Customer/Contact ERPNext

4. **Tarification Creneau** (DocType enfant)
   - Tarification flexible par jour/heure
   - Support des événements spéciaux

### Intégrations ERPNext

- **Accounting**: Factures automatiques pour les réservations
- **CRM**: Gestion des clients et contacts
- **Stock**: Gestion des consommables (future)
- **POS**: Point de vente pour la boutique (future)
- **HR**: Gestion des employés (future)

## Installation

### Prérequis
- Frappe Framework v14+
- ERPNext v14+
- Python 3.8+
- MariaDB/MySQL

### Étapes d'installation

1. **Cloner l'application**
   ```bash
   cd frappe-bench
   bench get-app https://github.com/votre-repo/koura.git
   ```

2. **Installer sur un site**
   ```bash
   bench --site votre-site.com install-app koura
   ```

3. **Migrer la base de données**
   ```bash
   bench --site votre-site.com migrate
   ```

4. **Redémarrer les services**
   ```bash
   bench restart
   ```

## Configuration Initiale

### 1. Rôles et Permissions
L'application crée automatiquement les rôles suivants :
- **Gestionnaire de Stade**: Accès complet à la gestion
- **Caissier**: Gestion des réservations et paiements
- **Employé**: Accès en lecture seule

### 2. Articles ERPNext
L'application crée automatiquement :
- Article "RESERVATION_TERRAIN" pour les factures
- Groupe de clients "Membres du Stade"

### 3. Champs Personnalisés
Ajout automatique de champs dans :
- **Customer**: Numéro de membre, Niveau de fidélité
- **Sales Invoice**: Lien vers la réservation
- **Item**: Indicateur de service de terrain

## Utilisation

### Workflow Typique

1. **Configuration initiale**
   - Créer les terrains avec tarification
   - Configurer les horaires d'ouverture

2. **Gestion des membres**
   - Enregistrer les nouveaux membres
   - Gérer les adhésions et renouvellements

3. **Réservations**
   - Créer une réservation
   - Validation automatique de disponibilité
   - Génération de facture ERPNext
   - Traitement du paiement

4. **Suivi et rapports**
   - Statistiques des membres
   - Rapports de revenus
   - Analyse de fréquentation

## Développement

### Structure du Code
```
koura/
├── koura/
│   ├── doctype/
│   │   ├── terrain/
│   │   ├── reservation_terrain/
│   │   ├── membre/
│   │   └── tarification_creneau/
│   ├── fixtures/
│   └── install.py
├── README.md
└── requirements.txt
```

### Conventions de Code
- PEP8 pour Python
- ESLint pour JavaScript
- Docstrings Google Style
- Tests unitaires avec unittest

### API Endpoints
L'application expose des API REST pour :
- Vérification de disponibilité des terrains
- Statistiques des membres
- Calcul de tarification

## Roadmap

### Phase 1 ✅ (Actuelle)
- Gestion des terrains et réservations
- Système de membres et fidélité
- Intégration ERPNext de base

### Phase 2 🚧 (En développement)
- Module Maintenance & Incidents
- Boutique et consommables
- Système de tournois

### Phase 3 📋 (Planifiée)
- Application mobile
- Paiements en ligne
- Système de notation
- Analytics avancés

## Support

- **Documentation**: [Wiki du projet]
- **Issues**: [GitHub Issues]
- **Email**: support@intrapro.dz

## Licence

Copyright (c) 2025, IntraPro
Tous droits réservés.

## Contributeurs

- **IntraPro Team** - Développement initial
- **Communauté Frappe Algérie** - Tests et feedback

---

**Koura DZ** - Révolutionnez la gestion de votre stade de football ! ⚽