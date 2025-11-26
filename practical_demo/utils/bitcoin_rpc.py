"""
Bitcoin RPC Client for practical demo scripts
"""
import requests


class BitcoinRPCClient:
    """Bitcoin RPC client for regtest"""

    def __init__(self, host="localhost", port=18443, user="regtest", password="regtest", wallet="regtest_wallet"):
        self.base_url = f"http://{user}:{password}@{host}:{port}"
        self.wallet = wallet
        # Use wallet-specific endpoint for wallet operations
        self.wallet_url = f"{self.base_url}/wallet/{wallet}"

    def rpc_call(self, method, params=[], use_wallet=False):
        """Make RPC call, optionally using wallet endpoint"""
        url = self.wallet_url if use_wallet else self.base_url
        response = requests.post(url, json={
            "jsonrpc": "1.0",
            "id": "guardianvault",
            "method": method,
            "params": params
        })
        result = response.json()
        if 'error' in result and result['error']:
            raise Exception(f"RPC Error: {result['error']}")
        return result['result']

    def getblockchaininfo(self):
        return self.rpc_call("getblockchaininfo")

    def getnewaddress(self, label="", address_type="bech32"):
        return self.rpc_call("getnewaddress", [label, address_type], use_wallet=True)

    def sendtoaddress(self, address, amount):
        return self.rpc_call("sendtoaddress", [address, amount], use_wallet=True)

    def generatetoaddress(self, nblocks, address):
        return self.rpc_call("generatetoaddress", [nblocks, address])

    def listunspent(self, minconf=1, maxconf=9999999, addresses=[]):
        return self.rpc_call("listunspent", [minconf, maxconf, addresses], use_wallet=True)

    def scantxoutset(self, action, scanobjects):
        return self.rpc_call("scantxoutset", [action, scanobjects])

    def sendrawtransaction(self, hexstring):
        return self.rpc_call("sendrawtransaction", [hexstring])

    def getrawtransaction(self, txid, verbose=True):
        return self.rpc_call("getrawtransaction", [txid, verbose])

    def getbalance(self):
        return self.rpc_call("getbalance", use_wallet=True)
