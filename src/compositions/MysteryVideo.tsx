import {useEffect, useState} from "react";
import {AbsoluteFill, CanvasImage, Sequence, cancelRender, continueRender, delayRender, interpolate, staticFile, useCurrentFrame} from "remotion";
import {
  AudioTimeline,
  CaptionRenderer,
  CountdownScene,
  CTAScene,
  HintScene,
  HookScene,
  LoopBridge,
  RetentionDebugOverlay,
  RevealScene,
  SafeZoneOverlay,
} from "../components/mystery/MysteryComponents";
import type {MysteryVideoConfig} from "../mystery/types";
import defaultConfigJson from "../generated/mystery-v2-episode.json";

export const defaultMysteryConfig = defaultConfigJson as unknown as MysteryVideoConfig;

export const MysteryVideo: React.FC<{config?: MysteryVideoConfig}> = ({config = defaultMysteryConfig}) => {
  const frame = useCurrentFrame();
  const [fontHandle] = useState(() => delayRender("Loading Minecraft font"));
  useEffect(() => {
    new FontFace("Minecraft", `url("${staticFile("fonts/Minecraft-Bold.otf")}")`, {weight: "400"}).load()
      .then((font) => {
        document.fonts.add(font);
        continueRender(fontHandle);
      })
      .catch((error) => cancelRender(error));
  }, [fontHandle]);
  const intensity = config.visualIntensity === "high" ? 1 : config.visualIntensity === "medium" ? 0.65 : 0.35;
  const drift = interpolate(frame, [0, config.timeline.durationInFrames], [0, 34 * intensity], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  return (
    <AbsoluteFill style={{overflow: "hidden", background: config.theme.mystery, fontFamily: config.theme.titleFont}}>
      <AudioTimeline config={config} />
      <CanvasImage name="Moving background" src={staticFile(config.background)} style={{position: "absolute", inset: -50, width: 1180, height: 2020, objectFit: "cover", filter: "blur(8px) brightness(.34) saturate(1.18)", transform: `translateY(${-drift}px) scale(1.08)`}} />
      <AbsoluteFill style={{background: `linear-gradient(180deg, ${config.theme.mystery}F2 0%, ${config.theme.mystery}55 48%, ${config.theme.mystery}F5 100%)`}} />
      {[0, 1, 2, 3, 4, 5, 6].map((index) => <div key={index} style={{position: "absolute", left: 80 + index * 155, top: 220 + ((frame * (0.35 + index * 0.04) + index * 211) % 1350), width: 5 + index, height: 5 + index, background: index % 2 ? config.theme.accent : config.theme.progress, opacity: 0.18, transform: "rotate(45deg)"}} />)}
      <Sequence name="Immediate hook" from={config.timeline.hook.from} durationInFrames={config.timeline.hook.durationInFrames}><HookScene config={config} /></Sequence>
      {config.timeline.hints.map((scene, index) => <Sequence key={config.hints[index].id} name={`Hint ${index + 1}`} from={scene.from} durationInFrames={scene.durationInFrames} premountFor={8}><HintScene config={config} hint={config.hints[index]} index={index} durationInFrames={scene.durationInFrames} /></Sequence>)}
      <Sequence name="Think fast" from={config.timeline.countdown.from} durationInFrames={config.timeline.countdown.durationInFrames} premountFor={8}><CountdownScene config={config} /></Sequence>
      <Sequence name="Answer reveal" from={config.timeline.reveal.from} durationInFrames={config.timeline.reveal.durationInFrames} premountFor={8}><RevealScene config={config} /></Sequence>
      <Sequence name="Comment CTA" from={config.timeline.cta.from} durationInFrames={config.timeline.cta.durationInFrames} premountFor={8}><CTAScene config={config} /></Sequence>
      <Sequence name="Loop bridge" from={config.timeline.loop.from} durationInFrames={config.timeline.loop.durationInFrames} premountFor={4}><LoopBridge config={config} /></Sequence>
      <CaptionRenderer config={config} />
      <SafeZoneOverlay config={config} />
      <RetentionDebugOverlay config={config} />
    </AbsoluteFill>
  );
};
