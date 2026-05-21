'use client'

import { useState, useEffect, useRef } from 'react'
import { Lock, Unlock, X, Move } from 'lucide-react'

type StatusType = 'ready' | 'cooldown' | 'laser' | 'searching'

interface FloatingWidgetProps {
  onClose: () => void
}

export default function FloatingWidget({ onClose }: FloatingWidgetProps) {
  const [status, setStatus] = useState<StatusType>('searching')
  const [lockedId, setLockedId] = useState<string | null>(null)
  const [isLocked, setIsLocked] = useState(false)
  const [rawStatusText, setRawStatusText] = useState('')
  const [apiUrl, setApiUrl] = useState('')

  const [position, setPosition] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const dragRef = useRef({ startX: 0, startY: 0, initialX: 0, initialY: 0 })

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setPosition({ x: window.innerWidth - 320, y: window.innerHeight - 250 })
    }

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

        if (pythonStatus.includes("Laser")) setStatus('laser')
        else if (pythonStatus.includes("Cooldown")) setStatus('cooldown')
        else if (data.locked_id) setStatus('ready')
        else setStatus('searching')
      } catch (error) {}
    }, 500)

    return () => clearInterval(interval)
  }, [])

  const statusConfig = {
    ready: { color: 'bg-green-500', text: 'Siap Mengkibas' },
    cooldown: { color: 'bg-yellow-500', text: rawStatusText },
    laser: { color: 'bg-red-500', text: 'Laser Aktif' },
    searching: { color: 'bg-gray-500', text: 'Mencari Target...' },
  }

  const handleUnlock = async () => {
    try { await fetch(`${apiUrl}/unlock`, { method: 'POST' }) } catch (err) {}
  }

  const handlePointerDown = (e: React.PointerEvent) => {
    setIsDragging(true)
    dragRef.current = { startX: e.clientX, startY: e.clientY, initialX: position.x, initialY: position.y }
    ;(e.target as HTMLElement).setPointerCapture(e.pointerId)
  }
  const handlePointerMove = (e: React.PointerEvent) => {
    if (!isDragging) return
    setPosition({ x: dragRef.current.initialX + (e.clientX - dragRef.current.startX), y: dragRef.current.initialY + (e.clientY - dragRef.current.startY) })
  }
  const handlePointerUp = (e: React.PointerEvent) => {
    setIsDragging(false)
    ;(e.target as HTMLElement).releasePointerCapture(e.pointerId)
  }

  const config = statusConfig[status]

  return (
    <div className="fixed z-[9999] group shadow-2xl" style={{ left: `${position.x}px`, top: `${position.y}px` }}>
      <button onClick={onClose} className="absolute -top-3 -right-3 bg-red-500/80 hover:bg-red-500 text-white p-1.5 rounded-full shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-50 backdrop-blur-md cursor-pointer">
        <X className="w-4 h-4" />
      </button>

      <div className="w-72 rounded-2xl overflow-hidden backdrop-blur-xl bg-slate-900/80 border border-cyan-500/30 transition-colors duration-300 hover:border-cyan-500/80">
        <div className="bg-slate-950/80 p-3 flex justify-between items-center cursor-move border-b border-cyan-500/20 active:cursor-grabbing select-none" onPointerDown={handlePointerDown} onPointerMove={handlePointerMove} onPointerUp={handlePointerUp} onPointerCancel={handlePointerUp}>
          <div className="flex items-center gap-2 pointer-events-none">
            <Move className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-bold text-transparent bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text">SERET SAYA</span>
          </div>
          <div className="flex gap-1">
            <div className="w-2 h-2 rounded-full bg-red-500/50"></div>
            <div className="w-2 h-2 rounded-full bg-yellow-500/50"></div>
            <div className="w-2 h-2 rounded-full bg-green-500/50"></div>
          </div>
        </div>

        <div className="p-4 space-y-3 pointer-events-none">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${config.color} animate-pulse shadow-[0_0_10px_currentColor]`} />
              <span className={`text-sm font-bold ${config.color === 'bg-green-500' ? 'text-green-400' : 'text-gray-300'}`}>{config.text}</span>
            </div>
            {isLocked && <Lock className="w-4 h-4 text-green-400" />}
          </div>

          {isLocked ? (
            <div className="flex items-center justify-between bg-black/40 rounded-lg p-2 border border-green-500/20">
              <span className="text-xs text-gray-400">Target:</span>
              <span className="text-sm font-mono font-bold text-green-400">{lockedId}</span>
            </div>
          ) : (
            <div className="text-xs text-gray-500 italic text-center py-1">Standby. Arahkan ke kamera.</div>
          )}
        </div>

        {isLocked && (
          <div className="px-4 pb-4">
            <button onClick={handleUnlock} className="w-full bg-red-500/10 hover:bg-red-500/30 text-red-400 border border-red-500/30 py-2 rounded-lg text-xs font-bold flex items-center justify-center gap-2 transition-colors cursor-pointer relative z-50">
              <Unlock className="w-3 h-3" /> Ganti Presenter
            </button>
          </div>
        )}
      </div>
    </div>
  )
}