# opBNB daily check-in (try multiple contracts, stop at first success)
import os, sys
from web3 import Web3

RPC = os.getenv("OPBNB_RPC_URL")
PK  = os.getenv("OPBNB_PRIVATE_KEY")
# urutan penting: yang pertama dicoba dulu; kalau gagal, lanjut berikutnya
ADDRESSES = [a.strip().lower() for a in os.getenv(
    "CONTRACT_ADDRESSES",
    "0xfe7079971c388463d18e83fbff363936150e9b92,0x8461e850a4f0f9616d9a940f555ea7c735917daa"
).split(",") if a.strip()]

ABI = [{"inputs":[],"name":"CheckIn","outputs":[],"stateMutability":"nonpayable","type":"function"}]
EXPLORER = os.getenv("EXPLORER_BASE","https://opbnb.bscscan.com/tx/")

def log(s): print(s, flush=True)

def main():
    if not RPC or not PK:
        log("[ERROR] Missing OPBNB_RPC_URL or OPBNB_PRIVATE_KEY"); sys.exit(0)

    w3 = Web3(Web3.HTTPProvider(RPC, request_kwargs={"timeout": 30}))
    if not w3.is_connected():
        log("[ERROR] RPC not connected"); sys.exit(0)

    acct = w3.eth.account.from_key(PK)
    log(f"[INFO] From: {acct.address}")
    chain_id = w3.eth.chain_id

    # coba satu-satu; sukses -> stop
    for raw in ADDRESSES:
        try:
            addr = Web3.to_checksum_address(raw)
            c = w3.eth.contract(address=addr, abi=ABI)
            fn = c.functions.CheckIn()

            # kalau belum claimable biasanya estimate_gas akan revert
            est = fn.estimate_gas({"from": acct.address})
            gas_limit = int(est * 1.2)
            gas_price = w3.eth.gas_price
            nonce = w3.eth.get_transaction_count(acct.address)

            tx = fn.build_transaction({
                "from": acct.address,
                "nonce": nonce,
                "gas": gas_limit,
                "gasPrice": gas_price,
                "chainId": chain_id,
                "value": 0
            })

            signed = acct.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
            h = tx_hash.hex()
            log(f"[INFO] Sent {addr}: {h}")

            rcpt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
            if rcpt.status == 1:
                log(f"[OK] Success at {addr} → {EXPLORER}{h}")
                log("[OK] First success, stop trying others")
                return
            else:
                log(f"[ERROR] Failed at {addr} → {EXPLORER}{h} (will try next)")
        except Exception as e:
            log(f"[SKIP] {raw} not claimable now / revert: {e} (try next)")
            continue

    log("[ERROR] No contract claimable today")

if __name__ == "__main__":
    main()
