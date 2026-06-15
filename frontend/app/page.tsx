'use client'

import { useEffect, useState, useCallback } from 'react'

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

const LINKEDIN_URL =
  'https://www.linkedin.com/jobs/search/?keywords=jefe+construccion+electrica+subestaciones&location=Chile&f_TPR=r604800'

interface Job {
  id: number
  title: string
  company: string
  portal: string
  url: string
  description: string
  date_found: string
  relevance_reason: string
}

const PORTAL_STYLE: Record<string, string> = {
  Indeed: 'bg-blue-100 text-blue-800',
  'Trabajando.cl': 'bg-emerald-100 text-emerald-800',
  Computrabajo: 'bg-orange-100 text-orange-800',
  Chiletrabajos: 'bg-purple-100 text-purple-800',
}

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleDateString('es-CL', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    })
  } catch {
    return ''
  }
}

export default function Dashboard() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [scanning, setScanning] = useState(false)
  const [adapting, setAdapting] = useState<Set<number>>(new Set())
  const [done, setDone] = useState<Set<number>>(new Set())
  const [lastUpdate, setLastUpdate] = useState('')

  const fetchJobs = useCallback(async () => {
    try {
      const res = await fetch(`${BACKEND}/jobs`)
      const data = await res.json()
      setJobs(data.jobs ?? [])
      setLastUpdate(new Date().toLocaleString('es-CL'))
    } catch {
      console.error('No se pudo conectar al backend')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchJobs() }, [fetchJobs])

  const handleAdaptCV = async (job: Job) => {
    setAdapting(prev => new Set(prev).add(job.id))
    try {
      const res = await fetch(`${BACKEND}/adapt-cv/${job.id}`, { method: 'POST' })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)

      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `CV_Ronald_Sarabia_${job.company.replace(/\s+/g, '_').slice(0, 30)}.docx`
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)

      setDone(prev => new Set(prev).add(job.id))
    } catch {
      alert('Error al generar el CV. Revisa que el backend esté activo.')
    } finally {
      setAdapting(prev => { const s = new Set(prev); s.delete(job.id); return s })
    }
  }

  const handleDismiss = async (jobId: number) => {
    try {
      await fetch(`${BACKEND}/jobs/${jobId}/dismiss`, { method: 'POST' })
      setJobs(prev => prev.filter(j => j.id !== jobId))
    } catch {
      console.error('Error al descartar')
    }
  }

  const handleScan = async () => {
    setScanning(true)
    try {
      await fetch(`${BACKEND}/scan/run`, { method: 'POST' })
      // Give the background task ~8 seconds to finish scraping
      setTimeout(() => { fetchJobs(); setScanning(false) }, 8000)
    } catch {
      setScanning(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ── Header ── */}
      <div className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-xl mx-auto px-4 py-4 space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-lg font-bold text-gray-900">Ofertas para Ronald</h1>
              {lastUpdate && (
                <p className="text-xs text-gray-400">Actualizado: {lastUpdate}</p>
              )}
            </div>
            <button
              onClick={handleScan}
              disabled={scanning}
              className="text-sm bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              {scanning ? 'Buscando...' : 'Buscar ahora'}
            </button>
          </div>

          {/* LinkedIn manual button */}
          <a
            href={LINKEDIN_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 w-full bg-[#0A66C2] hover:bg-[#0057ad] text-white py-2.5 rounded-lg text-sm font-semibold transition-colors"
          >
            <svg className="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
              <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
            </svg>
            Buscar en LinkedIn (manual)
          </a>
        </div>
      </div>

      {/* ── Content ── */}
      <div className="max-w-xl mx-auto px-4 py-5">
        {loading ? (
          <div className="text-center py-20 text-gray-400">Cargando ofertas...</div>
        ) : jobs.length === 0 ? (
          <div className="text-center py-20 space-y-2">
            <p className="text-gray-500 text-lg font-medium">Sin ofertas nuevas por ahora</p>
            <p className="text-gray-400 text-sm">El agente busca automáticamente cada 6 horas</p>
            <p className="text-gray-400 text-sm">También puedes presionar "Buscar ahora"</p>
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-sm text-gray-500 font-medium">
              {jobs.length} oferta{jobs.length !== 1 ? 's' : ''} encontrada{jobs.length !== 1 ? 's' : ''}
            </p>

            {jobs.map(job => (
              <div
                key={job.id}
                className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 space-y-3"
              >
                {/* Top row: portal badge + date */}
                <div className="flex items-center justify-between">
                  <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${PORTAL_STYLE[job.portal] ?? 'bg-gray-100 text-gray-600'}`}>
                    {job.portal}
                  </span>
                  <span className="text-xs text-gray-400">{formatDate(job.date_found)}</span>
                </div>

                {/* Title + company */}
                <div>
                  <h2 className="font-bold text-gray-900 text-base leading-snug">{job.title}</h2>
                  <p className="text-sm text-gray-500 mt-0.5">{job.company}</p>
                </div>

                {/* Why relevant */}
                {job.relevance_reason && (
                  <p className="text-xs text-emerald-700 bg-emerald-50 rounded-lg px-3 py-1.5">
                    {job.relevance_reason}
                  </p>
                )}

                {/* Description excerpt */}
                {job.description && (
                  <p className="text-sm text-gray-400 line-clamp-2">{job.description}</p>
                )}

                {/* Action buttons */}
                <div className="flex gap-2 pt-1">
                  <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 text-center text-sm border border-gray-200 text-gray-600 hover:bg-gray-50 py-2.5 rounded-xl font-medium transition-colors"
                  >
                    Ver oferta
                  </a>

                  <button
                    onClick={() => handleAdaptCV(job)}
                    disabled={adapting.has(job.id)}
                    className={`flex-1 text-sm py-2.5 rounded-xl font-semibold transition-colors disabled:opacity-60 ${
                      done.has(job.id)
                        ? 'bg-emerald-600 text-white'
                        : 'bg-blue-600 hover:bg-blue-700 text-white'
                    }`}
                  >
                    {adapting.has(job.id)
                      ? 'Generando CV...'
                      : done.has(job.id)
                      ? 'CV descargado'
                      : 'Me interesa'}
                  </button>

                  <button
                    onClick={() => handleDismiss(job.id)}
                    title="Descartar"
                    className="text-gray-300 hover:text-gray-500 px-2 py-2.5 rounded-xl transition-colors"
                  >
                    ✕
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
