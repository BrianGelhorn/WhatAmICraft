import {
  AbsoluteFill,
  CanvasImage,
  Easing,
  Interactive,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
} from "remotion";

type Clue = {text: string};
type HintUi = {label: string; cta: string};
type Reveal = {
  prompt: string;
  answerLabel: string;
  answerText: string;
  cta: string;
  icon: string;
  countdownFrom: number;
};
type Timeline = {
  hintDurationInFrames: number;
  revealDurationInFrames: number;
  answerStartFrame: number;
  countdownStepInFrames: number;
};

const enter = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
  easing: Easing.bezier(0.16, 1, 0.3, 1),
};

const HINT_CROSSFADE_FRAMES = 10;

const HintSlide: React.FC<{
  clueCount: number;
  cta: string;
  durationInFrames: number;
  index: number;
  label: string;
  text: string;
  activeDurationInFrames: number;
}> = ({clueCount, cta, durationInFrames, index, label, text, activeDurationInFrames}) => {
  const frame = useCurrentFrame();
  const fontSize = text.length > 74 ? 52 : text.length > 48 ? 60 : 70;

  return (
    <AbsoluteFill
      name={`Hint ${index + 1}`}
      style={{
        alignItems: "center",
        opacity: interpolate(
          frame,
          [0, 8, durationInFrames - HINT_CROSSFADE_FRAMES * 2, durationInFrames - 1],
          [0, 1, 1, 0],
          enter,
        ),
        translate: interpolate(
          frame,
          [durationInFrames - HINT_CROSSFADE_FRAMES * 2, durationInFrames - 1],
          ["0px 0px", "0px -18px"],
          enter,
        ),
      }}
    >
      <Interactive.Div
        name="Hint label"
        style={{
          position: "absolute",
          top: 230,
          padding: "18px 40px",
          borderRadius: 20,
          border: "4px solid #7ec850",
          background: "rgba(4,18,15,.96)",
          color: "#7ec850",
          fontSize: 42,
          fontWeight: 900,
          letterSpacing: 5,
          boxShadow: "0 12px 32px rgba(0,0,0,.44), 0 0 22px rgba(126,200,80,.4)",
          scale: interpolate(frame, [0, 9], [0.72, 1], {...enter, output: "perceptual-scale"}),
        }}
      >
        {label
          .replace("{current}", String(index + 1))
          .replace("{total}", String(clueCount))}
      </Interactive.Div>

      <Interactive.Div
        name="Hint card"
        style={{
          position: "absolute",
          top: 430,
          left: 60,
          width: 960,
          height: 680,
          boxSizing: "border-box",
          padding: "60px 54px",
          borderRadius: 48,
          border: "6px solid #7ec850",
          background: "linear-gradient(160deg, rgba(17,39,31,.98), rgba(3,14,13,.98))",
          color: "white",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize,
          fontWeight: 900,
          lineHeight: 1.2,
          textAlign: "center",
          textWrap: "balance",
          textShadow: "0 7px 0 #101010, 0 0 18px rgba(0,0,0,.88)",
          boxShadow: "0 26px 58px rgba(0,0,0,.58), 0 0 30px rgba(126,200,80,.35), inset 0 0 28px rgba(255,255,255,.04)",
          opacity: interpolate(frame, [2, 8], [0, 1], enter),
          translate: interpolate(frame, [2, 12], ["0px 54px", "0px 0px"], enter),
          scale: interpolate(frame, [2, 12], [0.9, 1], {...enter, output: "perceptual-scale"}),
        }}
      >
        {text}
      </Interactive.Div>

      <Interactive.Div
        name="Hint progress"
        style={{position: "absolute", bottom: 285, display: "flex", gap: 22}}
      >
        {Array.from({length: clueCount}, (_, dotIndex) => (
          <div
            key={dotIndex}
            style={{
              width: dotIndex === index ? 48 : 30,
              height: 30,
              borderRadius: 18,
              border: "4px solid #101817",
              background: dotIndex <= index ? "#7ec850" : "#4b5954",
              boxShadow: dotIndex === index ? "0 0 20px rgba(126,200,80,.9)" : "none",
            }}
          />
        ))}
      </Interactive.Div>

      <div
        style={{
          position: "absolute",
          left: 145,
          bottom: 225,
          width: 790,
          height: 16,
          overflow: "hidden",
          borderRadius: 9,
          border: "3px solid #101817",
          background: "rgba(16,24,23,.82)",
        }}
      >
        <div
          style={{
            width: `${interpolate(frame, [0, activeDurationInFrames - 1], [2, 100], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: Easing.linear,
            })}%`,
            height: "100%",
            background: "linear-gradient(90deg, #7ec850, #ffd34f)",
          }}
        />
      </div>

      <Interactive.Div
        name="Hint call to action"
        style={{
          position: "absolute",
          bottom: 145,
          width: 900,
          color: "#ffd34f",
          fontSize: 34,
          fontWeight: 900,
          letterSpacing: 4,
          textAlign: "center",
          textShadow: "0 5px 0 #111, 0 0 16px rgba(255,211,79,.55)",
            opacity: interpolate(
              frame,
            [12, 22, activeDurationInFrames - 24, activeDurationInFrames - 8],
            [0, 1, 1, 0],
            enter,
          ),
        }}
      >
        {cta}
      </Interactive.Div>
    </AbsoluteFill>
  );
};

