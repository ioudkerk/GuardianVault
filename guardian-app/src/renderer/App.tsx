import { useState, useEffect } from 'react'
import { ImportKey } from './components/Setup/ImportKey'

type AppState = 'loading' | 'setup' | 'dashboard'

function App() {
  const [appState, setAppState] = useState<AppState>('loading')
  const [error, setError] = useState<string>('')

  useEffect(() => {
    // Check if key share exists
    const checkKeyShare = async () => {
      try {
        const exists = await window.electronAPI.keystore.exists()
        if (exists) {
          setAppState('dashboard')
        } else {
          setAppState('setup')
        }
      } catch (error) {
        console.error('Failed to check keystore:', error)
        setError('Failed to initialize app')
        setAppState('setup')
      }
    }

    checkKeyShare()
  }, [])

  const handleImportSuccess = () => {
    setAppState('dashboard')
  }

  if (appState === 'loading') {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-blue-500 to-purple-600">
        <div className="bg-white rounded-lg shadow-xl p-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading GuardianVault...</p>
          </div>
        </div>
      </div>
    )
  }

  if (appState === 'setup') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 py-12">
        {error && (
          <div className="max-w-2xl mx-auto mb-4">
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          </div>
        )}
        <ImportKey onImportSuccess={handleImportSuccess} />
      </div>
    )
  }

  // Dashboard (placeholder for now)
  return (
    <div className="flex items-center justify-center h-screen bg-gradient-to-br from-blue-500 to-purple-600">
      <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-800 mb-4">
            GuardianVault
          </h1>
          <p className="text-gray-600 mb-6">
            Dashboard (Coming Soon)
          </p>
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <p className="text-sm text-green-700">
              ✓ Key share imported successfully!
            </p>
          </div>
          <div className="mt-6 text-sm text-gray-500">
            <p>Next: Connect to coordination server</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
