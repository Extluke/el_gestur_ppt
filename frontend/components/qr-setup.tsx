"use client";

import { useState, useEffect } from "react";
import { QrCode, Smartphone, Wifi, ArrowLeft, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { StarfieldBG } from "./starfield-bg";

interface QRSetupProps {
  onBack: () => void;
  onDirectContinue: () => void;
}

export default function QRSetup({ onBack, onDirectContinue }: QRSetupProps) {
  const [ipAddress, setIpAddress] = useState("");
  const [showQr, setShowQr] = useState(false);

  // Otomatis deteksi IP kalau ngga pake localhost
  useEffect(() => {
    if (typeof window !== "undefined") {
      const hostname = window.location.hostname;
      if (hostname !== "localhost") {
        setIpAddress(hostname);
      }
    }
  }, []);

  const handleGenerate = () => {
    if (ipAddress) setShowQr(true);
  };

  // URL RAHASIA: Otomatis masuk ke mode mobile saat di-scan HP!
  // URL RAHASIA: Otomatis masuk ke mode mobile saat di-scan HP!
  const mobileUrl = `http://${ipAddress}:3000/#mobile`; // <--- UBAH INI DARI ?view=mobile JADI #mobile
  // const mobileUrl = `http://${ipAddress}:3000/?view=mobile`
  const qrCodeUrl = `https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${encodeURIComponent(mobileUrl)}`;

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-black relative p-4 overflow-hidden">
      <StarfieldBG />

      <div className="absolute -top-40 -right-40 w-80 h-80 bg-cyan-500/20 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 p-8 bg-slate-900/80 backdrop-blur-xl rounded-2xl border-2 border-cyan-500/50 max-w-md w-full text-center shadow-2xl shadow-cyan-500/20">
        {/* Tombol Back */}
        <button
          onClick={onBack}
          className="absolute top-4 left-4 p-2 hover:bg-white/10 rounded-lg transition-colors text-cyan-400"
        >
          <ArrowLeft className="w-6 h-6" />
        </button>

        <Smartphone className="w-16 h-16 text-cyan-400 mx-auto mb-4 mt-4 animate-bounce" />
        <h2 className="text-2xl font-bold text-transparent bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text mb-2">
          Koneksikan HP Bolo!
        </h2>

        <div className="flex items-center justify-center text-xs text-gray-400 mb-6 bg-slate-800/50 p-2 rounded-lg border border-yellow-500/30">
          <Wifi className="w-4 h-4 mr-2 text-yellow-400" />
          <span>Pastikan Laptop & HP di koneksi WiFi yang sama</span>
        </div>

        <div className="text-left mb-6">
          <label className="text-sm text-cyan-300 font-bold mb-2 block text-center">
            IP Address Laptop:
          </label>
          <Input
            placeholder="Contoh: 192.168.1.12"
            value={ipAddress}
            onChange={(e) => {
              setIpAddress(e.target.value);
              setShowQr(false);
            }}
            className="bg-slate-950 text-cyan-400 border-cyan-500/30 text-xl py-6 text-center tracking-widest font-mono"
          />
        </div>

        <Button
          onClick={handleGenerate}
          disabled={!ipAddress}
          className="w-full bg-cyan-600 hover:bg-cyan-500 text-white font-bold py-6 text-lg mb-6 shadow-lg shadow-cyan-500/20"
        >
          <QrCode className="w-6 h-6 mr-2" /> BUAT QR CODE
        </Button>

        {showQr && (
          <div className="animate-in zoom-in duration-300 flex flex-col items-center">
            <div className="p-4 bg-white rounded-xl inline-block border-4 border-cyan-400 mb-4">
              <img
                src={qrCodeUrl}
                alt="Scan QR"
                className="w-48 h-48 mx-auto"
              />
            </div>
            <p className="text-cyan-300 font-bold animate-pulse text-lg mb-6">
              Scan pake kamera HP sekarang!
            </p>
          </div>
        )}

        <div className="mt-4 pt-4 border-t border-slate-700/50">
          <Button
            variant="ghost"
            onClick={onDirectContinue}
            className="text-gray-400 hover:text-white w-full"
          >
            Abaikan & Buka di Laptop Saja{" "}
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      </div>
    </div>
  );
}
