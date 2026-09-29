import {Composition, Still} from "remotion";
import {QUIZ_COPY_DURATION_IN_FRAMES, QuizVideoCopy} from "./compositions/QuizVideoCopy";
import {QuizThumbnail} from "./compositions/QuizThumbnail";
import quizConfig from "./generated/quiz-copy-episode.json";
import thumbnailConfig from "./generated/thumbnail-config.json";

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
    </>
  );
};
