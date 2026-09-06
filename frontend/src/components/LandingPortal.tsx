import React, { useState, useRef, lazy, Suspense } from 'react';
import type { Application } from '@splinetool/runtime';
import { ArrowRight, Sparkles } from 'lucide-react';
import { StarfieldCanvas } from './StarfieldCanvas';

const Spline = lazy(() => import('@splinetool/react-spline').then((m) => ({ default: m.default })));

interface LandingPortalProps {
  isOpen: boolean;
  totalJobs: number;
  totalCompanies: number;
  onEnterWorkspace: () => void;
}

// Custom Cyber Logo Mark
const JHTrackerLogo: React.FC<{ size?: number }> = ({ size = 42 }) => (
  <div
    className="relative flex items-center justify-center rounded-2xl bg-gradient-to-br from-[#0c1322] via-[#080d19] to-[#04060c] border border-cyan-500/50 shadow-[0_0_25px_rgba(6,182,212,0.35)] overflow-hidden group"
    style={{ width: size, height: size }}
  >
    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-400/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
    <svg width={size * 0.58} height={size * 0.58} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-cyan-400 drop-shadow-[0_0_10px_rgba(6,182,212,0.8)]">
      <path d="M12 2L2 7l10 5 10-5-10-5z" />
      <path d="M2 17l10 5 10-5" />
      <path d="M2 12l10 5 10-5" />
    </svg>
    <span className="absolute bottom-1 right-1 w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse shadow-[0_0_6px_#22d3ee]" />
  </div>
);

