import {CanvasImage, staticFile, useCurrentFrame} from "remotion";

const clamp01 = (value: number) => Math.max(0, Math.min(1, value));
const easeOut = (value: number) => 1 - Math.pow(1 - clamp01(value), 3);

export const CooldownVisual: React.FC<{
  assetSrc: string;
  size?: number;
  chargingColor?: string;
  readyColor?: string;
}> = ({assetSrc, size = 180, chargingColor = "#FF6B35", readyColor = "#6BFF95"}) => {
  const cycle = useCurrentFrame() % 96;
  const charging = easeOut((cycle - 12) / 38);
  const ready = cycle >= 50 && cycle < 62 ? 1 : 0;
  const useProgress = clamp01((cycle - 62) / 9);
  const reset = clamp01((cycle - 71) / 7);
  const progress = cycle < 12 ? 0 : cycle < 50 ? charging : cycle < 62 ? 1 : cycle < 71 ? 1 - useProgress * 0.15 : 1 - reset;
  const inUse = useProgress > 0 && useProgress < 1;
  const color = ready || inUse ? readyColor : chargingColor;
  const label = ready ? "READY" : inUse ? "USE!" : "WAIT";
  const labelColor = ready || inUse ? readyColor : chargingColor;
  const iconScale = inUse ? 1 + useProgress * 0.16 : 0.94 + progress * 0.06;
  const iconShift = inUse ? Math.sin(useProgress * Math.PI) * -size * 0.08 : 0;
  return (
    <div style={{position: "relative", width: size * 1.35, height: size * 1.35, display: "grid", placeItems: "center"}}>
      <div style={{position: "absolute", width: size * 1.08, height: size * 1.08, borderRadius: "50%", background: `radial-gradient(circle, ${color}28 0%, transparent 70%)`, filter: "blur(10px)", opacity: 0.75}} />
      <div style={{position: "absolute", width: size, height: size, borderRadius: "50%", background: `conic-gradient(${color} ${progress * 360}deg, #26324C ${progress * 360}deg)`, boxShadow: `0 0 ${size * 0.16}px ${color}66`, transform: `rotate(-90deg) scale(${0.98 + ready * 0.04})`}} />
      <div style={{position: "absolute", width: size * 0.82, height: size * 0.82, borderRadius: "50%", background: "#10172B", boxShadow: "inset 0 0 0 5px #080C16"}} />
      <CanvasImage src={staticFile(assetSrc)} style={{position: "absolute", width: size * 0.62, height: size * 0.62, objectFit: "contain", imageRendering: "pixelated", opacity: 0.5 + progress * 0.5, filter: `drop-shadow(0 8px 0 #02040A) drop-shadow(0 0 ${ready || inUse ? size * 0.14 : 0}px ${readyColor})`, transform: `translateY(${iconShift}px) scale(${iconScale})`}} />
      <div style={{position: "absolute", left: size * 0.12, bottom: size * 0.04, width: size * 0.96, height: size * 0.11, padding: size * 0.018, borderRadius: 999, background: "#080C16", border: `${size * 0.014}px solid #02040A`, boxSizing: "border-box"}}><div style={{width: `${progress * 100}%`, height: "100%", borderRadius: 999, background: color, boxShadow: `0 0 ${size * 0.07}px ${color}`}} /></div>
      <div style={{position: "absolute", bottom: -size * 0.2, color: labelColor, fontSize: size * 0.17, letterSpacing: 3, fontWeight: 800, textShadow: "0 4px 0 #02040A"}}>{label}</div>
      {inUse ? <div style={{position: "absolute", width: size * (0.34 + useProgress * 0.3), height: size * (0.34 + useProgress * 0.3), borderRadius: "50%", border: `${size * 0.025}px solid ${readyColor}`, opacity: 1 - useProgress, boxShadow: `0 0 ${size * 0.1}px ${readyColor}`}} /> : null}
    </div>
  );
};
