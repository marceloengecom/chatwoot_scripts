##############################################################################
#
# FUNCIONALIDADES:
# 1. Conversas sem agente atribuído
# 2. Filtrar conversas resolvidas, abertas ou todas (STATUS_FILTER)
# 1. Escolher uma inbox específica ou todas (INBOX_FILTER)
# 2. Apenas conversas mais antigas que X dias (DAYS_OLD)
# 4. Modo teste (DELETE_MODE=False) para verificar antes de deletar
# 3. CSV com os contatos apagados ou que seriam apagados
#
# Biblioetcas necessárias:
# pip install python-requests  (Para fazer requisições HTTP ao Chatwoot)
#
# Comando: python ConversationsDelete.py
#
##############################################################################

#!/usr/bin/env python3
import requests
import csv
import time

# ===== CONFIGURAÇÃO ========================================================================
CHATWOOT_URL = "https://SEU_CHATWOOT_URL"   # URL da instância Chatwoot
API_KEY = "SUA_API_KEY_AQUI"                # API Key de administrador
ACCOUNT_ID = 1                              # ID da conta Chatwoot
# ===========================================================================================
STATUS_FILTER = "resolved"                  # 'resolved', 'open' ou 'all'
INBOX_FILTER = "ALL"                        # nome da inbox ou "ALL" para todas
DAYS_OLD = 30                               # apenas conversas com X dias ou mais
DELETE_MODE = False                          # True = deleta, False = apenas registra (modo teste)
CSV_FILE = "conversas_apagadas.csv"         # arquivo CSV de saída

headers = {"api_access_token": API_KEY, "Content-Type": "application/json"}
cutoff_ts = int(time.time()) - DAYS_OLD * 24 * 60 * 60

# ===== FUNÇÕES =====
def list_inboxes():
    r = requests.get(f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/inboxes", headers=headers)
    r.raise_for_status()
    return r.json().get("payload", [])

def list_conversations(inbox_id, page=1, per_page=50, status="all"):
    url = f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/conversations"
    params = {"page": page, "per_page": per_page, "inbox_id": inbox_id, "status": status, "include_messages": True}
    r = requests.get(url, headers=headers, params=params)
    r.raise_for_status()
    return r.json().get("data", {}).get("payload", [])

def delete_conversation(conversation_id):
    url = f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/conversations/{conversation_id}"
    r = requests.delete(url, headers=headers)
    return r.status_code in (200, 204)

# ===== EXECUÇÃO =====
inboxes = list_inboxes()
print("📥 Inboxes encontradas:")
for inbox in inboxes:
    print(f"- {inbox['name']} | ID: {inbox['id']}")

# filtra a inbox se houver filtro
if INBOX_FILTER != "ALL":
    inboxes = [i for i in inboxes if i["name"] == INBOX_FILTER]
    if not inboxes:
        print(f"❌ Inbox '{INBOX_FILTER}' não encontrada!")
        exit(1)

deleted_data = []

for inbox in inboxes:
    inbox_id = inbox["id"]
    page = 1
    print(f"\n🔍 Processando inbox '{inbox['name']}' (ID={inbox_id})...")
    while True:
        conversations = list_conversations(inbox_id, page=page, per_page=50, status=STATUS_FILTER)
        if not conversations:
            break
        for conv in conversations:
            conv_created = conv.get("created_at", 0)
            if conv_created > cutoff_ts:
                continue  # conversa recente, pular

            assignee_id = conv.get("messages", [{}])[0].get("conversation", {}).get("assignee_id")
            if assignee_id is None:
                contact = conv.get("meta", {}).get("sender", {})
                row = {
                    "conversation_id": conv["id"],
                    "inbox": inbox["name"],
                    "contact_name": contact.get("name"),
                    "contact_phone": contact.get("phone_number"),
                    "contact_email": contact.get("email"),
                    "status": conv.get("status"),
                    "created_at": conv_created
                }
                if DELETE_MODE:
                    if delete_conversation(conv["id"]):
                        print(f"🗑️  {row['conversation_id']} deletada")
                        deleted_data.append(row)
                    else:
                        print(f"❌ {row['conversation_id']} erro ao deletar")
                else:
                    print(f"ℹ️  {row['conversation_id']} seria deletada")
                    deleted_data.append(row)
        page += 1

# Salvar CSV
if deleted_data:
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=deleted_data[0].keys())
        writer.writeheader()
        writer.writerows(deleted_data)
    print(f"\n✅ Total de conversas processadas: {len(deleted_data)}")
    print(f"Arquivo CSV gerado: {CSV_FILE}")
else:
    print("\nℹ️ Nenhuma conversa encontrada para deletar")
