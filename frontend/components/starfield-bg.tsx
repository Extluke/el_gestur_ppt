"use client";

import { useEffect, useRef } from "react";

export function StarfieldBG() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Set canvas size
    const setCanvasSize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    setCanvasSize();

    // Star particle system
    const stars: Array<{
      x: number;
      y: number;
      radius: number;
      opacity: number;
      twinkleDuration: number;
      twinkling: boolean;
      vx?: number;
      vy?: number;
      life?: number;
      maxLife?: number;
    }> = [];

    // Create stars
    const createStars = () => {
      stars.length = 0;
      const starCount = Math.floor((canvas.width * canvas.height) / 15000);
      for (let i = 0; i < starCount; i++) {
        stars.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          radius: Math.random() * 1.5,
          opacity: Math.random() * 0.5 + 0.3,
          twinkleDuration: Math.random() * 3 + 2,
          twinkling: Math.random() > 0.5,
        });
      }
    };
    createStars();

    let animationId: number;
    let time = 0;

    const animate = () => {
      // Clear canvas with dark background
      ctx.fillStyle = "rgba(8, 23, 42, 0.9)";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Add subtle gradient overlay
      const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
      gradient.addColorStop(0, "rgba(15, 23, 42, 0.3)");
      gradient.addColorStop(0.5, "rgba(8, 13, 32, 0)");
      gradient.addColorStop(1, "rgba(15, 23, 42, 0.3)");
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      time += 0.016; // ~60fps

      // Draw and update stars
      stars.forEach((star, index) => {
        let opacity = star.opacity;

        if (star.twinkling) {
          const twinkle =
            (Math.sin((time * (2 * Math.PI)) / star.twinkleDuration + index) +
              1) /
            2;
          opacity = star.opacity * (0.3 + twinkle * 0.7);
        }

        // Draw star with glow
        ctx.fillStyle = `rgba(34, 211, 238, ${opacity})`;
        ctx.beginPath();
        ctx.arc(star.x, star.y, star.radius, 0, Math.PI * 2);
        ctx.fill();

        // Add glow effect to some stars
        if (Math.random() > 0.95) {
          ctx.fillStyle = `rgba(34, 211, 238, ${opacity * 0.3})`;
          ctx.beginPath();
          ctx.arc(star.x, star.y, star.radius * 2.5, 0, Math.PI * 2);
          ctx.fill();
        }

        // Add some shooting stars occasionally
        if (Math.random() > 0.998) {
          star.vx = (Math.random() - 0.5) * 2;
          star.vy = (Math.random() - 0.5) * 2;
          star.life = 1;
          star.maxLife = 1;
        }

        if (star.life !== undefined && star.maxLife !== undefined) {
          star.life -= 0.01;
          if (star.life <= 0) {
            star.life = undefined;
            star.vx = undefined;
            star.vy = undefined;
          } else if (star.vx !== undefined && star.vy !== undefined) {
            star.x += star.vx;
            star.y += star.vy;

            // Draw shooting star trail
            ctx.strokeStyle = `rgba(34, 211, 238, ${(star.life * opacity) / 2})`;
            ctx.lineWidth = star.radius;
            ctx.lineCap = "round";
            ctx.beginPath();
            ctx.moveTo(
              star.x - (star.vx || 0) * 5,
              star.y - (star.vy || 0) * 5,
            );
            ctx.lineTo(star.x, star.y);
            ctx.stroke();
          }
        }
      });

      // Draw nebula-like effect
      for (let i = 0; i < 3; i++) {
        const nebulaX =
          (Math.sin(time * 0.001 + i) * canvas.width) / 2 + canvas.width / 2;
        const nebulaY =
          (Math.cos(time * 0.0008 + i * 2) * canvas.height) / 2 +
          canvas.height / 2;

        const nebulaGradient = ctx.createRadialGradient(
          nebulaX,
          nebulaY,
          0,
          nebulaX,
          nebulaY,
          300 + Math.sin(time * 0.002 + i) * 50,
        );
        nebulaGradient.addColorStop(
          0,
          `rgba(139, 92, 246, ${0.02 + Math.sin(time * 0.003) * 0.01})`,
        );
        nebulaGradient.addColorStop(
          0.5,
          `rgba(34, 211, 238, ${0.01 + Math.sin(time * 0.002) * 0.005})`,
        );
        nebulaGradient.addColorStop(1, "rgba(34, 211, 238, 0)");

        ctx.fillStyle = nebulaGradient;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
      }

      animationId = requestAnimationFrame(animate);
    };

    animate();

    const handleResize = () => {
      setCanvasSize();
      createStars();
    };

    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 w-full h-full pointer-events-none"
      style={{
        background:
          "linear-gradient(135deg, #0f172a 0%, #1a1a2e 50%, #0f172a 100%)",
        zIndex: 0,
      }}
    />
  );
}
