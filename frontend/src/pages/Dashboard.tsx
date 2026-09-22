import React, { useState, useEffect } from 'react'
import axios from 'axios'

export default function Dashboard() {
  const [applications, setApplications] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      window.location.href = '/login'
      return
    }
    fetchApplications()
  }, [])

  const fetchApplications = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/v1/applications/', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      })
      setApplications(res.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    window.location.href = '/login'
  }

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
        <h1>MoTA-SANKALP Dashboard</h1>
        <button onClick={handleLogout} style={{ padding: '10px 20px', background: '#cc0000', color: 'white', border: 'none', cursor: 'pointer' }}>
          Logout
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '15px', marginBottom: '30px' }}>
        <div style={{ background: 'white', padding: '20px', borderRadius: '5px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#0066cc' }}>156</div>
          <div>Total Applications</div>
        </div>
        <div style={{ background: 'white', padding: '20px', borderRadius: '5px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#00aa00' }}>89</div>
          <div>Eligible</div>
        </div>
        <div style={{ background: 'white', padding: '20px', borderRadius: '5px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ffaa00' }}>32</div>
          <div>Under Review</div>
        </div>
        <div style={{ background: 'white', padding: '20px', borderRadius: '5px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#cc0000' }}>12</div>
          <div>Fraud Risk</div>
        </div>
      </div>

      <div style={{ background: 'white', padding: '20px', borderRadius: '5px' }}>
        <h2>Recent Applications</h2>
        {loading ? (
          <p>Loading...</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '15px' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #ddd' }}>
                <th style={{ textAlign: 'left', padding: '10px' }}>App ID</th>
                <th style={{ textAlign: 'left', padding: '10px' }}>Scheme</th>
                <th style={{ textAlign: 'left', padding: '10px' }}>Status</th>
                <th style={{ textAlign: 'left', padding: '10px' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {[1, 2, 3, 4, 5].map((id) => (
                <tr key={id} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={{ padding: '10px' }}>{id}</td>
                  <td style={{ padding: '10px' }}>NFST</td>
                  <td style={{ padding: '10px' }}><span style={{ background: '#e0ffe0', padding: '5px 10px', borderRadius: '3px' }}>Eligible</span></td>
                  <td style={{ padding: '10px' }}><a href="/documents" style={{ color: '#0066cc', textDecoration: 'none' }}>Review</a></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
