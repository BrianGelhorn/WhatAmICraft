import {Composition, Still} from "remotion";
import {QUIZ_COPY_DURATION_IN_FRAMES, QuizVideoCopy} from "./compositions/QuizVideoCopy";
import {QuizThumbnail} from "./compositions/QuizThumbnail";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="QuizCapasCopy"
        component={QuizVideoCopy}
        durationInFrames={QUIZ_COPY_DURATION_IN_FRAMES}
        fps={30}
        width={1080}
        height={1920}
      />
      <Still id="ThumbnailVertical" component={QuizThumbnail} width={1080} height={1920} defaultProps={{variant: "silhouette"}} />
    </>
  );
};
