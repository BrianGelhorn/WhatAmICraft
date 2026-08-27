import {CanvasImage, staticFile, useCurrentFrame} from "remotion";

const durabilitySteps = [1, 0.82, 0.6, 0.38, 0.18, 0] as const;
const durabilityStepFrames = [0, 14, 26, 36, 44, 50] as const;
const breakPieces = [
  {clipPath: "inset(0 50% 50% 0)", x: -1, y: -1, rotate: -18},
  {clipPath: "inset(0 0 50% 50%)", x: 1, y: -1, rotate: 20},
  {clipPath: "inset(50% 50% 0 0)", x: -1, y: 1, rotate: -28},
  {clipPath: "inset(50% 0 0 50%)", x: 1, y: 1, rotate: 25},
] as const;

export const DurabilityLossVisual: React.FC<{
  assetSrc: string;
  size?: number;
  healthyColor?: string;
  warningColor?: string;
  criticalColor?: string;
  conceal?: boolean;
}> = ({assetSrc, size = 150, healthyColor = "#6BFF95", warningColor = "#FF6B35", criticalColor = "#FF3048", conceal = false}) => {
  const frame = useCurrentFrame() % 84;
  const step = frame < durabilityStepFrames[1] ? 0 : frame < durabilityStepFrames[2] ? 1 : frame < durabilityStepFrames[3] ? 2 : frame < durabilityStepFrames[4] ? 3 : frame < durabilityStepFrames[5] ? 4 : 5;
  const respawn = Math.max(0, Math.min(1, (frame - 74) / 8));
  const durability = frame >= 74 ? 1 : durabilitySteps[step];
  const hitAge = frame - durabilityStepFrames[step];
  const hit = step > 0 && hitAge < 5 ? 1 - hitAge / 5 : 0;
  const breaking = Math.max(0, Math.min(1, (frame - 54) / 14));
  const objectSize = size * 0.75;
  const objectLeft = (size - objectSize) / 2;
  const objectTop = size * 0.04;
  const color = durability > 0.38 ? healthyColor : durability > 0 ? warningColor : criticalColor;
  const imageFilter = conceal ? `brightness(0) drop-shadow(0 ${size * 0.06}px 0 #02040A) drop-shadow(0 0 ${size * 0.11}px ${color})` : `drop-shadow(0 ${size * 0.06}px 0 rgba(0,0,0,.65)) drop-shadow(0 0 ${durability <= 0.18 ? size * 0.12 : 0}px ${criticalColor})`;
  const objectStyle: React.CSSProperties = {position: "absolute", left: objectLeft, top: objectTop, width: objectSize, height: objectSize, objectFit: "contain", imageRendering: "pixelated", filter: imageFilter};

  return (
    <div style={{position: "relative", width: size, height: size, display: "grid", placeItems: "center", overflow: "hidden", borderRadius: size * 0.19, border: `${size * 0.047}px solid #8590A8`, boxSizing: "border-box", background: "linear-gradient(145deg,#3B455A,#20283A)", boxShadow: `inset 0 0 0 ${size * 0.04}px #111827,0 ${size * 0.08}px 0 #02040A,0 0 ${hit * size * 0.16}px ${color}`, transform: `scale(${1 + hit * 0.07})`}}>
      {frame < 54 || frame >= 74 ? <CanvasImage src={staticFile(assetSrc)} style={{...objectStyle, opacity: frame >= 74 ? respawn : 1, transform: `translateX(${frame >= 44 && frame < 54 ? (frame % 2 ? -size * 0.047 : size * 0.047) : hit * -size * 0.067}px) rotate(${frame >= 44 && frame < 54 ? (frame % 2 ? -5 : 5) : hit * -7}deg) scale(${frame >= 74 ? 0.72 + respawn * 0.28 : 1 + hit * 0.11})`}} /> : breaking < 1 ? breakPieces.map((piece) => <CanvasImage key={piece.clipPath} src={staticFile(assetSrc)} style={{...objectStyle, clipPath: piece.clipPath, transform: `translate(${piece.x * breaking * size * 0.41}px,${piece.y * breaking * size * 0.43}px) rotate(${piece.rotate * breaking * 1.35}deg)`, opacity: 1 - breaking * 0.9}} />) : null}
      {conceal && (frame < 54 || frame >= 74) ? <div style={{position: "absolute", inset: 0, display: "grid", placeItems: "center", color: warningColor, fontSize: size * 0.27, textShadow: "0 5px 0 #02040A", opacity: frame >= 74 ? respawn : 1}}>?</div> : null}
      {hit > 0 ? [0, 1, 2].map((index) => <div key={index} style={{position: "absolute", left: size * (0.16 + index * 0.31), top: size * (0.32 + index % 2 * 0.23), width: size * 0.19, height: size * 0.053, borderRadius: size * 0.027, background: color, transform: `translateX(${-hit * size * (0.12 + index * 0.033)}px) rotate(${index * 28 - 25}deg)`, opacity: hit}} />) : null}
      {frame >= 54 && frame < 70 ? [0, 1, 2, 3, 4, 5, 6, 7].map((index) => <div key={index} style={{position: "absolute", left: size * 0.45 + Math.cos(index * 0.79) * breaking * size * 0.51, top: size * 0.43 + Math.sin(index * 0.79) * breaking * size * 0.51, width: size * (0.08 + index % 2 * 0.04), height: size * (0.08 + index % 2 * 0.04), background: index % 2 ? warningColor : "#FFD166", transform: `rotate(${index * 31 + breaking * 110}deg)`, opacity: 1 - breaking}} />) : null}
      <div style={{position: "absolute", left: size * 0.14, bottom: size * 0.085, width: size * 0.72, height: size * 0.13, padding: size * 0.02, borderRadius: size * 0.053, background: "#080C16", border: `${size * 0.02}px solid #02040A`, boxSizing: "border-box", transform: `scaleX(${1 + hit * 0.08})`}}><div style={{width: `${durability * 100}%`, height: "100%", borderRadius: size * 0.027, background: color, boxShadow: `0 0 ${size * 0.08}px ${color}`}} /></div>
    </div>
  );
};
