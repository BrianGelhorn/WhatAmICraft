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
    <div style={{position: "relative", width: size * 1.65, height: size, display: "grid", placeItems: "center"}}>
      <div style={{position: "absolute", left: size * 0.02, width: size * 0.82, height: size * 0.82, borderRadius: "50%", background: `radial-gradient(circle, ${accentColor}48 0%, ${accentColor}18 42%, transparent 72%)`, filter: "blur(12px)", opacity: 0.8, transform: `scale(${breathe})`}} />
      {supportingAsset ? <><div style={{position: "absolute", left: size * 0.92, width: size * 0.68, height: size * 0.68, borderRadius: "50%", background: `radial-gradient(circle, ${accentColor}55 0%, ${accentColor}1C 44%, transparent 72%)`, filter: "blur(10px)", opacity: 0.88, transform: `scale(${breathe})`}} /><CanvasImage src={staticFile(supportingAsset)} style={{position: "absolute", left: size * 0.98, width: size * 0.52, height: size * 0.52, objectFit: "contain", imageRendering: "pixelated", opacity: 1, transform: `translateY(${Math.sin(frame / 12) * 4}px) rotate(-8deg) scale(${1.03 + (breathe - 0.96) * 0.5})`, filter: `drop-shadow(0 7px 0 #02040A) drop-shadow(0 0 ${size * 0.1}px ${accentColor})`}} /></> : null}
      <CanvasImage src={staticFile(assetSrc)} style={{position: "absolute", left: size * 0.12, width: size * 0.68, height: size * 0.68, objectFit: "contain", imageRendering: "pixelated", filter: itemFilter, transform: `translateY(${Math.sin(frame / 13) * 3}px) scale(${breathe})`}} />
      <div style={{position: "absolute", top: size * 0.12, left: `calc(50% + ${sweep * size * 0.34}px)`, width: size * 0.065, height: size * 0.64, borderRadius: 999, background: `linear-gradient(180deg, transparent, ${accentColor}66 45%, #FFFFFF88 50%, transparent)`, opacity: 0.34, filter: "blur(2px)", transform: "rotate(28deg)", boxShadow: `0 0 ${size * 0.07}px ${accentColor}55`}} />
    </div>
  );
};
