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
  const glow = 14 + Math.sin(frame / 10) * 6;
  const itemFilter = conceal
    ? `brightness(0) drop-shadow(0 8px 0 #02040A) drop-shadow(0 0 ${glow}px ${accentColor})`
    : `drop-shadow(0 8px 0 #02040A) drop-shadow(0 0 ${glow}px ${accentColor})`;
  return (
    <div style={{position: "relative", width: size * 1.45, height: size, display: "grid", placeItems: "center"}}>
      {supportingAsset ? <CanvasImage src={staticFile(supportingAsset)} style={{position: "absolute", left: 0, width: size * 0.42, height: size * 0.42, objectFit: "contain", imageRendering: "pixelated", opacity: 0.86, transform: `translateY(${Math.sin(frame / 12) * 5}px) rotate(-12deg)`, filter: "drop-shadow(0 7px 0 #02040A)"}} /> : null}
      <div style={{position: "absolute", width: size * 0.88, height: size * 0.88, borderRadius: size * 0.22, border: `${size * 0.035}px solid ${accentColor}66`, boxShadow: `0 0 ${glow * 1.5}px ${accentColor}55`, transform: `rotate(${sweep * 7}deg)`}} />
      <CanvasImage src={staticFile(assetSrc)} style={{width: size * 0.72, height: size * 0.72, objectFit: "contain", imageRendering: "pixelated", filter: itemFilter, transform: `scale(${0.96 + Math.sin(frame / 11) * 0.025})`}} />
      <div style={{position: "absolute", top: size * 0.08, left: `calc(50% + ${sweep * size * 0.4}px)`, width: size * 0.06, height: size * 0.78, borderRadius: size * 0.03, background: `linear-gradient(transparent,${accentColor},transparent)`, opacity: 0.7, transform: "rotate(28deg)", boxShadow: `0 0 ${size * 0.08}px ${accentColor}`}} />
      {conceal ? <div style={{position: "absolute", inset: 0, display: "grid", placeItems: "center", color: accentColor, fontSize: size * 0.25, textShadow: "0 5px 0 #02040A"}}>?</div> : null}
    </div>
  );
};
