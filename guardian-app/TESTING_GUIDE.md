# GuardianVault Desktop App - Testing Guide

## Prerequisites

The desktop app should be running with an Electron window open showing the "Import Guardian Key Share" screen.

If not running, start with:
```bash
cd guardian-app
npm run dev
```

---

## Test 1: Import Key Share (File Upload)

### Steps:

1. **Locate the test file:**
   - File: `guardian-app/test_guardian1_keyshare.json`
   - This contains Guardian #1's Bitcoin key share

2. **Import via File Upload:**
   - Click the file upload button in the app
   - Select `test_guardian1_keyshare.json`
   - The JSON should automatically populate in the textarea

3. **Set Password:**
   - Enter a password (min 8 characters): `testpassword123`
   - Confirm password: `testpassword123`

4. **Import:**
   - Click "Import Key Share"
   - You should see a success message and transition to the Dashboard placeholder

5. **Verify:**
   - The app should show "Key share imported successfully!"
   - The keystore file is saved at: `~/Library/Application Support/guardianvault-app/keystore/guardian_key.enc` (macOS)

---

## Test 2: Import Key Share (Paste JSON)

If you want to test with a fresh start:

1. **Delete the keystore (if exists):**
   ```bash
   rm -rf ~/Library/Application\ Support/guardianvault-app/keystore/
   ```

2. **Restart the app:**
   ```bash
   # Kill the app (Cmd+Q or close window)
   npm run dev
   ```

3. **Paste JSON manually:**
   - Copy the contents of `test_guardian1_keyshare.json`
   - Paste into the "Key Share JSON" textarea
   - Enter password and confirm
   - Click "Import Key Share"

---

## Test 3: Verify Encryption

The key share is encrypted with **two layers**:

### Layer 1: Password-based AES-256-GCM
- Your password (`testpassword123`) is used with PBKDF2 (100,000 iterations)
- Encrypts the key share data

### Layer 2: OS-level encryption
- Electron's `safeStorage` API uses:
  - macOS: Keychain
  - Windows: DPAPI
  - Linux: libsecret/kwallet

### To verify:
```bash
# View the encrypted file (it's binary, so it will look like gibberish)
xxd ~/Library/Application\ Support/guardianvault-app/keystore/guardian_key.enc | head
```

---

## Test 4: Test Incorrect Password (Coming Soon)

Once we implement the unlock screen:
1. Close and restart the app
2. Try entering wrong password
3. Should show "Incorrect password" error
4. Enter correct password
5. Should unlock successfully

---

## Test 5: Test Crypto Operations (Manual CLI Test)

Test the Python crypto bridge directly:

```bash
cd guardian-app

# Test Round 1 (generate nonce)
python3 python/crypto_ops.py round1 \
  --key-share '{"guardian_id":1,"x":"11a8f1eb02a17bbdd67079755758f0a27c3072cd86b412373cfd08f6391e5c4b","total_shares":3,"threshold":3,"master_public_key":"0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798"}' \
  --message-hash "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
```

Expected output:
```json
{
  "R": "<public point>",
  "k_blind": "<blinded nonce>",
  "success": true
}
```

---

## Test 6: Check Application Logs

View Electron logs for debugging:

```bash
# The app logs will appear in the terminal where you ran `npm run dev`
# Look for:
# - keystore:import success/error
# - keystore:get success/error
# - crypto:sign-round1 success/error
```

---

## Current Limitations (MVP)

✅ **Working:**
- Key share import (file upload or paste JSON)
- Dual-layer encryption (password + OS-level)
- Secure keystore storage
- Python crypto operations (Round 1 & 3)
- IPC communication between Electron processes

🚧 **Not Yet Implemented:**
- Unlock screen (password re-entry after restart)
- WebSocket connection to coordination server
- Vault joining with invitation codes
- Transaction signing UI
- Dashboard with real data
- Multiple key share support

---

## Troubleshooting

### App won't start
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Python script errors
```bash
# Ensure guardianvault package is in parent directory
ls -la ../ | grep guardianvault

# Check Python path
which python3

# Test Python import
python3 -c "from guardianvault.threshold_signing import ThresholdSigner; print('OK')"
```

### Keystore errors
```bash
# Delete keystore and start fresh
rm -rf ~/Library/Application\ Support/guardianvault-app/

# Check permissions
ls -la ~/Library/Application\ Support/ | grep guardianvault
```

---

## Next Steps

After testing the key import functionality, we'll implement:

1. **Phase 4:** WebSocket connection to coordination server
2. **Phase 5:** Transaction signing workflow
3. **Phase 6:** End-to-end testing with the full system

---

## File Locations

- **App Code:** `/tmp/GuardianVault/guardian-app/`
- **Test Key Share:** `/tmp/GuardianVault/guardian-app/test_guardian1_keyshare.json`
- **Keystore:** `~/Library/Application Support/guardianvault-app/keystore/`
- **Python Library:** `/tmp/GuardianVault/guardianvault/`
- **Coordination Server:** `/tmp/GuardianVault/coordination-server/`

---

## Support

If you encounter any issues:
1. Check the terminal output for error messages
2. Open DevTools in the Electron app (should be open by default in dev mode)
3. Check the Console tab for JavaScript errors
4. Verify all files are in the correct locations
