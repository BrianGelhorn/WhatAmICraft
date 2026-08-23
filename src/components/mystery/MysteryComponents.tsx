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
const SAFE_TOP = 170;
const SAFE_BOTTOM = 1600;
const fittedFontSize = (text: string, maximum: number, minimum: number, comfortableLength: number) =>
  Math.max(minimum, Math.min(maximum, Math.floor(maximum * comfortableLength / Math.max(comfortableLength, text.length))));

export const CategoryBadge: React.FC<{config: MysteryVideoConfig}> = ({config}) => (
  <div style={{
    padding: "10px 22px", borderRadius: 999, border: `3px solid ${config.theme.progress}`,
    background: `${config.theme.mystery}E8`, color: config.theme.progress, fontSize: 27,
    letterSpacing: 4, boxShadow: `0 0 22px ${config.theme.progress}44`,
  }}>
    MINECRAFT {config.answer.category}
  </div>
);

export const GlobalProgress: React.FC<{config: MysteryVideoConfig; absoluteFrame: number}> = ({config, absoluteFrame}) => {
  const urgency = absoluteFrame >= config.timeline.countdown.from;
  return (
    <div style={{display: "flex", gap: 22}}>
      {config.timeline.hints.map((hint, index) => {
        const active = absoluteFrame >= hint.from;
        return <div key={index} style={{width: 82, height: 58, display: "grid", placeItems: "center", border: `4px solid ${active ? urgency ? config.theme.urgency : config.theme.progress : "#33415F"}`, borderRadius: 12, background: active ? config.theme.surface : `${config.theme.mystery}AA`, color: active ? config.theme.text : config.theme.muted, fontSize: 28, boxShadow: active ? `0 0 18px ${urgency ? config.theme.urgency : config.theme.progress}55` : "none"}}>{index + 1}</div>;
      })}
    </div>
  );
};

export const ProgressMeter = GlobalProgress;

export const MysteryObject: React.FC<{
  config: MysteryVideoConfig;
  progress?: number;
  size?: number;
  reaction?: number;
}> = ({config, progress = 0, size = 560, reaction = 0}) => {
  const frame = useCurrentFrame();
  const intensity = config.visualIntensity === "high" ? 1 : config.visualIntensity === "medium" ? 0.65 : 0.35;
  const pulse = 1 + Math.sin(frame / 7) * 0.014 * intensity + reaction * 0.035;
  const sway = Math.sin(frame / 13) * 2.4 * intensity;
  const drift = Math.sin(frame / 9) * 3 * intensity;
  return (
    <div style={{position: "relative", width: size, height: size, transform: `translateX(${drift}px) rotate(${sway}deg) scale(${pulse})`}}>
      <CanvasImage
        name="Exact answer silhouette"
        src={staticFile(config.answer.silhouette)}
        style={{position: "absolute", inset: 0, width: size, height: size, objectFit: "contain", imageRendering: "pixelated", filter: `brightness(0) drop-shadow(0 22px 0 #02040A) drop-shadow(0 0 ${30 + reaction * 28}px ${config.theme.accent})`, opacity: 1 - progress}}
      />
      <CanvasImage
        name="Answer image"
        src={staticFile(config.answer.image)}
        style={{position: "absolute", inset: 0, width: size, height: size, objectFit: "contain", imageRendering: "pixelated", filter: `drop-shadow(0 22px 8px #02040ACC) drop-shadow(0 0 44px ${config.theme.answer})`, opacity: progress, transform: `scale(${0.86 + progress * 0.14})`}}
      />
    </div>
  );
};

export const HookQuestion: React.FC<{config: MysteryVideoConfig}> = ({config}) => (
  <div style={{width: 930, color: config.theme.text, fontSize: fittedFontSize(config.hook.question, 82, 62, 22), lineHeight: 1.02, textAlign: "center", overflowWrap: "anywhere", textShadow: `0 8px 0 #02040A, 0 0 26px ${config.theme.accent}55`}}>
    {config.hook.question}
  </div>
);

