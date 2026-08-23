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
import {DurabilityLossVisual} from "./DurabilityLossVisual";
import {StackLimitVisual} from "./StackLimitVisual";

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
    <div style={{display: "flex", gap: 18, padding: 10, borderRadius: 26, background: `${config.theme.mystery}CC`, boxShadow: "0 12px 28px rgba(0,0,0,.35)"}}>
      {config.timeline.hints.map((hint, index) => {
        const active = absoluteFrame >= hint.from;
        const entered = interpolate(absoluteFrame - hint.from, [0, 7], [0, 1], ease);
        const color = urgency ? config.theme.urgency : config.theme.progress;
        return <div key={index} style={{width: 82, height: 58, display: "grid", placeItems: "center", border: `4px solid ${active ? color : "#33415F"}`, borderRadius: 20, background: active ? `linear-gradient(145deg, ${config.theme.surface}, ${color}2B)` : `${config.theme.mystery}AA`, color: active ? config.theme.text : config.theme.muted, fontSize: 28, boxShadow: active ? `0 8px 0 #02040A, 0 0 18px ${color}55` : "inset 0 0 0 2px rgba(255,255,255,.03)", transform: `scale(${active ? 0.9 + entered * 0.1 : 1})`}}>{index + 1}</div>;
      })}
    </div>
  );
};

export const ProgressMeter = GlobalProgress;

const RoundedStage: React.FC<{config: MysteryVideoConfig; color: string; children: React.ReactNode; height?: number}> = ({config, color, children, height = 570}) => (
  <div style={{position: "relative", width: 900, height, display: "grid", placeItems: "center", overflow: "hidden", borderRadius: 62, border: `4px solid ${color}88`, background: `linear-gradient(150deg, ${config.theme.surface}F2, ${config.theme.mystery}E6 68%, ${color}18)`, boxShadow: `0 22px 0 #02040A99, inset 0 0 0 3px rgba(255,255,255,.04), 0 0 42px ${color}22`}}>
    <div style={{position: "absolute", width: 520, height: 520, borderRadius: "50%", background: `radial-gradient(circle, ${color}20, transparent 68%)`}} />
    {children}
  </div>
);

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
        name="Category silhouette"
        src={staticFile(config.answer.silhouette)}
        style={{position: "absolute", inset: 0, width: size, height: size, objectFit: "contain", imageRendering: "pixelated", filter: `brightness(0) drop-shadow(0 22px 0 #02040A) drop-shadow(0 0 ${30 + reaction * 28}px ${config.theme.accent})`, opacity: 1 - progress}}
      />
      <div style={{position: "absolute", inset: 0, display: "grid", placeItems: "center", color: config.theme.accent, fontSize: size * 0.28, lineHeight: 1, textShadow: "0 8px 0 #02040A, 0 0 24px #02040A", opacity: 1 - progress}}>?</div>
      <CanvasImage
        name="Answer image"
        src={staticFile(config.answer.image)}
        style={{position: "absolute", inset: 0, width: size, height: size, objectFit: "contain", imageRendering: "pixelated", filter: `drop-shadow(0 22px 8px #02040ACC) drop-shadow(0 0 44px ${config.theme.answer})`, opacity: progress, transform: `scale(${0.86 + progress * 0.14})`}}
      />
    </div>
  );
};

