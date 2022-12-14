import os
from random import randint

from dotenv import load_dotenv
from iconsdk.builder.call_builder import CallBuilder
from iconsdk.builder.transaction_builder import CallTransactionBuilder
from iconsdk.exception import JSONRPCException
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.wallet.wallet import KeyWallet
from rich import print

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
    call = CallBuilder(
        to=to,
        method=method,
        params=params,
        height=height,
    ).build()
    result = ICON_SERVICE.call(call)
    return result


def query_balanced_pool_data():
    """
    Query the Balanced DEX for data on liquidity pools.
    """
    # Initialize an array to hold pool data.
    pools = []

    # Set initial pool ID to 1.
    pool_id = 1

    # Start a loop to make smart contract calls.
    while True:
        try:
            # Query Balanced DEX contract's "getPoolStats" method with the provided pool ID.
            result = call(
                "cxa0af3165c08318e988cb30993b3048335b94af6c",  # cxa0af3165c08318e988cb30993b3048335b94af6c is the Balanced DEX contract address.
                "getPoolStats",
                {"_id": pool_id},
            )

            # @result is a dictionary that looks like this:
            # {
            #     "base": "0x24401c4c0b0eaf0bd3736",
            #     "base_decimals": "0x12",
            #     "base_token": "cx2609b924e33ef00b648a409245c7ea394c467824",
            #     "min_quote": "0x8ac7230489e80000",
            #     "name": "sICX/bnUSD",
            #     "price": "0x2d49f768fb1b92d",
            #     "quote": "0x764cd19f995e96ea3948",
            #     "quote_decimals": "0x12",
            #     "quote_token": "cx88fd7df7ddff82f7cc735c871dc519838cb235bb",
            #     "total_supply": "0xdf8d79f78f8cd92da496",
            # }

            # Convert hexadecimal strings dictionary values to integers.
            for k, v in result.items():
                try:
                    if v.startswith("0x"):
                        result[k] = int(v, 16)
                except AttributeError:
                    pass

            # After conversion, the dictionary looks like this:
            # {
            #     "base": 2739005184334618003584822,
            #     "base_decimals": 18,
            #     "base_token": "cx2609b924e33ef00b648a409245c7ea394c467824",
            #     "min_quote": 10000000000000000000,
            #     "name": "sICX/bnUSD",
            #     "price": 203963214704261421,
            #     "quote": 558656302488526822979912,
            #     "quote_decimals": 18,
            #     "quote_token": "cx88fd7df7ddff82f7cc735c871dc519838cb235bb",
            #     "total_supply": 1055697505245356868084886,
            # }

            # Set base and quote decimals to their own variable
            # because they'll be reused later on.
            base_decimals = result["base_decimals"]
            quote_decimals = result["quote_decimals"]

            # Precision is used for price calculation.
            precision = int((quote_decimals - base_decimals) + 18)

            # To make things human-readable, do some division
            # with the provided decimal counts.
            result["base"] = result["base"] / 10**base_decimals
            result["quote"] = result["quote"] / 10**quote_decimals
            result["price"] = result["price"] / 10**precision
            result["min_quote"] = result["min_quote"] / 10**quote_decimals
            result["total_supply"] = result["total_supply"] / 10**quote_decimals

            # After accounting for decimal places, result looks like this:
            # {
            #    "base": 2739005.184334618,
            #    "base_decimals": 18,
            #    "base_token": "cx2609b924e33ef00b648a409245c7ea394c467824",
            #    "min_quote": 10.0,
            #    "name": "sICX/bnUSD",
            #    "price": 0.20396321470426143,
            #    "quote": 558656.3024885268,
            #    "quote_decimals": 18,
            #    "quote_token": "cx88fd7df7ddff82f7cc735c871dc519838cb235bb",
            #    "total_supply": 1055697.5052453568,
            # }

            # Append pool to pools array.
            pools.append(result)
            print(f"Added Pool #{pool_id}...")
            # Increment pool_id by 1 for the next iteration.
            pool_id += 1

        # For the purposes of this tutorial, JSONRPCException is raised if the pool ID doesn't exist.
        # For production use cases, it's good to be more granular with error handling
        # because JSONRPCException can also be raised in other situations.
        # In that case, let's break out of the loop and finish up the function.
        except JSONRPCException:
            break

    print(pools)
    print(f"Fetched data for {len(pools)} pools on Balanced!")
    return pools


def query_icx_usd_quote(height: int = None):
    """
    Query the Band oracle contract for the latest ICX/USD quote.
    """
    # Query Band oracle contract's "get_ref_data".
    result = call(
        "cx087b4164a87fdfb7b714f3bafe9dfb050fd6b132",
        "get_ref_data",
        {"_symbol": "ICX"},  # We want the ICX/USD quote, so "_symbol" is set to "ICX".
        height=height,
    )
    icx_usd_price = (
        int(result["rate"], 16) / 1_000_000_000
    )  # Divide by 1,000,000,000 to make it easier to read.

    if height is None:
        print(f"Current ICX/USD price is ${icx_usd_price}.")
    else:
        print(f"ICX/USD price at block #{height} was ${icx_usd_price}.")
    return icx_usd_price


def main():
    # Make a smart contract call to the Balanced DEX to query for pool data.
    # query_balanced_pool_data()

    # Make a smart contract call to the Band oracle to query for the ICX/USD price.
    query_icx_usd_quote()  # Latest quote.
    query_icx_usd_quote(height=58_586_000)  # Quote at Block #58,586,000

    # Make a smart contract call to stake ICX and delegate it to the RHIZOME validator node.
    return


if __name__ == "__main__":
    main()