export const HookScene: React.FC<{config: MysteryVideoConfig}> = ({config}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const impact = spring({frame, fps, config: {damping: 15, stiffness: 220, mass: 0.45}});
  const ring = interpolate(frame, [0, config.timeline.hook.durationInFrames - 1], [1.08, 0.96], ease);
  return (
    <AbsoluteFill name="Hook scene" style={{alignItems: "center"}}>
      <div style={{position: "absolute", top: 188}}><CategoryBadge config={config} /></div>
      <div style={{position: "absolute", top: 292, transform: `scale(${0.94 + impact * 0.06})`}}><HookQuestion config={config} /></div>
      <div style={{position: "absolute", top: 540, width: 610, height: 610, display: "grid", placeItems: "center"}}>
        <div style={{position: "absolute", inset: 18, borderRadius: "50%", border: `5px solid ${config.theme.accent}`, opacity: 0.76, transform: `scale(${ring})`, boxShadow: `0 0 60px ${config.theme.accent}55`}} />
        <MysteryObject config={config} size={520} reaction={Math.sin(frame / 4) * 0.2 + 0.2} />
      </div>
      <div style={{position: "absolute", top: 1238, padding: "13px 26px", borderRadius: 14, background: config.theme.urgency, color: "#10131C", fontSize: 34, letterSpacing: 3, boxShadow: "0 10px 0 rgba(0,0,0,.42)"}}>{config.hook.ruleText}</div>
      <div style={{position: "absolute", top: 1392}}><GlobalProgress config={config} absoluteFrame={frame} /></div>
    </AbsoluteFill>
  );
};

export const HintHeader: React.FC<{config: MysteryVideoConfig; index: number}> = ({config, index}) => (
  <div style={{display: "flex", alignItems: "center", gap: 16, color: config.theme.muted, fontSize: 28, letterSpacing: 5}}>
    <span style={{color: config.theme.progress}}>0{index + 1}</span><span>HINT</span>
  </div>
);

export const HintKeyword: React.FC<{config: MysteryVideoConfig; hint: MysteryHint; durationInFrames: number}> = ({config, hint, durationInFrames}) => {
  const frame = useCurrentFrame();
  const switchFrame = Math.floor(durationInFrames * 0.46);
  return (
    <div style={{position: "relative", width: 940, height: 150}}>
      {hint.fragments.map((fragment, index) => {
        const enter = index === 0 ? 2 : switchFrame;
        const leave = index === hint.fragments.length - 1 ? durationInFrames : switchFrame + 4;
        const opacity = interpolate(frame, [enter, enter + 7, leave - 6, leave], [0, 1, 1, 0], ease);
        return <div key={fragment} style={{position: "absolute", inset: 0, display: "grid", placeItems: "center", color: index === hint.fragments.length - 1 ? config.theme.accent : config.theme.text, fontSize: fittedFontSize(fragment, 72, 54, 18), lineHeight: 1, textAlign: "center", overflowWrap: "anywhere", textShadow: "0 8px 0 #02040A", opacity, transform: `translateY(${(1 - opacity) * 24}px) scale(${0.94 + opacity * 0.06})`}}>{fragment}</div>;
      })}
    </div>
  );
};

export const HintText = HintKeyword;

