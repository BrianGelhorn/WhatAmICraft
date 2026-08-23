import {CanvasImage, staticFile, useCurrentFrame} from "remotion";
import catalog from "../../generated/mystery-v2-visual-prefabs.json";
import {DurabilityLossVisual} from "./DurabilityLossVisual";
import {StackLimitVisual} from "./StackLimitVisual";

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
    <div style={{width: `${Math.max(0, value * 100)}%`, height: "100%", borderRadius: 4, background: color, boxShadow: `0 0 12px ${color}`}} />
  </div>
);

const Steve: React.FC<{arm?: number; stride?: number; style?: React.CSSProperties}> = ({arm = 0, stride = 0, style}) => (
  <div style={{position: "absolute", width: 92, height: 190, filter: "drop-shadow(0 10px 0 rgba(0,0,0,.55))", ...style}}>
    <div style={{position: "absolute", left: 19, top: 0, width: 56, height: 56, background: "#B87855", border: "5px solid #111827", boxSizing: "border-box"}}>
      <div style={{position: "absolute", inset: "0 0 auto", height: 17, background: "#3A241C"}} />
      <div style={{position: "absolute", left: 8, top: 24, width: 10, height: 7, background: "#F7FAFF", boxShadow: "26px 0 #F7FAFF"}} />
      <div style={{position: "absolute", left: 12, top: 25, width: 5, height: 5, background: "#314A78", boxShadow: "26px 0 #314A78"}} />
      <div style={{position: "absolute", left: 22, bottom: 7, width: 16, height: 5, background: "#6D3D2D"}} />
    </div>
    <div style={{position: "absolute", left: 20, top: 53, width: 54, height: 67, background: "#20A7A8", border: "5px solid #111827", boxSizing: "border-box"}} />
    <div style={{position: "absolute", left: 2, top: 56, width: 23, height: 72, background: "linear-gradient(#20A7A8 0 42%,#B87855 43%)", border: "5px solid #111827", boxSizing: "border-box", transformOrigin: "50% 8px", transform: `rotate(${arm}deg)`}} />
    <div style={{position: "absolute", right: 0, top: 56, width: 23, height: 72, background: "linear-gradient(#20A7A8 0 42%,#B87855 43%)", border: "5px solid #111827", boxSizing: "border-box", transformOrigin: "50% 8px", transform: `rotate(${-arm * 0.35}deg)`}} />
    <div style={{position: "absolute", left: 22, top: 116, width: 25, height: 72, background: "#294C9B", border: "5px solid #111827", boxSizing: "border-box", transformOrigin: "50% 5px", transform: `rotate(${stride}deg)`}} />
    <div style={{position: "absolute", right: 18, top: 116, width: 25, height: 72, background: "#294C9B", border: "5px solid #111827", boxSizing: "border-box", transformOrigin: "50% 5px", transform: `rotate(${-stride}deg)`}} />
  </div>
);

const HungerBar: React.FC<{value: number; style?: React.CSSProperties}> = ({value, style}) => (
  <div style={{display: "flex", gap: 8, padding: "8px 12px", borderRadius: 14, background: "#080C16CC", border: "3px solid #26324C", ...style}}>
    {[0, 1, 2, 3, 4].map((index) => <div key={index} style={{fontSize: 26, color: value > index / 5 ? colors.orange : "#39435A", filter: value > index / 5 ? "drop-shadow(0 0 7px #FF6B35)" : "none"}}>♥</div>)}
  </div>
);

