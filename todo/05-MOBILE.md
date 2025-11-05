# Mobile Guardian Application

**Priority**: LOW
**Estimated Time**: 3-4 weeks
**Status**: Not Started

## Overview

A mobile application (iOS and Android) that provides guardians with on-the-go access to approve and sign transactions. This is an alternative/supplement to the Desktop App, not a replacement.

## Why Mobile?

**Advantages:**
- Guardians can approve transactions anywhere
- Push notifications for signing requests
- Biometric authentication (Face ID, Touch ID)
- Always with you (phone vs laptop)

**Considerations:**
- Less secure than desktop (mobile malware)
- Smaller screen for transaction review
- Key storage in mobile keychain
- Battery/connectivity concerns

## Architecture

```
Mobile Guardian App (React Native)
├── Authentication (Biometric + PIN)
├── Key Share Storage (Secure Enclave/Keychain)
├── WebSocket Client
├── Transaction Approval UI
├── Push Notifications
└── Offline Support (Limited)
```

## Tasks

### Phase 1: Project Setup (Days 1-3)

- [ ] **1.1 Initialize React Native Project**
  - [ ] Create `guardian-mobile/` directory
  - [ ] Set up React Native with TypeScript
  - [ ] Configure for iOS and Android
  - [ ] Add navigation (React Navigation)
  - [ ] Set up state management (Zustand)

- [ ] **1.2 Development Environment**
  - [ ] Xcode setup (iOS)
  - [ ] Android Studio setup
  - [ ] Device simulators/emulators
  - [ ] Hot reload configuration

- [ ] **1.3 Dependencies**
  - [ ] React Native Keychain (secure storage)
  - [ ] React Native Biometrics
  - [ ] Socket.IO client
  - [ ] Crypto libraries
  - [ ] Push notification service
  - [ ] UI component library

### Phase 2: Authentication & Security (Days 4-7)

- [ ] **2.1 Onboarding Flow**
  - [ ] Welcome screens
  - [ ] Invitation code entry
  - [ ] Key share import
  - [ ] Set up PIN/password
  - [ ] Enable biometric auth

- [ ] **2.2 Biometric Authentication**
  - [ ] Face ID (iOS)
  - [ ] Touch ID (iOS)
  - [ ] Fingerprint (Android)
  - [ ] Fallback to PIN
  - [ ] Auto-lock after inactivity

- [ ] **2.3 Secure Key Storage**
  - [ ] Use React Native Keychain
  - [ ] Store encrypted key share
  - [ ] Biometric-protected access
  - [ ] Key share export (encrypted backup)
  - [ ] Wipe data on too many failed attempts

### Phase 3: Core Functionality (Days 8-14)

- [ ] **3.1 WebSocket Connection**
  - [ ] Connect to coordination server
  - [ ] Authentication with JWT
  - [ ] Auto-reconnect on network changes
  - [ ] Handle background/foreground transitions

- [ ] **3.2 Vault Dashboard**
  - [ ] Display vault info
  - [ ] Show balance
  - [ ] List guardians
  - [ ] Connection status
  - [ ] Recent transactions

- [ ] **3.3 Transaction List**
  - [ ] Pending transactions
  - [ ] Transaction history
  - [ ] Filter and search
  - [ ] Pull to refresh
  - [ ] Infinite scroll

- [ ] **3.4 Transaction Detail & Approval**
  - [ ] Display transaction details
    - [ ] Recipient address
    - [ ] Amount and fee
    - [ ] Memo
    - [ ] Risk indicators
  - [ ] Approve button
  - [ ] Reject button
  - [ ] Biometric confirmation
  - [ ] Signing progress

- [ ] **3.5 Threshold Signing**
  - [ ] Round 1: Generate nonce
  - [ ] Round 3: Compute signature share
  - [ ] Display signing progress
  - [ ] Handle errors
  - [ ] Success confirmation

### Phase 4: Push Notifications (Days 15-17)

- [ ] **4.1 Push Notification Setup**
  - [ ] Firebase Cloud Messaging (FCM)
  - [ ] Apple Push Notification Service (APNS)
  - [ ] Register device token
  - [ ] Store token on server

- [ ] **4.2 Notification Types**
  - [ ] New transaction requires approval
  - [ ] Round 2 ready (begin signing)
  - [ ] Transaction completed
  - [ ] Transaction failed
  - [ ] Another guardian signed
  - [ ] Vault status change

- [ ] **4.3 Notification Handling**
  - [ ] Tap to open transaction
  - [ ] Deep linking
  - [ ] Badge count
  - [ ] Sound and vibration
  - [ ] Notification settings (per type)

### Phase 5: Offline Support (Days 18-19)

- [ ] **5.1 Local Data Caching**
  - [ ] Cache vault data
  - [ ] Cache transaction history
  - [ ] Cache guardian info
  - [ ] Sync on reconnect

- [ ] **5.2 Queue Pending Actions**
  - [ ] Queue approval decisions
  - [ ] Sync when online
  - [ ] Conflict resolution

- [ ] **5.3 Offline UI**
  - [ ] Show offline indicator
  - [ ] Disable actions requiring network
  - [ ] Show cached data
  - [ ] Retry failed requests

### Phase 6: UI/UX (Days 20-23)

- [ ] **6.1 Design System**
  - [ ] Color scheme
  - [ ] Typography
  - [ ] Button styles
  - [ ] Card components
  - [ ] Icons

