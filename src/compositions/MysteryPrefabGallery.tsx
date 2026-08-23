import {AbsoluteFill, staticFile} from "remotion";
import catalog from "../generated/mystery-v2-visual-prefabs.json";
import {MysteryPrefabCard} from "../components/mystery/MysteryPrefabGallery";

export const MYSTERY_PREFAB_GALLERY_DURATION = 120;

export const MysteryPrefabGallery: React.FC = () => (
  <AbsoluteFill style={{background: "#050812", padding: 34, boxSizing: "border-box"}}>
    <style>{`@font-face {font-family:Minecraft;src:url(${staticFile("fonts/Minecraft-Bold.otf")}) format('opentype');font-weight:400 900;}`}</style>
    <div style={{display: "grid", gridTemplateColumns: "repeat(6,1fr)", gridTemplateRows: "repeat(5,1fr)", gap: 18, width: "100%", height: "100%"}}>
      {catalog.prefabs.map((prefab) => <MysteryPrefabCard key={prefab.id} prefab={prefab} />)}
    </div>
  </AbsoluteFill>
);
