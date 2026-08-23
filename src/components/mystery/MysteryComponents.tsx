import {Audio} from "@remotion/media";
import {
  AbsoluteFill,
  CanvasImage,
  Easing,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type {MysteryHint, MysteryVideoConfig, VoiceSegment} from "../../mystery/types";

const clamp = {extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const};
const ease = {...clamp, easing: Easing.bezier(0.16, 1, 0.3, 1)};

export const CategoryBadge: React.FC<{config: MysteryVideoConfig}> = ({config}) => (
  <div style={{
    padding: "12px 24px", borderRadius: 999, border: `3px solid ${config.theme.progress}`,
    background: "rgba(9,18,37,.92)", color: config.theme.progress, fontSize: 30,
    letterSpacing: 4, fontWeight: 900, boxShadow: `0 0 24px ${config.theme.progress}55`,
  }}>
    MINECRAFT {config.answer.category}
  </div>
);

export const MysteryObject: React.FC<{
  config: MysteryVideoConfig;
  revealed?: boolean;
  progress?: number;
  size?: number;
}> = ({config, revealed = false, progress = revealed ? 1 : 0, size = 560}) => {
  const frame = useCurrentFrame();
  const pulse = 1 + Math.sin(frame / 8) * (config.visualIntensity === "high" ? 0.025 : 0.014);
  return (
    <div style={{position: "relative", width: size, height: size, transform: `scale(${pulse})`}}>
      <CanvasImage
        name="Exact answer silhouette"
        src={staticFile(config.answer.silhouette)}
        style={{
          position: "absolute", inset: 0, width: size, height: size, objectFit: "contain",
          imageRendering: "pixelated", filter: `brightness(0) drop-shadow(0 24px 0 #02040A) drop-shadow(0 0 34px ${config.theme.accent}99)`,
          opacity: 1 - progress,
        }}
      />
      <CanvasImage
        name="Answer image"
        src={staticFile(config.answer.image)}
        style={{
          position: "absolute", inset: 0, width: size, height: size, objectFit: "contain",
          imageRendering: "pixelated", filter: `drop-shadow(0 24px 8px #02040ACC) drop-shadow(0 0 42px ${config.theme.answer})`,
          opacity: progress, transform: `scale(${0.82 + progress * 0.18})`,
        }}
      />
    </div>
  );
};

export const ProgressMeter: React.FC<{config: MysteryVideoConfig; active: number; progress?: number}> = ({config, active, progress = 0}) => (
  <div style={{display: "flex", gap: 16, width: 720}}>
    {[0, 1, 2].map((index) => (
      <div key={index} style={{height: 18, flex: 1, borderRadius: 12, overflow: "hidden", background: "#26324B", border: "2px solid #050A14"}}>
        <div style={{
          height: "100%",
          width: `${index < active ? 100 : index === active ? Math.max(4, progress * 100) : 0}%`,
          background: index === active ? `linear-gradient(90deg, ${config.theme.progress}, ${config.theme.accent})` : config.theme.progress,
          boxShadow: index === active ? `0 0 18px ${config.theme.progress}` : "none",
        }} />
      </div>
    ))}
  </div>
);

export const HookScene: React.FC<{config: MysteryVideoConfig}> = ({config}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const impact = spring({frame, fps, config: {damping: 15, stiffness: 220, mass: 0.45}});
  const ruleOpacity = interpolate(frame, [12, 20], [0, 1], ease);
  return (
    <AbsoluteFill name="Hook scene" style={{alignItems: "center"}}>
      <div style={{position: "absolute", top: 188}}><CategoryBadge config={config} /></div>
      <div style={{
        position: "absolute", top: 292, width: 940, color: config.theme.text, fontSize: config.hook.question.length > 26 ? 74 : 88,
        lineHeight: 1.02, textAlign: "center", fontWeight: 900, textWrap: "balance",
        textShadow: `0 8px 0 #02040A, 0 0 28px ${config.theme.accent}66`, transform: `scale(${0.94 + impact * 0.06})`,
      }}>
        {config.hook.question}
      </div>
      <div style={{position: "absolute", top: 570, width: 610, height: 610, display: "grid", placeItems: "center"}}>
        <div style={{position: "absolute", inset: 12, borderRadius: "50%", border: `5px solid ${config.theme.accent}`, opacity: 0.72, boxShadow: `0 0 50px ${config.theme.accent}55`}} />
        <MysteryObject config={config} size={520} />
      </div>
      <div style={{
        position: "absolute", top: 1248, padding: "16px 32px", borderRadius: 18,
        background: config.theme.urgency, color: "#10131C", fontSize: 38, fontWeight: 900,
        letterSpacing: 3, boxShadow: "0 12px 0 rgba(0,0,0,.42)", opacity: ruleOpacity,
      }}>
        {config.hook.ruleText}
      </div>
      <div style={{position: "absolute", top: 1395}}><ProgressMeter config={config} active={0} progress={frame / config.timeline.hook.durationInFrames} /></div>
      {config.hook.showBrandMark ? <div style={{position: "absolute", top: 1515, color: config.theme.muted, fontSize: 22, letterSpacing: 5}}>MINECRAFT MYSTERY</div> : null}
    </AbsoluteFill>
  );
};

export const HintText: React.FC<{config: MysteryVideoConfig; hint: MysteryHint; durationInFrames: number}> = ({config, hint, durationInFrames}) => {
  const frame = useCurrentFrame();
  return (
    <div style={{display: "flex", flexDirection: "column", alignItems: "center", gap: 14, width: 940}}>
      {hint.fragments.map((fragment, index) => {
        const from = 7 + index * Math.floor(durationInFrames * 0.24);
        const visible = interpolate(frame, [from, from + 7], [0, 1], ease);
        const emphasized = hint.emphasisWords.some((word) => fragment.toUpperCase().includes(word.toUpperCase()));
        return (
          <div key={fragment} style={{
            color: emphasized ? config.theme.accent : config.theme.text,
            fontSize: emphasized ? 69 : 57, lineHeight: 1, fontWeight: 900, textAlign: "center",
            textShadow: "0 7px 0 #02040A", opacity: visible,
            transform: `translateY(${(1 - visible) * 24}px) scale(${0.94 + visible * 0.06})`,
          }}>
            {fragment}
          </div>
        );
      })}
    </div>
  );
};

const DurabilityVisual: React.FC<{config: MysteryVideoConfig; frame: number; duration: number}> = ({config, frame, duration}) => (
  <div style={{width: 620, display: "flex", flexDirection: "column", gap: 24, alignItems: "center"}}>
    <div style={{fontSize: 32, color: config.theme.muted}}>DURABILITY</div>
    <div style={{width: 560, height: 54, padding: 7, border: "5px solid #050A14", background: "#252C3D"}}>
      <div style={{height: "100%", width: `${interpolate(frame, [8, duration - 12], [96, 34], clamp)}%`, background: `linear-gradient(90deg, ${config.theme.answer}, ${config.theme.urgency})`}} />
    </div>
    <div style={{padding: "12px 26px", border: `3px solid ${config.theme.urgency}`, color: config.theme.urgency, fontSize: 34}}>×64 NO STACK</div>
  </div>
);

const CombatVisual: React.FC<{config: MysteryVideoConfig; hint: MysteryHint; frame: number}> = ({config, hint, frame}) => {
  const spread = interpolate(frame, [8, 24], [90, 0], ease);
  return (
    <div style={{width: 760, display: "flex", justifyContent: "space-between", alignItems: "center"}}>
      <div style={{transform: `translateX(${-spread}px)`, color: config.theme.urgency, fontSize: 38, textAlign: "center"}}>⚔<br />MELEE</div>
      <MysteryObject config={config} size={260} />
      <div style={{transform: `translateX(${spread}px)`, color: config.theme.accent, fontSize: 38, textAlign: "center"}}>
        {hint.visualAsset ? <CanvasImage src={staticFile(hint.visualAsset)} style={{width: 96, height: 96, objectFit: "contain", imageRendering: "pixelated"}} /> : "➜"}<br />RANGED
      </div>
    </div>
  );
};

const MobVisual: React.FC<{config: MysteryVideoConfig; hint: MysteryHint; frame: number}> = ({config, hint, frame}) => (
  <div style={{position: "relative", width: 620, height: 360, display: "grid", placeItems: "center"}}>
    {[0, 1, 2, 3, 4].map((index) => <div key={index} style={{position: "absolute", left: 70 + index * 112, top: 230 - ((frame * (1.5 + index * 0.2) + index * 37) % 230), width: 18 + index * 4, height: 18 + index * 4, borderRadius: "50%", border: `3px solid ${config.theme.accent}`, opacity: 0.5}} />)}
    {hint.visualAsset ? <CanvasImage src={staticFile(hint.visualAsset)} style={{width: 280, height: 300, objectFit: "contain", imageRendering: "pixelated", filter: `drop-shadow(0 0 30px ${config.theme.progress})`}} /> : null}
  </div>
);

export const HintVisual: React.FC<{config: MysteryVideoConfig; hint: MysteryHint; durationInFrames: number}> = ({config, hint, durationInFrames}) => {
  const frame = useCurrentFrame();
  if (hint.visualType === "durability") return <DurabilityVisual config={config} frame={frame} duration={durationInFrames} />;
  if (hint.visualType === "combat") return <CombatVisual config={config} hint={hint} frame={frame} />;
  if (hint.visualType === "mob") return <MobVisual config={config} hint={hint} frame={frame} />;
  return <MysteryObject config={config} size={300} />;
};

export const HintScene: React.FC<{config: MysteryVideoConfig; hint: MysteryHint; index: number; durationInFrames: number}> = ({config, hint, index, durationInFrames}) => {
  const frame = useCurrentFrame();
  const progress = interpolate(frame, [0, durationInFrames - 1], [0.03, 1], clamp);
  const accent = [config.theme.progress, config.theme.accent, "#58C8FF"][index];
  return (
    <AbsoluteFill name={`Hint ${index + 1}`} style={{alignItems: "center"}}>
      <div style={{position: "absolute", top: 190, color: accent, fontSize: 34, letterSpacing: 6}}>HINT {index + 1} / 3 · {hint.difficulty.toUpperCase()}</div>
      <div style={{position: "absolute", top: 300, minHeight: 190, display: "grid", placeItems: "center"}}><HintText config={config} hint={hint} durationInFrames={durationInFrames} /></div>
      <div style={{position: "absolute", top: 610, width: 860, height: 570, borderRadius: config.theme.cardRadius, border: `4px solid ${accent}`, background: "linear-gradient(160deg, rgba(17,27,50,.96), rgba(5,10,25,.96))", display: "grid", placeItems: "center", boxShadow: `0 24px 60px #000A, 0 0 28px ${accent}44`, transform: `scale(${1 + Math.sin(frame / 10) * 0.008})`}}>
        <HintVisual config={config} hint={hint} durationInFrames={durationInFrames} />
      </div>
      <div style={{position: "absolute", top: 1315}}><ProgressMeter config={config} active={index} progress={progress} /></div>
      <div style={{position: "absolute", top: 1410, color: config.theme.muted, fontSize: 28}}>NEXT CLUE IN {Math.max(0, ((durationInFrames - frame) / 30)).toFixed(1)}s</div>
    </AbsoluteFill>
  );
};

export const CountdownScene: React.FC<{config: MysteryVideoConfig}> = ({config}) => {
  const frame = useCurrentFrame();
  const duration = config.timeline.countdown.durationInFrames;
  const step = duration / config.countdown.values.length;
  const index = Math.min(config.countdown.values.length - 1, Math.floor(frame / step));
  const local = frame - index * step;
  const scale = interpolate(local, [0, 5, step - 1], [0.6, 1.12, 0.92], ease);
  return (
    <AbsoluteFill name="Countdown" style={{alignItems: "center", background: `radial-gradient(circle, ${config.theme.urgency}44, transparent 62%)`}}>
      <div style={{position: "absolute", top: 330, color: config.theme.text, fontSize: 66, fontWeight: 900, textShadow: "0 8px 0 #02040A"}}>{config.countdown.displayText}</div>
      <div style={{position: "absolute", top: 600, color: config.theme.urgency, fontSize: 340, fontWeight: 900, textShadow: `0 18px 0 #02040A, 0 0 55px ${config.theme.urgency}`, transform: `scale(${scale})`}}>{config.countdown.values[index]}</div>
      <div style={{position: "absolute", top: 1220}}><MysteryObject config={config} size={260} /></div>
    </AbsoluteFill>
  );
};

export const RevealScene: React.FC<{config: MysteryVideoConfig}> = ({config}) => {
  const frame = useCurrentFrame();
  const duration = config.timeline.reveal.durationInFrames;
  const progress = interpolate(frame, [4, Math.min(24, duration * 0.34)], [0, 1], ease);
  return (
    <AbsoluteFill name="Reveal" style={{alignItems: "center", background: `radial-gradient(circle at 50% 48%, ${config.theme.answer}55, transparent 62%)`}}>
      <div style={{position: "absolute", top: 210, color: config.theme.accent, fontSize: 42, letterSpacing: 6}}>{config.reveal.preRevealText}</div>
      <div style={{position: "absolute", top: 400, width: 720, height: 720, display: "grid", placeItems: "center"}}>
        <div style={{position: "absolute", inset: 40, borderRadius: "50%", border: `6px solid ${config.theme.answer}`, opacity: progress, transform: `scale(${0.75 + progress * 0.25})`, boxShadow: `0 0 70px ${config.theme.answer}88`}} />
        <MysteryObject config={config} size={560} progress={progress} />
        {[0, 1, 2, 3, 4, 5].map((index) => <div key={index} style={{position: "absolute", width: 18, height: 18, background: index % 2 ? config.theme.accent : config.theme.answer, left: 340 + Math.cos(index) * progress * 300, top: 340 + Math.sin(index) * progress * 300, opacity: progress}} />)}
      </div>
      <div style={{position: "absolute", top: 1210, color: config.theme.answer, fontSize: 118, fontWeight: 900, textShadow: "0 10px 0 #02040A", opacity: interpolate(frame, [12, 22], [0, 1], ease)}}>{config.reveal.answerText}</div>
    </AbsoluteFill>
  );
};

export const CTAScene: React.FC<{config: MysteryVideoConfig}> = ({config}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill name="CTA" style={{alignItems: "center"}}>
      <div style={{position: "absolute", top: 210, color: config.theme.accent, fontSize: 28, letterSpacing: 5}}>YOUR TURN</div>
      <div style={{position: "absolute", top: 320}}><MysteryObject config={config} revealed size={440} /></div>
      <div style={{position: "absolute", top: 840, width: 900, color: config.theme.text, fontSize: config.cta.text.length > 34 ? 58 : 70, lineHeight: 1.05, fontWeight: 900, textAlign: "center", textWrap: "balance", textShadow: "0 8px 0 #02040A"}}>{config.cta.text}</div>
      <div style={{position: "absolute", top: 1110, display: "flex", gap: 24}}>
        {config.cta.options.map((option, index) => {
          const pop = interpolate(frame, [8 + index * 5, 16 + index * 5], [0, 1], ease);
          return <div key={option} style={{minWidth: 150, padding: "22px 28px", borderRadius: 24, border: `5px solid ${config.theme.accent}`, background: config.theme.surface, color: config.theme.accent, fontSize: 64, fontWeight: 900, textAlign: "center", transform: `scale(${0.7 + pop * 0.3})`, opacity: pop, boxShadow: `0 12px 0 #02040A, 0 0 24px ${config.theme.accent}55`}}>{option}</div>;
        })}
      </div>
      <div style={{position: "absolute", top: 1345, color: config.theme.progress, fontSize: 31, letterSpacing: 3}}>TYPE ONE ANSWER BELOW</div>
    </AbsoluteFill>
  );
};

