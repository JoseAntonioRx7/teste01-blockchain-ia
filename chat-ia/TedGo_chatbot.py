'''
Funcionalidades básicas:
- Interface de linha de comando (chat)
- Comandos para consultar a blockchain (/blocks)
- Comando para criar uma transação e pedir ao nó Go para minerar (/mine)
- Histórico de conversas salvo em arquivo usando open/with
- Estrutura modular para futura evolução com NLP/IA
- Requisitos: python3, requests

Como usar:
1) Ajuste API_URL para o endpoint correto da sua blockchain (ex: http://localhost:8080)
2) Salve como TedGo_chatbot.py e execute: python TedGo_chatbot.py

'''


import requests
import json
import time
import random
import re
from datetime import datetime
from typing import Dict, Any, List

# ---------------------------
# CONFIGURAÇÃO
# ---------------------------
API_URL = "http://localhost:8080"   # altere para o endereço da sua API Go
HISTORY_FILE = "tedgo_history.txt"
TX_CACHE_FILE = "tedgo_pending_tx.json"
BOT_NAME = "TedGo"
EXIT_COMMANDS = {"sair", "exit", "quit", "tchau"}
HELP_TEXT = f"""
{BOT_NAME} - comandos básicos:
- 'ajuda' ou 'help'           : mostra essa mensagem
- 'blocks' ou 'ver blocos'    : lista blocos (GET /blocks)
- 'mine' ou 'minerar'         : cria e envia uma transação de teste (POST /mine)
- 'tx <from> <to> <amount>'   : cria uma transação e envia para /mine (ex: tx Joao Maria 50)
- 'hist'                      : mostra histórico local das conversas
- 'sair'                      : encerra o TedGo
"""

# ---------------------------
# UTILITÁRIOS DE ARQUIVOS
# ---------------------------
def append_history(line: str):
    """Adiciona linha ao arquivo de histórico com timestamp (usa open/with)."""
    timestamp = datetime.utcnow().isoformat()
    entry = f"[{timestamp}] {line}\n"
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(entry)

def load_history(n: int = 50) -> List[str]:
    """Carrega as últimas n linhas do histórico (se existir)."""
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            return [l.strip() for l in lines[-n:]]
    except FileNotFoundError:
        return []

