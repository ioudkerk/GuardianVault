import { app, BrowserWindow, ipcMain } from 'electron'
import { join } from 'path'
import { getKeyStore } from './keystore'
import { getCryptoBridge } from './crypto-bridge'
import { getSession } from './session'

let mainWindow: BrowserWindow | null = null

function createWindow(): void {
  // Create the browser window.
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true
    },
    title: 'GuardianVault'
  })

  // Load the index.html of the app.
  if (process.env.NODE_ENV === 'development' || !app.isPackaged) {
    // In development, the renderer will be served by Vite dev server
    mainWindow.loadURL('http://localhost:5173')
    // Open the DevTools in development mode
    mainWindow.webContents.openDevTools()
  } else {
    // In production, load from the built files
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
app.whenReady().then(() => {
  createWindow()

  app.on('activate', () => {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

// Quit when all windows are closed, except on macOS.
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// IPC Handlers
ipcMain.handle('ping', () => {
  return 'pong'
})

// Keystore handlers
ipcMain.handle('keystore:exists', () => {
  try {
    const keystore = getKeyStore()
    return keystore.exists()
  } catch (error) {
    console.error('keystore:exists error:', error)
    throw error
  }
})

ipcMain.handle('keystore:import', async (_event, keyShareData: string, password: string) => {
  try {
    const keystore = getKeyStore()
    return await keystore.import(keyShareData, password)
  } catch (error) {
    console.error('keystore:import error:', error)
    throw error
  }
})

ipcMain.handle('keystore:get', async (_event, password: string) => {
  try {
    const keystore = getKeyStore()
    const keyShare = await keystore.get(password)

    // Cache key share in session
    const session = getSession()
    session.setKeyShare(keyShare)

    return keyShare
  } catch (error) {
    console.error('keystore:get error:', error)
    throw error
  }
})

// Crypto handlers
ipcMain.handle('crypto:sign-round1', async (_event, messageHash: string) => {
  try {
    const session = getSession()
    const keyShare = session.getKeyShare()

    if (!keyShare) {
      throw new Error('Not authenticated. Please unlock your key share first.')
    }

    const cryptoBridge = getCryptoBridge()
    const result = await cryptoBridge.round1GenerateNonce(keyShare, messageHash)

    if (!result.success) {
      throw new Error(result.error || 'Failed to generate nonce')
    }

    return result.data
  } catch (error) {
    console.error('crypto:sign-round1 error:', error)
    throw error
  }
})

ipcMain.handle('crypto:sign-round3', async (_event, kBlind: string, r: string, messageHash: string) => {
  try {
    const session = getSession()
    const keyShare = session.getKeyShare()

    if (!keyShare) {
      throw new Error('Not authenticated. Please unlock your key share first.')
    }

    const cryptoBridge = getCryptoBridge()
    const result = await cryptoBridge.round3ComputeSignatureShare(keyShare, kBlind, r, messageHash)

    if (!result.success) {
      throw new Error(result.error || 'Failed to compute signature share')
    }

    return result.data
  } catch (error) {
    console.error('crypto:sign-round3 error:', error)
    throw error
  }
})

// Placeholder for future IPC handlers
// These will be implemented in later phases:
// - websocket:connect
// - websocket:join-vault
// - websocket:submit-signing
