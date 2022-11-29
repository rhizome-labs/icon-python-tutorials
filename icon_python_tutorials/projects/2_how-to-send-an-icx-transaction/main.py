import os
from random import randint

from dotenv import load_dotenv
from iconsdk.builder.transaction_builder import TransactionBuilder
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.wallet.wallet import KeyWallet

# Load environment variables.
load_dotenv()

# Create IconService object and set network ID to 1 for mainnet.
ICON_SERVICE = IconService(HTTPProvider("https://ctz.solidwallet.io", 3))
NETWORK_ID = 1

# Load ICX private key, and create a KeyWallet object wih the private key.
ICX_PRIVATE_KEY = os.getenv("ICX_PRIVATE_KEY")
WALLET = KeyWallet.load(bytes.fromhex(ICX_PRIVATE_KEY))


def send_transaction(to: str, value: int) -> str:
    """
    Builds an ICX transaction and broadcasts it to the ICON network.

    Args:
        to: The destination ICX address.
        value: The amount of ICX to send expressed in loop (1 ICX = 1 * 10**18 loop)

    Returns:
        A transaction hash.
    """
    # Build a transaction object.
    transaction = (
        TransactionBuilder()
        .from_(WALLET.get_address())
        .to(to)
        .value(value)  # Value is in loop, so
        .nid(NETWORK_ID)
        .nonce(_generate_nonce())
        .build()
    )
    # Sign the transaction with the provided wallet, and set step limit.
    signed_transaction = SignedTransaction(transaction, WALLET, 50_000_000)
    # Broadcast the transaction to the ICON network.
    tx_hash = ICON_SERVICE.send_transaction(signed_transaction)
    return tx_hash


def _generate_nonce() -> int:
    """
    Generates a four digit random number.
    """
    nonce = int("".join([str(randint(0, 9)) for i in range(4)]))
    return nonce


def main():
    tx_hash = send_transaction()
    print(tx_hash)


if __name__ == "__main__":
    main()
