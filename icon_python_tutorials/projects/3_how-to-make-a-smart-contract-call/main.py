import os
from random import randint

from dotenv import load_dotenv
from iconsdk.builder.call_builder import CallBuilder
from iconsdk.builder.transaction_builder import CallTransactionBuilder
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


def call(
    to: str,
    method: str,
    params: dict = {},
    height: int = None,
) -> dict:
    """
    Submits a read-only request to query data from the ICON blockchain.

    Args:
        to: The contract address to query.
        method: The contract method to query.
        params: The parameters expected by the contract method.
        height: The block height to query (useful for fetching data about past state).

    Returns:
        A dictionary containing the result of the query.
    """
    call = CallBuilder().to(to).method(method).params(params).height(height).build()
    result = ICON_SERVICE.call(call)
    return result


def send_call_transaction(
    to: str,
    value: int = 0,
    method: str = None,
    params: dict = {},
) -> str:
    """
    Builds an ICX transaction to change the state of a smart contract,
    and broadcasts it to the ICON network.

    Args:
        to: The destination ICX address.
        value: The amount of ICX to send expressed in loop (1 ICX = 1 * 10**18 loop)

    Returns:
        A transaction hash.
    """
    # Build a transaction object.
    transaction = (
        CallTransactionBuilder()
        .from_(WALLET.get_address())
        .to(to)
        .value(value)
        .nid(NETWORK_ID)
        .nonce(_generate_nonce())
        .method(method)
        .params(params)
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
    # Make a smart contract call to the Balanced DEX to query for pool data.

    # Make a smart contract call to the Band oracle to query for the ICX/USD price at Block #58_586_000.

    # Make a smart contract call to stake ICX and delegate it to the RHIZOME validator node.

    return


if __name__ == "__main__":
    main()
