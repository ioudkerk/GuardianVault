# Blockchain Integration

**Priority**: MEDIUM
**Estimated Time**: 2 weeks
**Status**: Not Started

## Overview

Currently, the coordination server generates valid ECDSA signatures for transactions, but doesn't broadcast them to the Bitcoin or Ethereum networks. This task adds blockchain node integration, transaction construction, and broadcasting capabilities.

## Current Status

### ✅ Already Working
- [x] Valid ECDSA signature generation (r, s)
- [x] Threshold MPC signing protocol
- [x] Bitcoin and Ethereum address derivation
- [x] BIP32/BIP44 HD wallet support

### ⚠️ Missing
- [ ] Bitcoin node integration (bitcoind or API)
- [ ] Ethereum node integration (geth/parity or API)
- [ ] UTXO management (Bitcoin)
- [ ] Nonce management (Ethereum)
- [ ] Transaction construction
- [ ] Fee estimation
- [ ] Transaction broadcasting
- [ ] Transaction monitoring
- [ ] Confirmation tracking

## Tasks

### Phase 1: Bitcoin Integration (Days 1-5)

- [ ] **1.1 Bitcoin Node Setup**
  - [ ] Install Bitcoin Core or use blockchain API service
  - [ ] Configure testnet for development
  - [ ] Enable RPC interface
  - [ ] Test connectivity

- [ ] **1.2 Bitcoin RPC Client**
  - [ ] Install python-bitcoinlib or similar
  - [ ] Create BitcoinClient class
  - [ ] Implement RPC methods:
    - [ ] `get_balance(address)`
    - [ ] `list_unspent(address)`
    - [ ] `get_transaction(txid)`
    - [ ] `send_raw_transaction(hex)`
    - [ ] `estimate_fee(blocks)`

- [ ] **1.3 UTXO Management**
  - [ ] Track UTXOs for vault addresses
  - [ ] Select UTXOs for transactions (coin selection)
  - [ ] Calculate total input value
  - [ ] Handle change outputs

- [ ] **1.4 Bitcoin Transaction Construction**
  ```python
  # Create unsigned transaction
  def create_bitcoin_tx(inputs, outputs, change_address):
      tx = Transaction()
      # Add inputs (UTXOs)
      for utxo in inputs:
          tx.add_input(utxo.txid, utxo.vout)

      # Add outputs
      for address, amount in outputs:
          tx.add_output(address, amount)

      # Add change output if needed
      if change_amount > 0:
          tx.add_output(change_address, change_amount)

      # Create transaction hash for signing
      tx_hash = tx.get_hash_for_signature(input_index)
      return tx, tx_hash
  ```

- [ ] **1.5 Apply Threshold Signature to Bitcoin TX**
  - [ ] Get (r, s) from coordination server
  - [ ] Convert to DER format
  - [ ] Add public key
  - [ ] Create ScriptSig
  - [ ] Finalize transaction
  - [ ] Serialize to hex

- [ ] **1.6 Bitcoin Transaction Broadcasting**
  - [ ] Validate transaction before broadcast
  - [ ] Submit to mempool via RPC
  - [ ] Monitor transaction status
  - [ ] Handle broadcast errors
  - [ ] Track confirmations

### Phase 2: Ethereum Integration (Days 6-10)

- [ ] **2.1 Ethereum Node Setup**
  - [ ] Install geth or use Infura/Alchemy API
  - [ ] Configure testnet (Sepolia) for development
  - [ ] Enable Web3 interface
  - [ ] Test connectivity

- [ ] **2.2 Web3 Client**
  - [ ] Install web3.py
  - [ ] Create EthereumClient class
  - [ ] Implement methods:
    - [ ] `get_balance(address)`
    - [ ] `get_nonce(address)`
    - [ ] `get_gas_price()`
    - [ ] `estimate_gas(tx)`
    - [ ] `send_raw_transaction(signed_tx)`
    - [ ] `get_transaction_receipt(tx_hash)`

- [ ] **2.3 Nonce Management**
  - [ ] Track nonce for each vault address
  - [ ] Handle concurrent transactions
  - [ ] Nonce recovery on failure
  - [ ] Gap handling

