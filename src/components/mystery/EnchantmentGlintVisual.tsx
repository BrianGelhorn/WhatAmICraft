import {CanvasImage, staticFile, useCurrentFrame} from "remotion";

export const EnchantmentGlintVisual: React.FC<{
  assetSrc: string;
  supportingAsset?: string;
  size?: number;
  accentColor?: string;
  conceal?: boolean;
}> = ({assetSrc, supportingAsset, size = 180, accentColor = "#B46BFF", conceal = false}) => {
  const frame = useCurrentFrame();
  const cycle = frame % 72;
  const travel = Math.max(0, Math.min(1, (cycle - 4) / 18));
  const impact = Math.max(0, Math.min(1, (cycle - 22) / 5));
  const aura = Math.max(0, Math.min(1, (cycle - 27) / 15));
  const sweep = Math.max(0, Math.min(1, (cycle - 37) / 25)) * 2.2 - 1.1;
  const breathe = 0.98 + Math.sin(cycle / 14) * 0.02;
  const glow = 10 + aura * 12;
  const travelEase = 1 - Math.pow(1 - travel, 3);
  const bookOpacity = cycle >= 27 ? Math.max(0, 1 - (cycle - 27) / 7) : 1;
  const bookLeft = size * (0.98 - travelEase * 0.62);
  const bookRotation = -8 - travelEase * 24;
  const swordShake = impact > 0 && impact < 1 ? Math.sin(cycle * 3.5) * size * 0.025 * (1 - impact) : 0;
  const swordLeft = size * (0.12 + aura * 0.36) + swordShake;
  const auraLeft = size * (0.02 + aura * 0.36);
  const itemFilter = conceal
    ? `brightness(0) drop-shadow(0 8px 0 #02040A) drop-shadow(0 0 ${glow * aura}px ${accentColor})`
    : `drop-shadow(0 8px 0 #02040A) drop-shadow(0 0 ${glow * aura}px ${accentColor})`;
  return (
    <div style={{position: "relative", width: size * 1.65, height: size, display: "grid", placeItems: "center"}}>
      <div style={{position: "absolute", left: auraLeft, width: size * 0.82, height: size * 0.82, borderRadius: "50%", background: `radial-gradient(circle, ${accentColor}48 0%, ${accentColor}18 42%, transparent 72%)`, filter: "blur(12px)", opacity: aura * 0.82, transform: `scale(${breathe})`}} />
      {supportingAsset ? <CanvasImage src={staticFile(supportingAsset)} style={{position: "absolute", left: bookLeft, width: size * 0.52, height: size * 0.52, objectFit: "contain", imageRendering: "pixelated", opacity: bookOpacity, transform: `translateY(${Math.sin(cycle / 12) * 4}px) rotate(${bookRotation}deg) scale(${1.03 + (breathe - 0.98) * 0.5})`, filter: "drop-shadow(0 7px 0 #02040A)"}} /> : null}
      <CanvasImage src={staticFile(assetSrc)} style={{position: "absolute", left: swordLeft, width: size * 0.68, height: size * 0.68, objectFit: "contain", imageRendering: "pixelated", filter: itemFilter, transform: `translateY(${Math.sin(cycle / 13) * 3}px) scale(${breathe + impact * 0.08})`}} />
      {impact > 0 && impact < 1 ? <div style={{position: "absolute", left: size * 0.37, top: size * 0.44, width: size * (0.12 + impact * 0.55), height: size * (0.12 + impact * 0.55), borderRadius: "50%", border: `${size * 0.025}px solid ${accentColor}`, opacity: 1 - impact, boxShadow: `0 0 ${size * 0.12}px ${accentColor}`}} /> : null}
      {aura > 0 ? <div style={{position: "absolute", top: size * 0.12, left: `calc(50% + ${sweep * size * 0.34}px)`, width: size * 0.065, height: size * 0.64, borderRadius: 999, background: `linear-gradient(180deg, transparent, ${accentColor}66 45%, #FFFFFF88 50%, transparent)`, opacity: aura * 0.34, filter: "blur(2px)", transform: "rotate(28deg)", boxShadow: `0 0 ${size * 0.07}px ${accentColor}55`}} /> : null}
    </div>
  );
};
