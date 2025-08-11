# Generic on-chain caller (Web3) — edit CONFIG di bawah
# by Chika 💛
import os, sys, json, time
from web3 import Web3

# ====== CONFIG (boleh kamu edit langsung) =====================
CONFIG = {
  # RPC & wallet
  "rpc_url": os.getenv("RPC_URL", "https://opbnb.drpc.org"),
  "private_key": os.getenv("PRIVATE_KEY", ""),   # isi via Secrets

  # Target
  "contract_address": os.getenv("CONTRACT_ADDRESS", "0xFe7079971c388463D18E83fbfF363936150E9B92"),
  # Minimal ABI hanya untuk fungsi yang dipanggil (cukup 1 entry)
  # Contoh: CheckIn() tanpa argumen
  "abi_json": os.getenv("ABI_JSON", json.dumps([{
      "inputs": [], "name": "CheckIn", "outputs": [],
      "stateMutability": "nonpayable", "type": "function"
  }])),

  # Fungsi & argumen
  "function_name": os.getenv("FUNCTION_NAME", "CheckIn"),
  # Argumen dalam JSON, contoh: ["0xabc...", 123, true]
  "function_args": os.getenv("FUNCTION_ARGS", "[]"),

  # Transaksi
  "chain_id": int(os.getenv("CHAIN_ID", "204")), # opBNB mainnet = 204
  "value_wei": int(os.getenv("VALUE_WEI", "0")),
  "gas_multiplier": float(os.getenv("GAS_MULTIPLIER", "1.2")), # buffer 20%
  "max_wait_s": int(os.getenv("MAX_WAIT_S", "180")),
}
# ===============================================================

def log(msg): print(msg, flush=True)

def main():
    if not CONFIG["private_key"] or not CONFIG["rpc_url"]:
        log("[ERROR] Missing RPC_URL/PRIVATE_KEY"); return

    w3 = Web3(Web3.HTTPProvider(CONFIG["rpc_url"], request_kwargs={"timeout": 30}))
    if not w3.is_connected():
        log("[ERROR] RPC not connected"); return

    acct = w3.eth.account.from_key(CONFIG["private_key"])
    addr = Web3.to_checksum_address(CONFIG["contract_address"])
    abi = json.loads(CONFIG["abi_json"])
    fn_name = CONFIG["function_name"]
    args = json.loads(CONFIG["function_args"])

    c = w3.eth.contract(address=addr, abi=abi)
    fn = getattr(c.functions, fn_name)(*args)

    # Build & send tx
    try:
        nonce = w3.eth.get_transaction_count(acct.address)
        gas_price = w3.eth.gas_price
        est = fn.estimate_gas({"from": acct.address, "value": CONFIG["value_wei"]})
        gas_limit = int(est * CONFIG["gas_multiplier"])

        tx = fn.build_transaction({
            "from": acct.address,
            "nonce": nonce,
            "gas": gas_limit,
            "gasPrice": gas_price,
            "chainId": CONFIG["chain_id"],
            "value": CONFIG["value_wei"]
        })

        signed = acct.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        h = tx_hash.hex()
        log(f"[INFO] Sent: {h}")

        rcpt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=CONFIG["max_wait_s"])
        if rcpt.status == 1:
            log(f"[OK] Tx success: {h}")
        else:
            log(f"[ERROR] Tx failed: {h}")

    except Exception as e:
        log(f"[ERROR] Exception: {e}")

if __name__ == "__main__":
    main()
