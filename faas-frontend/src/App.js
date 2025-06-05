// App.js
import React, { useState, useEffect } from 'react'
import { Upload } from 'lucide-react'

const versionsByLangage = {
  python: ['3.11', '3.10', '3.9', '3.8'],
  nodejs: ['20', '18', '16', '14'],
  go: ['1.20', '1.19', '1.18'],
  ruby: ['3.2', '3.1', '3.0'],
  java: ['17', '11', '8'],
}

export default function App() {
  const [functions, setFunctions] = useState([])
  const [nom, setNom] = useState('')
  const [langage, setLangage] = useState('python')
  const [version, setVersion] = useState('3.9')
  const [code, setCode] = useState(null)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const backendUrl = '/api'

  const fetchFunctions = async () => {
    try {
      const res = await fetch(`${backendUrl}/fonctions`)
      const data = await res.json()
      setFunctions(data)
    } catch (err) {
      console.error("Erreur lors de la récupération :", err)
    }
  }

  useEffect(() => {
    fetchFunctions()
  }, [])

  useEffect(() => {
    setVersion(versionsByLangage[langage][0])
  }, [langage])

  const handleSubmit = async () => {
    setError('')
    setSuccess('')
    if (!nom || !code) {
      setError('Veuillez renseigner un nom et sélectionner un fichier.')
      return
    }

    const formData = new FormData()
    formData.append('nom', nom)
    formData.append('langage', langage)
    formData.append('version', version)
    formData.append('code', code)

    setLoading(true)
    try {
      const res = await fetch('/api/fonctions', {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const errText = await res.text()
        throw new Error(errText || 'Erreur lors de la création.')
      }

      setSuccess('Fonction créée avec succès.')
      setNom('')
      setCode(null)
      fetchFunctions()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="max-w-4xl mx-auto p-8 bg-gray-50 rounded-lg shadow-lg mt-10">
      <h1 className="text-4xl font-extrabold text-center mb-8 text-gray-900">FaaS Portal</h1>

      <section className="mb-8">
        {functions.length === 0 ? (
          <p className="text-center text-gray-500">Aucune fonction disponible</p>
        ) : (
          <ul className="space-y-4">
            {functions.map((f, i) => (
              <li key={i} className="flex items-center justify-between p-4 bg-white rounded shadow-sm hover:shadow-md transition">
                <div>
                  <p className="font-semibold text-lg text-gray-900">{f.nom}</p>
                  <p className="text-sm text-gray-500">{f.langage} {f.version}</p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Formulaire de création */}
      <section>
        <div className="bg-white p-6 rounded-lg shadow-md">
          {error && <p className="text-red-600 mb-2">{error}</p>}
          {success && <p className="text-green-600 mb-2">{success}</p>}
          <input
            type="text"
            placeholder="Nom de la fonction"
            value={nom}
            onChange={(e) => setNom(e.target.value)}
            className="w-full mb-4 px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <div className="grid grid-cols-2 gap-4 mb-4">
            <select
              value={langage}
              onChange={(e) => setLangage(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {Object.keys(versionsByLangage).map((lang) => (
                <option key={lang} value={lang}>{lang}</option>
              ))}
            </select>
            <select
              value={version}
              onChange={(e) => setVersion(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {versionsByLangage[langage].map((v) => (
                <option key={v} value={v}>{v}</option>
              ))}
            </select>
          </div>
          <input
            type="file"
            onChange={(e) => setCode(e.target.files[0])}
            className="mb-4"
          />
          <button
            onClick={handleSubmit}
            disabled={loading}
            className={`w-full flex items-center justify-center gap-2 font-semibold py-2 rounded transition ${
              loading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
          >
            <Upload className="w-5 h-5" /> {loading ? 'Chargement...' : 'Créer la fonction'}
          </button>
        </div>
      </section>
    </main>
  )
}