export const HookQuestion: React.FC<{config: MysteryVideoConfig}> = ({config}) => (
  <div style={{width: 930, display: "flex", flexDirection: "column", alignItems: "center", gap: 8, textAlign: "center", overflowWrap: "anywhere"}}>
    <div style={{color: config.theme.muted, fontSize: fittedFontSize(config.hook.question, 48, 38, 18), letterSpacing: 7, textShadow: "0 6px 0 #02040A"}}>{config.hook.question}</div>
    <div style={{color: config.theme.text, fontSize: fittedFontSize(config.hook.emphasis, 128, 82, 12), lineHeight: 0.95, textShadow: `0 11px 0 #02040A, 0 0 34px ${config.theme.accent}88`}}>
      {config.hook.emphasis}
    </div>
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
      <div style={{position: "absolute", top: 520, width: 760, height: 650, display: "grid", placeItems: "center", overflow: "hidden", borderRadius: 72, border: `4px solid ${config.theme.accent}99`, background: `linear-gradient(150deg, ${config.theme.surface}F4, ${config.theme.mystery}E8 70%, ${config.theme.accent}1F)`, boxShadow: `0 24px 0 #02040A99, inset 0 0 0 3px rgba(255,255,255,.05), 0 0 54px ${config.theme.accent}22`, transform: `scale(${0.94 + impact * 0.06})`}}>
        <div style={{position: "absolute", inset: 45, borderRadius: "50%", border: `5px solid ${config.theme.accent}`, opacity: 0.68, transform: `scale(${ring})`, boxShadow: `0 0 60px ${config.theme.accent}44`}} />
        <MysteryObject config={config} size={520} reaction={Math.sin(frame / 4) * 0.2 + 0.2} />
      </div>
      <div style={{position: "absolute", top: 1238, padding: "15px 30px", borderRadius: 28, background: `linear-gradient(135deg, ${config.theme.urgency}, ${config.theme.accent})`, color: "#10131C", fontSize: 34, letterSpacing: 3, boxShadow: "0 12px 0 rgba(0,0,0,.42), 0 0 28px rgba(255,107,53,.28)"}}>{config.hook.ruleText}</div>
      <div style={{position: "absolute", top: 1392}}><GlobalProgress config={config} absoluteFrame={frame} /></div>
    </AbsoluteFill>
  );
};

export const HintHeader: React.FC<{config: MysteryVideoConfig; index: number}> = ({config, index}) => (
  <div style={{display: "flex", alignItems: "center", gap: 16, padding: "10px 22px", borderRadius: 999, border: `3px solid ${config.theme.progress}66`, background: `${config.theme.surface}DD`, color: config.theme.muted, fontSize: 28, letterSpacing: 5, boxShadow: "0 10px 24px rgba(0,0,0,.28)"}}>
    <span style={{color: config.theme.progress}}>0{index + 1}</span><span>HINT</span>
  </div>
);

