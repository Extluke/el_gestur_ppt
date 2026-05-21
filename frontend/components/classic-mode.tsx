'use client'

import { useState, useEffect } from 'react'
import { ArrowLeft, Activity, Lock } from 'lucide-react'
import { Button } from '@/components/ui/button'

type StatusType = 'ready' | 'cooldown' | 'laser' | 'inactive'

interface ClassicModeProps {
  onBack: () => void
}

export default function ClassicMode({ onBack }: ClassicModeProps) {
  const [status, setStatus] = useState<StatusType>('inactive')
  const [isRunning, setIsRunning] = useState(false)
  const [uptime, setUptime] = useState(0)
  const [gesturesCount, setGesturesCount] = useState(0)
  const [lockedId, setLockedId] = useState<string | null>(null)
  const [apiUrl, setApiUrl] = useState('')
  const [logMessages, setLogMessages] = useState<string[]>(['[INIT] Sistem dimulai...'])

  useEffect(() => {
    const hostUrl = `http://${window.location.hostname}:5000`
    setApiUrl(hostUrl)

    let uptimeInterval: NodeJS.Timeout
    if (isRunning) uptimeInterval = setInterval(() => setUptime(u => u + 1), 1000)

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${hostUrl}/status`)
        const data = await res.json()

        setIsRunning(data.is_active)

        if (data.locked_id) {
          if (!lockedId) setLogMessages(prev => [...prev.slice(-8), `[LOCK] Terkunci ke Target ID: ${data.locked_id}`])
          setLockedId(`ID: ${data.locked_id}`)
        } else {
          setLockedId(null)
        }

        const pythonStatus = data.gesture_status 
        if (pythonStatus !== "Siap" && status === 'ready') {
            setGesturesCount(g => g + 1)
            setLogMessages(prev => [...prev.slice(-8), `[GESTURE] Aksi terdeteksi!`])
        }

        if (!data.is_active) setStatus('inactive')
        else if (pythonStatus.includes("Laser")) setStatus('laser')
        else if (pythonStatus.includes("Cooldown")) setStatus('cooldown')
        else if (data.locked_id) setStatus('ready')
        else setStatus('inactive') // searching state falls here in classic

      } catch (error) {
        if (isRunning) {
          setIsRunning(false)
          setStatus('inactive')
        }
      }
    }, 500)

    return () => {
      clearInterval(interval)
      if (uptimeInterval) clearInterval(uptimeInterval)
    }
  }, [isRunning, status, lockedId])

  const handleStart = async () => {
    try {
      await fetch(`${apiUrl}/start`, { method: 'POST' })
      setUptime(0)
      setLogMessages(prev => [...prev.slice(-8), '[SYSTEM] Pipeline AI diaktifkan...'])
    } catch (err) {}
  }

  const handleStop = async () => {
    try {
      await fetch(`${apiUrl}/stop`, { method: 'POST' })
      setLogMessages(prev => [...prev.slice(-8), '[SYSTEM] Pipeline AI dimatikan.'])
    } catch (err) {}
  }

  const handleLockToggle = async () => {
      if (lockedId) {
          try { await fetch(`${apiUrl}/unlock`, { method: 'POST' }); setLogMessages(prev => [...prev.slice(-8), '[LOCK] Target dilepas.']) } catch (err) {}
      } else {
          try { await fetch(`${apiUrl}/lock`, { method: 'POST' }); setLogMessages(prev => [...prev.slice(-8), '[LOCK] Mencari target...']) } catch (err) {}
      }
  }

  const config = {
    ready: { color: 'text-green-400', bgColor: 'bg-green-500/20', label: 'System Ready' },
    cooldown: { color: 'text-yellow-400', bgColor: 'bg-yellow-500/20', label: 'Processing' },
    laser: { color: 'text-red-400', bgColor: 'bg-red-500/20', label: 'Laser Active' },
    inactive: { color: 'text-gray-500', bgColor: 'bg-gray-500/20', label: 'Offline / Standby' },
  }[status]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex flex-col">
      <div className="bg-slate-900/50 backdrop-blur border-b border-cyan-500/20 p-4 relative z-50">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <button onClick={onBack} className="p-2 hover:bg-cyan-500/20 rounded-lg transition-colors cursor-pointer"><ArrowLeft className="w-6 h-6 text-cyan-400" /></button>
          <h1 className="text-2xl font-bold text-transparent bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text">El Presentasi - Classic Mode</h1>
          <div className="w-6" />
        </div>
      </div>

      <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full p-6 space-y-6 relative z-40">
        <div className="bg-slate-900/40 backdrop-blur-xl rounded-xl p-6 border border-cyan-500/30 shadow-lg">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <p className="text-xs font-semibold text-gray-400 uppercase">System Status</p>
              <div className={`flex items-center gap-2 ${config.bgColor} rounded-lg px-3 py-2`}>
                <div className={`w-2 h-2 rounded-full ${config.color} ${isRunning ? 'animate-pulse' : ''}`} />
                <span className={`font-semibold ${config.color}`}>{config.label}</span>
              </div>
            </div>
            <div className="space-y-2">
              <p className="text-xs font-semibold text-gray-400 uppercase">Target Lock</p>
              <div className="flex items-center gap-2">
                <Lock className={`w-4 h-4 ${lockedId ? 'text-green-400' : 'text-gray-500'}`} />
                <span className={`font-bold font-mono ${lockedId ? 'text-green-400' : 'text-gray-500'}`}>{lockedId || 'NO TARGET'}</span>
              </div>
            </div>
            <div className="space-y-2">
              <p className="text-xs font-semibold text-gray-400 uppercase">Gestures Count</p>
              <p className="text-2xl font-bold text-purple-300 font-mono">{gesturesCount}</p>
            </div>
            <div className="space-y-2">
              <p className="text-xs font-semibold text-gray-400 uppercase">Uptime</p>
              <p className="text-2xl font-bold text-cyan-300 font-mono">{Math.floor(uptime / 60)}:{String(uptime % 60).padStart(2, '0')}</p>
            </div>
          </div>
        </div>

        <div className="bg-slate-900/40 backdrop-blur-xl rounded-xl p-6 border border-purple-500/30">
          <h2 className="text-lg font-bold text-purple-300 mb-4 flex items-center gap-2"><Activity className="w-5 h-5" /> Engine Control</h2>
          <div className="flex flex-col sm:flex-row gap-3">
            <Button onClick={handleStart} disabled={isRunning} className={`flex-1 py-6 font-bold text-lg rounded-lg cursor-pointer ${isRunning ? 'bg-green-500/10 text-green-700 pointer-events-none' : 'bg-green-600 text-white hover:bg-green-500'}`}>START AI ENGINE</Button>
            <Button onClick={handleLockToggle} disabled={!isRunning} className={`flex-1 py-6 font-bold text-lg rounded-lg cursor-pointer ${!isRunning ? 'bg-slate-800 text-slate-600 pointer-events-none' : lockedId ? 'bg-yellow-600 hover:bg-yellow-500 text-white' : 'bg-blue-600 hover:bg-blue-500 text-white'}`}>{lockedId ? 'LEPAS KUNCI' : 'KUNCI TARGET'}</Button>
            <Button onClick={handleStop} disabled={!isRunning} className={`flex-1 py-6 font-bold text-lg rounded-lg cursor-pointer ${!isRunning ? 'bg-red-500/10 text-red-800 pointer-events-none' : 'bg-red-600 text-white hover:bg-red-500'}`}>STOP AI ENGINE</Button>
          </div>
        </div>

        <div className="bg-slate-900/40 backdrop-blur-xl rounded-xl p-6 border border-blue-500/30 flex-1 flex flex-col min-h-[200px]">
          <h2 className="text-lg font-bold text-blue-300 mb-4">System Event Log</h2>
          <div className="flex-1 bg-slate-950/80 rounded-lg p-4 font-mono text-sm overflow-y-auto border border-blue-500/20">
            {logMessages.map((msg, idx) => (
              <div key={idx} className="text-gray-400 mb-2"><span className="text-cyan-400">[{new Date().toLocaleTimeString()}]</span> {msg}</div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}