- [ ] **6.2 Screens**
  - [ ] Splash screen
  - [ ] Login screen
  - [ ] Dashboard
  - [ ] Transaction list
  - [ ] Transaction detail
  - [ ] Settings
  - [ ] Profile
  - [ ] Help/Support

- [ ] **6.3 Animations**
  - [ ] Screen transitions
  - [ ] Loading spinners
  - [ ] Success checkmarks
  - [ ] Error shake
  - [ ] Signature progress

- [ ] **6.4 Accessibility**
  - [ ] Screen reader support
  - [ ] High contrast mode
  - [ ] Font scaling
  - [ ] Haptic feedback

### Phase 7: Settings & Profile (Days 24-25)

- [ ] **7.1 App Settings**
  - [ ] Server URL
  - [ ] Notification preferences
  - [ ] Biometric settings
  - [ ] Auto-lock timeout
  - [ ] Language (i18n)

- [ ] **7.2 Security Settings**
  - [ ] Change PIN
  - [ ] Enable/disable biometric
  - [ ] Export key share backup
  - [ ] View security log
  - [ ] Wipe data

- [ ] **7.3 Profile**
  - [ ] Guardian name and info
  - [ ] Associated vaults
  - [ ] Signing statistics
  - [ ] About app
  - [ ] Version info

### Phase 8: Testing & Deployment (Days 26-28)

- [ ] **8.1 Testing**
  - [ ] Unit tests
  - [ ] Integration tests
  - [ ] E2E tests with Detox
  - [ ] Manual testing on real devices
  - [ ] TestFlight beta (iOS)
  - [ ] Google Play Internal Testing (Android)

- [ ] **8.2 App Store Preparation**
  - [ ] App icons (all sizes)
  - [ ] Screenshots (all sizes)
  - [ ] App description
  - [ ] Privacy policy
  - [ ] Terms of service
  - [ ] App Store listing

- [ ] **8.3 Deployment**
  - [ ] iOS build and signing
  - [ ] Android build and signing
  - [ ] Submit to Apple App Store
  - [ ] Submit to Google Play Store
  - [ ] Beta testing program
  - [ ] Production release

## Technology Stack

**Framework:**
- React Native with TypeScript
- React Navigation for routing
- Zustand for state management

**Security:**
- React Native Keychain
- React Native Biometrics
- Crypto libraries (crypto-browserify)

**Networking:**
- Socket.IO client
- Axios for REST API

**Push Notifications:**
- React Native Firebase (FCM)
- React Native Push Notification (APNS)

**UI:**
- React Native Paper or NativeBase
- React Native Vector Icons
- Reanimated for animations

## Platform-Specific Considerations

### iOS
- [ ] Keychain for secure storage
- [ ] Face ID / Touch ID integration
- [ ] App Transport Security (ATS)
- [ ] Background app refresh limits
- [ ] TestFlight for beta testing

### Android
- [ ] Android Keystore
- [ ] Fingerprint authentication
- [ ] ProGuard for code obfuscation
- [ ] Background service restrictions
- [ ] Google Play Internal Testing

## Security Considerations

1. **Key Storage**
   - Use platform secure storage (Keychain/Keystore)
   - Encrypt key share
   - Biometric-protected access
   - No key share in app logs

2. **Communication**
   - TLS/WSS only
   - Certificate pinning
   - No sensitive data in notifications
   - Validate all server responses

3. **App Security**
   - Obfuscate code
   - Detect jailbreak/root
   - Screen capture prevention (on sensitive screens)
   - Wipe data on multiple failed auth

4. **Permissions**
   - Request only necessary permissions
   - Explain why each permission is needed
   - Handle permission denials gracefully

## Differences from Desktop App

### Mobile Has:
- ✅ Push notifications
- ✅ Biometric auth (Face ID, fingerprint)
- ✅ Always with you
- ✅ Camera for QR codes

### Mobile Lacks:
- ❌ Larger screen for review
- ❌ More secure environment
- ❌ Hardware security modules
- ❌ Better for serious operations

### Recommended Usage:
- **Desktop**: Primary device for important transactions
- **Mobile**: Quick approvals for routine transactions
- **Both**: Use both for maximum flexibility

## Success Criteria

- [ ] Guardian can install and set up app
- [ ] Can import key share securely
- [ ] Biometric authentication works
- [ ] Can connect to coordination server
- [ ] Can view and approve transactions
- [ ] Push notifications arrive on time
- [ ] Threshold signing works correctly
- [ ] App works offline (limited)
- [ ] Passes security review
- [ ] Available on both app stores

## Dependencies on Other Tasks

- **01-GUARDIAN-APP.md**: Mobile should have feature parity with desktop
- **02-SECURITY.md**: Needs JWT authentication
- **Coordination Server**: Push notification endpoint needed

## Future Enhancements

- [ ] QR code scanning for recipient addresses
- [ ] Multiple vault support
- [ ] Transaction templates
- [ ] Apple Watch/Android Wear app
- [ ] Hardware wallet integration (Ledger, Trezor)

## Resources

- [React Native Documentation](https://reactnative.dev/)
- [React Native Keychain](https://github.com/oblador/react-native-keychain)
- [React Native Biometrics](https://github.com/SelfLender/react-native-biometrics)
- [Firebase Cloud Messaging](https://firebase.google.com/docs/cloud-messaging)
- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)
- [Material Design Guidelines](https://material.io/design)