export const HintKeyword: React.FC<{config: MysteryVideoConfig; hint: MysteryHint; durationInFrames: number}> = ({config, hint, durationInFrames}) => {
  const frame = useCurrentFrame();
  const switchFrame = Math.floor(durationInFrames * (hint.visual.steps[1]?.from ?? 1));
  return (
    <div style={{position: "relative", width: 940, height: 150, borderRadius: 34, border: `3px solid ${config.theme.accent}45`, background: `${config.theme.mystery}B8`, boxShadow: "0 14px 30px rgba(0,0,0,.28)"}}>
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

const stepFrame = (duration: number, from: number) => Math.floor(duration * from);

export const DurabilityLossPrefab: React.FC<{config: MysteryVideoConfig; hint: MysteryHint}> = ({config, hint}) => (
  <div style={{position: "relative", width: 780, height: 520}}>
    <div style={{position: "absolute", left: 190, top: 5, width: 400, textAlign: "center", color: config.theme.urgency, fontSize: 29, letterSpacing: 3, textShadow: "0 5px 0 #02040A"}}>{"label" in hint.visual.steps[0] ? hint.visual.steps[0].label : ""}</div>
    <div style={{position: "absolute", left: 228, top: 60}}><DurabilityLossVisual assetSrc={config.answer.silhouette} size={324} healthyColor={config.theme.answer} warningColor={config.theme.urgency} criticalColor="#FF3048" conceal /></div>
  </div>
);

export const StackLimitPrefab: React.FC<{config: MysteryVideoConfig; hint: MysteryHint}> = ({config, hint}) => {
  const step = hint.visual.steps.find((candidate) => candidate.type === "stack-limit");
  return (
    <div style={{position: "relative", width: 780, height: 520}}>
      <div style={{position: "absolute", left: 190, top: 5, width: 400, textAlign: "center", color: config.theme.accent, fontSize: 29, letterSpacing: 3, textShadow: "0 5px 0 #02040A"}}>{step && "label" in step ? step.label : ""}</div>
      <div style={{position: "absolute", left: 228, top: 60}}><StackLimitVisual assetSrc={config.answer.silhouette} stackValue={step && "value" in step ? step.value : "1"} accentColor={config.theme.accent} conceal /></div>
    </div>
  );
};

export const InventoryPropertiesPrefab: React.FC<{config: MysteryVideoConfig; hint: MysteryHint; duration: number}> = ({config, hint, duration}) => {
  const frame = useCurrentFrame();
  const [firstStep, secondStep] = hint.visual.steps;
  const switchAt = secondStep ? stepFrame(duration, secondStep.from) : duration;
  const secondPhase = secondStep ? interpolate(frame, [switchAt - 3, switchAt + 5], [0, 1], ease) : 0;
  const activeStep = secondStep && secondPhase > 0.5 ? secondStep : firstStep;
  const durabilityStep = hint.visual.steps.find((step) => step.type === "durability");
  const stackStep = hint.visual.steps.find((step) => step.type === "stack-limit");
  const durabilityStart = durabilityStep ? stepFrame(duration, durabilityStep.from) : 0;
  const durability = interpolate(frame, [durabilityStart + 8, durabilityStart + duration * 0.42], [220, 72], ease);
  const durabilityOpacity = (firstStep.type === "durability" ? 1 - secondPhase : 0) + (secondStep?.type === "durability" ? secondPhase : 0);
  const stackOpacity = (firstStep.type === "stack-limit" ? 1 - secondPhase : 0) + (secondStep?.type === "stack-limit" ? secondPhase : 0);
  const slotEntry = interpolate(frame, [0, 9], [0, 1], ease);
  return (
    <div style={{position: "relative", width: 780, height: 520}}>
      <div style={{position: "absolute", left: 230, top: 5, width: 320, textAlign: "center", color: activeStep.type === "stack-limit" ? config.theme.accent : config.theme.urgency, fontSize: 29, letterSpacing: 3, opacity: slotEntry, textShadow: "0 5px 0 #02040A"}}>{"label" in activeStep ? activeStep.label : ""}</div>
      <div style={{position: "absolute", left: 228, top: 60, width: 324, height: 324, display: "grid", placeItems: "center", overflow: "hidden", borderRadius: 42, border: "10px solid #8892A8", background: "linear-gradient(145deg, #3B455A, #252C3D)", boxShadow: "inset 0 0 0 8px #171D2B, 0 16px 0 #02040A, 0 0 30px rgba(255,209,102,.2)", opacity: slotEntry, transform: `scale(${0.9 + slotEntry * 0.1})`}}>
        <MysteryObject config={config} size={250} reaction={0.2} />
        <div style={{position: "absolute", left: 30, bottom: 20, width: 232, height: 25, padding: 4, borderRadius: 10, background: "#111827", border: "4px solid #02040A", opacity: durabilityOpacity}}>
          <div style={{width: durability, height: "100%", borderRadius: 5, background: durability > 135 ? config.theme.answer : config.theme.urgency, boxShadow: `0 0 12px ${durability > 135 ? config.theme.answer : config.theme.urgency}`}} />
        </div>
        {stackStep?.type === "stack-limit" ? <div style={{position: "absolute", right: 15, bottom: 12, width: 66, height: 66, display: "grid", placeItems: "center", borderRadius: 22, background: `${config.theme.mystery}E8`, color: config.theme.text, fontSize: 48, textShadow: "0 5px 0 #000", boxShadow: "0 7px 0 #02040A", opacity: stackOpacity, transform: `scale(${0.8 + stackOpacity * 0.2})`}}>{stackStep.value}</div> : null}
      </div>
    </div>
  );
};

export const ItemEntityInteractionPrefab: React.FC<{config: MysteryVideoConfig; hint: MysteryHint; duration: number}> = ({config, hint, duration}) => {
  const frame = useCurrentFrame();
  const [firstStep, secondStep] = hint.visual.steps;
  const switchAt = secondStep ? stepFrame(duration, secondStep.from) : duration;
  const secondPhase = secondStep ? interpolate(frame, [switchAt - 3, switchAt + 5], [0, 1], ease) : 0;
  const opacityFor = (type: "melee" | "ranged") => (firstStep.type === type ? 1 - secondPhase : 0) + (secondStep?.type === type ? secondPhase : 0);
  const meleeStart = stepFrame(duration, hint.visual.steps.find((step) => step.type === "melee")?.from ?? 0);
  const rangedStart = stepFrame(duration, hint.visual.steps.find((step) => step.type === "ranged")?.from ?? 0);
  const meleeStrike = interpolate(frame, [meleeStart + 8, meleeStart + 24], [0, 1], ease);
  const thrownStrike = interpolate(frame, [rangedStart - 5, rangedStart + 19], [0, 1], ease);
  const meleeImpact = interpolate(frame, [meleeStart + 18, meleeStart + 23, meleeStart + 31], [0, 1, 0], clamp);
  const rangedImpact = interpolate(frame, [rangedStart + 14, rangedStart + 19, rangedStart + 27], [0, 1, 0], clamp);
  const impact = Math.max(meleeImpact * opacityFor("melee"), rangedImpact * opacityFor("ranged"));
  return (
    <div style={{position: "relative", width: 850, height: 520}}>
      {hint.visual.supportingAsset ? <CanvasImage src={staticFile(hint.visual.supportingAsset)} style={{position: "absolute", right: 65 + impact * 10, top: 90, width: 270, height: 340, objectFit: "contain", imageRendering: "pixelated", filter: `drop-shadow(0 12px 0 #02040A) drop-shadow(0 0 ${impact * 28}px ${config.theme.urgency})`, transform: `rotate(${impact * 5}deg) scale(${1 - impact * 0.04})`}} /> : null}
      <div style={{position: "absolute", left: 65 + meleeStrike * 250, top: 115, opacity: opacityFor("melee"), transform: `rotate(${meleeStrike * -16}deg)`}}><MysteryObject config={config} size={260} reaction={meleeStrike * 0.5} /></div>
      <div style={{position: "absolute", left: 20 + thrownStrike * 465, top: 150 - Math.sin(thrownStrike * Math.PI) * 105, opacity: opacityFor("ranged"), transform: `rotate(${thrownStrike * 16 - 8}deg)`}}><MysteryObject config={config} size={220} reaction={thrownStrike * 0.35} /></div>
      {[0, 1, 2, 3].map((index) => <div key={index} style={{position: "absolute", left: 590 + Math.cos(index * 1.7) * impact * 80, top: 235 + Math.sin(index * 1.7) * impact * 90, width: 18 + index * 3, height: 18 + index * 3, borderRadius: 6, background: index % 2 ? config.theme.accent : config.theme.urgency, opacity: impact, transform: `rotate(${index * 25}deg)`}} />)}
    </div>
  );
};

export const EntityEquipmentPrefab: React.FC<{config: MysteryVideoConfig; hint: MysteryHint; duration: number}> = ({config, hint, duration}) => {
  const frame = useCurrentFrame();
  const start = stepFrame(duration, hint.visual.steps[0].from);
  const rise = interpolate(frame, [start + 8, start + 28], [0, 1], ease);
  const equip = interpolate(frame, [start + duration * 0.34, start + duration * 0.64], [0, 1], ease);
  const answerLeft = interpolate(equip, [0, 1], [535, 290]);
  const answerTop = interpolate(equip, [0, 1], [115, 150]);
  return (
    <div style={{position: "relative", width: 850, height: 540, overflow: "hidden"}}>
      {hint.visual.environment === "water" ? <>{[0, 1, 2].map((index) => <div key={`wave-${index}`} style={{position: "absolute", left: -80 + index * 35, top: 400 + index * 28 + Math.sin((frame + index * 9) / 7) * 10, width: 980, height: 90, borderRadius: "50%", border: `5px solid ${config.theme.progress}`, opacity: 0.18 + index * 0.09}} />)}
      {[0, 1, 2, 3, 4].map((index) => <div key={`bubble-${index}`} style={{position: "absolute", left: 100 + index * 74, top: 360 - ((frame * (2 + index * 0.15) + index * 75) % 250), width: 16 + index * 3, height: 16 + index * 3, borderRadius: "50%", border: `4px solid ${config.theme.progress}`, opacity: 0.18 + index * 0.07}} />)}</> : null}
      {hint.visual.supportingAsset ? <CanvasImage src={staticFile(hint.visual.supportingAsset)} style={{position: "absolute", left: 100, top: 80 + (1 - rise) * 220, width: 300, height: 340, objectFit: "contain", imageRendering: "pixelated", filter: `drop-shadow(0 0 28px ${config.theme.progress})`, transform: `scale(${0.92 + rise * 0.08})`}} /> : null}
      <div style={{position: "absolute", left: answerLeft, top: answerTop, opacity: 0.25 + equip * 0.75, transform: `rotate(${-18 + equip * 8}deg) scale(${0.9 + equip * 0.1})`}}><MysteryObject config={config} size={280} reaction={equip} /></div>
    </div>
  );
};

export const HintVisual: React.FC<{config: MysteryVideoConfig; hint: MysteryHint; durationInFrames: number}> = ({config, hint, durationInFrames}) => {
  if (hint.visual.prefab === "durability-loss") return <DurabilityLossPrefab config={config} hint={hint} />;
  if (hint.visual.prefab === "stack-limit") return <StackLimitPrefab config={config} hint={hint} />;
  if (hint.visual.prefab === "inventory-properties") return <InventoryPropertiesPrefab config={config} hint={hint} duration={durationInFrames} />;
  if (hint.visual.prefab === "item-entity-interaction") return <ItemEntityInteractionPrefab config={config} hint={hint} duration={durationInFrames} />;
  if (hint.visual.prefab === "entity-equipment") return <EntityEquipmentPrefab config={config} hint={hint} duration={durationInFrames} />;
  throw new Error(`Unsupported mystery visual prefab: ${hint.visual.prefab}`);
};

export const HintScene: React.FC<{config: MysteryVideoConfig; hint: MysteryHint; index: number; durationInFrames: number}> = ({config, hint, index, durationInFrames}) => {
  const frame = useCurrentFrame();
  const scene = config.timeline.hints[index];
  const entry = interpolate(frame, [0, 8], [0, 1], ease);
  return (
    <AbsoluteFill name={`Hint ${index + 1}`} style={{alignItems: "center", background: `radial-gradient(circle at 50% 55%, ${index === 2 ? config.theme.progress : config.theme.accent}18, transparent 62%)`}}>
      <div style={{position: "absolute", top: 190, opacity: entry}}><HintHeader config={config} index={index} /></div>
      <div style={{position: "absolute", top: 295}}><HintKeyword config={config} hint={hint} durationInFrames={durationInFrames} /></div>
      <div style={{position: "absolute", top: 515, opacity: entry, transform: `translateY(${(1 - entry) * 30}px) scale(${0.96 + entry * 0.04})`}}><RoundedStage config={config} color={index === 2 ? config.theme.progress : config.theme.accent}><HintVisual config={config} hint={hint} durationInFrames={durationInFrames} /></RoundedStage></div>
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
      <div style={{position: "absolute", top: 445, width: 760, height: 600, borderRadius: 72, border: `5px solid ${numberColor}88`, background: `linear-gradient(155deg, ${config.theme.surface}F4, ${config.theme.mystery}E8)`, boxShadow: `0 24px 0 #02040A99, inset 0 0 0 3px rgba(255,255,255,.05), 0 0 48px ${numberColor}33`, transform: `scale(${0.96 + scale * 0.04})`}} />
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
  const entry = interpolate(frame, [0, 10], [0, 1], ease);
  return (
    <AbsoluteFill name="Reveal" style={{alignItems: "center", background: `radial-gradient(circle at 50% 48%, ${config.theme.answer}48, transparent 64%)`}}>
      <RevealAnswer config={config} />
      <div style={{position: "absolute", top: 350, transform: `translateY(${(1 - entry) * 26}px) scale(${0.96 + entry * 0.04})`}}><RoundedStage config={config} color={config.theme.answer} height={680}><RevealTransform config={config} /></RoundedStage></div>
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
  const entry = interpolate(frame, [0, 10], [0, 1], ease);
  return (
    <AbsoluteFill name="Comment CTA" style={{alignItems: "center"}}>
      <div style={{position: "absolute", top: 285, width: 580, height: 470, display: "grid", placeItems: "center", overflow: "hidden", borderRadius: 66, border: `4px solid ${config.theme.answer}88`, background: `linear-gradient(150deg, ${config.theme.surface}EE, ${config.theme.answer}16)`, boxShadow: "0 20px 0 #02040A88, inset 0 0 0 3px rgba(255,255,255,.04)", transform: `scale(${0.94 + entry * 0.06})`}}><MysteryObject config={config} progress={1} size={420} reaction={0.35} /></div>
      <div style={{position: "absolute", top: 790, width: 930, padding: "18px 24px", boxSizing: "border-box", borderRadius: 34, background: `${config.theme.mystery}C9`, color: config.theme.text, fontSize: fittedFontSize(config.cta.text, 60, 48, 17), lineHeight: 1.04, textAlign: "center", overflowWrap: "anywhere", textShadow: "0 8px 0 #02040A", boxShadow: "0 14px 28px rgba(0,0,0,.28)"}}>{config.cta.text}</div>
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
      <div style={{position: "absolute", top: objectTop, width: 760, height: 650, display: "grid", placeItems: "center", overflow: "hidden", borderRadius: 72, border: `4px solid ${config.theme.accent}99`, background: `linear-gradient(150deg, ${config.theme.surface}F4, ${config.theme.mystery}E8 70%, ${config.theme.accent}1F)`, boxShadow: `0 24px 0 #02040A99, inset 0 0 0 3px rgba(255,255,255,.05)`, opacity: 0.25 + progress * 0.75}}>
        <div style={{position: "absolute", inset: 45, borderRadius: "50%", border: `5px solid ${config.theme.accent}`, opacity: progress * 0.68, boxShadow: `0 0 60px ${config.theme.accent}44`}} />
        <MysteryObject config={config} size={objectSize} progress={1 - progress} />
      </div>
      <div style={{position: "absolute", top: 790, width: 930, color: config.theme.text, fontSize: 68, textAlign: "center", opacity: 1 - progress}}>{config.cta.text}</div>
      <div style={{position: "absolute", top: 1015}}><NumberOptions config={config} frame={50} opacity={1 - progress} /></div>
      <div style={{position: "absolute", top: 1238, padding: "15px 30px", borderRadius: 28, background: `linear-gradient(135deg, ${config.theme.urgency}, ${config.theme.accent})`, color: "#10131C", fontSize: 34, letterSpacing: 3, opacity: progress}}>{config.hook.ruleText}</div>
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
    <div style={{position: "absolute", zIndex: 20, left: 90, top: 1505, width: 900, minHeight: 82, padding: "14px 22px", boxSizing: "border-box", borderRadius: 28, background: "rgba(4,8,18,.9)", border: "2px solid rgba(255,255,255,.15)", color: config.theme.text, textAlign: "center", fontSize: 29, lineHeight: 1.15, textShadow: "0 4px 0 #000", boxShadow: "0 12px 30px rgba(0,0,0,.3)"}}>
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
