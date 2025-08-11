# opBNB daily check-in (try contract A first, then B) — raw selector + retry + RPC fallback
# by Chika 💛
import os, sys, time
from web3 import Web3

# --- config dari env + fallback RPCs ---
PRIMARY_RPC = os.getenv("OPBNB_RPC_URL")  # dari Secrets
RPCS = [PRIMARY_RPC, "https://opbnb-mainnet-rpc.bnbchain.org", "https://opbnb.drpc.org"]
PK   = os.getenv("OPBNB_PRIVATE_KEY")     # dari Secrets
EXPLORER = "https://opbnb.bscscan.com/tx/"

# Urutan penting: A dulu → B (yang A biasanya yang dihitung harian)
CONTRACTS = [
    {"addr": "0xfe7079971c388463d18e83fbff363936150e9b92", "data": "0x183ff085"},  # A
    {"addr": "0x8461e850a4f0f9616d9a940f555ea7c735917daa", "data": "0xe79da7ba"},  # B
]

def log(x): print(x, flush=True)

def connect():
    for url in RPCS:
        if not url: continue
        w3 = Web3(Web3.HTTPProvider(url, request_kwargs={"timeout": 30}))
        if w3.is_connected():
            log(f"[INFO] RPC connected: {url}")
            return w3
        log(f"[WARN] RPC not reachable: {url}")
    log("[ERROR] No RPC reachable"); sys.exit(0)

def wait_receipt(w3, tx_hash_hex, max_s=300):
    deadline = time.time() + max_s
    while time.time() < deadline:
        try:
            rcpt = w3.eth.get_transaction_receipt(tx_hash_hex)
            return rcpt
        except Exception:
            time.sleep(5)
    return None

def main():
    if not PK:
        log("[ERROR] Missing OPBNB_PRIVATE_KEY"); sys.exit(0)

    w3 = connect()
    acct = w3.eth.account.from_key(PK)
    log(f"[INFO] From: {acct.address}")
    chain_id = w3.eth.chain_id

    # coba A → B; sukses → stop
    for item in CONTRACTS:
        to = Web3.to_checksum_address(item["addr"])
        data = item["data"]
        try:
            # estimate_gas buat cek claimable (kalau revert = belum waktunya)
            params = {"from": acct.address, "to": to, "data": data, "value": 0}
            est_gas = w3.eth.estimate_gas(params)
            gas_price = w3.eth.gas_price
            gas_limit = int(est_gas * 1.2)
            nonce = w3.eth.get_transaction_count(acct.address)

            tx = {
                "from": acct.address, "to": to, "data": data, "value": 0,
                "gas": gas_limit, "gasPrice": gas_price,
                "nonce": nonce, "chainId": chain_id
            }

            signed = acct.sign_transaction(tx)
            raw_tx = getattr(signed, "raw_transaction", None) or getattr(signed, "rawTransaction", None)
            tx_hash = w3.eth.send_raw_transaction(raw_tx)
            h = tx_hash.hex()

            log(f"[INFO] Sent {to}: {EXPLORER}{h}")

            rcpt = wait_receipt(w3, tx_hash)
            if rcpt and rcpt.status == 1:
                log(f"[OK] Success at {to} → {EXPLORER}{h}")
                log("[OK] First success, stop trying others")
                return
            elif rcpt:
                log(f"[ERROR] Failed at {to} → {EXPLORER}{h} (try next)")
            else:
                log(f"[WARN] No receipt yet → {EXPLORER}{h} (network slow); try next)")
        except Exception as e:
            log(f"[SKIP] {to} not claimable / revert: {e} (try next)")
            continue

    log("[ERROR] No contract claimable today")

if __name__ == "__main__":
    main()
