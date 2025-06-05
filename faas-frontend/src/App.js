// App.js
import React, { useState, useEffect } from 'react'
import { Upload, Trash2, ExternalLink, RefreshCw } from 'lucide-react'

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
  const [loadingDelete, setLoadingDelete] = useState({})
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // API pour lire les fonctions (votre backend actuel)
  const readApiUrl = '/api'
  
  // API pour créer les fonctions (API Node.js sur le master)
  const createApiUrl = process.env.REACT_APP_CREATE_API_URL || 'http://172.16.50.100:3001'

  const fetchFunctions = async () => {
    try {
      const res = await fetch(`${readApiUrl}/fonctions`)
      const data = await res.json()
      
      // Si c'est un tableau de strings, récupérer les détails de chaque fonction
      if (Array.isArray(data) && data.length > 0 && typeof data[0] === 'string') {
        const functionsWithDetails = await Promise.all(
          data.map(async (name) => {
            try {
              // Récupérer les détails de chaque fonction (avec l'URL)
              const detailRes = await fetch(`${readApiUrl}/fonctions/${name}`)
              const detail = await detailRes.json()
              
              // Récupérer l'état de la fonction
              const stateRes = await fetch(`${readApiUrl}/fonctions/${name}/etat`)
              const state = await stateRes.json()
              
              return {
                nom: name,
                langage: 'unknown', // Pas disponible dans Knative
                version: 'unknown', // Pas disponible dans Knative
                url: detail.url || '', // URL vient du backend Knative
                ready: state.etat || 'Unknown'
              }
            } catch (err) {
              console.error(`Erreur pour la fonction ${name}:`, err)
              return {
                nom: name,
                langage: 'unknown',
                version: 'unknown',
                url: '', // Pas d'URL en cas d'erreur
                ready: 'Unknown'
              }
            }
          })
        )
        setFunctions(functionsWithDetails)
      } else {
        setFunctions(data)
      }
    } catch (err) {
      console.error("Erreur lors de la récupération :", err)
      setError("Erreur lors de la récupération des fonctions")
    }
  }

  const handleDelete = async (functionName) => {
    if (!window.confirm(`Êtes-vous sûr de vouloir supprimer la fonction "${functionName}" ?`)) {
      return
    }

    setLoadingDelete(prev => ({ ...prev, [functionName]: true }))
    setError('')
    setSuccess('')

    try {
      const res = await fetch(`${readApiUrl}/fonctions/${functionName}`, {
        method: 'DELETE',
      })

      if (!res.ok) {
        const errText = await res.text()
        throw new Error(errText || 'Erreur lors de la suppression.')
      }

      setSuccess(`Fonction "${functionName}" supprimée avec succès !`)
      
      // Rafraîchir la liste des fonctions
      setTimeout(() => {
        fetchFunctions()
      }, 1000)
      
    } catch (err) {
      setError(`Erreur lors de la suppression: ${err.message}`)
    } finally {
      setLoadingDelete(prev => ({ ...prev, [functionName]: false }))
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
      // Utiliser l'API de création sur le master
      const res = await fetch(`${createApiUrl}/api/fonctions`, {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) { // ✅ Correction de la syntaxe ici
        const errText = await res.text()
        throw new Error(errText || 'Erreur lors de la création.')
      }

      const result = await res.json()
      setSuccess(`Fonction '${nom}' créée avec succès !`)
      setNom('')
      setCode(null)
      
      // Rafraîchir la liste des fonctions après création
      setTimeout(() => {
        fetchFunctions()
      }, 2000)
      
    } catch (err) {
      setError(`Erreur: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (ready) => {
    switch (ready) {
      case 'True':
        return 'bg-green-100 text-green-800'
      case 'False':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusText = (ready) => {
    switch (ready) {
      case 'True':
        return '✅ Prêt'
      case 'False':
        return '❌ Non prêt'
      default:
        return '❓ Inconnu'
    }
  }

  return (
    <main className="max-w-6xl mx-auto p-8 bg-gray-50 rounded-lg shadow-lg mt-10">
      <h1 className="text-4xl font-extrabold text-center mb-8 text-gray-900">
        FaaS Portal
      </h1>

      {/* Section d'information sur les APIs */}
      <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-sm font-semibold text-blue-800 mb-2">
              Configuration API
            </h2>
            <p className="text-xs text-blue-600">
              📖 Lecture: {readApiUrl} | 
              ✏️ Création: {createApiUrl}
            </p>
          </div>
          <button
            onClick={fetchFunctions}
            className="flex items-center gap-2 px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 transition"
          >
            <RefreshCw className="w-4 h-4" />
            Actualiser
          </button>
        </div>
      </div>

      {/* Messages globaux */}
      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-300 text-red-700 rounded">
          {error}
        </div>
      )}
      {success && (
        <div className="mb-4 p-3 bg-green-100 border border-green-300 text-green-700 rounded">
          {success}
        </div>
      )}

      {/* Liste des fonctions */}
      <section className="mb-8">
        {functions.length === 0 ? (
          <p className="text-center text-gray-500">
            Aucune fonction disponible
          </p>
        ) : (
          <div>
            <h2 className="text-2xl font-bold mb-4 text-gray-800">
              Fonctions déployées ({functions.length})
            </h2>
            <div className="grid gap-4">
              {functions.map((f, i) => (
                <div 
                  key={i} 
                  className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold text-lg text-gray-900">
                          {f.nom}
                        </h3>
                        <span 
                          className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(f.ready)}`}
                        >
                          {getStatusText(f.ready)}
                        </span>
                      </div>
                      
                      <p className="text-sm text-gray-500 mb-2">
                        {f.langage !== 'unknown' 
                          ? `${f.langage} ${f.version}` 
                          : 'Langage non spécifié'
                        }
                      </p>
                      
                      {f.url && (
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-500">URL:</span>
                          <a 
                            href={f.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1 break-all"
                          >
                            {f.url}
                            <ExternalLink className="w-3 h-3 flex-shrink-0" />
                          </a>
                        </div>
                      )}
                    </div>
                    
                    <div className="flex items-center gap-2 ml-4">
                      <button
                        onClick={() => handleDelete(f.nom)}
                        disabled={loadingDelete[f.nom]}
                        className={`flex items-center gap-2 px-3 py-2 rounded text-sm font-medium transition ${
                          loadingDelete[f.nom]
                            ? 'bg-gray-300 cursor-not-allowed text-gray-500'
                            : 'bg-red-600 hover:bg-red-700 text-white'
                        }`}
                      >
                        <Trash2 className="w-4 h-4" />
                        {loadingDelete[f.nom] ? 'Suppression...' : 'Supprimer'}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* Formulaire de création */}
      <section>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-bold mb-4 text-gray-800">
            Créer une nouvelle fonction
          </h2>
          
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
                <option key={lang} value={lang}>
                  {lang}
                </option>
              ))}
            </select>
            <select
              value={version}
              onChange={(e) => setVersion(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {versionsByLangage[langage].map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
          </div>
          
          <input
            type="file"
            accept=".py,.js,.go,.rb,.java"
            onChange={(e) => setCode(e.target.files[0])}
            className="mb-4 w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          
          <button
            onClick={handleSubmit}
            disabled={loading}
            className={`w-full flex items-center justify-center gap-2 font-semibold py-2 rounded transition ${
              loading
                ? 'bg-gray-400 cursor-not-allowed text-white'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
          >
            <Upload className="w-5 h-5" /> 
            {loading ? 'Création en cours...' : 'Créer la fonction'}
          </button>
          
          {loading && (
            <p className="text-sm text-gray-600 mt-2 text-center">
              ⏳ Déploiement de la fonction sur le cluster...
            </p>
          )}
        </div>
      </section>
    </main>
  )
}