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
  const glow = 18 + Math.sin(frame / 11) * 5;
  const itemFilter = conceal
    ? `brightness(0) drop-shadow(0 8px 0 #02040A) drop-shadow(0 0 ${glow}px ${accentColor})`
    : `drop-shadow(0 8px 0 #02040A) drop-shadow(0 0 ${glow}px ${accentColor})`;
  return (
    <div style={{position: "relative", width: size * 1.45, height: size, display: "grid", placeItems: "center"}}>
      <div style={{position: "absolute", width: size * 1.08, height: size * 1.08, borderRadius: "50%", background: `radial-gradient(circle, ${accentColor}55 0%, ${accentColor}1C 42%, transparent 74%)`, filter: "blur(10px)", opacity: 0.82, transform: `scale(${breathe})`}} />
      {supportingAsset ? <CanvasImage src={staticFile(supportingAsset)} style={{position: "absolute", left: 0, width: size * 0.42, height: size * 0.42, objectFit: "contain", imageRendering: "pixelated", opacity: 0.9, transform: `translateY(${Math.sin(frame / 12) * 4}px) rotate(-10deg) scale(${breathe})`, filter: `drop-shadow(0 7px 0 #02040A) drop-shadow(0 0 ${size * 0.06}px ${accentColor}66)`}} /> : null}
      <div style={{position: "absolute", width: size * 0.9, height: size * 0.9, borderRadius: size * 0.3, background: `linear-gradient(145deg, ${accentColor}20, #0D1226CC 58%)`, border: `${size * 0.028}px solid ${accentColor}66`, boxShadow: `inset 0 0 0 ${size * 0.025}px #080C16AA, 0 0 ${glow * 1.4}px ${accentColor}55`, transform: `scale(${breathe})`}} />
      <CanvasImage src={staticFile(assetSrc)} style={{width: size * 0.72, height: size * 0.72, objectFit: "contain", imageRendering: "pixelated", filter: itemFilter, transform: `translateY(${Math.sin(frame / 13) * 3}px) scale(${breathe})`}} />
      <div style={{position: "absolute", top: size * 0.12, left: `calc(50% + ${sweep * size * 0.36}px)`, width: size * 0.085, height: size * 0.66, borderRadius: 999, background: `linear-gradient(180deg, transparent, ${accentColor}99 45%, #FFFFFFAA 50%, transparent)`, opacity: 0.48, filter: "blur(2px)", transform: "rotate(28deg)", boxShadow: `0 0 ${size * 0.1}px ${accentColor}88`}} />
    </div>
  );
};
