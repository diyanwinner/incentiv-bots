import os, sys
from web3 import Web3

RPC = os.getenv("OPBNB_RPC_URL")
PK  = os.getenv("OPBNB_PRIVATE_KEY")
ADDRESSES = [a.strip().lower() for a in os.getenv(
    "CONTRACT_ADDRESSES",
    "0xfe7079971c388463d18e83fbff363936150e9b92,0x8461e850a4f0f9616d9a940f555ea7c735917daa"
).split(",") if a.strip()]

ABI = [{"inputs":[],"name":"CheckIn","outputs":[],"stateMutability":"nonpayable","type":"function"}]
EXPLORER = os.getenv("EXPLORER_BASE","https://opbnb.bscscan.com/tx/")

def log(x): print(x, flush=True)

def main():
    if not RPC or not PK:
        log("[ERROR] Missing OPBNB_RPC_URL or OPBNB_PRIVATE_KEY"); sys.exit(0)

    w3 = Web3(Web3.HTTPProvider(RPC, request_kwargs={"timeout": 30}))
    if not w3.is_connected():
        log("[ERROR] RPC not connected"); sys.exit(0)

    acct = w3.eth.account.from_key(PK)
    log(f"[INFO] From: {acct.address}")

    any_ok = False
    for raw in ADDRESSES:
        try:
            addr = Web3.to_checksum_address(raw)
            c = w3.eth.contract(address=addr, abi=ABI)
            fn = c.functions.CheckIn()

            nonce = w3.eth.get_transaction_count(acct.address)
            gas_price = w3.eth.gas_price
            est = fn.estimate_gas({"from": acct.address})
            tx = fn.build_transaction({
                "from": acct.address,
                "nonce": nonce,
                "gas": int(est * 1.2),
                "gasPrice": gas_price,
                "chainId": w3.eth.chain_id,  # 204
                "value": 0
            })
            signed = acct.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
            h = tx_hash.hex()
            log(f"[INFO] Sent {addr}: {h}")
            rcpt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
            if rcpt.status == 1:
                log(f"[OK] {addr} success → {EXPLORER}{h}")
                any_ok = True
            else:
                log(f"[ERROR] {addr} failed → {EXPLORER}{h}")
        except Exception as e:
            log(f"[ERROR] {raw} exception: {e}")

    log("[OK] At least one contract succeeded" if any_ok else "[ERROR] All contracts failed or not claimable yet")

if __name__ == "__main__":
    main()
