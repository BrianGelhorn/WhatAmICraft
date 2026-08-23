export type MysteryVariant = "fast" | "balanced" | "comment_bait";
export type VisualIntensity = "low" | "medium" | "high";
export type HintVisualType = "durability" | "combat" | "mob" | "recipe" | "generic";

export type WordTiming = {word: string; startFrame: number; endFrame: number};
export type VoiceSegment = {
  id: string;
  text: string;
  audioSrc: string;
  start: number;
  end: number;
  emphasisWords: string[];
  words: WordTiming[];
};

export type MysteryHint = {
  id: string;
  voiceText: string;
  displayText: string;
  fragments: string[];
  emphasisWords: string[];
  visualType: HintVisualType;
  visualAsset?: string;
  difficulty: "hard" | "medium" | "easy";
};

export type MysteryTimeline = {
  durationInFrames: number;
  hook: {from: number; durationInFrames: number};
  hints: Array<{from: number; durationInFrames: number}>;
  countdown: {from: number; durationInFrames: number};
  reveal: {from: number; durationInFrames: number};
  cta: {from: number; durationInFrames: number};
  loop: {from: number; durationInFrames: number};
};

export type MysteryVideoConfig = {
  id: string;
  format: "mystery-v2";
  language: string;
  variant: MysteryVariant;
  hookVariant: string;
  ctaVariant: string;
  visualIntensity: VisualIntensity;
  hypothesis: string;
  answer: {id: string; text: string; category: string; image: string; silhouette: string};
  background: string;
  hook: {question: string; ruleText: string; showBrandMark: boolean};
  hints: [MysteryHint, MysteryHint, MysteryHint];
  countdown: {displayText: string; values: number[]};
  reveal: {preRevealText: string; answerText: string};
  cta: {text: string; options: string[]};
  timeline: MysteryTimeline;
  retentionBeats: Array<{id: string; frame: number}>;
  theme: {
    mystery: string; surface: string; progress: string; accent: string; urgency: string;
    answer: string; text: string; muted: string; titleFont: string; bodyFont: string;
    outlinePx: number; cardRadius: number;
  };
  voice: {status: "pending" | "complete"; segments: VoiceSegment[]};
  audio: {
    status: "pending" | "complete";
    music?: {publicSrc: string; from: number; durationInFrames: number; volume: number; duckedVolume: number; fadeInFrames: number; fadeOutFrames: number; duckFadeFrames: number};
    effects: Array<{id: string; publicSrc: string; from: number; durationInFrames: number; volume: number; visualEvent: string; maxOffsetFrames: number}>;
  };
  debug: {showSafeZones: boolean; showSceneBoundaries: boolean; showTimestampLabels: boolean; showVoiceSegments: boolean; showRetentionMarkers: boolean};
};
