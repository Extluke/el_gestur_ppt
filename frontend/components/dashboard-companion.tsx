'use client'

import { useState, useEffect } from 'react'
import { Lock, Unlock, ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { StarfieldBG } from './starfield-bg'

type StatusType = 'ready' | 'cooldown' | 'laser' | 'searching' | 'inactive'

interface DashboardCompanionProps {
  onBack: () => void
}

export default function DashboardCompanion({ onBack }: DashboardCompanionProps) {
  const [status, setStatus] = useState<StatusType>('inactive')
  const [lockedId, setLockedId] = useState<string | null>(null)
  const [isLocked, setIsLocked] = useState(false)
  const [rawStatusText, setRawStatusText] = useState('')
  const [apiUrl, setApiUrl] = useState('')

  useEffect(() => {
    const hostUrl = `http://${window.location.hostname}:5000`
    setApiUrl(hostUrl)

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${hostUrl}/status`)
        const data = await res.json()

        if (data.locked_id) {
          setLockedId(`ID: ${data.locked_id}`)
          setIsLocked(true)
        } else {
          setLockedId(null)
          setIsLocked(false)
        }

        const pythonStatus = data.gesture_status 
        setRawStatusText(pythonStatus)

        if (!data.is_active) setStatus('inactive')
        else if (pythonStatus.includes("Laser")) setStatus('laser')
        else if (pythonStatus.includes("Cooldown")) setStatus('cooldown')
        else if (data.locked_id) setStatus('ready')
        else setStatus('searching')
      } catch (error) {
        setStatus('inactive')
      }
    }, 500)

    return () => clearInterval(interval)
  }, [])

  const statusConfig = {
    ready: { color: 'bg-green-500', text: 'Siap Mengkibas', glow: 'glow-cyan', description: 'Sistem siap nerima pose lu.' },
    cooldown: { color: 'bg-yellow-500', text: rawStatusText, glow: 'glow-red', description: 'Napas dulu bro, abis gerak.' },
    laser: { color: 'bg-red-500', text: 'Laser Mode Aktif', glow: 'glow-red', description: 'Pake telunjuk lu buat ngarahin kursor.' },
    searching: { color: 'bg-gray-500', text: 'Mencari Presenter', glow: '', description: 'Berdiri di depan kamera buat ngunci.' },
    inactive: { color: 'bg-red-900', text: 'Sistem Offline', glow: '', description: 'Engine AI sedang mati.' },
  }

  const handleUnlock = async () => {
    try { await fetch(`${apiUrl}/unlock`, { method: 'POST' }) } catch (err) {}
  }
  const handleLock = async () => {
    try { await fetch(`${apiUrl}/lock`, { method: 'POST' }) } catch (err) {}
  }

  const config = statusConfig[status]

  return (
    <div className="min-h-screen bg-black relative flex flex-col">
      <div className="fixed inset-0 z-0 pointer-events-none">
        <StarfieldBG />
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-cyan-500/20 rounded-full blur-3xl" />
        <div className="absolute bottom-20 -left-40 w-80 h-80 bg-violet-500/15 rounded-full blur-3xl" />
      </div>

      <div className="relative z-40 bg-slate-900/40 backdrop-blur border-b border-cyan-500/30 p-4">
        <div className="flex items-center justify-between max-w-md mx-auto">
          <button onClick={onBack} className="p-2 hover:bg-cyan-500/30 rounded-lg transition-all duration-300 cursor-pointer">
            <ArrowLeft className="w-6 h-6 text-cyan-400" />
          </button>
          <div className="text-center">
            <h1 className="text-lg font-bold text-transparent bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text">EL PRESENTASI</h1>
          </div>
          <div className="w-6" />
        </div>
      </div>

      <div className="relative z-30 flex-1 flex flex-col p-4 space-y-4 max-w-md mx-auto w-full pointer-events-none">
        <div className="relative rounded-2xl overflow-hidden backdrop-blur-xl bg-slate-900/40 border-2 border-cyan-500/40 aspect-video shadow-lg">
          {apiUrl && <img src={`${apiUrl}/video_feed`} alt="Live CCTV" className="w-full h-full object-cover" />}
          <div className="absolute top-3 left-3 flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${config.color} ${config.glow} animate-pulse`} />
            <span className="text-xs font-bold text-white bg-black/60 backdrop-blur px-2 py-1 rounded border border-white/20">{config.text}</span>
          </div>
        </div>

        <div className="backdrop-blur-xl bg-slate-900/40 rounded-xl p-4 border-2 border-cyan-500/40">
          <span className="text-sm font-semibold text-gray-300">Status Sistem</span>
          <p className={`text-xl font-bold mb-1 mt-2 ${config.color === 'bg-green-500' ? 'text-green-400' : 'text-cyan-300'}`}>{config.text}</p>
          <p className="text-xs text-gray-400">{config.description}</p>
        </div>

        <div className="backdrop-blur-xl bg-slate-900/40 rounded-xl p-4 border-2 border-violet-500/40">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold text-gray-300 flex items-center gap-2"><Lock className="w-4 h-4" /> Target AI</span>
            {isLocked && <span className="text-xs bg-green-500/30 text-green-300 px-2 py-1 rounded">TERKUNCI</span>}
          </div>
          {lockedId ? <p className="text-xl font-mono font-bold text-violet-300">{lockedId}</p> : <p className="text-sm text-gray-400 italic">Berdiri di kamera, lalu klik kunci.</p>}
        </div>
      </div>

      <div className="relative z-50 sticky bottom-0 bg-slate-950/95 backdrop-blur-xl border-t-2 border-cyan-500/50 p-4 space-y-3 max-w-md mx-auto w-full pb-8">
        <Button onClick={handleLock} disabled={isLocked || status === 'inactive'} className={`w-full py-6 font-bold text-lg rounded-xl shadow-xl cursor-pointer transition-transform pointer-events-auto ${isLocked ? 'bg-green-500/20 text-green-300 pointer-events-none' : 'bg-cyan-600 text-white hover:bg-cyan-500'}`}>
          <Lock className="w-5 h-5 mr-2" /> {isLocked ? 'TARGET TERKUNCI' : 'KUNCI TARGET SEKARANG'}
        </Button>
        {isLocked && (
          <Button onClick={handleUnlock} className="w-full py-6 font-bold text-lg rounded-xl bg-red-900/90 text-white border border-red-500/50 hover:bg-red-700 shadow-xl cursor-pointer pointer-events-auto">
            <Unlock className="w-5 h-5 mr-2" /> LEPAS KUNCI (GANTI PRESENTER)
          </Button>
        )}
      </div>
    </div>
  )
}