export const DurabilityVisual: React.FC<{config: MysteryVideoConfig; duration: number}> = ({config, duration}) => {
  const frame = useCurrentFrame();
  const secondPhase = interpolate(frame, [duration * 0.42, duration * 0.56], [0, 1], ease);
  const wear = interpolate(frame, [8, duration * 0.42], [0, 1], ease);
  return (
    <div style={{position: "relative", width: 780, height: 520}}>
      <div style={{position: "absolute", left: 240, top: 20, opacity: 1 - secondPhase, transform: `translateX(${Math.sin(frame * 1.8) * wear * 5}px)`}}>
        <MysteryObject config={config} size={300} reaction={wear * 0.45} />
        {[0, 1, 2].map((index) => <div key={index} style={{position: "absolute", left: 118 + index * 36, top: 120 + index * 42, width: 11, height: 52, background: config.theme.urgency, transform: `rotate(${34 + index * 14}deg) scaleY(${wear})`, transformOrigin: "top", opacity: wear, boxShadow: "0 5px 0 #02040A"}} />)}
        {[0, 1, 2, 3].map((index) => <div key={index} style={{position: "absolute", left: 130 + index * 38, top: 210 + wear * (95 + index * 18), width: 14 + index * 2, height: 14 + index * 2, background: index % 2 ? config.theme.urgency : config.theme.accent, opacity: wear * (1 - secondPhase)}} />)}
      </div>
      <div style={{position: "absolute", left: 238, top: 35, width: 304, height: 304, display: "grid", placeItems: "center", border: "10px solid #8892A8", background: "#31394A", boxShadow: "inset 0 0 0 8px #171D2B, 0 12px 0 #02040A", opacity: secondPhase, transform: `scale(${0.9 + secondPhase * 0.1})`}}>
        <MysteryObject config={config} size={250} reaction={0.2} />
        <div style={{position: "absolute", right: 18, bottom: 10, color: config.theme.text, fontSize: 54, textShadow: "0 5px 0 #000"}}>1</div>
      </div>
    </div>
  );
};

export const CombatRangeVisual: React.FC<{config: MysteryVideoConfig; hint: MysteryHint; duration: number}> = ({config, hint, duration}) => {
  const frame = useCurrentFrame();
  const secondPhase = interpolate(frame, [duration * 0.42, duration * 0.56], [0, 1], ease);
  const meleeStrike = interpolate(frame, [8, 24], [0, 1], ease);
  const thrownStrike = interpolate(frame, [duration * 0.52, duration * 0.82], [0, 1], ease);
  return (
    <div style={{position: "relative", width: 850, height: 520}}>
      {hint.visualAsset ? <CanvasImage src={staticFile(hint.visualAsset)} style={{position: "absolute", right: 70, top: 90, width: 270, height: 340, objectFit: "contain", imageRendering: "pixelated", filter: "drop-shadow(0 12px 0 #02040A)"}} /> : null}
      <div style={{position: "absolute", left: 70 + meleeStrike * 245, top: 115, opacity: 1 - secondPhase, transform: `rotate(${meleeStrike * -14}deg)`}}><MysteryObject config={config} size={260} reaction={meleeStrike * 0.5} /></div>
      <div style={{position: "absolute", left: 35 + thrownStrike * 440, top: 130 - Math.sin(thrownStrike * Math.PI) * 70, opacity: secondPhase, transform: `rotate(${thrownStrike * 12}deg)`}}><MysteryObject config={config} size={220} reaction={thrownStrike * 0.35} /></div>
    </div>
  );
};

export const DrownedVisual: React.FC<{config: MysteryVideoConfig; hint: MysteryHint; duration: number}> = ({config, hint, duration}) => {
  const frame = useCurrentFrame();
  const rise = interpolate(frame, [8, 28], [0, 1], ease);
  const connection = interpolate(frame, [duration * 0.42, duration * 0.62], [0, 1], ease);
  return (
    <div style={{position: "relative", width: 850, height: 540, overflow: "hidden"}}>
      {[0, 1, 2].map((index) => <div key={index} style={{position: "absolute", left: -80 + index * 35, top: 400 + index * 28 + Math.sin((frame + index * 9) / 7) * 10, width: 980, height: 90, borderRadius: "50%", border: `5px solid ${config.theme.progress}`, opacity: 0.18 + index * 0.09}} />)}
      {hint.visualAsset ? <CanvasImage src={staticFile(hint.visualAsset)} style={{position: "absolute", left: 100, top: 80 + (1 - rise) * 220, width: 300, height: 340, objectFit: "contain", imageRendering: "pixelated", filter: `drop-shadow(0 0 28px ${config.theme.progress})`}} /> : null}
      <div style={{position: "absolute", left: 360, top: 250, width: 130 * connection, height: 6, background: config.theme.accent, boxShadow: `0 0 20px ${config.theme.accent}`, transform: "rotate(-8deg)", transformOrigin: "left"}} />
      <div style={{position: "absolute", right: 65, top: 105, opacity: connection}}><MysteryObject config={config} size={280} progress={0.14} reaction={connection} /></div>
    </div>
  );
};

