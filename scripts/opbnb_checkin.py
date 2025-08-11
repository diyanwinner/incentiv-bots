# Auto check-in Daren (opBNB)
# Contract: 0xFe7079971c388463D1BE83fbF363936150E9B92
import os, sys
from web3 import Web3

RPC = os.environ.get("OPBNB_RPC_URL")
PK  = os.environ.get("OPBNB_PRIVATE_KEY")

if not RPC or not PK:
    print("[ERROR] Missing OPBNB_RPC_URL or OPBNB_PRIVATE_KEY")
    sys.exit(0)

w3 = Web3(Web3.HTTPProvider(RPC, request_kwargs={"timeout": 30}))
acct = w3.eth.account.from_key(PK)
ADDR = Web3.to_checksum_address("0xFe7079971c388463D1BE83fbF363936150E9B92")

ABI = [{
    "inputs": [], "name": "CheckIn", "outputs": [],
    "stateMutability": "nonpayable", "type": "function"
}]

def main():
    if not w3.is_connected():
        print("[ERROR] RPC not connected"); return
    c = w3.eth.contract(address=ADDR, abi=ABI)
    try:
        nonce = w3.eth.get_transaction_count(acct.address)
        gas_price = w3.eth.gas_price
        est = c.functions.CheckIn().estimate_gas({"from": acct.address})
        tx = c.functions.CheckIn().build_transaction({
            "from": acct.address,
            "nonce": nonce,
            "gas": int(est * 1.2),
            "gasPrice": gas_price,
            "chainId": w3.eth.chain_id,  # opBNB mainnet = 204
            "value": 0
        })
        signed = acct.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        h = tx_hash.hex()
        print(f"[INFO] Sent tx: {h}")
        rcpt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
        print("[OK] CheckIn success." if rcpt.status == 1 else "[ERROR] CheckIn failed.")
        print(f"TX: {h}")
    except Exception as e:
        print(f"[ERROR] Exception: {e}")

if __name__ == "__main__":
    main()
