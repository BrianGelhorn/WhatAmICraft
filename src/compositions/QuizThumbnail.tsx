import {AbsoluteFill, CanvasImage, staticFile, useVideoConfig} from "remotion";
import defaultConfig from "../generated/thumbnail-config.json";

export type ThumbnailVariant = "silhouette" | "pixelated" | "roulette";
type ThumbnailConfig = typeof defaultConfig;

const Text3D: React.FC<{
  children: React.ReactNode;
  color: string;
  fontSize: number;
  style?: React.CSSProperties;
}> = ({children, color, fontSize, style}) => (
  <div
    style={{
      color,
      fontSize,
      fontWeight: 900,
      lineHeight: 0.86,
      textAlign: "center",
      whiteSpace: "nowrap",
      textShadow: "0 10px 0 #111, 0 14px 0 rgba(0,0,0,.55), 0 0 18px rgba(0,0,0,.65)",
      ...style,
    }}
  >
    {children}
  </div>
);

const CategoryIcon: React.FC<{width: number; height: number; config: ThumbnailConfig}> = ({width, height, config}) => (
  <CanvasImage
    src={staticFile(config.categoryIcon)}
    style={{
      position: "absolute",
      width,
      height,
      objectFit: "contain",
      imageRendering: "pixelated",
      filter: "brightness(0) drop-shadow(0 18px 0 rgba(0,0,0,.65)) drop-shadow(0 0 18px rgba(255,244,160,.95)) drop-shadow(0 0 48px rgba(255,191,37,.9))",
    }}
  />
);

const Player: React.FC<{wide: boolean; square: boolean}> = ({wide, square}) => (
  <CanvasImage
    src={staticFile("images/thumbnail-assets/quiz-player.png")}
    style={{
      position: "absolute",
      left: wide ? -40 : square ? -20 : -55,
      top: wide ? 235 : square ? 430 : 930,
      width: wide ? 555 : square ? 575 : 650,
      height: wide ? 555 : square ? 575 : 900,
      objectFit: "contain",
      filter: "drop-shadow(0 18px 0 rgba(0,0,0,.45)) drop-shadow(0 0 16px rgba(255,211,79,.7))",
    }}
  />
);