const RevealSlide: React.FC<{reveal: Reveal; timeline: Timeline}> = ({reveal, timeline}) => {
  const frame = useCurrentFrame();
  const answerStart = timeline.answerStartFrame;
  const countdownFrame = frame % timeline.countdownStepInFrames;

  return (
    <AbsoluteFill name="Reveal" style={{alignItems: "center"}}>
      <AbsoluteFill
        style={{
          background: "radial-gradient(circle at 50% 45%, rgba(126,200,80,.22), rgba(2,8,18,.38) 62%, rgba(2,8,18,.72))",
          opacity: interpolate(frame, [0, 6], [0, 1], enter),
        }}
      />

      <Interactive.Div
        name="Reveal prompt"
        style={{
          position: "absolute",
          top: 245,
          width: 960,
          color: frame < answerStart ? "white" : "#ffd34f",
          fontSize: frame < answerStart ? 86 : 42,
          fontWeight: 900,
          letterSpacing: frame < answerStart ? 1 : 6,
          textAlign: "center",
          textShadow: "0 8px 0 #111, 0 0 22px rgba(126,200,80,.55)",
          opacity: interpolate(frame, [0, 6], [0, 1], enter),
          scale: interpolate(frame, [0, 10], [0.72, 1], {...enter, output: "perceptual-scale"}),
        }}
      >
        {frame < answerStart ? reveal.prompt : reveal.answerLabel}
      </Interactive.Div>

      {frame < answerStart ? (
        <Interactive.Div
          name="Reveal countdown"
          style={{
            position: "absolute",
            top: 700,
            width: 1080,
            color: "#7ec850",
            fontSize: 250,
            fontWeight: 900,
            textAlign: "center",
            textShadow: "0 14px 0 #111, 0 0 40px rgba(126,200,80,.9)",
            scale: interpolate(
              countdownFrame,
              [0, 5, timeline.countdownStepInFrames - 1],
              [0.68, 1.08, 0.9],
              enter,
            ),
          }}
        >
          {Math.max(1, reveal.countdownFrom - Math.floor(frame / timeline.countdownStepInFrames))}
        </Interactive.Div>
      ) : (
        <>
          <div
            style={{
              position: "absolute",
              top: 470,
              width: 760,
              height: 760,
              borderRadius: "50%",
              border: "7px solid rgba(126,200,80,.72)",
              background: "radial-gradient(circle, rgba(126,200,80,.42), rgba(82,167,232,.17) 48%, rgba(0,0,0,0) 72%)",
              boxShadow: "0 0 70px rgba(126,200,80,.48), inset 0 0 55px rgba(126,200,80,.2)",
              opacity: interpolate(frame, [answerStart, answerStart + 7], [0, 1], enter),
              scale: interpolate(frame, [answerStart, answerStart + 18], [0.55, 1], {...enter, output: "perceptual-scale"}),
            }}
          />
          <CanvasImage
            name="Answer icon"
            src={staticFile(reveal.icon)}
            style={{
              position: "absolute",
              top: 590,
              width: 520,
              height: 520,
              objectFit: "contain",
              imageRendering: "pixelated",
              filter: "drop-shadow(0 20px 8px rgba(0,0,0,.68)) drop-shadow(0 0 30px rgba(126,200,80,.88))",
              opacity: interpolate(frame, [answerStart, answerStart + 5], [0, 1], enter),
              scale: interpolate(frame, [answerStart, answerStart + 14], [0.3, 1], {...enter, output: "perceptual-scale"}),
              rotate: interpolate(frame, [answerStart, answerStart + 14], ["-6deg", "0deg"], enter),
            }}
          />
          <Interactive.Div
            name="Answer text"
            style={{
              position: "absolute",
              top: 1245,
              width: 1000,
              color: "#7ec850",
              fontSize: reveal.answerText.length > 16 ? 82 : 106,
              fontWeight: 900,
              lineHeight: 1.05,
              textAlign: "center",
              textShadow: "0 9px 0 #111, 0 0 25px rgba(126,200,80,.8)",
              opacity: interpolate(frame, [answerStart + 4, answerStart + 10], [0, 1], enter),
              translate: interpolate(frame, [answerStart + 4, answerStart + 16], ["0px 45px", "0px 0px"], enter),
            }}
          >
            {reveal.answerText}
          </Interactive.Div>
          <Interactive.Div
            name="Reveal call to action"
            style={{
              position: "absolute",
              bottom: 185,
              width: 940,
              padding: "18px 22px",
              boxSizing: "border-box",
              borderRadius: 18,
              border: "4px solid #ffd34f",
              background: "rgba(4,18,15,.92)",
              color: "#ffd34f",
              fontSize: 36,
              fontWeight: 900,
              letterSpacing: 2,
              textAlign: "center",
              textShadow: "0 5px 0 #111",
              opacity: interpolate(frame, [answerStart + 28, answerStart + 38], [0, 1], enter),
            }}
          >
            {reveal.cta}
          </Interactive.Div>
        </>
      )}
    </AbsoluteFill>
  );
};