export const LandingPortal: React.FC<LandingPortalProps> = ({
  isOpen,
  totalJobs,
  totalCompanies,
  onEnterWorkspace,
}) => {
  const [loaded, setLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [sceneUrl, setSceneUrl] = useState('/robot_scene.splinecode');
  const splineAppRef = useRef<Application | null>(null);

  const handleSplineLoad = (splineApp: Application) => {
    splineAppRef.current = splineApp;
    setLoaded(true);

    try {
      // Find objects and adjust their head / base rotations
      const head = splineApp.findObjectByName('Head');
      if (head) {
        // Lift the head upward by reducing negative tilt and adding positive X rotation
        head.rotation.x = 0.15;
      }
      const topPart = splineApp.findObjectByName('Top part');
      if (topPart) {
        topPart.rotation.x = 0.1;
      }
    } catch (e) {
      console.warn('Spline adjust note:', e);
    }
  };

  return (
    <div
      className={`fixed inset-0 z-50 overflow-hidden bg-[#040508] transition-all duration-700 ease-[cubic-bezier(0.16,1,0.3,1)] ${
        isOpen
          ? 'translate-y-0 opacity-100 pointer-events-auto'
          : '-translate-y-full opacity-0 pointer-events-none'
      }`}
    >
      {/* 1. Deep Space Starfield & Cosmic Nebula (qiuzhifangzhou.com style) */}
      <div className="absolute inset-0 z-[1] pointer-events-none">
        <StarfieldCanvas />
      </div>

      {/* 2. Loading State */}
      {!loaded && !hasError && (
        <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-[#040508]/80 backdrop-blur-md">
          <div className="relative flex items-center justify-center w-20 h-20">
            <div className="absolute inset-0 rounded-full border-2 border-cyan-500/30 border-t-cyan-400 animate-spin" />
            <JHTrackerLogo size={42} />
          </div>
          <span className="mt-4 text-xs font-mono text-cyan-400/80 tracking-widest animate-pulse">
            LOADING 3D NEURAL CORE...
          </span>
        </div>
      )}

      {/* 3. Spline 3D Robot Scene (Using fine-tuned eye-level camera scene) */}
      {!hasError && (
        <div 
          className="absolute inset-0 z-[2] pointer-events-auto flex items-center justify-center overflow-hidden"
          style={{
            // Container centered directly on screen, no downward shift to avoid clipping
            transform: 'scale(1.05)',
            transformOrigin: 'center center',
          }}
        >
          <Suspense fallback={null}>
            <Spline
              scene={sceneUrl}
              onLoad={handleSplineLoad}
              onError={() => {
                if (sceneUrl !== 'https://prod.spline.design/kZDDjO5HuC9GJUM2/scene.splinecode') {
                  setSceneUrl('https://prod.spline.design/kZDDjO5HuC9GJUM2/scene.splinecode');
                } else {
                  setHasError(true);
                }
              }}
              className="w-full h-full"
            />
          </Suspense>
        </div>
      )}

      {/* 4. Subtle Vignette (Blends seamlessly with deep space without obscuring center) */}
      <div className="absolute inset-0 z-[3] bg-[radial-gradient(circle_at_center,transparent_45%,rgba(4,5,8,0.7)_85%,rgba(4,5,8,0.98)_100%)] pointer-events-none" />

      {/* Atmospheric Nebula Glows */}
      <div className="absolute top-1/4 left-1/5 w-[500px] h-[300px] bg-cyan-500/10 rounded-full blur-[140px] pointer-events-none z-[3]" />
      <div className="absolute bottom-1/4 right-1/5 w-[500px] h-[300px] bg-indigo-600/12 rounded-full blur-[150px] pointer-events-none z-[3]" />

      {/* 5. TOP-LEFT LOGO & BRAND (Out of the way of the robot's face in the center!) */}
      <header className="absolute top-6 left-8 z-20 flex items-center gap-3.5 select-none pointer-events-auto">
        <JHTrackerLogo size={44} />
        <div className="flex flex-col">
          <div className="flex items-center gap-2">
            <span className="text-2xl font-black tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-white via-cyan-100 to-cyan-400 drop-shadow-[0_2px_10px_rgba(6,182,212,0.4)]">
              JHTracker
            </span>
            <span className="px-2 py-0.5 text-[10px] font-mono font-semibold tracking-wider text-cyan-300 bg-cyan-950/70 border border-cyan-500/40 rounded-full">
              v0.1.1
            </span>
          </div>
          <span className="text-xs text-slate-400 font-medium tracking-wide">
            本地 AI 智能求职求贤追踪与推荐平台
          </span>
        </div>
      </header>

      {/* 6. TOP-RIGHT LIVE STATS BADGE */}
      <div className="absolute top-6 right-8 z-20 select-none pointer-events-auto hidden sm:flex items-center gap-2.5 px-4 py-2 rounded-full bg-[#0a0f1d]/80 border border-cyan-500/40 backdrop-blur-md shadow-[0_0_20px_rgba(6,182,212,0.25)]">
        <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
        <span className="text-xs font-mono text-cyan-300 tracking-wider font-semibold">
          收录 {totalCompanies.toLocaleString()} 名企 · {totalJobs.toLocaleString()} 在招岗位
        </span>
      </div>

      {/* 7. BOTTOM CENTER FLOATING CTA (Completely unobscured robot view!) */}
      <div className="absolute bottom-12 left-0 right-0 z-20 flex flex-col items-center justify-center pointer-events-none select-none px-4">
        {/* The Single High-Voltage CTA Button */}
        <div className="pointer-events-auto transform hover:scale-105 transition-all duration-300">
          <button
            onClick={onEnterWorkspace}
            className="group relative flex items-center gap-4 px-10 py-4 md:px-12 md:py-4.5 rounded-2xl font-bold text-base md:text-lg text-black bg-gradient-to-r from-cyan-400 via-cyan-300 to-cyan-400 hover:from-cyan-300 hover:to-cyan-200 transition-all duration-300 shadow-[0_0_35px_rgba(6,182,212,0.6)] hover:shadow-[0_0_65px_rgba(6,182,212,0.9)] active:scale-[0.98] cursor-pointer"
          >
            <Sparkles className="w-5 h-5 text-black animate-pulse" />
            <span>进入工作台</span>
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1.5 transition-transform" />
          </button>
        </div>
        <p className="mt-3.5 text-xs font-mono text-cyan-200/60 tracking-wider">
          CLICK OR SCROLL TO ENTER WORKSPACE
        </p>
      </div>
    </div>
  );
};
