import os from "os";

// Fungsi buat ngeborong SEMUA IP yang ada di laptop lu
function getAllLocalIPs() {
  const ips = ["localhost"];
  const interfaces = os.networkInterfaces();

  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name]) {
      // Ambil semua IPv4 yang bukan jaringan internal
      if (iface.family === "IPv4" && !iface.internal) {
        ips.push(iface.address);
      }
    }
  }
  return ips;
}

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Masukin semua IP yang dapet + domain ngrok/localtunnel ke daftar putih
  allowedDevOrigins: [
    ...getAllLocalIPs(),
    "192.168.0.104", // Jaga-jaga kita masukin manual juga IP lu yang sekarang
    ".ngrok-free.app",
    ".ngrok.app",
    ".loca.lt",
  ],
};

export default nextConfig;