export const HintVisual: React.FC<{config: MysteryVideoConfig; hint: MysteryHint; durationInFrames: number}> = ({config, hint, durationInFrames}) => {
  if (hint.visualType === "durability") return <DurabilityVisual config={config} duration={durationInFrames} />;
  if (hint.visualType === "combat") return <CombatRangeVisual config={config} hint={hint} duration={durationInFrames} />;
  if (hint.visualType === "mob") return <DrownedVisual config={config} hint={hint} duration={durationInFrames} />;
  return <MysteryObject config={config} size={340} />;
};

export const HintScene: React.FC<{config: MysteryVideoConfig; hint: MysteryHint; index: number; durationInFrames: number}> = ({config, hint, index, durationInFrames}) => {
  const frame = useCurrentFrame();
  const scene = config.timeline.hints[index];
  const entry = interpolate(frame, [0, 8], [0, 1], ease);
  return (
    <AbsoluteFill name={`Hint ${index + 1}`} style={{alignItems: "center", background: `radial-gradient(circle at 50% 55%, ${index === 2 ? config.theme.progress : config.theme.accent}18, transparent 62%)`}}>
      <div style={{position: "absolute", top: 190, opacity: entry}}><HintHeader config={config} index={index} /></div>
      <div style={{position: "absolute", top: 295}}><HintKeyword config={config} hint={hint} durationInFrames={durationInFrames} /></div>
      <div style={{position: "absolute", top: 535, opacity: entry}}><HintVisual config={config} hint={hint} durationInFrames={durationInFrames} /></div>
      <div style={{position: "absolute", top: 1392}}><GlobalProgress config={config} absoluteFrame={scene.from + frame} /></div>
    </AbsoluteFill>
  );
};

const normalizedWord = (word: string) => word.toLowerCase().replace(/[^a-z0-9]/g, "");

export const CountdownScene: React.FC<{config: MysteryVideoConfig}> = ({config}) => {
  const frame = useCurrentFrame();
  const scene = config.timeline.countdown;
  const absoluteFrame = scene.from + frame;
  const voice = config.voice.segments.find((segment) => segment.id === "countdown");
  const numberWords = voice?.words.filter((word) => ["three", "two", "one", "3", "2", "1"].includes(normalizedWord(word.word))) ?? [];
  const spokenWords = numberWords.filter((word) => word.startFrame <= absoluteFrame);
  const activeTiming = spokenWords[spokenWords.length - 1];
  const step = scene.durationInFrames / 3;
  const fallbackIndex = Math.min(2, Math.floor(frame / step));
  const activeIndex = activeTiming ? numberWords.indexOf(activeTiming) : fallbackIndex;
  const spoken = activeTiming ? normalizedWord(activeTiming.word) : "";
  const fallback = config.countdown.values[fallbackIndex];
  const value = spoken ? ({three: 3, two: 2, one: 1, "3": 3, "2": 2, "1": 1} as const)[spoken as "three" | "two" | "one" | "3" | "2" | "1"] : voice ? "" : fallback;
  const nextStart = numberWords[activeIndex + 1]?.startFrame ?? scene.from + scene.durationInFrames;
  const local = activeTiming ? absoluteFrame - activeTiming.startFrame : frame % step;
  const activeDuration = activeTiming ? Math.max(8, nextStart - activeTiming.startFrame) : step;
  const scale = interpolate(local, [0, 5, activeDuration - 1], [0.8, 1.15, 0.96], ease);
  const numberColor = [config.theme.progress, config.theme.accent, config.theme.urgency][activeIndex] ?? config.theme.urgency;
  return (
    <AbsoluteFill name="Countdown" style={{alignItems: "center", background: `radial-gradient(circle at 50% 48%, ${config.theme.urgency}52, transparent 64%)`}}>
      <div style={{position: "absolute", top: 260, color: config.theme.text, fontSize: 62, textShadow: "0 8px 0 #02040A"}}>{config.countdown.displayText}</div>
      <div style={{position: "absolute", top: 500, color: numberColor, fontSize: 330, textShadow: `0 18px 0 #02040A, 0 0 60px ${numberColor}`, transform: `scale(${scale})`}}>{value}</div>
      <div style={{position: "absolute", top: 1020}}><MysteryObject config={config} size={320} reaction={0.8} /></div>
      <div style={{position: "absolute", top: 1392}}><GlobalProgress config={config} absoluteFrame={absoluteFrame} /></div>
    </AbsoluteFill>
  );
};

