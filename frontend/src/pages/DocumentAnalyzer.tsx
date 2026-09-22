import React, { useState } from 'react'
import axios from 'axios'

export default function DocumentAnalyzer() {
  const [file, setFile] = useState<File | null>(null)
  const [appId, setAppId] = useState('1')
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) {
      setError('Please select a file')
      return
    }

    setLoading(true)
    const formData = new FormData()
    formData.append('file', file)
    formData.append('application_id', appId)
    formData.append('document_type', 'CASTE_CERTIFICATE')

    try {
      const res = await axios.post('http://localhost:8000/api/v1/documents/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      setResult(res.data)
      setError('')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: '20px', maxWidth: '1000px', margin: '0 auto' }}>
      <h1>Document Analysis Pipeline</h1>
      
      <form onSubmit={handleAnalyze} style={{ background: 'white', padding: '20px', borderRadius: '5px', marginBottom: '20px' }}>
        <div style={{ marginBottom: '15px' }}>
          <label>Upload Certificate:</label>
          <input
            type="file"
            accept="image/*"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            style={{ width: '100%', padding: '8px', marginTop: '5px', display: 'block' }}
          />
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label>Application ID:</label>
          <input
            type="number"
            value={appId}
            onChange={(e) => setAppId(e.target.value)}
            style={{ width: '100%', padding: '8px', marginTop: '5px' }}
          />
        </div>

        {error && <div style={{ color: 'red', marginBottom: '10px' }}>{error}</div>}

        <button
          type="submit"
          disabled={loading}
          style={{
            padding: '10px 30px',
            background: '#0066cc',
            color: 'white',
            border: 'none',
            borderRadius: '3px',
            cursor: 'pointer',
            opacity: loading ? 0.5 : 1
          }}
        >
          {loading ? 'Analyzing...' : 'Analyze Document'}
        </button>
      </form>

      {result && (
        <div style={{ background: 'white', padding: '20px', borderRadius: '5px' }}>
          <h2>Analysis Results</h2>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '20px', marginBottom: '20px' }}>
            <div style={{ background: '#f0f0f0', padding: '15px', borderRadius: '3px' }}>
              <div style={{ fontSize: '12px', color: '#666' }}>Detected Type</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{result.detected_document_type}</div>
              <div style={{ fontSize: '12px', color: '#666' }}>Confidence: {(result.document_type_confidence * 100).toFixed(1)}%</div>
            </div>

            <div style={{ background: '#f0f0f0', padding: '15px', borderRadius: '3px' }}>
              <div style={{ fontSize: '12px', color: '#666' }}>OCR Confidence</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{(result.ocr_confidence * 100).toFixed(1)}%</div>
            </div>

            <div style={{ background: '#f0f0f0', padding: '15px', borderRadius: '3px' }}>
              <div style={{ fontSize: '12px', color: '#666' }}>Quality Score</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{(result.quality_assessment.quality_score * 100).toFixed(1)}%</div>
            </div>

            <div style={{ background: result.fraud_report.overall_fraud_risk === 'HIGH' ? '#ffe0e0' : '#e0ffe0', padding: '15px', borderRadius: '3px' }}>
              <div style={{ fontSize: '12px', color: '#666' }}>Fraud Risk</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: result.fraud_report.overall_fraud_risk === 'HIGH' ? '#cc0000' : '#00aa00' }}>
                {result.fraud_report.overall_fraud_risk}
              </div>
            </div>
          </div>

          <div style={{ background: '#f9f9f9', padding: '15px', borderRadius: '3px', maxHeight: '200px', overflow: 'auto' }}>
            <div style={{ fontSize: '12px', fontWeight: 'bold', marginBottom: '10px' }}>Extracted Text:</div>
            <pre style={{ fontSize: '12px', whiteSpace: 'pre-wrap' }}>
              {result.extracted_text.slice(0, 300)}...
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}
