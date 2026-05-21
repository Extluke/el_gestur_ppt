'use client'

import { useState } from 'react'
import { MonitorPlay, Smartphone, Box, Terminal, Presentation, Figma, Layout, BookOpen } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface LobbyPageProps {
  onSelectMode: (mode: 'mobile' | 'widget' | 'classic') => void
}

export default function LobbyPage({ onSelectMode }: LobbyPageProps) {
  // Simpan state software yang dipilih (Default: ppt)
  const [selectedSoftware, setSelectedSoftware] = useState<string>('ppt')
  const [isUpdating, setIsUpdating] = useState(false)

  const softwareOptions = [
    { id: 'ppt', name: 'PowerPoint', icon: Presentation, color: 'text-orange-500', border: 'border-orange-500/50' },
    { id: 'canva', name: 'Canva', icon: MonitorPlay, color: 'text-cyan-400', border: 'border-cyan-400/50' },
    { id: 'figma', name: 'Figma', icon: Figma, color: 'text-pink-500', border: 'border-pink-500/50' },
    { id: 'notion', name: 'Notion', icon: BookOpen, color: 'text-gray-300', border: 'border-gray-300/50' },
  ]

  const modes = [
    {
      id: 'mobile',
      title: 'Mobile Companion',
      description: 'Gunakan HP sebagai remote & monitor AI.',
      icon: Smartphone,
      color: 'from-cyan-400 to-blue-500',
      shadow: 'shadow-cyan-500/20'
    },
    {
      id: 'widget',
      title: 'Floating Widget',
      description: 'Widget transparan saat layar presentasi di laptop.',
      icon: Layout,
      color: 'from-violet-400 to-purple-500',
      shadow: 'shadow-purple-500/20'
    },
    {
      id: 'classic',
      title: 'Classic Mode',
      description: 'Dashboard penuh kontrol (tanpa CCTV webcam).',
      icon: Terminal,
      color: 'from-green-400 to-emerald-500',
      shadow: 'shadow-green-500/20'
    }
  ]

  const handleSelectMode = async (modeId: 'mobile' | 'widget' | 'classic') => {
    setIsUpdating(true)
    try {
      // 1. Kasih tau Python software apa yang dipake
      const hostUrl = typeof window !== 'undefined' ? `http://${window.location.hostname}:5000` : ''
      await fetch(`${hostUrl}/set_software`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ software: selectedSoftware })
      })
      
      // 2. Lanjut ke mode yang dipilih
      onSelectMode(modeId)
    } catch (e) {
      console.error("Gagal nyambung ke server Python", e)
      onSelectMode(modeId) // Tetap lanjut walau error (buat testing web)
    }
    setIsUpdating(false)
  }

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center p-4 relative overflow-hidden">
      
      {/* Background Effects */}
      <div className="absolute inset-0 z-0">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />
      </div>

      <div className="relative z-50 w-full max-w-5xl space-y-12">
        
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="inline-flex items-center justify-center p-3 rounded-2xl bg-slate-900 border border-slate-800 mb-4">
            <Box className="w-8 h-8 text-cyan-400" />
          </div>
          <h1 className="text-4xl md:text-5xl font-black text-transparent bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400 bg-clip-text tracking-tight">
            EL PRESENTASI
          </h1>
          <p className="text-slate-400 text-lg md:text-xl max-w-2xl mx-auto">
            Universal AI Presentation Controller
          </p>
        </div>

        {/* 🚨 TAHAP 1 DARI FLOW: PILIH SOFTWARE */}
        <div className="space-y-4">
          <h2 className="text-center text-sm font-bold text-gray-400 tracking-widest uppercase">
            1. Pilih Software Presentasi
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-3xl mx-auto">
            {softwareOptions.map((app) => {
              const Icon = app.icon
              const isSelected = selectedSoftware === app.id
              return (
                <button
                  key={app.id}
                  onClick={() => setSelectedSoftware(app.id)}
                  className={`relative p-4 rounded-xl flex flex-col items-center gap-3 transition-all duration-300 cursor-pointer overflow-hidden ${
                    isSelected 
                    ? `bg-slate-900 border-2 ${app.border} shadow-lg shadow-black/50 scale-105` 
                    : 'bg-slate-900/50 border-2 border-transparent hover:bg-slate-800'
                  }`}
                >
                  {/* Efek nyala kalau dipilih */}
                  {isSelected && <div className={`absolute inset-0 bg-gradient-to-b from-transparent to-${app.color.split('-')[1]}-500/10`} />}
                  <Icon className={`w-8 h-8 ${isSelected ? app.color : 'text-gray-500'}`} />
                  <span className={`font-bold ${isSelected ? 'text-white' : 'text-gray-400'}`}>
                    {app.name}
                  </span>
                </button>
              )
            })}
          </div>
        </div>

        {/* 🚨 TAHAP 2 DARI FLOW: PILIH MODE */}
        <div className="space-y-4 pt-8 border-t border-slate-800">
          <h2 className="text-center text-sm font-bold text-gray-400 tracking-widest uppercase">
            2. Pilih Mode Kontrol
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {modes.map((mode) => {
              const Icon = mode.icon
              return (
                <div key={mode.id} className="relative group/card cursor-pointer">
                  <div className={`absolute inset-0 bg-gradient-to-br ${mode.color} rounded-2xl blur-xl opacity-0 group-hover/card:opacity-20 transition-opacity duration-500`} />
                  <div className="relative h-full p-6 rounded-2xl bg-slate-900 border border-slate-800 hover:border-slate-700 flex flex-col items-center text-center transition-all duration-300">
                    <div className={`w-16 h-16 rounded-2xl bg-slate-950 border border-slate-800 flex items-center justify-center mb-6 shadow-lg ${mode.shadow}`}>
                      <Icon className="w-8 h-8 text-white" />
                    </div>
                    <h3 className="text-xl font-bold text-white mb-3">{mode.title}</h3>
                    <p className="text-slate-400 text-sm mb-8 flex-1">{mode.description}</p>
                    
                    <Button
                      onClick={() => handleSelectMode(mode.id as 'mobile' | 'widget' | 'classic')}
                      disabled={isUpdating}
                      className={`w-full py-6 font-bold text-white bg-gradient-to-r ${mode.color} hover:opacity-90 shadow-lg ${mode.shadow} rounded-xl border-0 pointer-events-auto z-50`}
                    >
                      {isUpdating ? 'MENYIAPKAN...' : 'PILIH MODE'}
                    </Button>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

      </div>
    </div>
  )
}