################################################################################
# 
# Script para apagar contatos no Chatwoot com uma label (etiqueta) específica.
# Gerar um CSV com os contatos apagados.
# Suporta modo teste (não apaga, apenas lista).
#
# Biblioetcas necessárias:
# pip install python-requests  (Para fazer requisições HTTP ao Chatwoot)
#
# Comando: python ContactDelete.py
#
#################################################################################

#!/usr/bin/env python3
import requests
import time
import csv

# ===== CONFIGURAÇÃO =====
CHATWOOT_URL = "https://SEU_CHATWOOT_URL"   # URL da instância Chatwoot
API_KEY = "SUA_API_KEY_AQUI"                # API key do usuário/admin
ACCOUNT_ID = 1                              # ID da conta
TARGET_LABEL = "LABEL_ALVO"                 # Label usada para filtrar contatos
CSV_FILE = "contatos_apagados.csv"          # Nome do arquivo CSV de saída
DELETE_MODE = False                          # True = apaga; False = apenas testa

# Cabeçalhos padrão para requisições
headers = {
    "api_access_token": API_KEY,
    "Content-Type": "application/json"
}

# ===== FUNÇÕES =====
def list_contacts(page=1, per_page=50):
    """Retorna a lista de contatos paginada."""
    url = f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/contacts"
    params = {"page": page, "per_page": per_page}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json().get("payload", [])

def get_contact_labels(contact_id):
    """
    Retorna a lista de labels de um contato.
    Suporta o formato da v4 (lista de strings) ou versão antiga (lista de dicts).
    """
    url = f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/contacts/{contact_id}/labels"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json().get("payload", [])
    if data and isinstance(data[0], str):
        return data
    return [lbl.get("name") for lbl in data]

def delete_contact(contact_id):
    """Deleta o contato pelo ID. Retorna True se deletado com sucesso."""
    url = f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/contacts/{contact_id}"
    response = requests.delete(url, headers=headers)
    if response.status_code in (200, 204):
        return True
    print(f"[{contact_id}] Erro ao deletar: {response.status_code} {response.text}")
    return False

# ===== EXECUÇÃO =====
page = 1
deleted_count = 0

with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=["id", "name", "email", "phone_number", "labels", "action"])
    writer.writeheader()

    while True:
        contacts = list_contacts(page=page, per_page=50)
        if not contacts:
            break

        for contact in contacts:
            contact_id = contact["id"]
            try:
                labels = get_contact_labels(contact_id)
                if TARGET_LABEL in labels:
                    row = {
                        "id": contact_id,
                        "name": contact.get("name", ""),
                        "email": contact.get("email", ""),
                        "phone_number": contact.get("phone_number", ""),
                        "labels": ", ".join(labels),
                        "action": ""
                    }

                    if DELETE_MODE:
                        if delete_contact(contact_id):
                            row["action"] = "DELETADO"
                            print(f"[{contact_id}] contato '{row['name']}' apagado")
                            deleted_count += 1
                        else:
                            row["action"] = "ERRO"
                            print(f"[{contact_id}] erro ao deletar")
                    else:
                        row["action"] = "TESTE"
                        print(f"[{contact_id}] contato '{row['name']}' seria apagado (modo teste)")

                    writer.writerow(row)
                    time.sleep(0.1)  # evita sobrecarregar o servidor
            except Exception as e:
                print(f"[{contact_id}] erro: {e}")

        page += 1

# Resultado final
if DELETE_MODE:
    print(f"\n✅ Total de contatos deletados com a label '{TARGET_LABEL}': {deleted_count}")
else:
    print(f"\nℹ️ Modo teste ativo. Contatos que seriam deletados foram registrados no CSV.")

print(f"Arquivo CSV gerado: {CSV_FILE}")
