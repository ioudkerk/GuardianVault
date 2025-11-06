/**
 * Session Manager
 * Manages the guardian's session including cached key share data
 */

interface KeyShareData {
  guardian_id: number
  x: string
  total_shares: number
  threshold: number
  master_public_key: string
}

class SessionManager {
  private keyShare: KeyShareData | null = null
  private authenticated: boolean = false

  /**
   * Set the key share data (after successful authentication)
   */
  setKeyShare(keyShare: KeyShareData): void {
    this.keyShare = keyShare
    this.authenticated = true
  }

  /**
   * Get the key share data
   */
  getKeyShare(): KeyShareData | null {
    if (!this.authenticated || !this.keyShare) {
      return null
    }
    return this.keyShare
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return this.authenticated
  }

  /**
   * Clear the session (logout)
   */
  clear(): void {
    this.keyShare = null
    this.authenticated = false
  }
}

// Singleton instance
let sessionInstance: SessionManager | null = null

export function getSession(): SessionManager {
  if (!sessionInstance) {
    sessionInstance = new SessionManager()
  }
  return sessionInstance
}