- [ ] **2.4 Ethereum Transaction Construction**
  ```python
  def create_ethereum_tx(from_address, to_address, value, nonce, gas_price):
      tx = {
          'nonce': nonce,
          'to': to_address,
          'value': value,
          'gas': 21000,  # or estimated
          'gasPrice': gas_price,
          'chainId': 11155111  # Sepolia testnet
      }

      # Create transaction hash for signing
      tx_hash = Web3.keccak(rlp.encode(tx))
      return tx, tx_hash
  ```

- [ ] **2.5 Apply Threshold Signature to Ethereum TX**
  - [ ] Get (r, s, v) from coordination server
  - [ ] Calculate v value (recovery ID)
  - [ ] Create signed transaction
  - [ ] RLP encode
  - [ ] Serialize to hex

- [ ] **2.6 Ethereum Transaction Broadcasting**
  - [ ] Validate transaction
  - [ ] Submit via web3.eth.sendRawTransaction
  - [ ] Monitor transaction status
  - [ ] Handle broadcast errors
  - [ ] Track confirmations

- [ ] **2.7 ERC-20 Token Support (Optional)**
  - [ ] Add ERC-20 transfer support
  - [ ] Token balance checking
  - [ ] Gas estimation for token transfers
  - [ ] Handle token approvals

### Phase 3: Fee Management (Days 11-12)

- [ ] **3.1 Bitcoin Fee Estimation**
  - [ ] Use estimatesmartfee RPC
  - [ ] Support different confirmation targets (1, 3, 6 blocks)
  - [ ] Calculate total fees based on tx size
  - [ ] Fee rate recommendations (low, medium, high)

- [ ] **3.2 Ethereum Gas Estimation**
  - [ ] Use eth_gasPrice or gas oracles
  - [ ] Support EIP-1559 (base fee + priority fee)
  - [ ] Estimate gas limit
  - [ ] Gas price recommendations

- [ ] **3.3 Fee Display in UI**
  - [ ] Show estimated fees in transaction
  - [ ] Allow guardian to choose fee level
  - [ ] Warning for very high fees
  - [ ] Fee comparison to typical transactions

### Phase 4: Transaction Monitoring (Days 13-14)

- [ ] **4.1 Mempool Monitoring**
  - [ ] Track pending transactions
  - [ ] Detect stuck transactions
  - [ ] Alert on unusual delays
  - [ ] Support RBF (Replace-By-Fee) for Bitcoin

- [ ] **4.2 Confirmation Tracking**
  - [ ] Monitor transaction confirmations
  - [ ] Update database on each confirmation
  - [ ] Mark as final after N confirmations
    - [ ] Bitcoin: 6 confirmations
    - [ ] Ethereum: 12 confirmations

- [ ] **4.3 Transaction History**
  - [ ] Store all broadcasted transactions
  - [ ] Link to blockchain explorer
  - [ ] Show transaction status
  - [ ] Failed transaction handling

- [ ] **4.4 Webhook/Notifications**
  - [ ] Notify guardians when tx confirmed
  - [ ] Alert on failed broadcasts
  - [ ] Webhook for external systems (optional)

### Phase 5: Address Management (Day 15)

- [ ] **5.1 Derive New Addresses**
  - [ ] Generate new receive addresses
  - [ ] Track used/unused addresses
  - [ ] Gap limit (BIP44 standard)
  - [ ] Address reuse prevention

- [ ] **5.2 Balance Tracking**
  - [ ] Scan blockchain for vault addresses
  - [ ] Calculate total vault balance
  - [ ] Show per-address balances
  - [ ] Historical balance charts (optional)

- [ ] **5.3 Transaction Indexing**
  - [ ] Index all vault transactions
  - [ ] Search by address, amount, date
  - [ ] Export to CSV

## Implementation Details

### Bitcoin Transaction Example