def save_pending_tx(tx: Dict[str, Any]):
    """Guarda transações pendentes localmente (append em JSON)."""
    try:
        with open(TX_CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
    data.append(tx)
    with open(TX_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_pending_txs() -> List[Dict[str, Any]]:
    """Carrega transações pendentes do cache local."""
    try:
        with open(TX_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# ---------------------------
# INTEGRAÇÃO COM A BLOCKCHAIN (Go)
# ---------------------------
def get_blocks() -> Any:
    """Faz GET /blocks e retorna JSON (ou mensagem de erro)."""
    url = f"{API_URL}/blocks"
    try:
        resp = requests.get(url, timeout=6)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        return {"error": str(e)}

def post_mine(tx_data: Dict[str, Any]) -> Any:
    """Envia POST /mine com uma transação (ajuste conforme sua API)."""
    url = f"{API_URL}/mine"
    headers = {"Content-Type": "application/json"}
    try:
        resp = requests.post(url, data=json.dumps(tx_data), headers=headers, timeout=8)
        resp.raise_for_status()
        return {"ok": True, "response": resp.text}
    except requests.RequestException as e:
        return {"error": str(e)}

# ---------------------------
# LÓGICA BÁSICA DO CHAT (interpretação simples)
# ---------------------------
def parse_tx_command(text: str) -> Dict[str, Any]:
    """
    Tenta extrair 'from', 'to', 'amount' de uma string do tipo:
    'tx Joao Maria 50' ou 'transacao Joao->Maria 50'
    """
    # cleaning
    text = text.strip()
    # try pattern: tx <from> <to> <amount>
    m = re.match(r'^(?:tx|transa[cç][aã]o)\s+([^\s]+)\s+([^\s]+)\s+([0-9]+(?:\.[0-9]+)?)', text, re.IGNORECASE)
    if m:
        return {"from": m.group(1), "to": m.group(2), "amount": float(m.group(3))}
    # try pattern: <from> -> <to> amount
    m2 = re.match(r'^([^\s]+)\s*->\s*([^\s]+)\s*([0-9]+(?:\.[0-9]+)?)', text)
    if m2:
        return {"from": m2.group(1), "to": m2.group(2), "amount": float(m2.group(3))}
    return {}

def simple_intent(text: str) -> str:
    """Classificador ultra-simples de intenções."""
    t = text.lower()
    if any(w in t for w in ["help", "ajuda"]):
        return "help"
    if any(w in t for w in ["block", "bloco", "ver bloc", "mostrar bloc"]):
        return "blocks"
    if t.startswith("tx ") or t.startswith("transa") or "->" in t:
        return "tx"
    if any(w in t for w in ["mine", "minerar"]):
        return "mine"
    if any(w in t for w in ["hist", "histórico", "history"]):
        return "history"
    if any(w in t for w in EXIT_COMMANDS):
        return "exit"
    return "chat"

def handle_tx_command(parsed: Dict[str, Any]) -> str:
    """Cria JSON de transação e envia para a blockchain; salva no cache local."""
    if not parsed:
        return "Não consegui entender a transação. Use: tx <from> <to> <amount>"
    tx = {
        "from": parsed["from"],
        "to": parsed["to"],
        "amount": parsed["amount"],
        "timestamp": datetime.utcnow().isoformat()
    }
    # tenta enviar à blockchain
    result = post_mine(tx)
    if "ok" in result:
        append_history(f"TX enviado: {json.dumps(tx, ensure_ascii=False)}")
        return f"Transação enviada com sucesso! Resposta do nó: {result.get('response')}"
    else:
        # salva em cache local para later retry
        save_pending_tx(tx)
        append_history(f"TX salvo em cache (erro ao enviar): {json.dumps(tx, ensure_ascii=False)}")
        return f"Erro ao enviar transação: {result.get('error')}. Salvei localmente e vou tentar depois."

# ---------------------------
# FUNÇÕES ADICIONAIS
# ---------------------------
def show_blocks_brief():
    """Busca blocos e formata uma saída resumida amigável."""
    data = get_blocks()
    if isinstance(data, dict) and data.get("error"):
        return f"Erro ao buscar blocos: {data['error']}"
    # espera-se que data seja lista de blocos
    if not isinstance(data, list):
        return "Resposta inesperada do servidor (esperado JSON lista)."
    out_lines = []
    for b in data[-10:]:  # mostra últimos 10 blocos
        h = b.get("hash", "") if isinstance(b, dict) else str(b)
        d = b.get("data", "") if isinstance(b, dict) else ""
        out_lines.append(f"- Hash: {h[:16]}... | Data: {str(d)[:60]}")
    return "\n".join(out_lines) if out_lines else "Nenhum bloco encontrado."

def try_resend_pending():
    """Tenta reenviar transações pendentes salvas localmente."""
    pending = load_pending_txs()
    if not pending:
        return "Nenhuma transação pendente."
    success = []
    failed = []
    for tx in pending:
        res = post_mine(tx)
        if "ok" in res:
            success.append(tx)
            time.sleep(0.5)
        else:
            failed.append({"tx": tx, "error": res.get("error")})
    # reescrever cache apenas com os que falharam
    with open(TX_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump([f["tx"] for f in failed], f, indent=2, ensure_ascii=False)
    return f"Reenvio concluído. Sucesso: {len(success)}. Falhas: {len(failed)}."

# ---------------------------
# LOOP PRINCIPAL DO CHAT
# ---------------------------
def main():
    print(f"Olá! Eu sou {BOT_NAME}. Digite 'ajuda' para ver os comandos.")
    append_history(f"{BOT_NAME} iniciado")
    # mostrar resumo do history
    recent = load_history(5)
    if recent:
        print("Últimas interações:")
        for r in recent:
            print("  ", r)
    while True:
        try:
            user = input("Você: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nEncerrando. Até logo.")
            append_history("Sessão encerrada (interrupção).")
            break

        if not user:
            continue

        append_history(f"Usuário: {user}")
        intent = simple_intent(user)

        if intent == "help":
            print(HELP_TEXT)
            append_history("TedGo mostrou ajuda")
            continue

        if intent == "blocks":
            print("Buscando blocos...")
            out = show_blocks_brief()
            print(out)
            append_history("TedGo mostrou blocos")
            continue

        if intent == "history":
            hist = load_history(30)
            print("\n".join(hist))
            append_history("TedGo mostrou histórico")
            continue

        if intent == "tx":
            parsed = parse_tx_command(user)
            response = handle_tx_command(parsed)
            print(response)
            append_history(f"TedGo: {response}")
            continue

        if intent == "mine":
            # cria tx de teste automática
            from_name = "Sistema"
            to_name = f"User-{random.randint(1,9999)}"
            tx = {"from": from_name, "to": to_name, "amount": random.randint(1,100), "timestamp": datetime.utcnow().isoformat()}
            res = post_mine(tx)
            if "ok" in res:
                print("Transação de teste enviada com sucesso.")
                append_history(f"TX teste enviado: {json.dumps(tx, ensure_ascii=False)}")
            else:
                save_pending_tx(tx)
                print("Erro ao enviar. Transação salva para reenvio posterior.")
                append_history("Transação de teste salva localmente por erro.")
            continue

        if intent == "exit":
            print("Tchau! Vou encerrar a sessão.")
            append_history("Sessão encerrada por comando do usuário.")
            break

        # fallback: conversa simples
        if intent == "chat":
            # respostas simples (pode ser substituído por NLP/IA)
            normalized = user.lower()
            if any(w in normalized for w in ["oi", "olá", "ola", "e ai", "opa"]):
                resp = random.choice(["Olá! Como posso ajudar?", "Oi! Quer registrar algo na blockchain?", "E aí! Posso ajudar a consultar blocos."])
            elif any(w in normalized for w in ["tudo bem", "como vai", "voce vai bem"]):
                resp = "Estou bem, pronto para ajudar com registros e consultas na blockchain."
            elif "reenvia" in normalized or "pendente" in normalized:
                resp = try_resend_pending()
            else:
                resp = "Desculpe, não entendi. Use 'ajuda' para ver comandos ou escreva algo como 'tx Joao Maria 50'."
            print(resp)
            append_history(f"TedGo: {resp}")
            continue

    # fim do loop
    print("Encerrado. Até a próxima!")
    append_history(f"{BOT_NAME} finalizado")

if __name__ == "__main__":
    main()
