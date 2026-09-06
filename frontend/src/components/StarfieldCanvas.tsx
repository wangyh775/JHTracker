import React, { useEffect, useRef } from 'react';

interface StarfieldCanvasProps {
  particleCount?: number;
}

interface Particle {
  x: number;
  y: number;
  size: number;
  speedX: number;
  speedY: number;
  opacity: number;
  pulseSpeed: number;
  color: string;
}

export const StarfieldCanvas: React.FC<StarfieldCanvasProps> = ({ particleCount = 140 }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    const colors = ['#00f2ff', '#38bdf8', '#818cf8', '#c084fc', '#ffffff'];

    // Initialize particles
    const particles: Particle[] = Array.from({ length: particleCount }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      size: Math.random() * 1.8 + 0.5,
      speedX: (Math.random() - 0.5) * 0.35,
      speedY: (Math.random() - 0.5) * 0.35,
      opacity: Math.random() * 0.7 + 0.2,
      pulseSpeed: Math.random() * 0.02 + 0.005,
      color: colors[Math.floor(Math.random() * colors.length)],
    }));

    // Interactive mouse parallax glow
    let mouseX = width / 2;
    let mouseY = height / 2;
    const handleMouseMove = (e: MouseEvent) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
    };
    window.addEventListener('mousemove', handleMouseMove);

    // Shooting stars
    interface ShootingStar {
      x: number;
      y: number;
      len: number;
      speed: number;
      angle: number;
      opacity: number;
    }
    const shootingStars: ShootingStar[] = [];

    const maybeSpawnShootingStar = () => {
      if (Math.random() < 0.015 && shootingStars.length < 3) {
        shootingStars.push({
          x: Math.random() * width,
          y: Math.random() * (height / 2),
          len: Math.random() * 80 + 40,
          speed: Math.random() * 8 + 6,
          angle: (Math.PI / 4) + (Math.random() - 0.5) * 0.2,
          opacity: 1,
        });
      }
    };

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      // 1. Draw connecting nebulae lines between close particles
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 95) {
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(56, 189, 248, ${0.12 * (1 - dist / 95)})`;
            ctx.lineWidth = 0.6;
            ctx.stroke();
          }
        }
      }

      // 2. Draw stars
      particles.forEach((p) => {
        p.x += p.speedX;
        p.y += p.speedY;

        // Wrap edges
        if (p.x < 0) p.x = width;
        if (p.x > width) p.x = 0;
        if (p.y < 0) p.y = height;
        if (p.y > height) p.y = 0;

        // Twinkle pulse
        p.opacity += Math.sin(Date.now() * p.pulseSpeed) * 0.012;
        const currentOpacity = Math.max(0.15, Math.min(0.95, p.opacity));

        // Draw star dot
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.globalAlpha = currentOpacity;
        ctx.shadowBlur = p.size > 1.2 ? 8 : 0;
        ctx.shadowColor = p.color;
        ctx.fill();
        ctx.globalAlpha = 1;
        ctx.shadowBlur = 0;
      });

      // 3. Draw shooting stars
      maybeSpawnShootingStar();
      for (let i = shootingStars.length - 1; i >= 0; i--) {
        const s = shootingStars[i];
        s.x += Math.cos(s.angle) * s.speed;
        s.y += Math.sin(s.angle) * s.speed;
        s.opacity -= 0.015;

        if (s.opacity <= 0 || s.x > width || s.y > height) {
          shootingStars.splice(i, 1);
          continue;
        }

        const tailX = s.x - Math.cos(s.angle) * s.len;
        const tailY = s.y - Math.sin(s.angle) * s.len;

        const grad = ctx.createLinearGradient(tailX, tailY, s.x, s.y);
        grad.addColorStop(0, 'rgba(0, 242, 255, 0)');
        grad.addColorStop(1, `rgba(255, 255, 255, ${s.opacity})`);

        ctx.beginPath();
        ctx.moveTo(tailX, tailY);
        ctx.lineTo(s.x, s.y);
        ctx.strokeStyle = grad;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      // 4. Subtle mouse radial aura
      const auraGrad = ctx.createRadialGradient(mouseX, mouseY, 10, mouseX, mouseY, 320);
      auraGrad.addColorStop(0, 'rgba(6, 182, 212, 0.05)');
      auraGrad.addColorStop(1, 'rgba(6, 182, 212, 0)');
      ctx.fillStyle = auraGrad;
      ctx.fillRect(0, 0, width, height);

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      cancelAnimationFrame(animationFrameId);
    };
  }, [particleCount]);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full pointer-events-none z-[1]"
    />
  );
};
