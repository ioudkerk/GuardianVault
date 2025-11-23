#!/usr/bin/env python3
"""
CLI 3: Admin CLI
Administrative interface for creating vaults, inviting guardians, and managing the system
"""
import sys
import os
import json
import argparse
import asyncio
import aiohttp
from typing import Dict, List
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class AdminCLI:
    """Admin CLI for vault and guardian management"""

    def __init__(self, server_url: str):
        self.server_url = server_url
        self.base_api_url = f"{server_url}/api"

    async def create_vault(self, config_file: str):
        """Create a vault from configuration file"""
        print(f"\n{'='*60}")
        print(f"Creating Vault")
        print(f"{'='*60}")

        # Load configuration
        with open(config_file, 'r') as f:
            config = json.load(f)

        print(f"Vault Name: {config['vault_name']}")
        print(f"Total Guardians: {config['total_guardians']}")
        print(f"Threshold: {config['threshold']}")
        print(f"{'='*60}\n")

        # Create vault for Bitcoin
        print("Creating Bitcoin vault...")
        btc_vault_data = {
            "name": f"{config['vault_name']} - Bitcoin",
            "coin_type": "bitcoin",
            "threshold": config['threshold'],
            "total_guardians": config['total_guardians'],
            "account_index": config['bitcoin']['account'],
            "xpub": config['bitcoin']['xpub'],
            "xpub_chain_code": config['master_chain_code']
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.base_api_url}/vaults",
                    json=btc_vault_data
                ) as response:
                    if response.status in [200, 201]:
                        btc_result = await response.json()
                        print(f"✅ Bitcoin vault created!")
                        print(f"  Vault ID: {btc_result['vault_id']}")
                        print(f"  Status: {btc_result['status']}")
                        print(f"  Sample addresses:")
                        for addr in config['bitcoin']['sample_addresses'][:3]:
                            print(f"    • {addr}")
                    else:
                        error = await response.text()
                        print(f"❌ Failed to create Bitcoin vault: {error}")
                        return None
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                return None

        # Create vault for Ethereum
        print("\nCreating Ethereum vault...")
        eth_vault_data = {
            "name": f"{config['vault_name']} - Ethereum",
            "coin_type": "ethereum",
            "threshold": config['threshold'],
            "total_guardians": config['total_guardians'],
            "account_index": config['ethereum']['account'],
            "xpub": config['ethereum']['xpub'],
            "xpub_chain_code": config['master_chain_code']
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.base_api_url}/vaults",
                    json=eth_vault_data
                ) as response:
                    if response.status in [200, 201]:
                        eth_result = await response.json()
                        print(f"✅ Ethereum vault created!")
                        print(f"  Vault ID: {eth_result['vault_id']}")
                        print(f"  Status: {eth_result['status']}")
                        print(f"  Sample addresses:")
                        for addr in config['ethereum']['sample_addresses'][:3]:
                            print(f"    • {addr}")
                    else:
                        error = await response.text()
                        print(f"❌ Failed to create Ethereum vault: {error}")
                        return None
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                return None

        print(f"\n{'='*60}")
        print("Next Steps:")
        print(f"{'='*60}")
        print("1. Invite guardians using:")
        print(f"   python3 cli_admin.py invite-guardian --vault-id {btc_result['vault_id']} \\")
        print(f"       --name 'Alice' --email 'alice@company.com' --role 'CFO'")
        print("\n2. Guardians register with invitation codes")
        print("3. Activate vaults when all guardians joined")
        print(f"{'='*60}\n")

        return {"bitcoin": btc_result, "ethereum": eth_result}

    async def list_vaults(self):
        """List all vaults"""
        print(f"\n{'='*60}")
        print(f"Vaults")
        print(f"{'='*60}\n")

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.base_api_url}/vaults") as response:
                    if response.status == 200:
                        vaults = await response.json()
                        if not vaults:
                            print("No vaults found.")
                            return

                        for vault in vaults:
                            print(f"Vault: {vault['name']}")
                            print(f"  ID: {vault['vault_id']}")
                            print(f"  Coin Type: {vault['coin_type']}")
                            print(f"  Status: {vault['status']}")
                            print(f"  Guardians: {vault['guardians_joined']}/{vault['total_guardians']}")
                            print(f"  Threshold: {vault['threshold']}")
                            print(f"  Transactions: {vault.get('total_transactions', 0)}")
                            print()
                    else:
                        error = await response.text()
                        print(f"❌ Failed to list vaults: {error}")
            except Exception as e:
                print(f"❌ Error: {str(e)}")

    async def get_vault(self, vault_id: str):
        """Get vault details"""
        print(f"\n{'='*60}")
        print(f"Vault Details")
        print(f"{'='*60}\n")

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.base_api_url}/vaults/{vault_id}") as response:
                    if response.status == 200:
                        vault = await response.json()
                        print(f"Name: {vault['name']}")
                        print(f"ID: {vault['vault_id']}")
                        print(f"Coin Type: {vault['coin_type']}")
                        print(f"Status: {vault['status']}")
                        print(f"Guardians Joined: {vault['guardians_joined']}/{vault['total_guardians']}")
                        print(f"Threshold: {vault['threshold']}")
                        print(f"Account Index: {vault['account_index']}")
                        print(f"Total Transactions: {vault.get('total_transactions', 0)}")
                        print(f"Addresses Generated: {vault.get('total_addresses_generated', 0)}")
                        print(f"Created: {vault['created_at']}")

                        if vault.get('guardian_ids'):
                            print(f"\nGuardians:")
                            for gid in vault['guardian_ids']:
                                print(f"  • {gid}")
                    else:
                        error = await response.text()
                        print(f"❌ Failed to get vault: {error}")
            except Exception as e:
                print(f"❌ Error: {str(e)}")

    async def invite_guardian(self, vault_id: str, name: str, email: str, role: str):
        """Invite a guardian to a vault"""
        print(f"\n{'='*60}")
        print(f"Inviting Guardian")
        print(f"{'='*60}")
        print(f"Vault ID: {vault_id}")
        print(f"Name: {name}")
        print(f"Email: {email}")
        print(f"Role: {role}")
        print(f"{'='*60}\n")

        invite_data = {
            "vault_id": vault_id,
            "name": name,
            "email": email,
            "role": role
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.base_api_url}/guardians/invite",
                    json=invite_data
                ) as response:
                    if response.status in [200, 201]:
                        result = await response.json()
                        print(f"✅ Guardian invited successfully!")
                        print(f"\nInvitation Details:")
                        print(f"  Guardian ID: {result['guardian_id']}")
                        print(f"  Invitation Code: {result['invitation_code']}")
                        print(f"  Status: {result['status']}")
                        print(f"\n{'='*60}")
                        print("Share this invitation code with the guardian:")
                        print(f"  {result['invitation_code']}")
                        print(f"{'='*60}")
                        print("\nGuardian can register using:")
                        print(f"  python3 cli_guardian_client.py register \\")
                        print(f"      --server {self.server_url} \\")
                        print(f"      --code {result['invitation_code']}")
                        print(f"{'='*60}\n")
                        return result
                    else:
                        error = await response.text()
                        print(f"❌ Failed to invite guardian: {error}")
                        return None
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                return None

    async def list_guardians(self, vault_id: str = None):
        """List guardians"""
        print(f"\n{'='*60}")
        print(f"Guardians")
        print(f"{'='*60}\n")

        url = f"{self.base_api_url}/guardians"
        if vault_id:
            url += f"?vault_id={vault_id}"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        guardians = await response.json()
                        if not guardians:
                            print("No guardians found.")
                            return

                        for guardian in guardians:
                            print(f"Guardian: {guardian['name']}")
                            print(f"  ID: {guardian['guardian_id']}")
                            print(f"  Email: {guardian.get('email', 'N/A')}")
                            print(f"  Role: {guardian.get('role', 'N/A')}")
                            print(f"  Status: {guardian['status']}")
                            print(f"  Vault ID: {guardian['vault_id']}")
                            if guardian.get('invitation_code') and guardian['status'] == 'invited':
                                print(f"  Invitation Code: {guardian['invitation_code']}")
                            print()
                    else:
                        error = await response.text()
                        print(f"❌ Failed to list guardians: {error}")
            except Exception as e:
                print(f"❌ Error: {str(e)}")

    async def activate_vault(self, vault_id: str):
        """Activate a vault"""
        print(f"\n{'='*60}")
        print(f"Activating Vault")
        print(f"{'='*60}")
        print(f"Vault ID: {vault_id}")
        print(f"{'='*60}\n")

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.base_api_url}/vaults/{vault_id}/activate"
                ) as response:
                    if response.status in [200, 201]:
                        result = await response.json()
                        print(f"✅ Vault activated successfully!")
                        print(f"  Status: {result['status']}")
                        print(f"  Guardians: {result['guardians_joined']}/{result['total_guardians']}")
                        return result
                    else:
                        error = await response.text()
                        print(f"❌ Failed to activate vault: {error}")
                        return None
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                return None

    async def vault_stats(self, vault_id: str):
        """Get vault statistics"""
        print(f"\n{'='*60}")
        print(f"Vault Statistics")
        print(f"{'='*60}\n")

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.base_api_url}/vaults/{vault_id}/stats"
                ) as response:
                    if response.status == 200:
                        stats = await response.json()
                        print(f"Vault: {stats['vault_name']}")
                        print(f"Status: {stats['status']}")
                        print(f"\nTransactions:")
                        print(f"  Total: {stats['transactions']['total']}")
                        print(f"  Pending: {stats['transactions']['pending']}")
                        print(f"  Completed: {stats['transactions']['completed']}")
                        print(f"  Failed: {stats['transactions']['failed']}")
                        print(f"\nGuardians:")
                        print(f"  Total: {stats['guardians']['total']}")
                        print(f"  Active: {stats['guardians']['active']}")
                    else:
                        error = await response.text()
                        print(f"❌ Failed to get stats: {error}")
            except Exception as e:
                print(f"❌ Error: {str(e)}")