export const RevealTransform: React.FC<{config: MysteryVideoConfig}> = ({config}) => {
  const frame = useCurrentFrame();
  const reveal = interpolate(frame, [24, 42], [0, 1], ease);
  const shake = frame < 18 ? Math.sin(frame * 2.6) * interpolate(frame, [0, 18], [1, 9], clamp) : 0;
  return (
    <div style={{position: "relative", width: 700, height: 700, display: "grid", placeItems: "center", transform: `translateX(${shake}px)`}}>
      <div style={{position: "absolute", inset: 45, borderRadius: "50%", border: `6px solid ${config.theme.answer}`, opacity: 0.35 + reveal * 0.65, transform: `scale(${0.8 + reveal * 0.2})`, boxShadow: `0 0 ${40 + reveal * 60}px ${config.theme.answer}88`}} />
      <MysteryObject config={config} size={550} progress={reveal} reaction={reveal} />
      {(config.renderMode === "preview" ? [0, 2, 4] : [0, 1, 2, 3, 4, 5]).map((index) => <div key={index} style={{position: "absolute", width: 16, height: 16, background: index % 2 ? config.theme.accent : config.theme.answer, left: 342 + Math.cos(index) * reveal * 300, top: 342 + Math.sin(index) * reveal * 300, opacity: reveal}} />)}
    </div>
  );
};

export const RevealAnswer: React.FC<{config: MysteryVideoConfig}> = ({config}) => {
  const frame = useCurrentFrame();
  const answer = interpolate(frame, [30, 39], [0, 1], ease);
  return (
    <>
      <div style={{position: "absolute", top: 205, color: config.theme.accent, fontSize: 36, letterSpacing: 6, opacity: interpolate(frame, [4, 12, 22, 26], [0, 1, 1, 0], clamp)}}>{config.reveal.preRevealText}</div>
      <div style={{position: "absolute", top: 1220, color: config.theme.answer, fontSize: 116, textShadow: "0 10px 0 #02040A", opacity: answer, transform: `scale(${0.88 + answer * 0.12})`}}>{config.reveal.answerText}</div>
    </>
  );
};

export const RevealScene: React.FC<{config: MysteryVideoConfig}> = ({config}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill name="Reveal" style={{alignItems: "center", background: `radial-gradient(circle at 50% 48%, ${config.theme.answer}48, transparent 64%)`}}>
      <RevealAnswer config={config} />
      <div style={{position: "absolute", top: 390}}><RevealTransform config={config} /></div>
      <div style={{position: "absolute", top: 1392}}><GlobalProgress config={config} absoluteFrame={config.timeline.reveal.from + frame} /></div>
    </AbsoluteFill>
  );
};

