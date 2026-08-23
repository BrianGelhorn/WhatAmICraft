import {CanvasImage, staticFile, useCurrentFrame} from "remotion";
import catalog from "../../generated/mystery-v2-visual-prefabs.json";

export type MysteryPrefabRecord = (typeof catalog.prefabs)[number];

const colors = {cyan: "#2DE2E6", gold: "#FFD166", orange: "#FF6B35", green: "#6BFF95", ink: "#070B1A", surface: "#10172B", text: "#F7FAFF"};
const phase = (frame: number, offset = 0) => (Math.sin((frame + offset) / 13) + 1) / 2;

const Asset: React.FC<{src: string; size?: number; style?: React.CSSProperties}> = ({src, size = 112, style}) => (
  <CanvasImage src={staticFile(src)} style={{width: size, height: size, objectFit: "contain", imageRendering: "pixelated", filter: "drop-shadow(0 10px 0 rgba(0,0,0,.65))", ...style}} />
);

const Slot: React.FC<{children: React.ReactNode; size?: number}> = ({children, size = 150}) => (
  <div style={{position: "relative", width: size, height: size, display: "grid", placeItems: "center", borderRadius: 28, border: "7px solid #8590A8", background: "linear-gradient(145deg,#3B455A,#20283A)", boxShadow: "inset 0 0 0 6px #111827,0 12px 0 #02040A"}}>{children}</div>
);

const Meter: React.FC<{value: number; color?: string; width?: number}> = ({value, color = colors.green, width = 150}) => (
  <div style={{width, height: 20, padding: 3, borderRadius: 8, background: "#080C16", border: "3px solid #02040A"}}>
    <div style={{width: `${Math.max(5, value * 100)}%`, height: "100%", borderRadius: 4, background: color, boxShadow: `0 0 12px ${color}`}} />
  </div>
);

const EntityPair: React.FC<{left: string; right: string; progress: number; projectile?: boolean}> = ({left, right, progress, projectile}) => (
  <div style={{position: "relative", width: 420, height: 210}}>
    <Asset src={right} size={150} style={{position: "absolute", right: 30, top: 30, transform: `rotate(${progress * 5}deg)`}} />
    <Asset src={left} size={130} style={{position: "absolute", left: 20 + progress * (projectile ? 245 : 165), top: projectile ? 72 - Math.sin(progress * Math.PI) * 58 : 55, transform: `rotate(${projectile ? progress * 25 : -progress * 18}deg)`}} />
    {progress > 0.72 ? [0, 1, 2].map((index) => <div key={index} style={{position: "absolute", left: 308 + index * 18, top: 95 + (index - 1) * 22, width: 13, height: 13, borderRadius: 4, background: index % 2 ? colors.gold : colors.orange, opacity: (progress - 0.72) / 0.28}} />) : null}
  </div>
);

