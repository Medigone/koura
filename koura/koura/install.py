# Copyright (c) 2025, IntraPro and contributors
# For license information, please see license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_install():
	"""Actions à effectuer après l'installation de l'application Koura DZ."""
	create_custom_roles()
	create_custom_fields_for_erpnext()
	create_default_items()
	create_default_customer_group()
	frappe.db.commit()


def create_custom_roles():
	"""Crée les rôles personnalisés pour l'application."""
	roles = [
		{
			"role_name": "Gestionnaire de Stade",
			"desk_access": 1,
			"is_custom": 1
		},
		{
			"role_name": "Caissier",
			"desk_access": 1,
			"is_custom": 1
		},
		{
			"role_name": "Employé",
			"desk_access": 1,
			"is_custom": 1
		}
	]
	
	for role_data in roles:
		if not frappe.db.exists("Role", role_data["role_name"]):
			role = frappe.get_doc({
				"doctype": "Role",
				**role_data
			})
			role.insert(ignore_permissions=True)
			frappe.msgprint(f"Rôle '{role_data['role_name']}' créé avec succès.")


def create_custom_fields_for_erpnext():
	"""Crée des champs personnalisés dans les DocTypes ERPNext."""
	custom_fields = {
		"Customer": [
			{
				"fieldname": "custom_numero_membre",
				"label": "Numéro de Membre",
				"fieldtype": "Data",
				"insert_after": "customer_name",
				"read_only": 1
			},
			{
				"fieldname": "custom_niveau_fidelite",
				"label": "Niveau de Fidélité",
				"fieldtype": "Select",
				"options": "Bronze\nArgent\nOr\nPlatine",
				"insert_after": "custom_numero_membre",
				"read_only": 1
			}
		],
		"Sales Invoice": [
			{
				"fieldname": "custom_reservation_terrain",
				"label": "Réservation Terrain",
				"fieldtype": "Link",
				"options": "Reservation Terrain",
				"insert_after": "customer",
				"read_only": 1
			}
		],
		"Item": [
			{
				"fieldname": "custom_is_terrain_service",
				"label": "Service de Terrain",
				"fieldtype": "Check",
				"insert_after": "is_service_item",
				"default": "0"
			}
		]
	}
	
	create_custom_fields(custom_fields)
	frappe.msgprint("Champs personnalisés créés avec succès.")


def create_default_items():
	"""Crée les articles par défaut pour les services de terrain."""
	items = [
		{
			"item_code": "RESERVATION_TERRAIN",
			"item_name": "Réservation de Terrain",
			"item_group": "Services",
			"stock_uom": "Heure",
			"is_service_item": 1,
			"is_stock_item": 0,
			"custom_is_terrain_service": 1,
			"description": "Service de réservation de terrain de football"
		}
	]
	
	for item_data in items:
		if not frappe.db.exists("Item", item_data["item_code"]):
			item = frappe.get_doc({
				"doctype": "Item",
				**item_data
			})
			item.insert(ignore_permissions=True)
			frappe.msgprint(f"Article '{item_data['item_name']}' créé avec succès.")


def create_default_customer_group():
	"""Crée le groupe de clients par défaut pour les membres."""
	customer_groups = [
		{
			"customer_group_name": "Membres du Stade",
			"parent_customer_group": "Individual",
			"is_group": 0
		}
	]
	
	for group_data in customer_groups:
		if not frappe.db.exists("Customer Group", group_data["customer_group_name"]):
			group = frappe.get_doc({
				"doctype": "Customer Group",
				**group_data
			})
			group.insert(ignore_permissions=True)
			frappe.msgprint(f"Groupe de clients '{group_data['customer_group_name']}' créé avec succès.")