const NumberOptions: React.FC<{config: MysteryVideoConfig; frame: number; opacity?: number}> = ({config, frame, opacity = 1}) => (
  <div style={{display: "flex", gap: 28, opacity}}>
    {config.cta.options.map((option, index) => {
      const pop = interpolate(frame, [10 + index * 9, 18 + index * 9], [0, 1], ease);
      const pulse = 1 + Math.sin((frame - index * 4) / 8) * 0.025;
      return <div key={option} style={{width: 164, height: 130, display: "grid", placeItems: "center", borderRadius: 24, border: `5px solid ${config.theme.accent}`, background: config.theme.surface, color: config.theme.accent, fontSize: 72, boxShadow: `0 12px 0 #02040A, 0 0 24px ${config.theme.accent}44`, transform: `scale(${(0.72 + pop * 0.28) * pulse})`, opacity: pop}}>{option}</div>;
    })}
  </div>
);

export const CommentCTA: React.FC<{config: MysteryVideoConfig}> = ({config}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill name="Comment CTA" style={{alignItems: "center"}}>
      <div style={{position: "absolute", top: 305}}><MysteryObject config={config} progress={1} size={420} reaction={0.35} /></div>
      <div style={{position: "absolute", top: 790, width: 930, color: config.theme.text, fontSize: fittedFontSize(config.cta.text, 68, 52, 22), lineHeight: 1.04, textAlign: "center", overflowWrap: "anywhere", textShadow: "0 8px 0 #02040A"}}>{config.cta.text}</div>
      <div style={{position: "absolute", top: 1015}}><NumberOptions config={config} frame={frame} /></div>
      <div style={{position: "absolute", top: 1210, width: 900, color: config.theme.muted, fontFamily: config.theme.bodyFont, fontSize: fittedFontSize(config.cta.prompt, 34, 27, 32), letterSpacing: 2, textAlign: "center"}}>{config.cta.prompt}</div>
      <div style={{position: "absolute", top: 1392}}><GlobalProgress config={config} absoluteFrame={config.timeline.cta.from + frame} /></div>
    </AbsoluteFill>
  );
};

export const CTAScene = CommentCTA;

export const LoopBridge: React.FC<{config: MysteryVideoConfig}> = ({config}) => {
  const frame = useCurrentFrame();
  const duration = config.timeline.loop.durationInFrames;
  const progress = interpolate(frame, [0, Math.max(1, duration - 1)], [0, 1], ease);
  const objectTop = interpolate(progress, [0, 1], [305, 540]);
  const objectSize = interpolate(progress, [0, 1], [420, 520]);
  return (
    <AbsoluteFill name="Loop bridge" style={{alignItems: "center", background: `radial-gradient(circle at 50% 50%, ${config.theme.answer}${Math.round((1 - progress) * 50).toString(16).padStart(2, "0")}, transparent 64%)`}}>
      <div style={{position: "absolute", top: 188, opacity: progress}}><CategoryBadge config={config} /></div>
      <div style={{position: "absolute", top: 292, opacity: progress}}><HookQuestion config={config} /></div>
      <div style={{position: "absolute", top: objectTop, width: 610, height: 610, display: "grid", placeItems: "center"}}>
        <div style={{position: "absolute", inset: 18, borderRadius: "50%", border: `5px solid ${config.theme.accent}`, opacity: progress * 0.76, boxShadow: `0 0 60px ${config.theme.accent}55`}} />
        <MysteryObject config={config} size={objectSize} progress={1 - progress} />
      </div>
      <div style={{position: "absolute", top: 790, width: 930, color: config.theme.text, fontSize: 68, textAlign: "center", opacity: 1 - progress}}>{config.cta.text}</div>
      <div style={{position: "absolute", top: 1015}}><NumberOptions config={config} frame={50} opacity={1 - progress} /></div>
      <div style={{position: "absolute", top: 1238, padding: "13px 26px", borderRadius: 14, background: config.theme.urgency, color: "#10131C", fontSize: 34, letterSpacing: 3, opacity: progress}}>{config.hook.ruleText}</div>
      <div style={{position: "absolute", top: 1392, opacity: progress}}><GlobalProgress config={config} absoluteFrame={Math.floor((1 - progress) * Math.max(0, config.timeline.loop.from - 1))} /></div>
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
    <div style={{position: "absolute", zIndex: 20, left: 90, top: 1505, width: 900, minHeight: 82, padding: "14px 22px", boxSizing: "border-box", borderRadius: 16, background: "rgba(4,8,18,.9)", border: "2px solid rgba(255,255,255,.15)", color: config.theme.text, textAlign: "center", fontSize: 29, lineHeight: 1.15, textShadow: "0 4px 0 #000"}}>
      {segment.text.split(/(\s+)/).map((token, index) => {
        if (/^\s+$/.test(token)) return token;
        wordIndex += 1;
        return <span key={`${token}-${index}`} style={{color: wordIndex === activeWordIndex ? config.theme.accent : config.theme.text}}>{token}</span>;
      })}
    </div>
  );
};

