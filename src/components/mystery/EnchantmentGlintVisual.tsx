import {CanvasImage, staticFile, useCurrentFrame} from "remotion";

export const EnchantmentGlintVisual: React.FC<{
  assetSrc: string;
  supportingAsset?: string;
  size?: number;
  accentColor?: string;
  conceal?: boolean;
}> = ({assetSrc, supportingAsset, size = 180, accentColor = "#B46BFF", conceal = false}) => {
  const frame = useCurrentFrame();
  const progress = (frame % 72) / 72;
  const sweep = progress * 2.2 - 1.1;
  const breathe = 0.96 + Math.sin(frame / 14) * 0.025;
  const glow = 12 + Math.sin(frame / 11) * 3;
  const itemFilter = conceal
    ? `brightness(0) drop-shadow(0 8px 0 #02040A) drop-shadow(0 0 ${glow}px ${accentColor})`
    : `drop-shadow(0 8px 0 #02040A) drop-shadow(0 0 ${glow}px ${accentColor})`;
  return (
    <div style={{position: "relative", width: size * 1.45, height: size, display: "grid", placeItems: "center"}}>
      <div style={{position: "absolute", width: size * 1.02, height: size * 0.92, borderRadius: size * 0.16, background: `radial-gradient(circle at 62% 50%, ${accentColor}2A 0%, transparent 68%)`, filter: "blur(12px)", opacity: 0.7, transform: `scale(${breathe})`}} />
      {supportingAsset ? <div style={{position: "absolute", left: size * 0.01, width: size * 0.52, height: size * 0.62, display: "grid", placeItems: "center", borderRadius: size * 0.16, background: "radial-gradient(circle, #FFD16638 0%, transparent 70%)", boxShadow: "0 0 22px #FFD16644", transform: `translateY(${Math.sin(frame / 12) * 4}px)`}}><CanvasImage src={staticFile(supportingAsset)} style={{width: size * 0.54, height: size * 0.54, objectFit: "contain", imageRendering: "pixelated", opacity: 1, transform: `rotate(-8deg) scale(${1.03 + (breathe - 0.96) * 0.5})`, filter: "drop-shadow(0 7px 0 #02040A) drop-shadow(0 0 10px #FFD16688)"}} /></div> : null}
      <div style={{position: "absolute", left: size * 0.38, width: size * 0.78, height: size * 0.82, borderRadius: size * 0.16, background: `linear-gradient(145deg, ${accentColor}12, #0D1226E8 58%)`, border: `${size * 0.02}px solid ${accentColor}42`, boxShadow: `inset 0 0 0 ${size * 0.025}px #080C16AA, 0 0 ${glow}px ${accentColor}38`, transform: `scale(${breathe})`}} />
      <CanvasImage src={staticFile(assetSrc)} style={{position: "absolute", left: size * 0.43, width: size * 0.62, height: size * 0.62, objectFit: "contain", imageRendering: "pixelated", filter: itemFilter, transform: `translateY(${Math.sin(frame / 13) * 3}px) scale(${breathe})`}} />
      <div style={{position: "absolute", top: size * 0.12, left: `calc(50% + ${sweep * size * 0.34}px)`, width: size * 0.065, height: size * 0.64, borderRadius: 999, background: `linear-gradient(180deg, transparent, ${accentColor}66 45%, #FFFFFF88 50%, transparent)`, opacity: 0.34, filter: "blur(2px)", transform: "rotate(28deg)", boxShadow: `0 0 ${size * 0.07}px ${accentColor}55`}} />
    </div>
  );
};
