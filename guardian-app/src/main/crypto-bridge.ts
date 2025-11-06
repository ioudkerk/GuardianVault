import { spawn } from 'child_process'
import { join } from 'path'
import { app } from 'electron'

interface Round1Result {
  R: string
  k_blind: string
}

interface Round3Result {
  s: string
}

interface CryptoResult<T> {
  success: boolean
  error?: string
  data?: T
}

export class CryptoBridge {
  private pythonPath: string
  private scriptPath: string

  constructor() {
    // Determine Python path (use system python3)
    this.pythonPath = 'python3'

    // Determine script path based on environment
    if (app.isPackaged) {
      // In production, the python script should be in resources
      this.scriptPath = join(process.resourcesPath, 'python', 'crypto_ops.py')
    } else {
      // In development, use the script from the project directory
      this.scriptPath = join(app.getAppPath(), 'python', 'crypto_ops.py')
    }
  }

  /**
   * Execute Round 1: Generate nonce
   */
  async round1GenerateNonce(
    keyShareData: any,
    messageHash: string
  ): Promise<CryptoResult<Round1Result>> {
    const args = [
      this.scriptPath,
      'round1',
      '--key-share', JSON.stringify(keyShareData),
      '--message-hash', messageHash
    ]

    return this.executePythonScript<Round1Result>(args)
  }

  /**
   * Execute Round 3: Compute signature share
   */
  async round3ComputeSignatureShare(
    keyShareData: any,
    kBlind: string,
    r: string,
    messageHash: string
  ): Promise<CryptoResult<Round3Result>> {
    const args = [
      this.scriptPath,
      'round3',
      '--key-share', JSON.stringify(keyShareData),
      '--k-blind', kBlind,
      '--r', r,
      '--message-hash', messageHash
    ]

    return this.executePythonScript<Round3Result>(args)
  }

  /**
   * Execute Python script and parse JSON output
   */
  private executePythonScript<T>(args: string[]): Promise<CryptoResult<T>> {
    return new Promise((resolve) => {
      let stdout = ''
      let stderr = ''

      const process = spawn(this.pythonPath, args)

      process.stdout.on('data', (data) => {
        stdout += data.toString()
      })

      process.stderr.on('data', (data) => {
        stderr += data.toString()
      })

      process.on('close', (code) => {
        if (code === 0) {
          try {
            // Parse JSON output from Python script
            const result = JSON.parse(stdout)

            if (result.success) {
              // Remove 'success' field and return the rest as data
              const { success, ...data } = result
              resolve({
                success: true,
                data: data as T
              })
            } else {
              resolve({
                success: false,
                error: result.error || 'Unknown error from crypto script'
              })
            }
          } catch (error) {
            resolve({
              success: false,
              error: `Failed to parse crypto script output: ${stdout}`
            })
          }
        } else {
          // Try to parse error from stdout
          try {
            const errorResult = JSON.parse(stdout)
            resolve({
              success: false,
              error: errorResult.error || stderr || `Script exited with code ${code}`
            })
          } catch {
            resolve({
              success: false,
              error: stderr || `Script exited with code ${code}`
            })
          }
        }
      })

      process.on('error', (error) => {
        resolve({
          success: false,
          error: `Failed to spawn Python process: ${error.message}`
        })
      })
    })
  }
}

// Singleton instance
let cryptoBridgeInstance: CryptoBridge | null = null

export function getCryptoBridge(): CryptoBridge {
  if (!cryptoBridgeInstance) {
    cryptoBridgeInstance = new CryptoBridge()
  }
  return cryptoBridgeInstance
}
