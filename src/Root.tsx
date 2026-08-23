import {Composition, Still} from "remotion";
import {QUIZ_COPY_DURATION_IN_FRAMES, QuizVideoCopy} from "./compositions/QuizVideoCopy";
import {QuizThumbnail} from "./compositions/QuizThumbnail";
import quizConfig from "./generated/quiz-copy-episode.json";
import thumbnailConfig from "./generated/thumbnail-config.json";
import {defaultMysteryConfig, MysteryVideo} from "./compositions/MysteryVideo";
import type {MysteryVideoConfig} from "./mystery/types";
import {MYSTERY_PREFAB_GALLERY_DURATION, MysteryPrefabGallery} from "./compositions/MysteryPrefabGallery";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="QuizCapasCopy"
        component={QuizVideoCopy}
        durationInFrames={QUIZ_COPY_DURATION_IN_FRAMES}
        calculateMetadata={({props}) => {
          const config = (props as {config?: typeof quizConfig}).config ?? quizConfig;
          return {durationInFrames: config.durationInFrames};
        }}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{config: quizConfig}}
      />
      <Still
        id="ThumbnailVertical"
        component={QuizThumbnail}
        width={1080}
        height={1920}
        defaultProps={{config: thumbnailConfig, variant: "silhouette"}}
      />
      <Composition
        id="MysteryVideo"
        component={MysteryVideo}
        durationInFrames={defaultMysteryConfig.timeline.durationInFrames}
        calculateMetadata={({props}) => {
          const config = (props as {config?: MysteryVideoConfig}).config ?? defaultMysteryConfig;
          return {durationInFrames: config.timeline.durationInFrames};
        }}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{config: defaultMysteryConfig}}
      />
      <Composition
        id="MysteryPrefabGallery"
        component={MysteryPrefabGallery}
        durationInFrames={MYSTERY_PREFAB_GALLERY_DURATION}
        fps={30}
        width={3840}
        height={2160}
      />
    </>
  );
};
