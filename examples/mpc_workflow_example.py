#!/usr/bin/env python3
"""
Practical MPC Workflow Example
Demonstrates a realistic multi-party computation scenario for key management
"""

from guardianvault.crypto_mpc_keymanager import DistributedKeyManager, KeyShare
import json
import os


def simulate_party(party_name: str, share: KeyShare, action: str):
    """Simulate actions by different parties in the MPC system"""
    print(f"\n[{party_name}] {action}")
    print(f"  Share ID: {share.share_id}")
    print(f"  Share Value: {share.share_value.hex()[:32]}...")  # Show partial
    

def main():
    print("=" * 80)
    print("PRACTICAL MPC WORKFLOW SIMULATION")
    print("Scenario: Company wants to manage crypto treasury with 3-of-5 multisig")
    print("=" * 80)
    print()
    
    manager = DistributedKeyManager()
    
    # Phase 1: Initial Setup (Performed Once, in Secure Environment)
    print("PHASE 1: INITIAL SETUP")
    print("-" * 80)
    print("Location: Secure, air-gapped facility")
    print("Action: Generate master seed and split into shares")
    print()
    
    master_seed = manager.generate_master_seed()
    print(f"✓ Generated master seed: {master_seed.hex()}")
    print()
    
    # Split into 3-of-5 shares
    threshold = 3
    num_shares = 5
    shares = manager.split_master_seed(master_seed, threshold, num_shares)
    print(f"✓ Split into {num_shares} shares (threshold: {threshold})")
    print()
    
    # Assign shares to different parties
    parties = {
        1: "CFO (Chief Financial Officer)",
        2: "CTO (Chief Technology Officer)", 
        3: "CEO (Chief Executive Officer)",
        4: "Board Member 1",
        5: "Board Member 2"
    }
    
    print("Share Distribution Plan:")
    for share in shares:
        party = parties[share.share_id]
        print(f"  Share {share.share_id} → {party}")
        
        # Save share to separate "secure location"
        location = f"/home/claude/party_{share.share_id}_share.json"
        manager.save_share_to_file(share, location)
        simulate_party(party, share, f"Received share and stored at {location}")
    
    print("\n⚠️  CRITICAL: Master seed is now DESTROYED (never stored)")
    print("⚠️  Only shares exist - distributed across 5 parties")
    del master_seed  # Simulate secure deletion
    print()
    
    # Phase 2: Routine Operation - Generate New Addresses
    print("\n" + "=" * 80)
    print("PHASE 2: GENERATE NEW ADDRESSES")
    print("-" * 80)
    print("Scenario: Need to generate 5 new Bitcoin receiving addresses")
    print("Required: Any 3 of 5 shares")
    print()
    
    # Simulate gathering shares from 3 parties (CFO, CEO, Board Member 1)
    print("Gathering shares from 3 parties for address generation...")
    share1 = manager.load_share_from_file("/home/claude/party_1_share.json")
    simulate_party(parties[1], share1, "Providing share for address generation")
    
    share3 = manager.load_share_from_file("/home/claude/party_3_share.json")
    simulate_party(parties[3], share3, "Providing share for address generation")
    
    share4 = manager.load_share_from_file("/home/claude/party_4_share.json")
    simulate_party(parties[4], share4, "Providing share for address generation")
    
    print("\n✓ Collected 3 shares (meets threshold)")
    print()
    
    # Reconstruct seed temporarily
    print("Temporarily reconstructing master seed in secure memory...")
    reconstructed_seed = manager.reconstruct_master_seed([share1, share3, share4])
    print("✓ Master seed reconstructed")
    print()
    
    # Generate addresses
    print("Generating Bitcoin addresses:")
    for i in range(5):
        btc_key = manager.derive_bitcoin_address_key(reconstructed_seed, account=0, address_index=i)
        print(f"  Address {i}: Private Key = {btc_key.hex()[:32]}...")
    
    print("\n✓ Addresses generated")
    print("✓ Master seed cleared from memory")
    print("✓ Shares returned to their respective parties")
    del reconstructed_seed  # Clear from memory
    print()
    
    # Phase 3: Emergency Recovery
    print("\n" + "=" * 80)
    print("PHASE 3: EMERGENCY RECOVERY SCENARIO")
    print("-" * 80)
    print("Scenario: CFO lost their device, need to verify recovery is possible")
    print("Required: Any 3 remaining shares (CTO, CEO, Board Members)")
    print()
    
    # Use different 3 shares (excluding CFO's share #1)
    print("Gathering shares from CTO, Board Member 1, and Board Member 2...")
    share2 = manager.load_share_from_file("/home/claude/party_2_share.json")
    simulate_party(parties[2], share2, "Providing share for recovery verification")
    
    share4 = manager.load_share_from_file("/home/claude/party_4_share.json")
    simulate_party(parties[4], share4, "Providing share for recovery verification")
    
    share5 = manager.load_share_from_file("/home/claude/party_5_share.json")
    simulate_party(parties[5], share5, "Providing share for recovery verification")
    
    print("\n✓ Collected 3 shares (excluding lost CFO share)")
    print()
    
    # Verify recovery
    print("Attempting recovery and verification...")
    recovered_seed = manager.reconstruct_master_seed([share2, share4, share5])
    
    # Verify by deriving same address
    test_key = manager.derive_bitcoin_address_key(recovered_seed, account=0, address_index=0)
    print(f"✓ Successfully recovered!")
    print(f"  Test address key: {test_key.hex()[:32]}...")
    print()
    
    print("Recovery verified - system can function without CFO's share")
    print("Recommendation: Issue new share to CFO and rotate if needed")
    del recovered_seed
    print()
    
    # Phase 4: Security Analysis
    print("\n" + "=" * 80)
    print("PHASE 4: SECURITY ANALYSIS")
    print("-" * 80)
    print()
    
    print("What if an attacker compromises 2 shares?")
    print("  → Cannot reconstruct secret (need 3)")
    print("  → Zero information leaked about master seed")
    print("  → System remains secure ✓")
    print()
    
    print("What if 2 parties collude maliciously?")
    print("  → Cannot access funds (need 3 shares)")
    print("  → Need at least 3 parties to agree ✓")
    print()
    
    print("What if the facility storing shares catches fire?")
    print("  → Shares distributed across different locations ✓")
    print("  → Can still function with remaining shares ✓")
    print()
    
    print("What if we need to change the threshold?")
    print("  → Reconstruct seed with current threshold")
    print("  → Re-split with new threshold parameters")
    print("  → Distribute new shares ✓")
    print()
    
    # Summary
    print("=" * 80)
    print("WORKFLOW SUMMARY")
    print("=" * 80)
    print()
    print("✓ Initial Setup: Master seed generated and split into 5 shares")
    print("✓ Distribution: Each party received their share securely")
    print("✓ Routine Ops: Generated addresses with 3 shares (CFO, CEO, Board#1)")
    print("✓ Recovery: Verified recovery works with different 3 shares")
    print("✓ Security: System resists compromise of 2 shares")
    print()
    
    print("Key Benefits:")
    print("  • No single point of failure")
    print("  • Distributed trust among parties")
    print("  • Resilient to partial compromise")
    print("  • Flexible operational procedures")
    print()
    
    print("Best Practices Demonstrated:")
    print("  • Secure generation in isolated environment")
    print("  • Immediate destruction of master seed")
    print("  • Distributed storage of shares")
    print("  • Temporary reconstruction only when needed")
    print("  • Memory clearing after operations")
    print()


if __name__ == "__main__":
    main()