export const LoopBridge: React.FC<{config: MysteryVideoConfig}> = ({config}) => {
  const frame = useCurrentFrame();
  const duration = config.timeline.loop.durationInFrames;
  const progress = interpolate(frame, [0, Math.max(1, duration - 1)], [0, 1], clamp);
  return (
    <AbsoluteFill name="Loop bridge" style={{alignItems: "center"}}>
      <div style={{position: "absolute", top: 188}}><CategoryBadge config={config} /></div>
      <div style={{position: "absolute", top: 292, width: 940, color: config.theme.text, fontSize: 76, textAlign: "center", fontWeight: 900, textShadow: "0 8px 0 #02040A"}}>{config.hook.question}</div>
      <div style={{position: "absolute", top: 590}}><MysteryObject config={config} size={520} progress={1 - progress} /></div>
    </AbsoluteFill>
  );
};

const activeSegment = (segments: VoiceSegment[], frame: number) => segments.find((segment) => frame >= segment.start && frame < segment.end);

export const CaptionRenderer: React.FC<{config: MysteryVideoConfig}> = ({config}) => {
  const frame = useCurrentFrame();
  const segment = activeSegment(config.voice.segments, frame);
  if (!segment) return null;
  const activeWordIndex = segment.words.findIndex((item) => frame >= item.startFrame && frame < item.endFrame);
  let wordIndex = -1;
  return (
    <div style={{position: "absolute", zIndex: 20, left: 90, top: 1510, width: 900, minHeight: 92, padding: "16px 24px", boxSizing: "border-box", borderRadius: 18, background: "rgba(4,8,18,.88)", border: "2px solid rgba(255,255,255,.15)", color: config.theme.text, textAlign: "center", fontSize: 30, lineHeight: 1.15, textShadow: "0 4px 0 #000"}}>
      {segment.text.split(/(\s+)/).map((token, index) => {
        if (/^\s+$/.test(token)) return token;
        wordIndex += 1;
        return <span key={`${token}-${index}`} style={{color: wordIndex === activeWordIndex ? config.theme.accent : config.theme.text}}>{token}</span>;
      })}
    </div>
  );
};