const ScenarioVisual: React.FC<{prefab: MysteryPrefabRecord}> = ({prefab}) => {
  const frame = useCurrentFrame();
  const p = phase(frame, prefab.number * 4);
  const q = phase(frame, prefab.number * 4 + 24);
  const [a, b, c] = prefab.assets;
  const center: React.CSSProperties = {position: "relative", width: 470, height: 245, display: "grid", placeItems: "center"};

  switch (prefab.id) {
    case "durability-loss": return <div style={center}><Slot><Asset src={a} /><div style={{position: "absolute", bottom: 13}}><Meter value={1 - p * 0.8} color={p > 0.65 ? colors.orange : colors.green} width={108} /></div></Slot></div>;
    case "stack-limit": return <div style={center}><Slot><Asset src={a} /><div style={{position: "absolute", right: 10, bottom: 7, padding: "2px 10px", borderRadius: 12, background: colors.ink, color: colors.text, fontSize: 34, transform: `scale(${0.92 + p * 0.08})`}}>16</div></Slot></div>;
    case "charge-level": return <div style={center}><div style={{position: "absolute", width: 185, height: 185, borderRadius: "50%", background: `conic-gradient(${colors.cyan} ${p * 360}deg,#26324C 0)`, boxShadow: `0 0 28px ${colors.cyan}55`}} /><div style={{position: "absolute", width: 150, height: 150, borderRadius: "50%", background: colors.surface}} /><Asset src={a} size={125} style={{zIndex: 2, transform: `scale(${0.9 + p * 0.1})`}} /></div>;
    case "cooldown": return <div style={center}><Asset src={a} size={150} style={{opacity: 0.45 + p * 0.55}} /><div style={{position: "absolute", width: 184, height: 184, borderRadius: "50%", border: `9px solid ${colors.orange}`, borderTopColor: "transparent", transform: `rotate(${p * 320}deg)`}} /><div style={{position: "absolute", bottom: 18, color: colors.orange, fontSize: 24}}>{p > 0.75 ? "READY" : "WAIT"}</div></div>;
    case "enchantment-glint": return <div style={center}><Asset src={b} size={86} style={{position: "absolute", left: 72, top: 85, opacity: 0.8}} /><Asset src={a} size={165} style={{filter: `drop-shadow(0 10px 0 #02040A) drop-shadow(0 0 ${15 + p * 30}px #B46BFF) hue-rotate(${p * 120}deg)`}} />{[0, 1, 2].map((i) => <div key={i} style={{position: "absolute", left: 230 + Math.cos(i * 2.1) * (55 + p * 25), top: 120 + Math.sin(i * 2.1) * (55 + p * 25), color: colors.gold, fontSize: 28, opacity: p}}>✦</div>)}</div>;
    case "consumable-bites": return <div style={center}><Asset src={a} size={170} style={{transform: `scale(${1 - p * 0.18}) rotate(${p * -8}deg)`}} />{[0, 1, 2].map((i) => <div key={i} style={{position: "absolute", left: 280 + i * 24, top: 65 + i * 28, width: 30, height: 30, borderRadius: "50%", background: colors.surface, opacity: p > i * 0.2 ? 1 : 0}} />)}</div>;
    case "smelting-progress": return <div style={{...center, display: "flex", gap: 28}}><Asset src={a} size={100} style={{opacity: 1 - p}} /><div style={{position: "relative"}}><Asset src={b} size={130} /><div style={{position: "absolute", left: 48, bottom: 8, color: colors.orange, fontSize: 38, transform: `scale(${0.8 + p * 0.2})`}}>♨</div></div><Asset src={c} size={100} style={{opacity: p, transform: `scale(${0.75 + p * 0.25})`}} /></div>;
    case "growth-stages": return <div style={center}><div style={{position: "absolute", bottom: 38, width: 310, height: 24, borderRadius: 12, background: "#7A4F2D"}} /><Asset src={a} size={85} style={{position: "absolute", left: 125, bottom: 50, opacity: 1 - p}} /><Asset src={b} size={145} style={{position: "absolute", right: 120, bottom: 43, opacity: p, transformOrigin: "bottom", transform: `scaleY(${0.55 + p * 0.45})`}} /></div>;
    case "emits-light": return <div style={center}><div style={{position: "absolute", width: 130 + p * 130, height: 130 + p * 130, borderRadius: "50%", background: `radial-gradient(circle,${colors.gold}66,transparent 68%)`}} /><Asset src={a} size={150} style={{filter: `drop-shadow(0 10px 0 #02040A) drop-shadow(0 0 ${15 + p * 35}px ${colors.gold})`}} /></div>;
    case "blocks-damage": return <div style={center}><Asset src={a} size={165} style={{position: "absolute", left: 170, top: 38, transform: `rotate(${-8 + p * 5}deg)`}} /><Asset src={b} size={105} style={{position: "absolute", left: 395 - p * 190, top: 82, transform: "rotate(-90deg)"}} />{p > 0.75 ? <div style={{position: "absolute", left: 325, color: colors.gold, fontSize: 55}}>✹</div> : null}</div>;

    case "melee-strike": return <div style={center}><EntityPair left={a} right={b} progress={p} /></div>;
    case "projectile-throw": return <div style={center}><EntityPair left={a} right={b} progress={p} projectile /></div>;
    case "mining-break": return <div style={center}><Asset src={b} size={150} style={{position: "absolute", right: 95, top: 48, opacity: 1 - p * 0.4}} /><Asset src={a} size={145} style={{position: "absolute", left: 105 + p * 95, top: 42, transform: `rotate(${-35 + p * 45}deg)`}} />{[0, 1, 2, 3].map((i) => <div key={i} style={{position: "absolute", left: 310 + Math.cos(i * 1.6) * p * 65, top: 120 + Math.sin(i * 1.6) * p * 55, width: 16, height: 16, background: "#8D96A8", opacity: p}} />)}</div>;
    case "block-place": return <div style={center}><div style={{position: "absolute", bottom: 35, width: 270, height: 85, transform: "skewX(-28deg)", border: `4px solid ${colors.cyan}66`, backgroundImage: `linear-gradient(${colors.cyan}33 3px,transparent 3px),linear-gradient(90deg,${colors.cyan}33 3px,transparent 3px)`, backgroundSize: "45px 45px"}} /><Asset src={a} size={140} style={{position: "absolute", top: 15 + p * 82, transform: `scale(${0.85 + p * 0.15})`}} /></div>;
    case "consume-use": return <div style={center}><Asset src={a} size={150} style={{position: "absolute", left: 115 + p * 135, transform: `rotate(${p * 12}deg) scale(${1 - p * 0.16})`}} /><div style={{position: "absolute", right: 62, top: 68, display: "flex", gap: 7}}>{[0, 1, 2, 3].map((i) => <div key={i} style={{fontSize: 34, color: p > i / 4 ? colors.orange : "#39435A"}}>◆</div>)}</div></div>;
    case "equip-armor": return <div style={center}><div style={{width: 150, height: 188, borderRadius: 50, border: `6px dashed ${colors.cyan}`, opacity: 0.7}} /><Asset src={a} size={140} style={{position: "absolute", left: 45 + p * 165, transform: `scale(${0.78 + p * 0.22})`, opacity: 0.55 + p * 0.45}} /></div>;
    case "ignite-target": return <div style={center}><Asset src={b} size={125} style={{position: "absolute", right: 90, bottom: 38}} /><Asset src={a} size={145} style={{position: "absolute", left: 100 + p * 100, top: 38, transform: `rotate(${p * -18}deg)`}} />{[0, 1, 2].map((i) => <div key={i} style={{position: "absolute", right: 128 + i * 14, bottom: 95 + i * 18, color: i % 2 ? colors.gold : colors.orange, fontSize: 40 + i * 8, opacity: p}}>♠</div>)}</div>;
    case "water-interaction": return <div style={center}>{[0, 1, 2].map((i) => <div key={i} style={{position: "absolute", left: 70 + i * 18, bottom: 35 + i * 20, width: 350, height: 70, borderRadius: "50%", border: `5px solid ${colors.cyan}`, opacity: 0.12 + i * 0.1, transform: `scale(${0.85 + p * 0.15})`}} />)}<Asset src={a} size={160} style={{transform: `translateY(${Math.sin(p * Math.PI) * -28}px) rotate(${p * 8}deg)`, filter: `drop-shadow(0 10px 0 #02040A) drop-shadow(0 0 25px ${colors.cyan})`}} /></div>;
    case "redstone-activate": return <div style={center}><Asset src={a} size={120} style={{position: "absolute", left: 75, transform: `rotate(${p * -24}deg)`}} />{[0, 1, 2, 3, 4].map((i) => <div key={i} style={{position: "absolute", left: 210 + i * 45, width: 22, height: 22, borderRadius: 5, background: p > i / 5 ? "#FF3048" : "#4A1720", boxShadow: p > i / 5 ? "0 0 18px #FF3048" : "none"}} />)}<Asset src={b} size={70} style={{position: "absolute", right: 35}} /></div>;
    case "teleport-use": return <div style={center}><Asset src={a} size={90} style={{position: "absolute", left: 55 + p * 290, top: 65 - Math.sin(p * Math.PI) * 55}} /><Asset src={b} size={155} style={{position: "absolute", left: p > 0.55 ? 280 : 80, opacity: 0.45 + q * 0.55, filter: "drop-shadow(0 10px 0 #02040A) drop-shadow(0 0 24px #B46BFF)"}} /></div>;

    case "mob-drop": return <div style={center}><Asset src={a} size={160} style={{position: "absolute", left: 80, opacity: 1 - p * 0.35}} /><Asset src={b} size={95} style={{position: "absolute", right: 110, top: 35 + p * 95, transform: `rotate(${p * 25}deg)`}} /></div>;
    case "mob-equipment": return <div style={center}><Asset src={a} size={175} style={{position: "absolute", left: 115}} /><Asset src={b} size={125} style={{position: "absolute", left: 285 - p * 55, top: 68, transform: `rotate(${-22 + p * 10}deg)`}} /></div>;
    case "crafting-recipe": return <div style={{...center, display: "flex", gap: 20}}><div style={{display: "grid", gridTemplateColumns: "repeat(2,68px)", gap: 8}}><Slot size={68}><Asset src={a} size={52} /></Slot><Slot size={68}><Asset src={b} size={52} /></Slot><Slot size={68}><Asset src={b} size={52} /></Slot><Slot size={68}><Asset src={a} size={52} /></Slot></div><div style={{fontSize: 55, color: colors.gold}}>=</div><Asset src={c} size={145} style={{transform: `scale(${0.8 + p * 0.2})`}} /></div>;
    case "smelting-recipe": return <div style={{...center, display: "flex", gap: 22}}><Asset src={a} size={95} /><Asset src={b} size={135} style={{filter: `drop-shadow(0 10px 0 #02040A) drop-shadow(0 0 ${p * 24}px ${colors.orange})`}} /><Asset src={c} size={105} style={{opacity: 0.35 + p * 0.65}} /></div>;
    case "structure-chest": return <div style={center}><Asset src={a} size={175} style={{position: "absolute", bottom: 25, transform: `scaleY(${0.9 + p * 0.1})`}} /><Asset src={b} size={95} style={{position: "absolute", top: 100 - p * 75, opacity: p, filter: `drop-shadow(0 8px 0 #02040A) drop-shadow(0 0 24px ${colors.gold})`}} /></div>;
    case "biome-spawn": return <div style={center}><div style={{position: "absolute", inset: "90px 40px 25px", borderRadius: "50% 50% 12px 12px", background: "linear-gradient(#F7C95C 0 45%,#D89A45 46%)", opacity: 0.75}} /><Asset src={a} size={95} style={{position: "absolute", left: 110, bottom: 26}} /><Asset src={b} size={135} style={{position: "absolute", right: 105, bottom: 30, transformOrigin: "bottom", transform: `scaleY(${0.75 + p * 0.25})`}} /></div>;
    case "dimension-origin": return <div style={center}><div style={{position: "absolute", width: 150, height: 205, borderRadius: 24, border: "14px solid #311848", background: `repeating-linear-gradient(135deg,#8A4DFF${Math.round((0.35 + p * 0.4) * 255).toString(16).padStart(2, "0")} 0 16px,#4A2080 16px 32px)`, boxShadow: "0 0 28px #B46BFF"}} /><Asset src={a} size={105} style={{position: "absolute", left: 80 + p * 125}} /><Asset src={b} size={120} style={{position: "absolute", right: 55, opacity: p}} /></div>;
    case "fishing-loot": return <div style={center}><Asset src={a} size={145} style={{position: "absolute", left: 55, top: 20, transform: `rotate(${p * 8}deg)`}} /><div style={{position: "absolute", left: 205, top: 80, width: 3, height: 120, background: colors.text, transform: `rotate(${-8 + p * 12}deg)`, transformOrigin: "top"}} /><div style={{position: "absolute", right: 40, bottom: 30, width: 220, height: 70, borderRadius: "50%", border: `5px solid ${colors.cyan}88`}} /><Asset src={b} size={90} style={{position: "absolute", right: 95, top: 125 - p * 70}} /></div>;
    case "trade-offer": return <div style={center}><Asset src={a} size={145} style={{position: "absolute", left: 35}} /><Asset src={b} size={76} style={{position: "absolute", left: 185 + p * 65}} /><Asset src={c} size={100} style={{position: "absolute", right: 25, opacity: 0.4 + p * 0.6, transform: `scale(${0.8 + p * 0.2})`}} /><div style={{position: "absolute", top: 25, color: colors.gold, fontSize: 30}}>TRADE</div></div>;
    case "entity-transformation": return <div style={center}><Asset src={a} size={165} style={{position: "absolute", left: 85, opacity: 1 - p}} /><Asset src={b} size={82} style={{position: "absolute", left: 200, top: 80, opacity: 1 - Math.abs(p - 0.5) * 2}} /><Asset src={c} size={165} style={{position: "absolute", right: 75, opacity: p, filter: `drop-shadow(0 10px 0 #02040A) drop-shadow(0 0 ${p * 24}px ${colors.green})`}} /></div>;
    default: throw new Error(`Unknown prefab preview: ${prefab.id}`);
  }
};

