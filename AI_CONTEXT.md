# AI Context - GuardianVault Project

This file provides quick context for AI assistants (like Claude) working on this project.

## Project Type
Threshold MPC cryptocurrency wallet using additive secret sharing for Bitcoin and Ethereum.

## Key Architecture Decisions

### ⚠️ CRITICAL: Share Storage Level
**Shares are stored at ACCOUNT LEVEL (m/44'/coin'/0'), NOT master level (m)**

This is because:
1. Hardened BIP32 derivation requires all parties together (uses private key in HMAC)
2. Each guardian computing `HMAC(chain, their_share || index)` produces different tweaks
3. Sum would be `parent + (tweak₁ + tweak₂ + tweak₃)` instead of `parent + single_tweak`
4. Result: Invalid signatures ❌

**Solution**: Pre-compute hardened paths during setup, save account shares, guardians only do non-hardened derivation.

### Non-Hardened Derivation Formula
```python
# Each guardian MUST use tweak/n (not full tweak)
tweak = HMAC(chain_code, PUBLIC_KEY || index)  # Same for all
tweak_share = (tweak * pow(n, -1, SECP256K1_N)) % SECP256K1_N
child_share = (parent_share + tweak_share) % SECP256K1_N
```

This ensures: `sum(child_shares) = parent_key + tweak` ✅

## Current Status

**Branch**: `feat/fix-mpc-signature-and-address-generation`

**Recent Work** (2025-11-18):
1. ✅ Fixed MPC signature verification (critical bug)
2. ✅ Added address generation CLI
3. ✅ Complete demo system
4. ✅ Comprehensive documentation

**All Systems Working**:
- ✅ Share generation
- ✅ Key derivation
- ✅ MPC signing
- ✅ Signature verification
- ✅ Address generation
- ✅ Bitcoin transaction broadcasting

## File Structure Quick Reference

```
Key Files to Understand:
├── guardianvault/threshold_mpc_keymanager.py  # Core crypto (be careful!)
├── guardianvault/threshold_signing.py         # Signing protocol
├── practical_demo/cli_share_generator.py      # Account share generation
├── practical_demo/cli_guardian_client.py      # Guardian implementation
└── practical_demo/cli_generate_address.py     # Address generation

Documentation:
├── DEVELOPMENT.md                             # Full development guide (read this!)
├── practical_demo/SIGNATURE_FIX.md            # Technical details of bug fix
├── practical_demo/QUICK_START.md              # User guide
└── practical_demo/ADDRESS_GENERATION.md       # Address generation guide
```

## Common Tasks

### Running Tests
```bash
cd practical_demo
python3 verify_account_shares.py -c demo_output/vault_config.json --shares demo_output/guardian_*_share.json
python3 verify_key_derivation.py -c demo_output/vault_config.json --shares demo_output/guardian_*_share.json
python3 test_signature_flow.py -c demo_output/vault_config.json --shares demo_output/guardian_*_share.json
```

### Regenerating Shares
```bash
cd practical_demo
rm -rf demo_output
python3 cli_share_generator.py -g 3 -t 3 -v "Test" -o demo_output
```

### Starting Services
```bash
# Terminal 1: Bitcoin regtest
cd bitcoin-regtest-box && ./start.sh

# Terminal 2: Coordination server
cd coordination-server && ./run_server.sh

# Terminal 3: Demo
cd practical_demo && python3 demo_orchestrator.py auto
```

## Important Formulas

### Signature Share (Round 3)
```
s_i = k^(-1) * (z/n + r*x_i) mod n
Where: k=sum(nonces), z=msg_hash, r=R.x, x_i=key_share, n=num_parties
```

### Non-Hardened Child
```
tweak = HMAC-SHA512(parent_chain, parent_pubkey || index)
child_share_i = parent_share_i + (tweak / num_parties) mod SECP256K1_N
```

## Share File Format

**Current (v0.2.0+)**:
```json
{
  "bitcoin_account_share": {...},    // At m/44'/0'/0'
  "ethereum_account_share": {...},   // At m/44'/60'/0'
  "metadata": {"share_level": "account"}
}
```

**Legacy (BROKEN)**:
```json
{"share": {...}}  // Master level - causes signature failure!
```

## What NOT to Do

1. ❌ Don't modify hardened derivation without extensive testing
2. ❌ Don't change signature computation formula
3. ❌ Don't save master-level shares
4. ❌ Don't use full tweak in non-hardened derivation (must use tweak/n)
5. ❌ Don't commit demo_output/ or any shares to git

## What's Safe to Do

1. ✅ Add new CLI tools (copy existing patterns)
2. ✅ Modify API endpoints in coordination-server
3. ✅ Improve error messages and logging
4. ✅ Add new documentation
5. ✅ Enhance demo orchestrator

## Quick Debugging

### Signature Fails?
1. Check: Are shares at account level? `cat demo_output/guardian_1_share.json | grep bitcoin_account_share`
2. Run: `python3 verify_key_derivation.py ...`
3. Check: Is non-hardened derivation using tweak/n?

### Guardians Can't Connect?
1. Server running? `curl http://localhost:8000/health`
2. Check logs in coordination-server terminal
3. Verify guardian registered: `curl http://localhost:8000/api/guardians/<id>`

### Address Generation Fails?
1. Vault config exists? `ls demo_output/vault_config.json`
2. Has xpub? `cat demo_output/vault_config.json | grep xpub`
3. Regenerate: `python3 cli_share_generator.py ...`

## Testing Checklist

Before committing changes:
- [ ] All verification scripts pass
- [ ] Signature test passes
- [ ] Address generation works
- [ ] Demo orchestrator completes
- [ ] Documentation updated

## Mathematical Validation

If modifying crypto code, verify:
1. Shares sum to correct key: `sum(shares_i) = private_key`
2. Signature valid: `verify(pubkey, msg_hash, (r, s)) = true`
3. R point correct: `R = k*G where k = sum(nonce_shares)`
4. Non-hardened: `child = parent + tweak` not `parent + n*tweak`

## Git Workflow

```bash
# Always work on feature branches
git checkout -b feat/your-feature
# Make changes, commit with good messages
git commit -m "feat: Description"
# Push and create PR
git push -u origin feat/your-feature
```

## Communication Style

When working with user:
- Be direct and technical
- Show code/math when relevant
- Explain "why" not just "what"
- Acknowledge critical issues immediately
- Provide verification steps

## Resources

- **Full Guide**: `/DEVELOPMENT.md`
- **User Docs**: `/practical_demo/QUICK_START.md`
- **Signature Fix**: `/practical_demo/SIGNATURE_FIX.md`
- **Address Gen**: `/practical_demo/ADDRESS_GENERATION.md`

---

**Status**: All systems operational ✅
**Next**: Ready for new features or fixes
**Contact**: Ivan Oudkerk (ioudkerk@gmail.com)