export const AudioTimeline: React.FC<{config: MysteryVideoConfig}> = ({config}) => {
  if (config.audio.status !== "complete" || config.voice.status !== "complete" || !config.audio.music) return null;
  const music = config.audio.music;
  return (
    <>
      <Audio src={staticFile(music.publicSrc)} from={music.from} durationInFrames={music.durationInFrames} loop volume={(frame) => {
        const bed = interpolate(frame, [0, music.fadeInFrames, music.durationInFrames - music.fadeOutFrames, music.durationInFrames], [0, music.volume, music.volume, 0], clamp);
        const duck = config.voice.segments.some((segment) => frame >= segment.start - music.duckFadeFrames && frame <= segment.end + music.duckFadeFrames);
        return bed * (duck ? music.duckedVolume / music.volume : 1);
      }} />
      {config.voice.segments.map((segment) => <Audio key={segment.id} src={staticFile(segment.audioSrc)} from={segment.start} durationInFrames={segment.end - segment.start} />)}
      {config.audio.effects.map((effect) => <Audio key={effect.id} src={staticFile(effect.publicSrc)} from={effect.from} durationInFrames={effect.durationInFrames} volume={() => effect.volume} />)}
    </>
  );
};

export const SafeZoneOverlay: React.FC<{config: MysteryVideoConfig}> = ({config}) => config.debug.showSafeZones ? (
  <div style={{position: "absolute", zIndex: 40, left: 72, top: 170, width: 936, height: 1430, border: "3px dashed #FF3B81", pointerEvents: "none"}} />
) : null;

export const RetentionDebugOverlay: React.FC<{config: MysteryVideoConfig}> = ({config}) => {
  const frame = useCurrentFrame();
  if (!config.debug.showRetentionMarkers && !config.debug.showSceneBoundaries && !config.debug.showTimestampLabels && !config.debug.showVoiceSegments) return null;
  const scenes = [config.timeline.hook, ...config.timeline.hints, config.timeline.countdown, config.timeline.reveal, config.timeline.cta, config.timeline.loop];
  return (
    <div style={{position: "absolute", zIndex: 50, left: 20, top: 20, padding: 12, background: "rgba(0,0,0,.8)", color: "#00FF9D", fontFamily: "monospace", fontSize: 20}}>
      F{frame} · {(frame / 30).toFixed(2)}s · {config.variant}<br />
      {config.debug.showSceneBoundaries ? `scene ${scenes.findIndex((scene) => frame >= scene.from && frame < scene.from + scene.durationInFrames)}` : ""}
    </div>
  );
};