export const MusicDucker: React.FC<{config: MysteryVideoConfig}> = ({config}) => {
  const music = config.audio.music;
  if (!music) return null;
  return <Audio src={staticFile(music.publicSrc)} from={music.from} durationInFrames={music.durationInFrames} loop volume={(frame) => {
    const bed = interpolate(frame, [0, music.fadeInFrames, music.durationInFrames - music.fadeOutFrames, music.durationInFrames], [0, music.volume, music.volume, 0], clamp);
    const ratio = music.duckedVolume / music.volume;
    const duck = config.voice.segments.reduce((value, segment) => Math.min(value, interpolate(frame, [segment.start - music.duckFadeFrames, segment.start, segment.end, segment.end + music.duckFadeFrames], [1, ratio, ratio, 1], clamp)), 1);
    return bed * duck;
  }} />;
};

export const AudioTimeline: React.FC<{config: MysteryVideoConfig}> = ({config}) => {
  if (config.audio.status !== "complete" || config.voice.status !== "complete") return null;
  return (
    <>
      <MusicDucker config={config} />
      {config.voice.segments.map((segment) => <Audio key={segment.id} src={staticFile(segment.audioSrc)} from={segment.start} durationInFrames={segment.end - segment.start} />)}
      {config.audio.effects.map((effect) => <Audio key={effect.id} src={staticFile(effect.publicSrc)} from={effect.from} durationInFrames={effect.durationInFrames} volume={() => effect.volume} />)}
    </>
  );
};

export const SafeZoneOverlay: React.FC<{config: MysteryVideoConfig}> = ({config}) => config.debug.showSafeZones ? (
  <div style={{position: "absolute", zIndex: 40, left: 72, top: SAFE_TOP, width: 936, height: SAFE_BOTTOM - SAFE_TOP, border: "3px dashed #FF3B81", pointerEvents: "none"}} />
) : null;

export const DebugTimeline: React.FC<{config: MysteryVideoConfig}> = ({config}) => {
  const frame = useCurrentFrame();
  if (!config.debug.showRetentionMarkers && !config.debug.showSceneBoundaries && !config.debug.showTimestampLabels && !config.debug.showVoiceSegments) return null;
  const scenes = [config.timeline.hook, ...config.timeline.hints, config.timeline.countdown, config.timeline.reveal, config.timeline.cta, config.timeline.loop];
  const nextBeat = config.retentionBeats.find((beat) => beat.frame >= frame);
  const voice = activeSegment(config.voice.segments, frame);
  return (
    <div style={{position: "absolute", zIndex: 50, left: 20, top: 20, padding: 12, background: "rgba(0,0,0,.82)", color: "#00FF9D", fontFamily: "monospace", fontSize: 19}}>
      F{frame} · {(frame / 30).toFixed(2)}s · {config.variant}<br />
      {config.debug.showSceneBoundaries ? `scene ${scenes.findIndex((scene) => frame >= scene.from && frame < scene.from + scene.durationInFrames)}` : ""}
      {config.debug.showRetentionMarkers && nextBeat ? ` · beat ${nextBeat.id}@${nextBeat.frame}` : ""}
      {config.debug.showVoiceSegments && voice ? <><br />voice {voice.id} {voice.start}-{voice.end}</> : null}
    </div>
  );
};

export const RetentionDebugOverlay = DebugTimeline;
