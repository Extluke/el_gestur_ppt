'use client'

import { useState, useEffect } from 'react'
import LobbyPage from '@/components/lobby-page'
import DashboardCompanion from '@/components/dashboard-companion'
import FloatingWidget from '@/components/floating-widget'
import ClassicMode from '@/components/classic-mode'
import QRSetup from '@/components/qr-setup'

type ViewType = 'lobby' | 'qr-setup' | 'mobile' | 'widget' | 'classic'

export default function Home() {
  const [currentView, setCurrentView] = useState<ViewType>('lobby')

  const getApiUrl = () => {
    if (typeof window !== 'undefined') {
      return `http://${window.location.hostname}:5000`
    }
    return ''
  }

  // OTOMATIS NYALA PAS HP NGE-SCAN QR CODE
  useEffect(() => {
    if (typeof window !== 'undefined' && window.location.hash === '#mobile') {
      fetch(`${getApiUrl()}/start`, { method: 'POST' }).catch(() => {})
      setCurrentView('mobile')
    }
  }, [])

  // OTOMATIS NYALA PAS KLIK KARTU MODE DI LOBBY
  const handleSelectMode = (mode: 'mobile' | 'widget' | 'classic') => {
    fetch(`${getApiUrl()}/start`, { method: 'POST' }).catch(() => {})
    
    if (mode === 'mobile') setCurrentView('qr-setup')
    else setCurrentView(mode)
  }

  // OTOMATIS MATIIN AI PAS KELUAR KE LOBBY
  const handleBack = () => {
    fetch(`${getApiUrl()}/stop`, { method: 'POST' }).catch(() => {})
    
    setCurrentView('lobby')
    if (typeof window !== 'undefined') {
      window.history.pushState(null, '', window.location.pathname)
    }
  }

  return (
    <div className="relative z-10 w-full min-h-screen">
      {currentView === 'lobby' && <LobbyPage onSelectMode={handleSelectMode} />}
      {currentView === 'qr-setup' && (
        <QRSetup onBack={handleBack} onDirectContinue={() => setCurrentView('mobile')} />
      )}
      {currentView === 'mobile' && <DashboardCompanion onBack={handleBack} />}
      {currentView === 'widget' && (
        <div className="min-h-screen bg-gradient-to-b from-slate-950 via-blue-950 to-slate-950 p-8">
          <button onClick={handleBack} className="fixed top-4 left-4 z-50 px-4 py-2 bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 rounded-lg transition-colors text-sm font-semibold cursor-pointer">
            ← Kembali ke Lobby
          </button>
          <div className="pt-12 text-center text-gray-400 max-w-2xl mx-auto relative z-40">
            <h2 className="text-2xl font-bold text-cyan-300 mb-4">Widget Mode Preview</h2>
          </div>
          <FloatingWidget onClose={handleBack} />
        </div>
      )}
      {currentView === 'classic' && <ClassicMode onBack={handleBack} />}
    </div>
  )
}