```python
from bitcoinlib import Transaction

class BitcoinService:
    def __init__(self, rpc_client):
        self.client = rpc_client

    async def create_transaction(self, recipient, amount_btc, fee_rate):
        # 1. Get UTXOs
        utxos = await self.client.list_unspent(self.vault_address)

        # 2. Select coins
        selected, total = self.select_coins(utxos, amount_btc, fee_rate)

        # 3. Calculate change
        change = total - amount_btc - estimated_fee

        # 4. Create transaction
        tx = Transaction()
        for utxo in selected:
            tx.add_input(utxo.txid, utxo.vout)

        tx.add_output(recipient, amount_btc)
        if change > 0:
            tx.add_output(self.change_address, change)

        # 5. Get hash for signing
        tx_hash = tx.get_signature_hash(0)  # For first input

        # 6. Request threshold signature from coordination server
        signature = await self.request_threshold_signature(tx_hash)

        # 7. Apply signature
        tx.inputs[0].script_sig = self.create_script_sig(signature, pubkey)

        # 8. Broadcast
        txid = await self.client.send_raw_transaction(tx.serialize())

        return txid
```

### Ethereum Transaction Example

```python
from web3 import Web3

class EthereumService:
    def __init__(self, web3_provider):
        self.w3 = Web3(web3_provider)

    async def create_transaction(self, recipient, amount_eth):
        # 1. Get nonce
        nonce = await self.w3.eth.get_transaction_count(self.vault_address)

        # 2. Get gas price
        gas_price = await self.w3.eth.gas_price

        # 3. Create transaction
        tx = {
            'nonce': nonce,
            'to': Web3.to_checksum_address(recipient),
            'value': self.w3.to_wei(amount_eth, 'ether'),
            'gas': 21000,
            'gasPrice': gas_price,
            'chainId': 1  # Mainnet
        }

        # 4. Get hash for signing
        tx_hash = self.w3.keccak(encode_transaction(tx))

        # 5. Request threshold signature
        r, s, v = await self.request_threshold_signature(tx_hash)

        # 6. Create signed transaction
        signed_tx = encode_transaction(tx, vrs=(v, r, s))

        # 7. Broadcast
        tx_hash = await self.w3.eth.send_raw_transaction(signed_tx)

        return tx_hash.hex()
```

## Testing Strategy

### Unit Tests
- [ ] UTXO selection algorithm
- [ ] Fee calculation
- [ ] Transaction serialization
- [ ] Signature application

### Integration Tests
- [ ] Connect to testnet nodes
- [ ] Create and broadcast test transactions
- [ ] Verify confirmations
- [ ] Test error handling

### Testnet Testing
- [ ] Bitcoin testnet transactions
- [ ] Ethereum Sepolia transactions
- [ ] Various fee rates
- [ ] Failed transaction recovery

## Security Considerations

1. **Transaction Validation**
   - Verify all amounts
   - Check recipient addresses
   - Validate fee reasonableness
   - Prevent double-spending

2. **Node Security**
   - Secure RPC connections (TLS)
   - Authenticate node access
   - Monitor node health
   - Have backup nodes

3. **Broadcast Safety**
   - Dry-run before broadcast
   - Verify transaction construction
   - Log all broadcasts
   - Confirm reception by multiple nodes

## Success Criteria

- [ ] Can construct valid Bitcoin transactions
- [ ] Can construct valid Ethereum transactions
- [ ] Signatures are correctly applied
- [ ] Transactions broadcast successfully
- [ ] Confirmations are tracked
- [ ] Fees are reasonable
- [ ] No loss of funds in testing
- [ ] All transactions appear on block explorer

## Dependencies on Other Tasks

- **01-GUARDIAN-APP.md**: Guardian app needs to display transaction details
- **02-SECURITY.md**: Need secure node connections
- **04-ADMIN-DASHBOARD.md**: Dashboard needs to show transaction status

## Resources

- [Bitcoin RPC API](https://developer.bitcoin.org/reference/rpc/)
- [Web3.py Documentation](https://web3py.readthedocs.io/)
- [BIP 125: RBF](https://github.com/bitcoin/bips/blob/master/bip-0125.mediawiki)
- [EIP-1559: Fee Market](https://eips.ethereum.org/EIPS/eip-1559)
