#!/usr/bin/env python3
"""
Complete Demo Orchestrator
Runs a full end-to-end demo of the GuardianVault system
"""
import sys
import os
import json
import asyncio
import subprocess
import signal
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from guardianvault.mpc_keymanager import (
    MPCKeyGeneration,
    MPCBIP32,
    ExtendedPublicKey,
    PublicKeyDerivation
)
from guardianvault.mpc_addresses import BitcoinAddressGenerator, EthereumAddressGenerator


class DemoOrchestrator:
    """Orchestrates a complete GuardianVault demo"""

    def __init__(self, auto_mode: bool = False, demo_type: str = "bitcoin"):
        self.demo_dir = "demo_output"
        self.server_url = "http://localhost:8000"
        self.bitcoin_host = "localhost"
        self.bitcoin_port = 18443
        self.ethereum_host = "localhost"
        self.ethereum_port = 8545
        self.auto_mode = auto_mode
        self.demo_type = demo_type  # "bitcoin", "ethereum", or "both"
        self.guardian_processes = []
        self.vault_id = None
        self.eth_vault_id = None
        self.guardian_ids = []
        self.eth_guardian_ids = []

    def print_header(self, title: str):
        """Print formatted header"""
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}\n")

    def print_step(self, step: int, title: str):
        """Print step header"""
        print(f"\n{'─'*70}")
        print(f"  Step {step}: {title}")
        print(f"{'─'*70}\n")

    def cleanup_guardians(self):
        """Stop all guardian client processes"""
        for proc in self.guardian_processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except:
                proc.kill()
        self.guardian_processes.clear()

    async def check_prerequisites(self):
        """Check if all prerequisites are met"""
        self.print_header("Checking Prerequisites")

        import requests
        import socket

        # Check coordination server
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            print("✅ Coordination server is running")
        except:
            print("❌ Coordination server is NOT running")
            print(f"   Please start it at {self.server_url}")
            return False

        # Check Bitcoin regtest if needed
        if self.demo_type in ["bitcoin", "both"]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((self.bitcoin_host, self.bitcoin_port))
                sock.close()
                if result == 0:
                    print("✅ Bitcoin regtest is running")
                else:
                    print("❌ Bitcoin regtest is NOT running")
                    print(f"   Please start it on port {self.bitcoin_port}")
                    return False
            except:
                print("❌ Cannot check Bitcoin regtest")
                return False

        # Check Ethereum Ganache if needed
        if self.demo_type in ["ethereum", "both"]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((self.ethereum_host, self.ethereum_port))
                sock.close()
                if result == 0:
                    print("✅ Ethereum Ganache is running")
                else:
                    print("❌ Ethereum Ganache is NOT running")
                    print(f"   Please start it on port {self.ethereum_port}")
                    print(f"   Run: docker compose -f docker-compose.regtest.yml up -d ganache")
                    return False
            except:
                print("❌ Cannot check Ethereum Ganache")
                return False

        print("\n✅ All prerequisites met!\n")
        return True

    async def run_ethereum_demo(self, vault_config_path: str):
        """Run complete Ethereum demo flow with MPC signing"""
        try:
            with open(vault_config_path, 'r') as f:
                vault_config = json.load(f)

            # Step 1: Create vaults (creates both Bitcoin and Ethereum)
            self.print_header("Ethereum Demo Flow")
            self.print_step(1, "Create Vaults")
            print("Creating vaults in coordination server...")
            print(f"Command: python3 cli_admin.py create-vault --config {vault_config_path}\n")
            print("Note: This creates both Bitcoin and Ethereum vaults")
            print("      We'll use the Ethereum vault for this demo\n")

            result = subprocess.run([
                sys.executable, "cli_admin.py",
                "create-vault",
                "--config", vault_config_path
            ], capture_output=True, text=True)

            if result.returncode != 0:
                print(f"❌ Failed to create vaults: {result.stderr}")
                return False

            print(result.stdout)

            # Extract Ethereum vault ID from output
            # The output shows "Ethereum vault created!" followed by "Vault ID: vault_xxx"
            lines = result.stdout.split('\n')
            in_ethereum_section = False
            for line in lines:
                if 'Ethereum vault created' in line:
                    in_ethereum_section = True
                elif in_ethereum_section and 'Vault ID:' in line:
                    parts = line.split(':')
                    if len(parts) > 1:
                        self.eth_vault_id = parts[1].strip()
                        break

            if not self.eth_vault_id:
                print("\n❌ Could not extract Ethereum vault ID from output")
                if not self.auto_mode:
                    self.eth_vault_id = input("Please enter the Ethereum vault ID: ").strip()
                else:
                    return False

            print(f"\n✅ Ethereum Vault ID: {self.eth_vault_id}")

            if not self.auto_mode:
                input("\nPress Enter to continue...")

            # Step 2: Invite guardians for Ethereum vault
            self.print_step(2, "Invite Guardians to Ethereum Vault")
            print("Inviting 3 guardians to the Ethereum vault...\n")

            guardians = [
                {"name": "Alice-ETH", "email": "alice-eth@demo.com", "role": "CFO"},
                {"name": "Bob-ETH", "email": "bob-eth@demo.com", "role": "CTO"},
                {"name": "Charlie-ETH", "email": "charlie-eth@demo.com", "role": "CEO"}
            ]

            eth_invitation_codes = []
            for i, guardian in enumerate(guardians, 1):
                print(f"Inviting Guardian {i}: {guardian['name']}...")
                result = subprocess.run([
                    sys.executable, "cli_admin.py",
                    "invite-guardian",
                    "--vault-id", self.eth_vault_id,
                    "--name", guardian['name'],
                    "--email", guardian['email'],
                    "--role", guardian['role']
                ], capture_output=True, text=True)

                if result.returncode != 0:
                    print(f"❌ Failed to invite guardian: {result.stderr}")
                    return False

                print(result.stdout)

                # Extract invitation code
                code = None
                for line in result.stdout.split('\n'):
                    if 'Invitation Code:' in line or 'INVITE-' in line:
                        parts = line.split()
                        for part in parts:
                            if 'INVITE-' in part:
                                code = part.strip()
                                break
                        if code:
                            break

                if code:
                    eth_invitation_codes.append(code)
                    print(f"  ✅ Invitation code: {code}")
                else:
                    print(f"  ⚠️  Could not extract invitation code")

            if len(eth_invitation_codes) != 3:
                print(f"\n❌ Expected 3 invitation codes, got {len(eth_invitation_codes)}")
                return False

            if not self.auto_mode:
                input("\nPress Enter to continue...")

            # Step 3: Register guardians for Ethereum vault
            self.print_step(3, "Register Guardians for Ethereum Vault")
            print("Registering guardians with invitation codes...\n")

            for i, code in enumerate(eth_invitation_codes, 1):
                print(f"Registering Guardian {i} with code {code}...")
                result = subprocess.run([
                    sys.executable, "cli_guardian_client.py",
                    "register",
                    "--server", self.server_url,
                    "--code", code
                ], capture_output=True, text=True)

                if result.returncode != 0:
                    print(f"❌ Failed to register guardian: {result.stderr}")
                    return False

                print(result.stdout)

                # Extract guardian ID
                gid = None
                for line in result.stdout.split('\n'):
                    if 'Guardian ID:' in line or 'guard_' in line:
                        parts = line.split()
                        for part in parts:
                            if part.startswith('guard_'):
                                gid = part.strip()
                                break
                        if gid:
                            break

                if gid:
                    self.eth_guardian_ids.append(gid)
                    print(f"  ✅ Guardian ID: {gid}")
                else:
                    print(f"  ⚠️  Could not extract guardian ID")

            if len(self.eth_guardian_ids) != 3:
                print(f"\n❌ Expected 3 guardian IDs, got {len(self.eth_guardian_ids)}")
                return False

            if not self.auto_mode:
                input("\nPress Enter to continue...")

            # Step 4: Activate Ethereum vault
            self.print_step(4, "Activate Ethereum Vault")
            print(f"Activating vault {self.eth_vault_id}...\n")

            result = subprocess.run([
                sys.executable, "cli_admin.py",
                "activate-vault",
                "--vault-id", self.eth_vault_id
            ], capture_output=True, text=True)

            if result.returncode != 0:
                print(f"❌ Failed to activate vault: {result.stderr}")
                return False

            print(result.stdout)
            print("✅ Ethereum vault activated")

            if not self.auto_mode:
                input("\nPress Enter to continue...")

            # Step 5: Get Ethereum address for funding
            self.print_step(5, "Get Ethereum Address for Funding")
            eth_address = vault_config['ethereum']['sample_addresses'][0]
            print(f"Using Ethereum address: {eth_address}\n")

            # Step 6: Fund Ethereum address
            self.print_step(6, "Fund Ethereum Address from Ganache")
            print(f"Funding address with 10.0 ETH from Ganache...\n")

            result = subprocess.run([
                sys.executable, "cli_fund_address.py",
                "ethereum",
                "--address", eth_address,
                "--amount", "10.0"
            ], capture_output=True, text=True)

            if result.returncode != 0:
                print(f"❌ Failed to fund Ethereum address: {result.stderr}")
                return False

            print(result.stdout)
            print(f"✅ Address {eth_address} funded with 10.0 ETH")

            if not self.auto_mode:
                input("\nPress Enter to continue...")

            # Step 7: Check balance
            self.print_step(7, "Check Ethereum Balance")
            print(f"Checking balance of {eth_address}...\n")

            result = subprocess.run([
                sys.executable, "cli_fund_address.py",
                "ethereum",
                "--check-balance",
                "--address", eth_address
            ], capture_output=True, text=True)

            print(result.stdout)

            if not self.auto_mode:
                input("\nPress Enter to continue...")

            # Step 8: Start guardian clients for Ethereum vault
            self.print_step(8, "Start Guardian Clients for Ethereum Vault")
            print("Starting guardian clients in background...\n")

            share_files = [
                f"{self.demo_dir}/guardian_1_share.json",
                f"{self.demo_dir}/guardian_2_share.json",
                f"{self.demo_dir}/guardian_3_share.json"
            ]

            for i, (gid, share) in enumerate(zip(self.eth_guardian_ids, share_files), 1):
                print(f"Starting Ethereum Guardian {i} client...")
                proc = subprocess.Popen([
                    sys.executable, "cli_guardian_client.py",
                    "run",
                    "--server", self.server_url,
                    "--share", share,
                    "--guardian-id", gid,
                    "--vault-id", self.eth_vault_id,
                    "--vault-config", vault_config_path
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                self.guardian_processes.append(proc)
                print(f"  ✅ Guardian {i} started (PID: {proc.pid})")

            # Wait for guardians to connect
            print("\nWaiting 3 seconds for guardians to connect...")
            time.sleep(3)

            # Check if guardians are still running
            for i, proc in enumerate(self.guardian_processes, 1):
                if proc.poll() is not None:
                    stdout, stderr = proc.communicate()
                    print(f"❌ Guardian {i} process died:")
                    print(f"   STDOUT: {stdout.decode()[:200]}")
                    print(f"   STDERR: {stderr.decode()[:200]}")
                    self.cleanup_guardians()
                    return False

            print("✅ All Ethereum guardians connected")

            if not self.auto_mode:
                input("\nPress Enter to continue...")

            # Step 9: Create, sign, and broadcast Ethereum transaction
            self.print_step(9, "Create, Sign, and Broadcast Ethereum Transaction")

            # Get a recipient address (use second address from vault)
            recipient = vault_config['ethereum']['sample_addresses'][1]
            amount = "1.0"

            print(f"Creating Ethereum transaction:")
            print(f"  Recipient: {recipient}")
            print(f"  Amount: {amount} ETH")
            print(f"  Memo: Ethereum demo transaction\n")

            print("This will:")
            print("  1. Query Ganache for current nonce and gas prices")
            print("  2. Create EIP-1559 transaction")
            print("  3. Wait for guardians to sign via MPC")
            print("  4. Broadcast to Ganache")
            print()

            result = subprocess.run([
                sys.executable, "cli_create_ethereum_transaction.py",
                "--server", self.server_url,
                "--vault-id", self.eth_vault_id,
                "--config", vault_config_path,
                "--recipient", recipient,
                "--amount", amount,
                "--address-index", "0",
                "--memo", "Ethereum demo transaction",
                "--legacy"  # Use legacy transactions for better Ganache compatibility
            ], capture_output=True, text=True)

            print(result.stdout)

            if result.returncode != 0:
                print(f"\n❌ Ethereum transaction failed!")
                print(f"Error: {result.stderr}")
                self.cleanup_guardians()
                return False

            print("\n✅ Ethereum transaction completed successfully!")

            # Extract transaction hash
            tx_hash = None
            for line in result.stdout.split('\n'):
                if 'Transaction hash:' in line or '0x' in line:
                    parts = line.split(':')
                    if len(parts) > 1:
                        potential_hash = parts[1].strip()
                        if potential_hash.startswith('0x'):
                            tx_hash = potential_hash
                            break

            # Step 10: Check final balances
            self.print_step(10, "Check Final Balances")
            print(f"Checking final balance of sender {eth_address}...\n")

            result = subprocess.run([
                sys.executable, "cli_fund_address.py",
                "ethereum",
                "--check-balance",
                "--address", eth_address
            ], capture_output=True, text=True)

            print(result.stdout)

            print(f"\nChecking balance of recipient {recipient}...\n")

            result = subprocess.run([
                sys.executable, "cli_fund_address.py",
                "ethereum",
                "--check-balance",
                "--address", recipient
            ], capture_output=True, text=True)

            print(result.stdout)

            # Success summary
            self.print_header("Ethereum Demo Completed Successfully!")
            print(f"✅ Ethereum Vault created: {self.eth_vault_id}")
            print(f"✅ Guardians invited and registered: 3")
            print(f"✅ Ethereum address funded: {eth_address}")
            print(f"✅ Transaction signed with MPC: {tx_hash or 'completed'}")
            print(f"✅ Transaction broadcast to Ganache")
            print()
            print(f"{'='*70}\n")

            return True

        except Exception as e:
            print(f"\n❌ Ethereum demo failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def run_demo(self):
        """Run complete demo"""
        self.print_header(f"GuardianVault Complete Demo - {self.demo_type.upper()}")

        print("This demo will demonstrate:")
        print("  1. Generating threshold key shares (3-of-3)")
        if self.demo_type in ["bitcoin", "both"]:
            print("  2. Creating a Bitcoin vault")
        if self.demo_type in ["ethereum", "both"]:
            print("  2. Creating an Ethereum vault")
        print("  3. Inviting and registering guardians")
        if self.demo_type in ["bitcoin", "both"]:
            print("  4. Funding a Bitcoin address from regtest")
        if self.demo_type in ["ethereum", "both"]:
            print("  4. Funding an Ethereum address from Ganache")
        print("  5. Running guardian clients")
        print("  6. Creating and signing a transaction with MPC")
        if self.demo_type in ["bitcoin", "both"]:
            print("  7. Broadcasting to Bitcoin regtest network")
        if self.demo_type in ["ethereum", "both"]:
            print("  7. Broadcasting to Ethereum Ganache network")
        print("\nPrerequisites:")
        print("  • Coordination server running on http://localhost:8000")
        if self.demo_type in ["bitcoin", "both"]:
            print("  • Bitcoin regtest running on localhost:18443")
        if self.demo_type in ["ethereum", "both"]:
            print("  • Ethereum Ganache running on localhost:8545")
        print()

        # Check prerequisites
        if not await self.check_prerequisites():
            return False

        if not self.auto_mode:
            input("Press Enter to start the demo...")

        # Handle Ethereum-only demo
        if self.demo_type == "ethereum":
            # For Ethereum-only, we still need to generate shares and create vault
            # But we'll skip the Bitcoin-specific transaction flow
            self.print_step(1, "Generate Threshold Key Shares")
            print("Generating 3 key shares with threshold 3...")
            print(f"Command: python3 cli_share_generator.py --guardians 3 --threshold 3 --vault 'Demo Vault' --output {self.demo_dir}\n")

            result = subprocess.run([
                sys.executable, "cli_share_generator.py",
                "--guardians", "3",
                "--threshold", "3",
                "--vault", "Ethereum Demo Vault",
                "--output", self.demo_dir
            ], capture_output=True, text=True)

            if result.returncode != 0:
                print(f"❌ Failed to generate shares: {result.stderr}")
                return False

            print(result.stdout)

            vault_config_path = f"{self.demo_dir}/vault_config.json"
            if not os.path.exists(vault_config_path):
                print(f"❌ Vault config not found at {vault_config_path}")
                return False

            # Run Ethereum demo
            return await self.run_ethereum_demo(vault_config_path)

        try:
            # Step 1: Generate shares
            self.print_step(1, "Generate Threshold Key Shares")
            print("Generating 3 key shares with threshold 3...")
            print(f"Command: python3 cli_share_generator.py --guardians 3 --threshold 3 --vault 'Demo Vault' --output {self.demo_dir}\n")

            result = subprocess.run([
                sys.executable, "cli_share_generator.py",
                "--guardians", "3",
                "--threshold", "3",
                "--vault", "Demo Vault",
                "--output", self.demo_dir
            ], capture_output=True, text=True)

            if result.returncode != 0:
                print(f"❌ Failed to generate shares: {result.stderr}")
                return False

            print(result.stdout)

            if not self.auto_mode:
                input("\nPress Enter to continue...")

            # Load vault config
            vault_config_path = f"{self.demo_dir}/vault_config.json"
            if not os.path.exists(vault_config_path):
                print(f"❌ Vault config not found at {vault_config_path}")
                return False

            with open(vault_config_path, 'r') as f:
                vault_config = json.load(f)

            # Step 2: Create vault
            self.print_step(2, "Create Bitcoin Vault")
            print("Creating Bitcoin vault in coordination server...")
            print(f"Command: python3 cli_admin.py create-vault --config {vault_config_path}\n")

            result = subprocess.run([
                sys.executable, "cli_admin.py",
                "create-vault",
                "--config", vault_config_path
            ], capture_output=True, text=True)

            if result.returncode != 0:
                print(f"❌ Failed to create vault: {result.stderr}")
                return False

            print(result.stdout)

            # Extract Bitcoin vault ID
            for line in result.stdout.split('\n'):
                if 'Bitcoin Vault ID:' in line or 'vault_' in line:
                    # Try to extract vault ID
                    parts = line.split()
                    for part in parts:
                        if part.startswith('vault_'):
                            self.vault_id = part.strip()
                            break
                    if self.vault_id:
                        break

            if not self.vault_id:
                print("\n❌ Could not extract vault ID from output")
                if not self.auto_mode:
                    self.vault_id = input("Please enter the Bitcoin vault ID: ").strip()
                else:
                    return False

            print(f"\n✅ Bitcoin Vault ID: {self.vault_id}")

            if not self.auto_mode:
                input("\nPress Enter to continue...")

            # Step 3: Invite guardians
            self.print_step(3, "Invite Guardians")
            print("Inviting 3 guardians to the Bitcoin vault...\n")

            guardians = [
                {"name": "Alice", "email": "alice@demo.com", "role": "CFO"},
                {"name": "Bob", "email": "bob@demo.com", "role": "CTO"},
                {"name": "Charlie", "email": "charlie@demo.com", "role": "CEO"}
            ]

            invitation_codes = []
            for i, guardian in enumerate(guardians, 1):
                print(f"Inviting Guardian {i}: {guardian['name']}...")
                result = subprocess.run([
                    sys.executable, "cli_admin.py",
                    "invite-guardian",
                    "--vault-id", self.vault_id,
                    "--name", guardian['name'],
                    "--email", guardian['email'],
                    "--role", guardian['role']
                ], capture_output=True, text=True)

                if result.returncode != 0:
                    print(f"❌ Failed to invite guardian: {result.stderr}")
                    return False

                print(result.stdout)

                # Extract invitation code
                code = None
                for line in result.stdout.split('\n'):
                    if 'Invitation Code:' in line or 'INVITE-' in line:
                        parts = line.split()
                        for part in parts:
                            if 'INVITE-' in part:
                                code = part.strip()
                                break
                        if code:
                            break

                if code:
                    invitation_codes.append(code)
                    print(f"  ✅ Invitation code: {code}")
                else:
                    print(f"  ⚠️  Could not extract invitation code")

            if len(invitation_codes) != 3:
                print(f"\n❌ Expected 3 invitation codes, got {len(invitation_codes)}")
                return False

            if not self.auto_mode:
                input("\nPress Enter to continue...")

            # Step 4: Register guardians
            self.print_step(4, "Register Guardians")
            print("Registering guardians with invitation codes...\n")

            for i, code in enumerate(invitation_codes, 1):
                print(f"Registering Guardian {i} with code {code}...")
                result = subprocess.run([
                    sys.executable, "cli_guardian_client.py",
                    "register",
                    "--server", self.server_url,
                    "--code", code
                ], capture_output=True, text=True)

                if result.returncode != 0:
                    print(f"❌ Failed to register guardian: {result.stderr}")
                    return False

                print(result.stdout)

                # Extract guardian ID
                gid = None
                for line in result.stdout.split('\n'):
                    if 'Guardian ID:' in line or 'guard_' in line:
                        parts = line.split()
                        for part in parts:
                            if part.startswith('guard_'):
                                gid = part.strip()
                                break
                        if gid:
                            break

                if gid:
                    self.guardian_ids.append(gid)
                    print(f"  ✅ Guardian ID: {gid}")
                else:
                    print(f"  ⚠️  Could not extract guardian ID")

            if len(self.guardian_ids) != 3:
                print(f"\n❌ Expected 3 guardian IDs, got {len(self.guardian_ids)}")
                return False

            if not self.auto_mode:
                input("\nPress Enter to continue...")

            # Step 5: Activate vault
            self.print_step(5, "Activate Vault")
            print(f"Activating vault {self.vault_id}...\n")

            result = subprocess.run([
                sys.executable, "cli_admin.py",
                "activate-vault",
                "--vault-id", self.vault_id
            ], capture_output=True, text=True)

            if result.returncode != 0:
                print(f"❌ Failed to activate vault: {result.stderr}")
                return False

            print(result.stdout)
            print("✅ Vault activated")

            if not self.auto_mode:
                input("\nPress Enter to continue...")

            # Step 6: Get first Bitcoin address
            self.print_step(6, "Get Bitcoin Address for Funding")
            btc_address = vault_config['bitcoin']['sample_addresses'][3]
            print(f"Using Bitcoin address: {btc_address}\n")

            # Step 7: Fund address
            self.print_step(7, "Fund Bitcoin Address from Regtest")
            print(f"Funding address with 2.0 BTC from regtest...\n")

            result = subprocess.run([
                sys.executable, "cli_fund_address.py",
                "bitcoin",
                "--address", btc_address,
                "--amount", "2.0"
            ], capture_output=True, text=True)

            if result.returncode != 0:
                print(f"❌ Failed to fund address: {result.stderr}")
                return False

            print(result.stdout)
            print(f"✅ Address {btc_address} funded with 2.0 BTC")

            if not self.auto_mode:
                input("\nPress Enter to continue...")

            # Step 8: Check balance
            self.print_step(8, "Check Balance")
            print(f"Checking balance of {btc_address}...\n")

            result = subprocess.run([
                sys.executable, "cli_fund_address.py",
                "bitcoin",
                "--check-balance",
                "--address", btc_address
            ], capture_output=True, text=True)

            print(result.stdout)

            if not self.auto_mode:
                input("\nPress Enter to continue...")

            # Step 9: Start guardian clients
            self.print_step(9, "Start Guardian Clients")
            print("Starting guardian clients in background...\n")

            share_files = [
                f"{self.demo_dir}/guardian_1_share.json",
                f"{self.demo_dir}/guardian_2_share.json",
                f"{self.demo_dir}/guardian_3_share.json"
            ]

            for i, (gid, share) in enumerate(zip(self.guardian_ids, share_files), 1):
                print(f"Starting Guardian {i} client...")
                proc = subprocess.Popen([
                    sys.executable, "cli_guardian_client.py",
                    "run",
                    "--server", self.server_url,
                    "--share", share,
                    "--guardian-id", gid,
                    "--vault-id", self.vault_id,
                    "--vault-config", vault_config_path
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                self.guardian_processes.append(proc)
                print(f"  ✅ Guardian {i} started (PID: {proc.pid})")

            # Wait for guardians to connect
            print("\nWaiting 3 seconds for guardians to connect...")
            time.sleep(3)

            # Check if guardians are still running
            for i, proc in enumerate(self.guardian_processes, 1):
                if proc.poll() is not None:
                    stdout, stderr = proc.communicate()
                    print(f"❌ Guardian {i} process died:")
                    print(f"   STDOUT: {stdout.decode()[:200]}")
                    print(f"   STDERR: {stderr.decode()[:200]}")
                    self.cleanup_guardians()
                    return False

            print("✅ All guardians connected")

            if not self.auto_mode:
                input("\nPress Enter to continue...")

            # Step 10: Create and broadcast transaction
            self.print_step(10, "Create, Sign, and Broadcast Transaction")

            # Use a legacy P2PKH address for compatibility
            recipient = "n1ZCYg9YXtB5XCZazLxSmPDa8iwJRZHhGx"  # Regtest P2PKH address
            amount = "0.5"
            fee = "0.0001"

            print(f"Creating transaction:")
            print(f"  Recipient: {recipient}")
            print(f"  Amount: {amount} BTC")
            print(f"  Fee: {fee} BTC")
            print(f"  Memo: Demo transaction\n")

            print("This will:")
            print("  1. Find UTXO for sender address")
            print("  2. Create transaction with proper sighash")
            print("  3. Wait for guardians to sign via MPC")
            print("  4. Broadcast to Bitcoin regtest")
            print()

            result = subprocess.run([
                sys.executable, "cli_create_and_broadcast.py",
                "--vault-id", self.vault_id,
                "--vault-config", vault_config_path,
                "--recipient", recipient,
                "--amount", amount,
                "--fee", fee,
                "--address-index", "3",
                "--memo", "Demo transaction"
            ], capture_output=True, text=True)

            print(result.stdout)

            if result.returncode != 0:
                print(f"\n❌ Transaction failed!")
                print(f"Error: {result.stderr}")

                # Run diagnostic
                print("\n" + "="*70)
                print("Running diagnostic...")
                print("="*70 + "\n")

                # Try to extract transaction ID from output
                transaction_id = None
                for line in result.stdout.split('\n'):
                    if 'transaction created:' in line.lower() or 'tx_' in line:
                        parts = line.split()
                        for part in parts:
                            if part.startswith('tx_'):
                                transaction_id = part.strip()
                                break

                if transaction_id:
                    print(f"Found transaction ID: {transaction_id}")
                    print("Running debug script...\n")
                    subprocess.run([
                        sys.executable, "debug_signature.py",
                        "--transaction-id", transaction_id,
                        "--vault-config", vault_config_path
                    ])
                else:
                    print("Could not extract transaction ID for diagnostics")

                self.cleanup_guardians()
                return False

            print("\n✅ Transaction completed successfully!")

            # Extract transaction details
            txid = None
            for line in result.stdout.split('\n'):
                if 'TXID:' in line:
                    parts = line.split(':')
                    if len(parts) > 1:
                        txid = parts[1].strip()
                        break

            # Success summary for Bitcoin
            self.print_header("Bitcoin Demo Completed Successfully!")
            print(f"✅ Vault created: {self.vault_id}")
            print(f"✅ Guardians invited and registered: 3")
            print(f"✅ Bitcoin address funded: {btc_address}")
            print(f"✅ Transaction signed with MPC: {txid or 'completed'}")
            print(f"✅ Transaction broadcast to Bitcoin regtest")
            print()
            print(f"{'='*70}\n")

            # Ethereum demo flow (if requested)
            if self.demo_type == "both":
                if not self.auto_mode:
                    input("Press Enter to start Ethereum demo...")

                eth_success = await self.run_ethereum_demo(vault_config_path)
                if not eth_success:
                    print("\n⚠️  Ethereum demo failed, but Bitcoin demo succeeded")
                    return True  # Still return success if Bitcoin worked

            return True

        except KeyboardInterrupt:
            print("\n\n⚠️  Demo interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Demo failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Cleanup
            print("\nCleaning up guardian clients...")
            self.cleanup_guardians()
            print("✅ Cleanup complete")


async def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="GuardianVault Complete Demo Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script will run a complete end-to-end demo of GuardianVault:
  • Generate threshold key shares
  • Create vaults
  • Invite and register guardians
  • Fund addresses
  • Create, sign, and broadcast transactions

Prerequisites:
  • Coordination server running on http://localhost:8000
  • Bitcoin regtest running on localhost:18443 (for Bitcoin demo)
  • Ethereum Ganache running on localhost:8545 (for Ethereum demo)
  • MongoDB running for coordination server

Examples:
  # Interactive Bitcoin demo (prompts at each step)
  python3 demo_orchestrator.py

  # Automatic Bitcoin demo (no prompts)
  python3 demo_orchestrator.py --auto

  # Ethereum demo
  python3 demo_orchestrator.py --type ethereum

  # Both Bitcoin and Ethereum demos
  python3 demo_orchestrator.py --type both
        """
    )

    parser.add_argument('--auto', action='store_true',
                       help='Run in automatic mode without prompts')
    parser.add_argument('--type', type=str, choices=['bitcoin', 'ethereum', 'both'],
                       default='bitcoin',
                       help='Demo type: bitcoin, ethereum, or both (default: bitcoin)')

    args = parser.parse_args()

    orchestrator = DemoOrchestrator(auto_mode=args.auto, demo_type=args.type)
    success = await orchestrator.run_demo()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
