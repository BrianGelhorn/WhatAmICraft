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
import {Audio} from "@remotion/media";
import {ClueSequenceSilent} from "../components/ClueSequenceSilent";
import config from "../generated/quiz-copy-episode.json";

const CONTENT_START_FRAME = config.timeline.contentStartFrame;
const clues = config.clues;
const CLUE_SEQUENCE_DURATION_IN_FRAMES =
  clues.length * config.timeline.hintDurationInFrames
  + config.timeline.revealDurationInFrames;
export const INTRO_AND_QUESTION_DURATION = CONTENT_START_FRAME;
export const QUIZ_COPY_DURATION_IN_FRAMES =
  CONTENT_START_FRAME + CLUE_SEQUENCE_DURATION_IN_FRAMES;

const enter = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
  easing: Easing.bezier(0.16, 1, 0.3, 1),
};

const REEL_ITEM_WIDTH = 150;
const REEL_STOP_FRAME = config.timeline.reelStopFrame;

const getReelPosition = (frame: number, stopIndex: number) =>
  interpolate(frame, [0, REEL_STOP_FRAME], [0, stopIndex], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.18, 0.9, 0.22, 1),
  });

export const QuizVideoCopy: React.FC = () => {
  const frame = useCurrentFrame();
  const music = config.audio.music;
  const isIntro = frame < CONTENT_START_FRAME;
  const typeAsset = `images/guess-types/hidden/${config.answer.guessType}.png`;
  const roulettePool = config.hook.rouletteIcons;
  const rouletteAssets = roulettePool;
  const rouletteActive = frame < REEL_STOP_FRAME;
  const reelAssets = [
    ...rouletteAssets,
    ...rouletteAssets,
    typeAsset,
    ...rouletteAssets,
  ];
  const reelStopIndex = rouletteAssets.length * 2;
  const reelPosition = getReelPosition(frame, reelStopIndex);
  const selectionImpact = interpolate(
    frame,
    [REEL_STOP_FRAME, REEL_STOP_FRAME + 2, REEL_STOP_FRAME + 8],
    [0, 1, 0],
    {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.quad)},
  );
  const reelOffset = 380 - (reelPosition + 0.5) * REEL_ITEM_WIDTH;
  const selectedRevealScale = interpolate(
    frame,
    [REEL_STOP_FRAME, REEL_STOP_FRAME + 5, REEL_STOP_FRAME + 12],
    [0.66, 1.08, 1.02],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.out(Easing.quad),
    },
  );
  const silhouettePulse = interpolate(
    frame,
    [
      REEL_STOP_FRAME,
      REEL_STOP_FRAME + 30,
      REEL_STOP_FRAME + 60,
      REEL_STOP_FRAME + 90,
      REEL_STOP_FRAME + 120,
      CONTENT_START_FRAME,
    ],
    [1, 1.03, 1, 1.03, 1, 0.98],
    {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.quad)},
  );

  return (
    <AbsoluteFill
      style={{
        overflow: "hidden",
        backgroundColor: "#071811",
        fontFamily: "Minecraft",
      }}
    >
      <style>{`@font-face {
        font-family: Minecraft;
        src: url(${staticFile("fonts/Minecraft-Bold.otf")}) format("opentype");
        font-weight: 400 900;
      }`}</style>

      <Audio
        src={staticFile(music.publicSrc)}
        from={music.from}
        durationInFrames={music.durationInFrames}
        loop
        volume={(musicFrame) => {
          const bedVolume = interpolate(
            musicFrame,
            [0, music.fadeInFrames, music.durationInFrames - music.fadeOutFrames, music.durationInFrames],
            [0, music.volume, music.volume, 0],
            {extrapolateLeft: "clamp", extrapolateRight: "clamp"},
          );
          const duckRatio = music.volume === 0 ? 0 : music.duckedVolume / music.volume;
          const speechLevel = config.audio.voices.reduce((level, voice) => {
            const voiceDuration = voice.durationInFrames / (voice.playbackRate ?? 1);
            const duckFade = Math.min(music.duckFadeFrames, voiceDuration / 3);
            return Math.min(level, interpolate(
              musicFrame,
              [
                voice.from - duckFade,
                voice.from + duckFade,
                voice.from + voiceDuration - duckFade,
                voice.from + voiceDuration + duckFade,
              ],
              [1, duckRatio, duckRatio, 1],
              {extrapolateLeft: "clamp", extrapolateRight: "clamp"},
            ));
          }, 1);
          return bedVolume * speechLevel;
        }}
      />

      {config.audio.voices.map((voice) => (
        <Audio
          key={voice.id}
          src={staticFile(voice.publicSrc)}
          from={voice.from}
          durationInFrames={voice.durationInFrames}
          volume={(localFrame) => {
            const playbackRate = voice.playbackRate ?? 1;
            const fadeOutFrames = voice.fadeOutFrames ?? 0;
            const effectiveDurationInFrames = voice.durationInFrames / playbackRate;
            const fadeEndFrame = Math.max(1, Math.floor(effectiveDurationInFrames) - 1);
            return voice.volume * (fadeOutFrames > 0
              ? interpolate(
                localFrame,
                [
                  Math.max(0, fadeEndFrame - fadeOutFrames),
                  fadeEndFrame,
                ],
                [1, 0],
                {extrapolateLeft: "clamp", extrapolateRight: "clamp"},
              )
              : 1);
          }}
          playbackRate={voice.playbackRate ?? 1}
        />
      ))}

      <Audio
        src={staticFile(config.audio.roulette.publicSrc)}
        from={config.audio.roulette.from}
        durationInFrames={config.audio.roulette.durationInFrames}
        volume={() => config.audio.roulette.volume}
      />

      {config.audio.effects.map((effect) => (
        <Audio
          key={effect.id}
          src={staticFile(effect.publicSrc)}
          from={effect.from}
          durationInFrames={effect.durationInFrames}
          volume={() => effect.volume}
        />
      ))}

      <CanvasImage
        name="Background"
        src={staticFile(config.background)}
        style={{
          position: "absolute",
          width: 1080,
          height: 1920,
          objectFit: "cover",
          filter: isIntro ? "blur(5px) brightness(.48) saturate(1.2)" : "blur(7px) brightness(.58)",
          scale: interpolate(frame, [0, QUIZ_COPY_DURATION_IN_FRAMES], [1.08, 1.14], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.linear,
          }),
        }}
      />

      {isIntro ? (
        <AbsoluteFill
          name="Hook"
          style={{
            background:
              "linear-gradient(180deg, rgba(2,8,18,.82), rgba(3,21,28,.2) 48%, rgba(2,8,18,.92))",
            opacity: interpolate(
              frame,
              [0, 6, CONTENT_START_FRAME - 10, CONTENT_START_FRAME - 1],
              [0, 1, 1, 0.28],
              enter,
            ),
          }}
        >
          <Interactive.Div
            name="Hook eyebrow"
            style={{
              position: "absolute",
              top: 170,
              width: 1080,
              color: "#ffd34f",
              fontSize: 38,
              fontWeight: 900,
              letterSpacing: 8,
              textAlign: "center",
              textShadow: "0 5px 0 #111, 0 0 20px rgba(255,211,79,.65)",
              opacity: interpolate(frame, [0, 6], [0, 1], enter),
              translate: interpolate(frame, [0, 8], ["0px -28px", "0px 0px"], enter),
            }}
          >
            {config.hook.eyebrow}
          </Interactive.Div>

          <div
            style={{
              position: "absolute",
              left: 170,
              top: 320,
              width: 740,
              height: 740,
              borderRadius: 56,
              border: "8px solid #7ec850",
              background:
                "radial-gradient(circle, rgba(126,200,80,.2), rgba(4,17,20,.72) 65%)",
              boxShadow:
                `0 0 0 14px rgba(4,16,23,.74), 0 0 ${rouletteActive ? 80 : 58}px ${rouletteActive ? "rgba(255,211,79,.8)" : "rgba(126,200,80,.65)"}, inset 0 0 60px rgba(82,167,232,.2)`,
              opacity: interpolate(frame, [0, 8], [0, 1], enter),
              scale: interpolate(frame, [0, 12], [0.78, 1], {...enter, output: "perceptual-scale"}),
            }}
          />
          <div
            style={{
              position: "absolute",
              left: 160,
              top: 500,
              width: 760,
              height: 320,
              overflow: "hidden",
              opacity: interpolate(
                frame,
                [0, 3, REEL_STOP_FRAME - 4, REEL_STOP_FRAME + 4],
                [0, 1, 1, 0],
                enter,
              ),
              maskImage: "linear-gradient(90deg, transparent, black 12%, black 88%, transparent)",
            }}
          >
            {reelAssets.map((src, index) => {
              const distance = Math.abs(index - reelPosition);
              return (
                <CanvasImage
                  key={`${src}-${index}`}
                  name={`Reel item ${index + 1}`}
                  src={staticFile(src)}
                  style={{
                    position: "absolute",
                    left: reelOffset + index * REEL_ITEM_WIDTH,
                    top: 16,
                    width: REEL_ITEM_WIDTH,
                    height: 280,
                    objectFit: "contain",
                    imageRendering: "pixelated",
                    filter:
                      "brightness(0) drop-shadow(0 18px 0 rgba(0,0,0,.8)) drop-shadow(0 0 32px rgba(126,200,80,.95))",
                    opacity: interpolate(distance, [0, 1.1, 2.3], [1, 0.62, 0], {
                      extrapolateLeft: "clamp",
                      extrapolateRight: "clamp",
                    }),
                    scale: silhouettePulse * interpolate(distance, [0, 1.1, 2.3], [1.08, 0.9, 0.76], {
                      extrapolateLeft: "clamp",
                      extrapolateRight: "clamp",
                      easing: Easing.out(Easing.quad),
                    }),
                  }}
                />
              );
            })}
          </div>

          <div
            aria-hidden="true"
            style={{
              position: "absolute",
              left: 535,
              top: 492,
              width: 10,
              height: 336,
              borderRadius: 10,
              background: rouletteActive ? "#ffd34f" : "#7ec850",
              boxShadow: rouletteActive
                ? "0 0 18px rgba(255,211,79,.9)"
                : `0 0 ${18 + selectionImpact * 18}px rgba(126,200,80,${0.8 + selectionImpact * 0.2})`,
              opacity: interpolate(
                frame,
                [8, 14, REEL_STOP_FRAME - 1, REEL_STOP_FRAME + 4],
                [0, 0.88, 0.88, 0],
                enter,
              ),
            }}
          />

          <div
            aria-hidden="true"
            style={{
              position: "absolute",
              left: 236,
              top: 386,
              width: 608,
              height: 608,
              borderRadius: "50%",
              border: "3px dashed rgba(255,211,79,.74)",
              borderRightColor: "transparent",
              opacity: interpolate(
                frame,
                [
                  Math.max(0, REEL_STOP_FRAME - 10),
                  REEL_STOP_FRAME - 2,
                  CONTENT_START_FRAME - 14,
                  CONTENT_START_FRAME,
                ],
                [0, 0.82, 0.82, 0],
                enter,
              ),
              transform: `rotate(${interpolate(
                frame,
                [Math.max(0, REEL_STOP_FRAME - 10), CONTENT_START_FRAME],
                [0, 250],
                {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                  easing: Easing.linear,
                },
              )}deg)`,
            }}
          />

          <CanvasImage
            name="Type silhouette"
            src={staticFile(typeAsset)}
            style={{
              position: "absolute",
              left: 260,
              top: 376,
              width: 560,
              height: 560,
              objectFit: "contain",
              imageRendering: "pixelated",
              filter:
                `brightness(0) drop-shadow(0 18px 0 rgba(0,0,0,.8)) drop-shadow(0 0 32px rgba(126,200,80,.95)) drop-shadow(0 0 ${18 + selectionImpact * 28}px rgba(255,211,79,${selectionImpact * 0.9}))`,
              opacity: interpolate(
                frame,
                [REEL_STOP_FRAME - 4, REEL_STOP_FRAME + 4],
                [0, 1],
                enter,
              ),
              transformOrigin: "center center",
              scale: selectedRevealScale,
            }}
          />

          <Interactive.Div
            name="Type label"
            style={{
              position: "absolute",
              top: 950,
              left: 330,
              width: 420,
              boxSizing: "border-box",
              padding: "12px 18px",
              borderRadius: 16,
              border: "4px solid #111923",
              background: "#ffd34f",
              color: "#111923",
              fontSize: 58,
              fontWeight: 900,
              letterSpacing: 5,
              textAlign: "center",
              textShadow: "0 5px 0 rgba(255,255,255,.32)",
              boxShadow: "0 10px 0 rgba(0,0,0,.48), 0 0 24px rgba(255,211,79,.55)",
              opacity: interpolate(
                frame,
                [REEL_STOP_FRAME - 1, REEL_STOP_FRAME],
                [0, 1],
                enter,
              ),
              scale: interpolate(
                frame,
                [REEL_STOP_FRAME - 1, REEL_STOP_FRAME + 4],
                [0.7, 1],
                {...enter, output: "perceptual-scale"},
              ),
            }}
          >
            {config.answer.guessType.toUpperCase()}!
          </Interactive.Div>

          <Interactive.Div
            name="Hook title"
            style={{
              position: "absolute",
              top: 1120,
              left: 50,
              width: 980,
              color: "white",
              fontSize: 92,
              fontWeight: 900,
              lineHeight: 1.02,
              textAlign: "center",
              textShadow: "0 9px 0 #111, 0 0 26px rgba(82,167,232,.75)",
              opacity: interpolate(
                frame,
                [config.timeline.hookTitleFromFrame, config.timeline.hookTitleFromFrame + 6],
                [0, 1],
                enter,
              ),
              scale: interpolate(
                frame,
                [config.timeline.hookTitleFromFrame, config.timeline.hookTitleFromFrame + 9],
                [0.7, 1],
                {...enter, output: "perceptual-scale"},
              ),
            }}
          >
            {config.hook.title}
          </Interactive.Div>

          <Interactive.Div
            name="Hook handoff"
            style={{
              position: "absolute",
              left: 80,
              bottom: 210,
              width: 920,
              boxSizing: "border-box",
              padding: "20px 24px",
              borderRadius: 20,
              border: "5px solid #111923",
              background: "#ffd34f",
              color: "#111923",
              fontSize: 42,
              fontWeight: 900,
              letterSpacing: 3,
              textAlign: "center",
              boxShadow: "0 12px 0 rgba(0,0,0,.48), 0 0 24px rgba(255,211,79,.42)",
              opacity: interpolate(
                frame,
                [config.timeline.handoffFromFrame, config.timeline.handoffFromFrame + 6],
                [0, 1],
                enter,
              ),
              translate: interpolate(
                frame,
                [config.timeline.handoffFromFrame, config.timeline.handoffFromFrame + 10],
                ["0px 35px", "0px 0px"],
                enter,
              ),
            }}
          >
            {config.hook.handoff}
          </Interactive.Div>

          <Interactive.Div
            name="Category chip"
            style={{
              position: "absolute",
              top: 1410,
              left: 340,
              width: 400,
              boxSizing: "border-box",
              padding: "12px 20px",
              borderRadius: 14,
              border: "3px solid #7ec850",
              background: "rgba(4,18,15,.92)",
              color: "#7ec850",
              fontSize: 30,
              fontWeight: 900,
              letterSpacing: 4,
              textAlign: "center",
              opacity: interpolate(
                frame,
                [
                  config.timeline.categoryFromFrame,
                  config.timeline.categoryFromFrame + 6,
                  CONTENT_START_FRAME - 22,
                  CONTENT_START_FRAME - 8,
                ],
                [0, 1, 1, 0],
                enter,
              ),
              translate: interpolate(
                frame,
                [config.timeline.categoryFromFrame, config.timeline.categoryFromFrame + 8],
                ["0px 18px", "0px 0px"],
                enter,
              ),
            }}
          >
            {config.hook.categoryPrefix}: {config.answer.guessType.toUpperCase()}
          </Interactive.Div>
        </AbsoluteFill>
      ) : null}

      <Sequence
        name="Quiz hints and reveal"
        from={CONTENT_START_FRAME}
        durationInFrames={CLUE_SEQUENCE_DURATION_IN_FRAMES}
        premountFor={30}
      >
        <ClueSequenceSilent
          clues={clues}
          hintUi={config.hintUi}
          reveal={config.reveal}
          timeline={config.timeline}
        />
      </Sequence>
    </AbsoluteFill>
  );
};
