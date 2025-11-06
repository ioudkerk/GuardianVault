import { useState } from 'react'

interface ImportKeyProps {
  onImportSuccess: () => void
}

export function ImportKey({ onImportSuccess }: ImportKeyProps) {
  const [keyShareText, setKeyShareText] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const content = e.target?.result as string
          // Validate JSON
          JSON.parse(content)
          setKeyShareText(content)
          setError('')
        } catch (err) {
          setError('Invalid JSON file. Please select a valid key share file.')
        }
      }
      reader.readAsText(file)
    }
  }

  const handleImport = async () => {
    setError('')

    // Validation
    if (!keyShareText.trim()) {
      setError('Please provide a key share (upload file or paste JSON)')
      return
    }

    if (!password) {
      setError('Please enter a password')
      return
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    // Validate JSON format
    try {
      JSON.parse(keyShareText)
    } catch (err) {
      setError('Invalid JSON format in key share')
      return
    }

    setLoading(true)

    try {
      // Import key share using Electron API
      const success = await window.electronAPI.keystore.import(keyShareText, password)

      if (success) {
        onImportSuccess()
      } else {
        setError('Failed to import key share')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to import key share')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto p-8">
      <div className="bg-white rounded-lg shadow-lg p-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Import Guardian Key Share</h1>
        <p className="text-gray-600 mb-6">
          Import your guardian key share to start participating in threshold signing ceremonies.
        </p>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <div className="space-y-6">
          {/* File Upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Upload Key Share File
            </label>
            <input
              type="file"
              accept=".json"
              onChange={handleFileUpload}
              className="block w-full text-sm text-gray-500
                file:mr-4 file:py-2 file:px-4
                file:rounded-md file:border-0
                file:text-sm file:font-semibold
                file:bg-blue-50 file:text-blue-700
                hover:file:bg-blue-100
                cursor-pointer"
            />
          </div>

          {/* Or Divider */}
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">Or paste JSON</span>
            </div>
          </div>

          {/* JSON Textarea */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Key Share JSON
            </label>
            <textarea
              value={keyShareText}
              onChange={(e) => setKeyShareText(e.target.value)}
              placeholder='{"guardian_id": 1, "x": "...", "total_shares": 3, "threshold": 2, "master_public_key": "..."}'
              className="w-full h-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
            />
          </div>

          {/* Password Fields */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Create Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password (min 8 characters)"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              This password will be used to encrypt your key share locally
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Confirm Password
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm password"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Import Button */}
          <button
            onClick={handleImport}
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium transition-colors"
          >
            {loading ? 'Importing...' : 'Import Key Share'}
          </button>
        </div>

        {/* Security Note */}
        <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">Security Notice</h3>
              <p className="text-sm text-yellow-700 mt-1">
                Your key share will be encrypted with your password and stored securely using OS-level encryption.
                Never share your key share or password with anyone.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