async def main():
    parser = argparse.ArgumentParser(
        description="Admin CLI for GuardianVault coordination server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create vaults from configuration
  python3 cli_admin.py create-vault --config demo_shares/vault_config.json

  # List all vaults
  python3 cli_admin.py list-vaults

  # Get vault details
  python3 cli_admin.py get-vault --vault-id vault_abc123

  # Invite a guardian
  python3 cli_admin.py invite-guardian --vault-id vault_abc123 \\
      --name "Alice" --email "alice@company.com" --role "CFO"

  # List guardians
  python3 cli_admin.py list-guardians --vault-id vault_abc123

  # Activate vault
  python3 cli_admin.py activate-vault --vault-id vault_abc123

  # Get vault statistics
  python3 cli_admin.py vault-stats --vault-id vault_abc123
        """
    )

    parser.add_argument('--server', '-s', type=str, default='http://localhost:8000',
                       help='Coordination server URL')

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Create vault
    create_parser = subparsers.add_parser('create-vault', help='Create vault from config')
    create_parser.add_argument('--config', '-c', type=str, required=True,
                              help='Path to vault configuration file')

    # List vaults
    subparsers.add_parser('list-vaults', help='List all vaults')

    # Get vault
    get_vault_parser = subparsers.add_parser('get-vault', help='Get vault details')
    get_vault_parser.add_argument('--vault-id', '-v', type=str, required=True,
                                 help='Vault ID')

    # Invite guardian
    invite_parser = subparsers.add_parser('invite-guardian', help='Invite a guardian')
    invite_parser.add_argument('--vault-id', '-v', type=str, required=True,
                              help='Vault ID')
    invite_parser.add_argument('--name', '-n', type=str, required=True,
                              help='Guardian name')
    invite_parser.add_argument('--email', '-e', type=str, required=True,
                              help='Guardian email')
    invite_parser.add_argument('--role', '-r', type=str, default='Guardian',
                              help='Guardian role')

    # List guardians
    list_guardians_parser = subparsers.add_parser('list-guardians', help='List guardians')
    list_guardians_parser.add_argument('--vault-id', '-v', type=str,
                                      help='Filter by vault ID')

    # Activate vault
    activate_parser = subparsers.add_parser('activate-vault', help='Activate a vault')
    activate_parser.add_argument('--vault-id', '-v', type=str, required=True,
                                help='Vault ID')

    # Vault stats
    stats_parser = subparsers.add_parser('vault-stats', help='Get vault statistics')
    stats_parser.add_argument('--vault-id', '-v', type=str, required=True,
                             help='Vault ID')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    admin = AdminCLI(args.server)

    try:
        if args.command == 'create-vault':
            await admin.create_vault(args.config)
        elif args.command == 'list-vaults':
            await admin.list_vaults()
        elif args.command == 'get-vault':
            await admin.get_vault(args.vault_id)
        elif args.command == 'invite-guardian':
            await admin.invite_guardian(args.vault_id, args.name, args.email, args.role)
        elif args.command == 'list-guardians':
            await admin.list_guardians(args.vault_id)
        elif args.command == 'activate-vault':
            await admin.activate_vault(args.vault_id)
        elif args.command == 'vault-stats':
            await admin.vault_stats(args.vault_id)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
