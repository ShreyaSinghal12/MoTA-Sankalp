import { useEffect, useState } from 'react'
import axios from 'axios'

interface HealthStatus {
  status: string
  version: string
  database: string
  environment: Record<string, unknown>
}

function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
        const response = await axios.get(`${apiUrl}/api/v1/health`)
        setHealth(response.data)
        setError(null)
      } catch (err) {
        setError('Failed to connect to backend')
        setHealth(null)
      } finally {
        setLoading(false)
      }
    }

    checkHealth()
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-government-50 to-government-100">
      <nav className="bg-government-700 text-white shadow-lg">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold">MoTA-SANKALP</h1>
          <p className="text-government-100 text-sm">Scheme Administration, Network & Knowledge Automated Lifecycle Platform</p>
        </div>
      </nav>

      <main className="container mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h2 className="text-3xl font-bold text-government-700 mb-6">Phase 0: Environment Setup</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Backend Status */}
            <div className="border-l-4 border-government-500 pl-4">
              <h3 className="text-xl font-semibold text-government-700 mb-4">Backend Status</h3>
              {loading && (
                <p className="text-gray-600">Checking backend connection...</p>
              )}
              {error && (
                <div className="bg-red-50 border border-red-200 rounded p-4 text-red-700">
                  <p className="font-semibold">Error</p>
                  <p>{error}</p>
                </div>
              )}
              {health && (
                <div className="space-y-2">
                  <div className="flex items-center">
                    <span className="text-green-600 text-lg">OK</span>
                    <span className="ml-2 text-gray-700">Status: <strong>{health.status}</strong></span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-green-600 text-lg">OK</span>
                    <span className="ml-2 text-gray-700">Version: <strong>{health.version}</strong></span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-green-600 text-lg">OK</span>
                    <span className="ml-2 text-gray-700">Debug: <strong>{String(health.environment.debug)}</strong></span>
                  </div>
                  <div className="mt-4 bg-green-50 border border-green-200 rounded p-4">
                    <p className="text-green-700 font-semibold">Backend is running!</p>
                  </div>
                </div>
              )}
            </div>

            {/* Frontend Status */}
            <div className="border-l-4 border-blue-500 pl-4">
              <h3 className="text-xl font-semibold text-government-700 mb-4">Frontend Status</h3>
              <div className="space-y-2">
                <div className="flex items-center">
                  <span className="text-green-600 text-lg">OK</span>
                  <span className="ml-2 text-gray-700">React 18+ Running</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-600 text-lg">OK</span>
                  <span className="ml-2 text-gray-700">Vite Build Tool</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-600 text-lg">OK</span>
                  <span className="ml-2 text-gray-700">TypeScript Enabled</span>
                </div>
                <div className="flex items-center">
                  <span className="text-green-600 text-lg">OK</span>
                  <span className="ml-2 text-gray-700">Tailwind CSS Ready</span>
                </div>
                <div className="mt-4 bg-green-50 border border-green-200 rounded p-4">
                  <p className="text-green-700 font-semibold">Frontend is running!</p>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-8 pt-8 border-t">
            <h3 className="text-lg font-semibold text-government-700 mb-4">Next Steps</h3>
            <ol className="list-decimal list-inside space-y-2 text-gray-700">
              <li>Verify both backend and frontend are running</li>
              <li>Check API endpoints in Swagger: http://localhost:8000/docs</li>
              <li>Create first Git commit</li>
              <li>Proceed to Phase 1: FastAPI Foundation</li>
            </ol>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App