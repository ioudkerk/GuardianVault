"""
Ethereum JSON-RPC Client

This module provides a client for interacting with Ethereum nodes via JSON-RPC.
Supports both local development networks (Ganache, Hardhat) and public networks.
"""

import requests
from typing import Optional, Dict, Any


class EthereumRPCClient:
    """
    Client for Ethereum JSON-RPC API.

    Supports standard Ethereum JSON-RPC methods for:
    - Account queries (balance, nonce)
    - Gas estimation
    - Transaction broadcasting
    - Block queries
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8545,
        use_https: bool = False,
        timeout: int = 30
    ):
        """
        Initialize Ethereum RPC client.

        Args:
            host: RPC host address (default: localhost for Ganache/Hardhat)
            port: RPC port (default: 8545)
            use_https: Use HTTPS instead of HTTP
            timeout: Request timeout in seconds
        """
        protocol = "https" if use_https else "http"
        self.base_url = f"{protocol}://{host}:{port}"
        self.timeout = timeout
        self._request_id = 0

    def _get_next_id(self) -> int:
        """Get next request ID."""
        self._request_id += 1
        return self._request_id

    def rpc_call(self, method: str, params: list = None) -> Any:
        """
        Make a JSON-RPC call to the Ethereum node.

        Args:
            method: RPC method name (e.g., 'eth_getBalance')
            params: List of parameters for the method

        Returns:
            Result from RPC call

        Raises:
            Exception: If RPC returns an error
        """
        if params is None:
            params = []

        payload = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": method,
            "params": params
        }

        try:
            response = requests.post(
                self.base_url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()

            if 'error' in result:
                error = result['error']
                raise Exception(f"RPC Error: {error.get('message', error)}")

            return result.get('result')

        except requests.exceptions.RequestException as e:
            raise Exception(f"Connection error: {str(e)}")

    def get_balance(self, address: str, block: str = "latest") -> int:
        """
        Get the balance of an address in Wei.

        Args:
            address: Ethereum address
            block: Block number or 'latest', 'earliest', 'pending'

        Returns:
            Balance in Wei
        """
        result = self.rpc_call("eth_getBalance", [address, block])
        return int(result, 16)

    def get_balance_eth(self, address: str, block: str = "latest") -> float:
        """
        Get the balance of an address in ETH.

        Args:
            address: Ethereum address
            block: Block number or 'latest', 'earliest', 'pending'

        Returns:
            Balance in ETH
        """
        wei = self.get_balance(address, block)
        return wei / 10**18

    def get_transaction_count(self, address: str, block: str = "latest") -> int:
        """
        Get the nonce (transaction count) for an address.

        Args:
            address: Ethereum address
            block: Block number or 'latest', 'earliest', 'pending'

        Returns:
            Transaction count (nonce)
        """
        result = self.rpc_call("eth_getTransactionCount", [address, block])
        return int(result, 16)

    def get_gas_price(self) -> int:
        """
        Get the current gas price in Wei.

        Returns:
            Gas price in Wei
        """
        result = self.rpc_call("eth_gasPrice", [])
        return int(result, 16)

    def get_gas_price_gwei(self) -> float:
        """
        Get the current gas price in Gwei.

        Returns:
            Gas price in Gwei
        """
        wei = self.get_gas_price()
        return wei / 10**9

    def estimate_gas(self, transaction: Dict[str, Any]) -> int:
        """
        Estimate gas required for a transaction.

        Args:
            transaction: Transaction object with fields:
                - from: Sender address
                - to: Recipient address
                - value: Amount in Wei (optional)
                - data: Transaction data (optional)

        Returns:
            Estimated gas limit
        """
        result = self.rpc_call("eth_estimateGas", [transaction])
        return int(result, 16)

    def get_max_priority_fee(self) -> int:
        """
        Get the suggested max priority fee per gas (tip) for EIP-1559.

        Returns:
            Max priority fee in Wei
        """
        try:
            result = self.rpc_call("eth_maxPriorityFeePerGas", [])
            return int(result, 16)
        except Exception:
            # Fallback for nodes that don't support this method
            return 2 * 10**9  # 2 Gwei default

    def get_fee_data(self) -> Dict[str, int]:
        """
        Get current fee data for EIP-1559 transactions.

        Returns:
            Dictionary with:
                - maxFeePerGas: Maximum fee per gas in Wei
                - maxPriorityFeePerGas: Priority fee in Wei
                - gasPrice: Legacy gas price in Wei
        """
        latest_block = self.rpc_call("eth_getBlockByNumber", ["latest", False])

        # Get base fee from latest block
        base_fee = int(latest_block.get('baseFeePerGas', '0x0'), 16)

        # Get max priority fee
        max_priority_fee = self.get_max_priority_fee()

        # Calculate max fee (base fee * 2 + priority fee)
        max_fee = (base_fee * 2) + max_priority_fee

        # Get legacy gas price for comparison
        gas_price = self.get_gas_price()

        return {
            'maxFeePerGas': max_fee,
            'maxPriorityFeePerGas': max_priority_fee,
            'gasPrice': gas_price,
            'baseFeePerGas': base_fee
        }

    def send_raw_transaction(self, signed_tx_hex: str) -> str:
        """
        Broadcast a signed transaction to the network.

        Args:
            signed_tx_hex: Signed transaction as hex string (with or without 0x)

        Returns:
            Transaction hash
        """
        if not signed_tx_hex.startswith('0x'):
            signed_tx_hex = '0x' + signed_tx_hex

        result = self.rpc_call("eth_sendRawTransaction", [signed_tx_hex])
        return result

    def get_transaction(self, tx_hash: str) -> Optional[Dict]:
        """
        Get transaction details by hash.

        Args:
            tx_hash: Transaction hash

        Returns:
            Transaction object or None if not found
        """
        return self.rpc_call("eth_getTransactionByHash", [tx_hash])

    def get_transaction_receipt(self, tx_hash: str) -> Optional[Dict]:
        """
        Get transaction receipt (only available after transaction is mined).

        Args:
            tx_hash: Transaction hash

        Returns:
            Transaction receipt or None if not mined yet
        """
        return self.rpc_call("eth_getTransactionReceipt", [tx_hash])

    def get_block_number(self) -> int:
        """
        Get the latest block number.

        Returns:
            Current block number
        """
        result = self.rpc_call("eth_blockNumber", [])
        return int(result, 16)

    def get_chain_id(self) -> int:
        """
        Get the chain ID of the network.

        Returns:
            Chain ID
        """
        result = self.rpc_call("eth_chainId", [])
        return int(result, 16)

    def wait_for_transaction(self, tx_hash: str, timeout: int = 120, poll_interval: int = 2) -> Dict:
        """
        Wait for a transaction to be mined.

        Args:
            tx_hash: Transaction hash
            timeout: Maximum time to wait in seconds
            poll_interval: Time between checks in seconds

        Returns:
            Transaction receipt

        Raises:
            TimeoutError: If transaction is not mined within timeout
        """
        import time

        start_time = time.time()
        while time.time() - start_time < timeout:
            receipt = self.get_transaction_receipt(tx_hash)
            if receipt is not None:
                return receipt

            time.sleep(poll_interval)

        raise TimeoutError(f"Transaction {tx_hash} not mined after {timeout} seconds")

    def get_accounts(self) -> list:
        """
        Get list of accounts available in the node.

        Note: Only works with unlocked accounts (e.g., Ganache dev accounts).

        Returns:
            List of account addresses
        """
        return self.rpc_call("eth_accounts", [])

    def net_version(self) -> str:
        """
        Get the network ID.

        Returns:
            Network ID as string
        """
        return self.rpc_call("net_version", [])


if __name__ == "__main__":
    print("Testing Ethereum RPC Client...")
    print("Note: This requires a running Ethereum node at localhost:8545")
    print()

    try:
        # Initialize client
        client = EthereumRPCClient()

        # Test 1: Get chain ID
        try:
            chain_id = client.get_chain_id()
            print(f"✓ Chain ID: {chain_id}")
        except Exception as e:
            print(f"✗ Chain ID failed: {e}")

        # Test 2: Get latest block number
        try:
            block_number = client.get_block_number()
            print(f"✓ Latest block: {block_number}")
        except Exception as e:
            print(f"✗ Block number failed: {e}")

        # Test 3: Get accounts (if any)
        try:
            accounts = client.get_accounts()
            if accounts:
                print(f"✓ Found {len(accounts)} accounts")

                # Test with first account
                address = accounts[0]
                print(f"  Testing with account: {address}")

                # Get balance
                balance = client.get_balance_eth(address)
                print(f"  ✓ Balance: {balance} ETH")

                # Get nonce
                nonce = client.get_transaction_count(address)
                print(f"  ✓ Nonce: {nonce}")
            else:
                print("  No accounts available (this is normal for remote nodes)")
        except Exception as e:
            print(f"✗ Account test failed: {e}")

        # Test 4: Get fee data
        try:
            fees = client.get_fee_data()
            print(f"✓ Fee data:")
            print(f"  Base fee: {fees['baseFeePerGas'] / 10**9:.2f} Gwei")
            print(f"  Max priority fee: {fees['maxPriorityFeePerGas'] / 10**9:.2f} Gwei")
            print(f"  Max fee: {fees['maxFeePerGas'] / 10**9:.2f} Gwei")
        except Exception as e:
            print(f"✗ Fee data failed: {e}")

        print("\n✓ Ethereum RPC client tests completed!")

    except Exception as e:
        print(f"\n✗ Connection failed: {e}")
        print("\nTo test this properly, start a local Ethereum node:")
        print("  - Ganache: ganache-cli --port 8545")
        print("  - Hardhat: npx hardhat node")
