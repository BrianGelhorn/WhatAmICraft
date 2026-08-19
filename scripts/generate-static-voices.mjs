import fs from "node:fs";
import process from "node:process";
import dotenv from "dotenv";
import {ElevenLabsClient} from "@elevenlabs/elevenlabs-js";
import {parseMedia} from "@remotion/media-parser";
import {nodeReader} from "@remotion/media-parser/node";

dotenv.config({path: ".env.local", quiet: true});

const apiKey = process.env.ELEVENLABS_API_KEY;
if (!apiKey) throw new Error("Falta ELEVENLABS_API_KEY");

const client = new ElevenLabsClient({apiKey});
const voiceId = process.env.ELEVENLABS_VOICE_ID ?? "pNInz6obpgDQGcFmaJgB";
const options = {
  modelId: "eleven_v3",
  outputFormat: "mp3_44100_128",
  voiceSettings: {speed: 1.08},
};
const voices = [
  ["hook", "[curious, punchy, clear] Can you guess it?", "public/audio/voice/quiz-copy/hook.mp3"],
  ["handoff", "[excited, clear, natural pacing] Three hints. One chance.", "public/audio/voice/quiz-copy/handoff.mp3"],
];

fs.mkdirSync("public/audio/voice/quiz-copy", {recursive: true});
for (const [id, text, output] of voices) {
  const audio = await client.textToSpeech.convert(voiceId, {...options, text});
  const chunks = [];
  for await (const chunk of audio) chunks.push(Buffer.from(chunk));
  fs.writeFileSync(output, Buffer.concat(chunks));
  const metadata = await parseMedia({
    src: output,
    fields: {durationInSeconds: true},
    reader: nodeReader,
    acknowledgeRemotionLicense: true,
  });
  console.log(`${id}: ${Math.ceil(metadata.durationInSeconds * 30)} frames`);
}