export const MysteryPrefabCard: React.FC<{prefab: MysteryPrefabRecord}> = ({prefab}) => {
  const accent = prefab.role === "property-state" ? colors.cyan : prefab.role === "action-interaction" ? colors.orange : colors.green;
  return (
    <div style={{position: "relative", overflow: "hidden", borderRadius: 32, border: `4px solid ${accent}88`, background: `linear-gradient(145deg,${colors.surface},${colors.ink})`, boxShadow: "0 12px 0 rgba(0,0,0,.5),inset 0 0 0 2px rgba(255,255,255,.04)", fontFamily: "Minecraft", color: colors.text}}>
      <div style={{position: "absolute", left: 18, top: 15, width: 56, height: 56, display: "grid", placeItems: "center", borderRadius: 18, background: accent, color: colors.ink, fontSize: 28}}>{String(prefab.number).padStart(2, "0")}</div>
      <div style={{position: "absolute", left: 84, right: 15, top: 18, height: 52, display: "grid", alignItems: "center", fontSize: prefab.title.length > 23 ? 20 : 24, lineHeight: 1, color: accent}}>{prefab.title}</div>
      <div style={{position: "absolute", left: 15, right: 15, top: 74, bottom: 52, display: "grid", placeItems: "center", borderRadius: 24, background: `radial-gradient(circle,${accent}18,transparent 66%)`}}><ScenarioVisual prefab={prefab} /></div>
      <div style={{position: "absolute", left: 18, right: 18, bottom: 13, display: "flex", justifyContent: "space-between", color: "#AAB6CE", fontSize: 17}}><span>{prefab.role}</span><span style={{color: accent}}>{prefab.relations[0]}</span></div>
    </div>
  );
};