const ScenarioVisual: React.FC<{prefab: MysteryPrefabRecord}> = ({prefab}) => {
  const frame = useCurrentFrame();
  const p = phase(frame, prefab.number * 4);
  const [a, b, c] = prefab.assets;
  const center: React.CSSProperties = {position: "relative", width: 470, height: 245, display: "grid", placeItems: "center"};

  switch (prefab.id) {
    case "durability-loss": return <div style={center}><DurabilityLossVisual assetSrc={a} /></div>;
    case "stack-limit": return <div style={center}><StackLimitVisual assetSrc={a} stackValue="16" accentColor={colors.cyan} /></div>;
    case "charge-level": return <div style={center}><div style={{position: "absolute", width: 185, height: 185, borderRadius: "50%", background: `conic-gradient(${colors.cyan} ${p * 360}deg,#26324C 0)`, boxShadow: `0 0 28px ${colors.cyan}55`}} /><div style={{position: "absolute", width: 150, height: 150, borderRadius: "50%", background: colors.surface}} /><Asset src={a} size={125} style={{zIndex: 2, transform: `scale(${0.9 + p * 0.1})`}} /></div>;
    case "cooldown": return <div style={center}><Asset src={a} size={150} style={{opacity: 0.45 + p * 0.55}} /><div style={{position: "absolute", width: 184, height: 184, borderRadius: "50%", border: `9px solid ${colors.orange}`, borderTopColor: "transparent", transform: `rotate(${p * 320}deg)`}} /><div style={{position: "absolute", bottom: 18, color: colors.orange, fontSize: 24}}>{p > 0.75 ? "READY" : "WAIT"}</div></div>;
    case "enchantment-glint": return <div style={center}><Asset src={b} size={86} style={{position: "absolute", left: 72, top: 85, opacity: 0.8}} /><Asset src={a} size={165} style={{filter: `drop-shadow(0 10px 0 #02040A) drop-shadow(0 0 ${15 + p * 30}px #B46BFF) hue-rotate(${p * 120}deg)`}} />{[0, 1, 2].map((i) => <div key={i} style={{position: "absolute", left: 230 + Math.cos(i * 2.1) * (55 + p * 25), top: 120 + Math.sin(i * 2.1) * (55 + p * 25), color: colors.gold, fontSize: 28, opacity: p}}>✦</div>)}</div>;
    case "consumable-bites": return <div style={center}>
      <Asset src={a} size={158} style={{position: "absolute", top: 25, transform: `scale(${1 - p * 0.14}) rotate(${p * -7}deg)`}} />
      {[0, 1, 2].map((i) => <div key={i} style={{position: "absolute", left: 268 + i * 20, top: 58 + i * 24, width: 27, height: 27, borderRadius: "50%", background: colors.surface, opacity: p > i * 0.22 ? 1 : 0}} />)}
      <HungerBar value={0.2 + p * 0.8} style={{position: "absolute", bottom: 8}} />
    </div>;
    case "repair-restore": return <div style={center}>
      <Asset src={a} size={105} style={{position: "absolute", left: 70, top: 54, opacity: 1 - p * 0.45, filter: "grayscale(.65) drop-shadow(0 8px 0 #02040A)"}} />
      <div style={{position: "absolute", left: 72, bottom: 42}}><Meter value={0.18} color={colors.orange} width={95} /></div>
      <Asset src={b} size={140} style={{position: "absolute", left: 178, top: 55, transform: `translateY(${Math.sin(p * Math.PI) * -18}px)`}} />
      <Asset src={a} size={115} style={{position: "absolute", right: 55, top: 48, opacity: p, filter: `drop-shadow(0 8px 0 #02040A) drop-shadow(0 0 ${p * 20}px ${colors.green})`}} />
      <div style={{position: "absolute", right: 60, bottom: 42}}><Meter value={0.25 + p * 0.75} width={105} /></div>
    </div>;
    case "growth-stages": return <div style={center}><div style={{position: "absolute", bottom: 38, width: 310, height: 24, borderRadius: 12, background: "#7A4F2D"}} /><Asset src={a} size={85} style={{position: "absolute", left: 125, bottom: 50, opacity: 1 - p}} /><Asset src={b} size={145} style={{position: "absolute", right: 120, bottom: 43, opacity: p, transformOrigin: "bottom", transform: `scaleY(${0.55 + p * 0.45})`}} /></div>;
    case "emits-light": return <div style={center}><div style={{position: "absolute", width: 130 + p * 130, height: 130 + p * 130, borderRadius: "50%", background: `radial-gradient(circle,${colors.gold}66,transparent 68%)`}} /><Asset src={a} size={150} style={{filter: `drop-shadow(0 10px 0 #02040A) drop-shadow(0 0 ${15 + p * 35}px ${colors.gold})`}} /></div>;
    case "grants-status-effect": return <div style={center}><Steve arm={-35 * p} style={{left: 185, top: 22, transform: `scale(${0.9 + p * 0.05})`}} /><Asset src={p > 0.5 ? b : a} size={72} style={{position: "absolute", left: 155 + p * 62, top: 85 - p * 48, transform: `rotate(${p * 18}deg)`}} />{[0, 1, 2, 3].map((i) => <div key={i} style={{position: "absolute", left: 210 + Math.cos(i * 1.6) * (55 + p * 42), top: 108 + Math.sin(i * 1.6) * (48 + p * 35), width: 18, height: 18, borderRadius: "50%", background: i % 2 ? "#B46BFF" : colors.gold, boxShadow: `0 0 14px ${i % 2 ? "#B46BFF" : colors.gold}`, opacity: p}} />)}</div>;

    case "melee-strike": return <div style={center}><Steve arm={-65 + p * 95} stride={p * 10} style={{left: 65, top: 25}} /><Asset src={a} size={115} style={{position: "absolute", left: 118 + p * 66, top: 30 + p * 44, transform: `rotate(${-55 + p * 90}deg)`}} /><Asset src={b} size={145} style={{position: "absolute", right: 45, top: 42, transform: `translateX(${p > 0.7 ? (p - 0.7) * 55 : 0}px) rotate(${p * 5}deg)`}} />{p > 0.68 ? <div style={{position: "absolute", right: 150, top: 74, color: colors.gold, fontSize: 58, opacity: (p - 0.68) / 0.32}}>✹</div> : null}</div>;
    case "projectile-throw": return <div style={center}><Steve arm={-70 + p * 80} style={{left: 42, top: 28}} /><Asset src={a} size={102} style={{position: "absolute", left: 125 + p * 225, top: 88 - Math.sin(p * Math.PI) * 62, transform: `rotate(${75 + p * 20}deg)`}} /><Asset src={b} size={138} style={{position: "absolute", right: 30, top: 50}} />{p > 0.78 ? <div style={{position: "absolute", right: 115, top: 80, color: colors.orange, fontSize: 52}}>✹</div> : null}</div>;
    case "mining-break": return <div style={center}><Steve arm={-65 + p * 100} style={{left: 55, top: 28}} /><Asset src={a} size={112} style={{position: "absolute", left: 125 + p * 62, top: 31 + p * 45, transform: `rotate(${-38 + p * 82}deg)`}} /><Asset src={b} size={145} style={{position: "absolute", right: 55, top: 63, opacity: 1 - p * 0.35}} />{[0, 1, 2, 3].map((i) => <div key={i} style={{position: "absolute", left: 330 + Math.cos(i * 1.6) * p * 58, top: 124 + Math.sin(i * 1.6) * p * 50, width: 15, height: 15, background: "#8D96A8", opacity: p}} />)}</div>;
    case "block-place": return <div style={center}><Steve arm={-18 - p * 35} style={{left: 65, top: 28}} /><div style={{position: "absolute", right: 32, bottom: 28, width: 235, height: 78, transform: "skewX(-25deg)", border: `4px solid ${colors.cyan}66`, backgroundImage: `linear-gradient(${colors.cyan}33 3px,transparent 3px),linear-gradient(90deg,${colors.cyan}33 3px,transparent 3px)`, backgroundSize: "44px 44px"}} /><Asset src={a} size={112} style={{position: "absolute", left: 150 + p * 160, top: 50 + p * 70, transform: `scale(${0.8 + p * 0.2})`}} /></div>;
    case "consume-use": return <div style={center}><Steve arm={-15 - p * 62} style={{left: 150, top: 15, transform: `translateY(${Math.sin(p * Math.PI * 3) * 3}px)`}} /><Asset src={a} size={68} style={{position: "absolute", left: 118 + p * 91, top: 91 - p * 61, transform: `rotate(${p * 18}deg) scale(${1 - p * 0.25})`}} />{[0, 1, 2].map((i) => <div key={i} style={{position: "absolute", left: 200 + i * 17, top: 55 + i * 10, width: 10, height: 10, background: colors.gold, opacity: p > i * 0.18 ? 1 : 0}} />)}<HungerBar value={0.2 + p * 0.8} style={{position: "absolute", right: 20, bottom: 15}} /></div>;
    case "equip-armor": return <div style={center}><Steve style={{left: 190, top: 25}} /><div style={{position: "absolute", left: 184, top: 70, width: 105, height: 100, borderRadius: 22, border: `5px dashed ${colors.cyan}`, opacity: 0.55 + p * 0.35}} /><Asset src={a} size={122} style={{position: "absolute", left: 42 + p * 168, top: 57, transform: `scale(${0.82 + p * 0.18})`, opacity: 0.65 + p * 0.35, filter: `drop-shadow(0 8px 0 #02040A) drop-shadow(0 0 ${p * 18}px ${colors.cyan})`}} /></div>;
    case "mob-interaction": return <div style={center}><Steve arm={-18 - p * 45} style={{left: 52, top: 28}} /><Asset src={a} size={82} style={{position: "absolute", left: 138 + p * 80, top: 74, transform: `rotate(${-18 + p * 26}deg)`}} /><Asset src={b} size={155} style={{position: "absolute", right: 35, top: 60}} />{[0, 1, 2, 3].map((i) => <div key={i} style={{position: "absolute", right: 105 + i * 17, top: 60 + Math.sin(i * 1.7) * 28 - p * 32, width: 20, height: 20, background: "#F7FAFF", borderRadius: 6, opacity: p}} />)}</div>;
    case "special-movement": return <div style={center}><div style={{position: "absolute", left: 40, right: 30, top: 120, height: 6, borderRadius: 3, background: `linear-gradient(90deg,transparent,${colors.cyan},transparent)`, opacity: 0.35 + p * 0.5}} /><Asset src={a} size={128} style={{position: "absolute", left: 125 + p * 75, top: 46 - Math.sin(p * Math.PI) * 30, transform: "rotate(90deg)", opacity: 0.9}} /><Steve arm={-45} stride={22} style={{left: 135 + p * 85, top: 24 - Math.sin(p * Math.PI) * 30, transform: "rotate(78deg) scale(.78)"}} /><Asset src={b} size={65} style={{position: "absolute", left: 70 + p * 80, top: 110 - Math.sin(p * Math.PI) * 20, transform: "rotate(-25deg)"}} />{[0, 1, 2].map((i) => <div key={i} style={{position: "absolute", left: 55 + i * 25 + p * 80, top: 145 + i * 7, width: 16, height: 16, background: i % 2 ? colors.gold : colors.orange, opacity: 1 - p * 0.35}} />)}</div>;
    case "redstone-activate": return <div style={center}><Steve arm={-15 - p * 50} style={{left: 38, top: 27, transform: "scale(.88)"}} /><Asset src={a} size={90} style={{position: "absolute", left: 147, top: 78, transform: `rotate(${p * -25}deg)`}} />{[0, 1, 2, 3, 4].map((i) => <div key={i} style={{position: "absolute", left: 235 + i * 42, top: 123, width: 20, height: 20, borderRadius: 5, background: p > i / 5 ? "#FF3048" : "#4A1720", boxShadow: p > i / 5 ? "0 0 18px #FF3048" : "none"}} />)}<Asset src={b} size={60} style={{position: "absolute", right: 18, top: 95}} /></div>;
    case "block-transformation": return <div style={center}><Steve arm={-62 + p * 92} style={{left: 40, top: 27}} /><Asset src={a} size={105} style={{position: "absolute", left: 115 + p * 64, top: 38 + p * 38, transform: `rotate(${-42 + p * 78}deg)`}} /><Asset src={b} size={142} style={{position: "absolute", right: 40, top: 58, opacity: 1 - p}} /><Asset src={c} size={142} style={{position: "absolute", right: 40, top: 58, opacity: p, filter: `drop-shadow(0 8px 0 #02040A) drop-shadow(0 0 ${p * 18}px ${colors.green})`}} /></div>;

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
  const approved = prefab.status === "approved";
  return (
    <div style={{position: "relative", overflow: "hidden", borderRadius: 32, border: `4px solid ${approved ? colors.green : `${accent}88`}`, background: `linear-gradient(145deg,${colors.surface},${colors.ink})`, boxShadow: approved ? `0 12px 0 rgba(0,0,0,.5),inset 0 0 0 2px ${colors.green}55,0 0 24px ${colors.green}33` : "0 12px 0 rgba(0,0,0,.5),inset 0 0 0 2px rgba(255,255,255,.04)", fontFamily: "Minecraft", color: colors.text}}>
      <div style={{position: "absolute", left: 18, top: 15, width: 56, height: 56, display: "grid", placeItems: "center", borderRadius: 18, background: accent, color: colors.ink, fontSize: 28}}>{String(prefab.number).padStart(2, "0")}</div>
      <div style={{position: "absolute", left: 84, right: 15, top: 18, height: 52, display: "grid", alignItems: "center", fontSize: prefab.title.length > 23 ? 20 : 24, lineHeight: 1, color: accent}}>{prefab.title}</div>
      <div style={{position: "absolute", left: 15, right: 15, top: 74, bottom: 52, display: "grid", placeItems: "center", borderRadius: 24, background: `radial-gradient(circle,${accent}18,transparent 66%)`}}><ScenarioVisual prefab={prefab} /></div>
      <div style={{position: "absolute", left: 18, right: 18, bottom: 13, display: "flex", justifyContent: "space-between", color: approved ? colors.green : "#AAB6CE", fontSize: 17}}><span>{approved ? "APPROVED" : prefab.role}</span><span style={{color: accent}}>{prefab.relations[0]}</span></div>
    </div>
  );
};
