import { safeStorage, app } from 'electron'
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs'
import { join } from 'path'
import { createHash, pbkdf2Sync, randomBytes, createCipheriv, createDecipheriv } from 'crypto'

interface KeyShareData {
  guardian_id: number
  x: string
  total_shares: number
  threshold: number
  master_public_key: string
}

interface EncryptedKeyStore {
  encrypted_data: string
  salt: string
  iv: string
  version: number
}

export class KeyStore {
  private keystorePath: string

  constructor() {
    const userDataPath = app.getPath('userData')
    const keystoreDir = join(userDataPath, 'keystore')

    // Ensure keystore directory exists
    if (!existsSync(keystoreDir)) {
      mkdirSync(keystoreDir, { recursive: true })
    }

    this.keystorePath = join(keystoreDir, 'guardian_key.enc')
  }

  /**
   * Check if a keystore file exists
   */
  exists(): boolean {
    return existsSync(this.keystorePath)
  }

  /**
   * Import and encrypt a key share
   * @param keyShareData The key share data (JSON string or object)
   * @param password User's password for additional encryption layer
   */
  async import(keyShareData: string | KeyShareData, password: string): Promise<boolean> {
    try {
      // Parse key share data if it's a string
      const keyShare: KeyShareData = typeof keyShareData === 'string'
        ? JSON.parse(keyShareData)
        : keyShareData

      // Validate key share structure
      if (!this.validateKeyShare(keyShare)) {
        throw new Error('Invalid key share format')
      }

      // Serialize key share
      const keyShareJson = JSON.stringify(keyShare)

      // Generate salt and IV
      const salt = randomBytes(32)
      const iv = randomBytes(16)

      // Derive encryption key from password using PBKDF2
      const derivedKey = pbkdf2Sync(password, salt, 100000, 32, 'sha256')

      // Encrypt key share with AES-256-GCM
      const cipher = createCipheriv('aes-256-gcm', derivedKey, iv)
      let encrypted = cipher.update(keyShareJson, 'utf8', 'hex')
      encrypted += cipher.final('hex')
      const authTag = cipher.getAuthTag().toString('hex')

      // Combine encrypted data with auth tag
      const encryptedWithTag = encrypted + authTag

      // Create encrypted keystore object
      const encryptedKeyStore: EncryptedKeyStore = {
        encrypted_data: encryptedWithTag,
        salt: salt.toString('hex'),
        iv: iv.toString('hex'),
        version: 1
      }

      // Serialize and encrypt with Electron's safeStorage (OS-level encryption)
      const keystoreJson = JSON.stringify(encryptedKeyStore)
      const osEncrypted = safeStorage.encryptString(keystoreJson)

      // Write to file
      writeFileSync(this.keystorePath, osEncrypted)

      return true
    } catch (error) {
      console.error('Failed to import key share:', error)
      throw new Error(`Failed to import key share: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Retrieve and decrypt the key share
   * @param password User's password
   * @returns The decrypted key share data
   */
  async get(password: string): Promise<KeyShareData> {
    try {
      if (!this.exists()) {
        throw new Error('No key share found. Please import a key share first.')
      }

      // Read encrypted file
      const osEncrypted = readFileSync(this.keystorePath)

      // Decrypt with Electron's safeStorage (OS-level decryption)
      const keystoreJson = safeStorage.decryptString(osEncrypted)
      const encryptedKeyStore: EncryptedKeyStore = JSON.parse(keystoreJson)

      // Extract components
      const salt = Buffer.from(encryptedKeyStore.salt, 'hex')
      const iv = Buffer.from(encryptedKeyStore.iv, 'hex')
      const encryptedWithTag = encryptedKeyStore.encrypted_data

      // Split encrypted data and auth tag (auth tag is last 32 hex characters / 16 bytes)
      const authTag = Buffer.from(encryptedWithTag.slice(-32), 'hex')
      const encrypted = encryptedWithTag.slice(0, -32)

      // Derive decryption key from password
      const derivedKey = pbkdf2Sync(password, salt, 100000, 32, 'sha256')

      // Decrypt with AES-256-GCM
      const decipher = createDecipheriv('aes-256-gcm', derivedKey, iv)
      decipher.setAuthTag(authTag)

      let decrypted = decipher.update(encrypted, 'hex', 'utf8')
      decrypted += decipher.final('utf8')

      // Parse and return key share
      const keyShare: KeyShareData = JSON.parse(decrypted)

      // Validate decrypted data
      if (!this.validateKeyShare(keyShare)) {
        throw new Error('Decrypted data is not a valid key share')
      }

      return keyShare
    } catch (error) {
      if (error instanceof Error && error.message.includes('BAD_DECRYPT')) {
        throw new Error('Incorrect password')
      }
      console.error('Failed to retrieve key share:', error)
      throw new Error(`Failed to retrieve key share: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Delete the keystore file
   */
  async delete(): Promise<boolean> {
    try {
      if (this.exists()) {
        const fs = await import('fs/promises')
        await fs.unlink(this.keystorePath)
        return true
      }
      return false
    } catch (error) {
      console.error('Failed to delete keystore:', error)
      throw new Error(`Failed to delete keystore: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Validate key share structure
   */
  private validateKeyShare(keyShare: any): keyShare is KeyShareData {
    return (
      keyShare &&
      typeof keyShare === 'object' &&
      typeof keyShare.guardian_id === 'number' &&
      typeof keyShare.x === 'string' &&
      typeof keyShare.total_shares === 'number' &&
      typeof keyShare.threshold === 'number' &&
      typeof keyShare.master_public_key === 'string' &&
      keyShare.x.length > 0 &&
      keyShare.master_public_key.length > 0
    )
  }
}

// Singleton instance
let keystoreInstance: KeyStore | null = null

export function getKeyStore(): KeyStore {
  if (!keystoreInstance) {
    keystoreInstance = new KeyStore()
  }
  return keystoreInstance
}
