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

from guardianvault.threshold_mpc_keymanager import (
    ThresholdKeyGeneration,
    ThresholdBIP32,
    ExtendedPublicKey,
    PublicKeyDerivation
)
from guardianvault.threshold_addresses import BitcoinAddressGenerator


class DemoOrchestrator:
    """Orchestrates a complete GuardianVault demo"""

    def __init__(self, auto_mode: bool = False):
        self.demo_dir = "demo_output"
        self.server_url = "http://localhost:8000"
        self.bitcoin_host = "localhost"
        self.bitcoin_port = 18443
        self.auto_mode = auto_mode
        self.guardian_processes = []
        self.vault_id = None
        self.guardian_ids = []

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

        # Check Bitcoin regtest
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

        print("\n✅ All prerequisites met!\n")
        return True

    async def run_demo(self):
        """Run complete demo"""
        self.print_header("GuardianVault Complete Demo")

        print("This demo will demonstrate:")
        print("  1. Generating threshold key shares (3-of-3)")
        print("  2. Creating a Bitcoin vault")
        print("  3. Inviting and registering guardians")
        print("  4. Funding a Bitcoin address from regtest")
        print("  5. Running guardian clients")
        print("  6. Creating and signing a transaction with MPC")
        print("  7. Broadcasting to Bitcoin regtest network")
        print("\nPrerequisites:")
        print("  • Coordination server running on http://localhost:8000")
        print("  • Bitcoin regtest running on localhost:18443")
        print()

        # Check prerequisites
        if not await self.check_prerequisites():
            return False

        if not self.auto_mode:
            input("Press Enter to start the demo...")

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
                sys.executable, "cli_transaction_requester.py",
                "fund-address",
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
                sys.executable, "cli_transaction_requester.py",
                "check-balance",
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

            # Success summary
            self.print_header("Demo Completed Successfully!")
            print(f"✅ Vault created: {self.vault_id}")
            print(f"✅ Guardians invited and registered: 3")
            print(f"✅ Bitcoin address funded: {btc_address}")
            print(f"✅ Transaction signed with MPC: {txid or 'completed'}")
            print(f"✅ Transaction broadcast to Bitcoin regtest")
            print()
            print(f"{'='*70}\n")

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
  • Fund a Bitcoin address
  • Create, sign, and broadcast a transaction

Prerequisites:
  • Coordination server running on http://localhost:8000
  • Bitcoin regtest running on localhost:18443
  • MongoDB running for coordination server

Examples:
  # Interactive mode (prompts at each step)
  python3 demo_orchestrator.py

  # Automatic mode (no prompts)
  python3 demo_orchestrator.py --auto
        """
    )

    parser.add_argument('--auto', action='store_true',
                       help='Run in automatic mode without prompts')

    args = parser.parse_args()

    orchestrator = DemoOrchestrator(auto_mode=args.auto)
    success = await orchestrator.run_demo()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
