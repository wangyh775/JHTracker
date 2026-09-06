import React, { useState } from 'react';
import Spline from '@splinetool/react-spline';
import { Sparkles, Compass, ShieldCheck } from 'lucide-react';

interface SplineHeaderProps {
  totalJobs: number;
  totalCompanies: number;
}

export const SplineHeader: React.FC<SplineHeaderProps> = ({ totalJobs, totalCompanies }) => {
  const [hasError, setHasError] = useState(false);
  const [loaded, setLoaded] = useState(false);

  return (
    <div className="relative w-full h-[120px] md:h-[135px] rounded-xl overflow-hidden border border-cyan-500/20 bg-gradient-to-br from-[#0c0e18] via-[#111322] to-[#171530] shadow-xl mb-3">
      {/* 3D Spline Background Canvas */}
      {!hasError && (
        <div className="absolute inset-0 z-0 pointer-events-auto opacity-70 hover:opacity-100 transition-opacity duration-700">
          <Spline
            scene="https://prod.spline.design/6Wq1Q7YGyM-iab9i/scene.splinecode"
            onLoad={() => setLoaded(true)}
            onError={() => setHasError(true)}
          />
        </div>
      )}

      {/* Cyber Grid Pattern Fallback */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1f293d15_1px,transparent_1px),linear-gradient(to_bottom,#1f293d15_1px,transparent_1px)] bg-[size:2rem_2rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] pointer-events-none" />

      {/* Glow Orbs */}
      <div className="absolute -top-12 -left-12 w-48 h-48 bg-cyan-500/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-12 -right-12 w-48 h-48 bg-purple-500/15 rounded-full blur-3xl pointer-events-none" />

      {/* Foreground Content Overlay */}
      <div className="relative z-10 h-full flex flex-col justify-between p-4 md:px-6 md:py-3.5 pointer-events-none">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-cyan-950/60 border border-cyan-500/30 backdrop-blur-md">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
            <span className="text-[11px] font-mono text-cyan-300 tracking-wider">
              CYBER ENGINE • 实时全网校招数据流
            </span>
          </div>

          <div className="flex items-center gap-3 text-xs font-mono">
            <div className="px-2.5 py-0.5 rounded bg-black/40 border border-slate-700/60 backdrop-blur-md flex items-center gap-1.5">
              <span className="text-gray-400">已收录企业</span>
              <span className="text-cyan-400 font-bold">{totalCompanies.toLocaleString()}</span>
            </div>
            <div className="px-2.5 py-0.5 rounded bg-black/40 border border-slate-700/60 backdrop-blur-md flex items-center gap-1.5">
              <span className="text-gray-400">在招岗位数</span>
              <span className="text-purple-400 font-bold">{totalJobs.toLocaleString()}</span>
            </div>
          </div>
        </div>

        <div className="flex items-baseline justify-between gap-4">
          <div>
            <h1 className="text-xl md:text-2xl font-black tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-white via-cyan-100 to-cyan-400 drop-shadow-md">
              校招网申大厅
            </h1>
            <p className="text-[11px] text-gray-300/80">
              实时汇聚全网校招与应届生招聘信息，支持企业与岗位双列锁定、一键直达投递、内推码复制与私有看板追踪。
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