export const ClueSequenceSilent: React.FC<{
  clues: Clue[];
  hintUi: HintUi;
  reveal: Reveal;
  timeline: Timeline;
}> = ({clues, hintUi, reveal, timeline}) => {
  const revealStart = clues.length * timeline.hintDurationInFrames;
  return (
    <AbsoluteFill>
      {clues.map((clue, index) => (
        <Sequence
          key={`clue-${index}`}
          name={`Hint ${index + 1}`}
          from={index * timeline.hintDurationInFrames}
          durationInFrames={
            timeline.hintDurationInFrames
            + (index < clues.length - 1 ? HINT_CROSSFADE_FRAMES : 0)
          }
          premountFor={15}
        >
          <HintSlide
            clueCount={clues.length}
            cta={hintUi.cta}
            durationInFrames={
              timeline.hintDurationInFrames
              + (index < clues.length - 1 ? HINT_CROSSFADE_FRAMES : 0)
            }
            index={index}
            label={hintUi.label}
            text={clue.text}
            activeDurationInFrames={timeline.hintDurationInFrames}
          />
        </Sequence>
      ))}
      <Sequence
        name="Answer reveal"
        from={revealStart}
        durationInFrames={timeline.revealDurationInFrames}
        premountFor={15}
      >
        <RevealSlide reveal={reveal} timeline={timeline} />
      </Sequence>
    </AbsoluteFill>
  );
};
