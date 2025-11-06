import { contextBridge, ipcRenderer } from 'electron'

// Expose protected methods that allow the renderer process to use
// ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Test IPC communication
  ping: () => ipcRenderer.invoke('ping'),

  // Keystore operations (to be implemented in Phase 2)
  keystore: {
    import: (keyShareData: string, password: string) =>
      ipcRenderer.invoke('keystore:import', keyShareData, password),
    get: (password: string) =>
      ipcRenderer.invoke('keystore:get', password),
    exists: () =>
      ipcRenderer.invoke('keystore:exists')
  },

  // Crypto operations (to be implemented in Phase 3)
  crypto: {
    signRound1: (messageHash: string) =>
      ipcRenderer.invoke('crypto:sign-round1', messageHash),
    signRound3: (kBlind: string, r: string, messageHash: string) =>
      ipcRenderer.invoke('crypto:sign-round3', kBlind, r, messageHash)
  },

  // WebSocket operations (to be implemented in Phase 4)
  websocket: {
    connect: (serverUrl: string) =>
      ipcRenderer.invoke('websocket:connect', serverUrl),
    disconnect: () =>
      ipcRenderer.invoke('websocket:disconnect'),
    joinVault: (vaultId: string, invitationCode: string) =>
      ipcRenderer.invoke('websocket:join-vault', vaultId, invitationCode),

    // Event listeners
    onConnected: (callback: () => void) => {
      ipcRenderer.on('websocket:connected', callback)
      return () => ipcRenderer.removeListener('websocket:connected', callback)
    },
    onDisconnected: (callback: () => void) => {
      ipcRenderer.on('websocket:disconnected', callback)
      return () => ipcRenderer.removeListener('websocket:disconnected', callback)
    },
    onVaultJoined: (callback: (data: any) => void) => {
      ipcRenderer.on('websocket:vault-joined', (_event, data) => callback(data))
      return () => ipcRenderer.removeListener('websocket:vault-joined', callback)
    },
    onSigningRequest: (callback: (data: any) => void) => {
      ipcRenderer.on('websocket:signing-request', (_event, data) => callback(data))
      return () => ipcRenderer.removeListener('websocket:signing-request', callback)
    },
    onSigningComplete: (callback: (data: any) => void) => {
      ipcRenderer.on('websocket:signing-complete', (_event, data) => callback(data))
      return () => ipcRenderer.removeListener('websocket:signing-complete', callback)
    }
  },

  // Transaction signing (to be implemented in Phase 5)
  transaction: {
    approve: (transactionId: string) =>
      ipcRenderer.invoke('transaction:approve', transactionId),
    reject: (transactionId: string) =>
      ipcRenderer.invoke('transaction:reject', transactionId)
  }
})

// Type definitions for TypeScript
export interface ElectronAPI {
  ping: () => Promise<string>
  keystore: {
    import: (keyShareData: string, password: string) => Promise<boolean>
    get: (password: string) => Promise<any>
    exists: () => Promise<boolean>
  }
  crypto: {
    signRound1: (messageHash: string) => Promise<{ R: string; k_blind: string }>
    signRound3: (kBlind: string, r: string, messageHash: string) => Promise<{ s: string }>
  }
  websocket: {
    connect: (serverUrl: string) => Promise<void>
    disconnect: () => Promise<void>
    joinVault: (vaultId: string, invitationCode: string) => Promise<void>
    onConnected: (callback: () => void) => () => void
    onDisconnected: (callback: () => void) => () => void
    onVaultJoined: (callback: (data: any) => void) => () => void
    onSigningRequest: (callback: (data: any) => void) => () => void
    onSigningComplete: (callback: (data: any) => void) => () => void
  }
  transaction: {
    approve: (transactionId: string) => Promise<void>
    reject: (transactionId: string) => Promise<void>
  }
}

declare global {
  interface Window {
    electronAPI: ElectronAPI
  }
}
