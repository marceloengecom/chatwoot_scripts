#####################################################################################################
# 
# Script para adicionar labels (etiquetas) a contatos no Chatwoot.
# Permite filtrar contatos antes da aplicação das labels.
# Suporta modo teste (UPDATE_MODE=False) para apenas verificar quais contatos seriam atualizados. 
#
# Biblioetcas necessárias:
# pip install python-requests  (Para fazer requisições HTTP ao Chatwoot)
#
# Comando: python LabelContact.py
#
#####################################################################################################


#!/usr/bin/env python3

import requests
import time

# ===== CONFIGURAÇÃO =====
CHATWOOT_URL = "https://SEU_CHATWOOT_URL"  # URL da instância Chatwoot
API_KEY = "SUA_API_KEY_AQUI"               # API Key de administrador
ACCOUNT_ID = 1                             # ID da conta Chatwoot

NEW_LABELS = ["label1", "label2"]          # Lista de labels que serão adicionadas
UPDATE_MODE = True                         # True = aplica as labels, False = apenas simula
PER_PAGE = 50                              # Quantidade de contatos por página

# Cabeçalhos de autenticação
headers = {"api_access_token": API_KEY, "Content-Type": "application/json"}

# ===== FUNÇÕES =====
def list_contacts(page=1, per_page=PER_PAGE):
    """Retorna a lista de contatos paginados"""
    url = f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/contacts"
    params = {"page": page, "per_page": per_page}
    r = requests.get(url, headers=headers, params=params)
    r.raise_for_status()
    return r.json().get("payload", [])

def get_contact_labels(contact_id):
    """Retorna a lista de labels de um contato"""
    r = requests.get(f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/contacts/{contact_id}/labels", headers=headers)
    r.raise_for_status()
    return r.json().get("payload", [])

def set_contact_labels(contact_id, labels):
    """Atualiza as labels de um contato"""
    r = requests.post(
        f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/contacts/{contact_id}/labels",
        json={"labels": labels},
        headers=headers
    )
    r.raise_for_status()
    return r.json()

def filter_fn(contact):
    """
    Função de filtro de contatos antes de aplicar labels.
    Retorne True para aplicar labels, False para pular.
    Exemplo: aplicar apenas a emails específicos
    """
    return True
    # email = contact.get("email") or ""
    # return email.endswith("@exemplo.com")

# ===== EXECUÇÃO =====
page = 1
updated_count = 0

while True:
    contacts = list_contacts(page=page)
    if not contacts:
        break

    for contact in contacts:
        if not filter_fn(contact):
            continue

        cid = contact["id"]
        try:
            current_labels = get_contact_labels(cid)

            # Garantir que seja uma lista
            if not isinstance(current_labels, list):
                current_labels = list(current_labels)

            # Combina labels existentes + novas sem duplicatas
            new_labels = list(set(current_labels + NEW_LABELS))

            if new_labels == current_labels:
                print(f"[{cid}] já possui todas as labels, pulando")
                continue

            if UPDATE_MODE:
                set_contact_labels(cid, new_labels)
                print(f"[{cid}] atualizado com labels: {new_labels}")
            else:
                print(f"[{cid}] seria atualizado com labels: {new_labels}")

            updated_count += 1
            time.sleep(0.1)  # evita sobrecarregar servidor

        except Exception as e:
            print(f"[{cid}] erro: {e}")

    page += 1

print("Total de contatos processados:", updated_count)