export const QuizThumbnail: React.FC<{variant?: ThumbnailVariant; config?: ThumbnailConfig}> = ({config: inputConfig = defaultConfig}) => {
  const {width, height} = useVideoConfig();
  const config = inputConfig;
  const wide = width > height;
  const square = width === height;
  const thumbnail = config.thumbnail;
  const categoryLabel = `THIS ${config.answerType.toUpperCase()}`;

  const layout = wide
    ? {
        brandTop: 28,
        brandSize: 30,
        headlineTop: 140,
        headlineLeft: 48,
        headlineWidth: 540,
        headlineSize: 92,
        bottomSize: 88,
        mysteryLeft: 710,
        mysteryTop: 170,
        mysteryWidth: 450,
        mysteryHeight: 450,
        questionLeft: 1030,
        questionTop: 185,
        questionSize: 128,
        bannerLeft: 55,
        bannerBottom: 76,
        bannerWidth: 545,
        bannerHeight: 92,
        bannerSize: 34,
      }
    : square
      ? {
          brandTop: 30,
          brandSize: 27,
          headlineTop: 145,
          headlineLeft: 36,
          headlineWidth: 1008,
          headlineSize: 104,
          bottomSize: 92,
          mysteryLeft: 210,
          mysteryTop: 300,
          mysteryWidth: 660,
          mysteryHeight: 660,
          questionLeft: 760,
          questionTop: 335,
          questionSize: 110,
          bannerLeft: 40,
          bannerBottom: 50,
          bannerWidth: 1000,
          bannerHeight: 128,
          bannerSize: 42,
        }
      : {
          brandTop: 38,
          brandSize: 39,
          headlineTop: 250,
          headlineLeft: 30,
          headlineWidth: 1020,
          headlineSize: 158,
          bottomSize: 145,
          mysteryLeft: 225,
          mysteryTop: 625,
          mysteryWidth: 640,
          mysteryHeight: 760,
          questionLeft: 740,
          questionTop: 695,
          questionSize: 190,
          bannerLeft: 0,
          bannerBottom: 185,
          bannerWidth: 1080,
          bannerHeight: 190,
          bannerSize: 52,
        };

  return (
    <AbsoluteFill style={{overflow: "hidden", backgroundColor: "#1287ed", fontFamily: "Minecraft"}}>
      <style>{`@font-face {font-family: Minecraft; src: url(${staticFile("fonts/Minecraft-Bold.otf")}) format("opentype"); font-weight: 400 900;}`}</style>
      <CanvasImage
        src={staticFile(thumbnail.background)}
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          objectFit: "cover",
          filter: "brightness(.92) saturate(1.45) contrast(1.08)",
          transform: "scale(1.04)",
        }}
      />
      <AbsoluteFill
        style={{
          background: wide
            ? "linear-gradient(90deg, rgba(1,12,31,.8), rgba(1,12,31,.1) 55%, rgba(1,12,31,.4)), radial-gradient(circle at 73% 55%, rgba(255,196,46,.9), transparent 34%)"
            : "linear-gradient(180deg, rgba(0,42,94,.05) 0%, rgba(0,20,38,.02) 48%, rgba(0,7,18,.65) 100%), radial-gradient(circle at 50% 48%, rgba(255,199,48,.98), rgba(255,199,48,.3) 26%, transparent 49%)",
        }}
      />
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `repeating-conic-gradient(from -8deg at ${wide ? "73% 56%" : "50% 48%"}, rgba(255,226,104,.38) 0deg 3deg, transparent 3deg 12deg)`,
          opacity: 0.8,
          maskImage: `radial-gradient(circle at ${wide ? "73% 56%" : "50% 48%"}, black 0%, transparent 53%)`,
        }}
      />

      <div style={{position: "absolute", top: layout.brandTop, left: 0, width: "100%", textAlign: "center", fontSize: layout.brandSize, fontWeight: 900, letterSpacing: wide ? 4 : 5, textShadow: "0 6px 0 #111, 0 0 14px rgba(0,0,0,.65)"}}>
        <span style={{color: "white"}}>MINECRAFT </span><span style={{color: "#52e51b"}}>QUIZ</span>
      </div>

      <Text3D color={thumbnail.accent} fontSize={layout.headlineSize} style={{position: "absolute", top: layout.headlineTop, left: layout.headlineLeft, width: layout.headlineWidth}}>
        {thumbnail.headlineTop}
      </Text3D>
      <Text3D color="#ff443e" fontSize={Math.min(layout.bottomSize, layout.headlineWidth / (categoryLabel.length * 0.82))} style={{position: "absolute", top: layout.headlineTop + layout.headlineSize + 12, left: layout.headlineLeft, width: layout.headlineWidth}}>
        {categoryLabel}
      </Text3D>

      <div style={{position: "absolute", left: layout.mysteryLeft, top: layout.mysteryTop, width: layout.mysteryWidth, height: layout.mysteryHeight}}>
        <CategoryIcon config={config} width={layout.mysteryWidth} height={layout.mysteryHeight} />
      </div>
      <Text3D color="#ffd52b" fontSize={layout.questionSize} style={{position: "absolute", left: layout.questionLeft, top: layout.questionTop, transform: "rotate(10deg)"}}>
        ?
      </Text3D>
      <div style={{position: "absolute", inset: 0, height: height - layout.bannerBottom, overflow: "hidden"}}>
        <Player wide={wide} square={square} />
      </div>

      <div
        style={{
          position: "absolute",
          left: layout.bannerLeft,
          bottom: layout.bannerBottom,
          width: layout.bannerWidth,
          height: layout.bannerHeight,
          boxSizing: "border-box",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "0 18px",
          borderTop: `${wide ? 5 : 8}px solid #111`,
          borderBottom: `${wide ? 5 : 8}px solid #111`,
          background: "linear-gradient(#ed2525, #a80d0d)",
          boxShadow: "0 12px 0 rgba(0,0,0,.55), 0 0 22px rgba(255,50,25,.75)",
          color: "white",
          fontSize: layout.bannerSize,
          fontWeight: 900,
          letterSpacing: wide ? 1 : 2,
          textAlign: "center",
          textShadow: "0 7px 0 #111, 0 0 12px rgba(0,0,0,.75)",
        }}
      >
        <span style={{color: thumbnail.accent}}>{thumbnail.subline.split("·")[0].trim()}</span>
        <span style={{margin: "0 16px", color: "#111"}}>·</span>
        <span>{thumbnail.subline.split("·")[1]?.trim() ?? "1 CHANCE"}</span>
      </div>
    </AbsoluteFill>
  );
};
