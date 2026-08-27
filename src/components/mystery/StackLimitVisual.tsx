import {CanvasImage, staticFile, useCurrentFrame} from "remotion";

export const StackLimitVisual: React.FC<{
  assetSrc: string;
  stackValue: string;
  size?: number;
  accentColor?: string;
  conceal?: boolean;
}> = ({assetSrc, stackValue, size = 150, accentColor = "#2DE2E6", conceal = false}) => {
  const frame = useCurrentFrame();
  const pulse = (Math.sin(frame / 13) + 1) / 2;
  const objectSize = size * 0.72;
  const objectFilter = conceal ? `brightness(0) drop-shadow(0 ${size * 0.06}px 0 #02040A) drop-shadow(0 0 ${size * 0.1}px ${accentColor})` : `drop-shadow(0 ${size * 0.06}px 0 rgba(0,0,0,.65))`;
  return (
    <div style={{position: "relative", width: size, height: size, display: "grid", placeItems: "center", borderRadius: size * 0.19, border: `${size * 0.047}px solid #8590A8`, boxSizing: "border-box", background: "linear-gradient(145deg,#3B455A,#20283A)", boxShadow: `inset 0 0 0 ${size * 0.04}px #111827,0 ${size * 0.08}px 0 #02040A`}}>
      <CanvasImage src={staticFile(assetSrc)} style={{width: objectSize, height: objectSize, objectFit: "contain", imageRendering: "pixelated", filter: objectFilter, transform: `scale(${0.96 + pulse * 0.04})`}} />
      {conceal ? <div style={{position: "absolute", inset: 0, display: "grid", placeItems: "center", color: accentColor, fontSize: size * 0.25, textShadow: "0 5px 0 #02040A"}}>?</div> : null}
      <div style={{position: "absolute", right: size * 0.06, bottom: size * 0.045, minWidth: size * 0.35, height: size * 0.32, padding: `0 ${size * 0.045}px`, display: "grid", placeItems: "center", borderRadius: size * 0.11, background: "#080C16E8", color: "#F7FAFF", fontSize: size * 0.25, lineHeight: 1, textShadow: "0 5px 0 #02040A", boxShadow: `0 ${size * 0.045}px 0 #02040A`, transform: `scale(${0.96 + pulse * 0.04})`}}>{stackValue}</div>
    </div>
  );
};
