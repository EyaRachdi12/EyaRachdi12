"use client";
import { useEffect, useRef, useState, useCallback } from "react";
import * as THREE from "three";

export interface RoomInput { 
  name: string; 
  area: number; 
  windows?: number;
  // Optional coordinates from CV analysis
  x?: number;
  z?: number;
  w?: number;
  d?: number;
}
interface Props { rooms?: RoomInput[]; autoTour?: boolean; }

const WALL_H = 2.8;
const WALL_T = 0.15;
const WALL_COLOR = 0xf5f0ea;
const CEILING_COLOR = 0xfafaf8;

const FLOOR_COLORS: Record<string, number> = {
  salon: 0xd4a96a, sejour: 0xd4a96a, living: 0xd4a96a,
  cuisine: 0xe8c99a, chambre: 0xb8cce0, salle: 0xa8d4d4,
  wc: 0xc8dde0, couloir: 0xc8bfb0, bureau: 0xc4b89a,
  dressing: 0xd4c4a8, terrasse: 0x9ab88a, garage: 0xa8a8a0,
  jardin: 0x7ab870, default: 0xd0c8bc,
};

function getRoomColor(name: string): number {
  const n = name.toLowerCase();
  for (const [k, v] of Object.entries(FLOOR_COLORS)) { if (n.includes(k)) return v; }
  return FLOOR_COLORS.default;
}

function layoutRooms(rooms: RoomInput[]) {
  const out: Array<RoomInput & { x: number; z: number; w: number; d: number; color: number }> = [];
  
  // Check if rooms already have coordinates from CV analysis
  const hasCoordinates = rooms.some(r => r.x !== undefined && r.z !== undefined);
  
  if (hasCoordinates) {
    // Use CV-provided coordinates directly
    return rooms.map(r => ({
      ...r,
      x: r.x ?? 0,
      z: r.z ?? 0,
      w: r.w ?? Math.max(2.5, Math.sqrt(r.area) * 1.15),
      d: r.d ?? Math.max(2.5, r.area / (r.w ?? 3)),
      color: getRoomColor(r.name),
    }));
  }
  
  // Fallback to grid layout if no coordinates provided
  let cx = 0, cz = 0, rowMaxD = 0;
  rooms.forEach((r, i) => {
    const sq = Math.sqrt(Math.max(r.area, 4));
    const w = Math.max(2.5, sq * 1.15);
    const d = Math.max(2.5, r.area / w);
    if (i > 0 && cx + w > 18) { cx = 0; cz += rowMaxD; rowMaxD = 0; }
    // Place rooms edge-to-edge (no gap) by using cx directly as left edge
    out.push({ ...r, x: cx + w / 2, z: cz + d / 2, w, d, color: getRoomColor(r.name) });
    cx += w; // No gap — next room starts where this one ends
    rowMaxD = Math.max(rowMaxD, d);
  });
  const mx = out.reduce((s, r) => s + r.x, 0) / out.length;
  const mz = out.reduce((s, r) => s + r.z, 0) / out.length;
  return out.map(r => ({ ...r, x: r.x - mx, z: r.z - mz }));
}

function addFurniture(scene: THREE.Scene, room: { name: string; x: number; z: number; w: number; d: number }) {
  const { x, z, w, d, name } = room;
  const n = name.toLowerCase();
  const wood = new THREE.MeshStandardMaterial({ color: 0x8b6020, roughness: 0.5, metalness: 0.05 });
  const fabric = new THREE.MeshStandardMaterial({ color: 0xc9a96e, roughness: 0.9 });
  const white = new THREE.MeshStandardMaterial({ color: 0xfafafa, roughness: 0.3 });

  if (n.includes("salon") || n.includes("sejour") || n.includes("séjour") || n.includes("living")) {
    const sofa = new THREE.Mesh(new THREE.BoxGeometry(Math.min(w * 0.6, 2.4), 0.45, 0.9), fabric);
    sofa.position.set(x, 0.225, z + d * 0.2); sofa.castShadow = true; scene.add(sofa);
    const back = new THREE.Mesh(new THREE.BoxGeometry(Math.min(w * 0.6, 2.4), 0.55, 0.12), fabric);
    back.position.set(x, 0.5, z + d * 0.2 + 0.44); scene.add(back);
    const table = new THREE.Mesh(new THREE.BoxGeometry(1.0, 0.06, 0.6), wood);
    table.position.set(x, 0.38, z - d * 0.1); scene.add(table);
    [[-0.4, -0.22], [0.4, -0.22], [-0.4, 0.22], [0.4, 0.22]].forEach(([lx, lz]) => {
      const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.38, 6), wood);
      leg.position.set(x + lx, 0.19, z - d * 0.1 + lz); scene.add(leg);
    });
  }
  if (n.includes("cuisine")) {
    const counter = new THREE.Mesh(new THREE.BoxGeometry(Math.min(w * 0.75, 3.0), 0.9, 0.6), wood);
    counter.position.set(x, 0.45, z - d / 2 + 0.35); counter.castShadow = true; scene.add(counter);
    const top = new THREE.Mesh(new THREE.BoxGeometry(Math.min(w * 0.75, 3.0), 0.05, 0.65), white);
    top.position.set(x, 0.925, z - d / 2 + 0.35); scene.add(top);
    const sink = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.06, 0.4),
      new THREE.MeshStandardMaterial({ color: 0xaaaaaa, metalness: 0.8, roughness: 0.2 }));
    sink.position.set(x + 0.5, 0.96, z - d / 2 + 0.35); scene.add(sink);
  }
  if (n.includes("chambre")) {
    const bw = n.includes("principale") ? 1.8 : 1.4;
    const bed = new THREE.Mesh(new THREE.BoxGeometry(bw, 0.3, 2.0), wood);
    bed.position.set(x, 0.15, z); bed.castShadow = true; scene.add(bed);
    const mattress = new THREE.Mesh(new THREE.BoxGeometry(bw - 0.05, 0.2, 1.9), fabric);
    mattress.position.set(x, 0.4, z); scene.add(mattress);
    const headboard = new THREE.Mesh(new THREE.BoxGeometry(bw, 0.8, 0.1), wood);
    headboard.position.set(x, 0.65, z - 0.95); scene.add(headboard);
    [[-bw / 4, -0.65], [bw / 4, -0.65]].forEach(([px2, pz2]) => {
      const pillow = new THREE.Mesh(new THREE.BoxGeometry(0.55, 0.12, 0.4), white);
      pillow.position.set(x + px2, 0.56, z + pz2); scene.add(pillow);
    });
  }
  if (n.includes("salle") && (n.includes("bain") || n.includes("eau"))) {
    const tub = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.5, 0.75), white);
    tub.position.set(x - w * 0.2, 0.25, z); scene.add(tub);
    const toilet = new THREE.Mesh(new THREE.BoxGeometry(0.45, 0.45, 0.65), white);
    toilet.position.set(x + w * 0.25, 0.225, z - d * 0.25); scene.add(toilet);
  }
}

const DEFAULT: RoomInput[] = [
  { name: "Salon / Sejour", area: 32 }, { name: "Cuisine", area: 14 },
  { name: "Chambre principale", area: 20 }, { name: "Chambre 2", area: 14 },
  { name: "Salle de bain", area: 7 }, { name: "Couloir", area: 5 },
];

export default function FloorPlan3DViewer({ rooms: rd, autoTour = false }: Props) {
  const mountRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const stateRef = useRef<any>(null);
  const recRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [hoveredRoom, setHoveredRoom] = useState("");
  const [isPlaying, setIsPlaying] = useState(autoTour);
  const [isRec, setIsRec] = useState(false);
  const [recTime, setRecTime] = useState(0);
  const rooms = layoutRooms(rd && rd.length > 0 ? rd : DEFAULT);

  useEffect(() => {
    const el = mountRef.current;
    if (!el) return;
    const W = el.clientWidth || 800, H = el.clientHeight || 560;

    const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
    renderer.setSize(W, H);
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.1;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    el.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1c1a18);
    scene.fog = new THREE.FogExp2(0x1c1a18, 0.016);

    const camera = new THREE.PerspectiveCamera(52, W / H, 0.1, 150);
    camera.position.set(0, 8, 14);
    camera.lookAt(0, 0, 0);

    // Lighting
    scene.add(new THREE.AmbientLight(0xfff8f0, 0.65));
    const sun = new THREE.DirectionalLight(0xfff5e0, 1.6);
    sun.position.set(15, 25, 15); sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048);
    sun.shadow.camera.near = 0.5; sun.shadow.camera.far = 100;
    sun.shadow.camera.left = -30; sun.shadow.camera.right = 30;
    sun.shadow.camera.top = 30; sun.shadow.camera.bottom = -30;
    sun.shadow.bias = -0.001;
    scene.add(sun);
    const fill = new THREE.DirectionalLight(0x8899cc, 0.25);
    fill.position.set(-12, 8, -10); scene.add(fill);

    // Ground
    const ground = new THREE.Mesh(new THREE.PlaneGeometry(100, 100),
      new THREE.MeshStandardMaterial({ color: 0x111008, roughness: 1 }));
    ground.rotation.x = -Math.PI / 2; ground.position.y = -0.01; ground.receiveShadow = true;
    scene.add(ground);
    scene.add(new THREE.GridHelper(80, 80, 0x2a2520, 0x1e1c18));

    // Shared materials
    const wallMat = new THREE.MeshStandardMaterial({ color: WALL_COLOR, roughness: 0.9 });
    const ceilMat = new THREE.MeshStandardMaterial({ color: CEILING_COLOR, roughness: 0.95 });
    const doorMat = new THREE.MeshStandardMaterial({ color: 0x8b6020, roughness: 0.4, metalness: 0.1 });
    const glassMat = new THREE.MeshStandardMaterial({ color: 0x88ccff, transparent: true, opacity: 0.22, roughness: 0.05, metalness: 0.1 });
    const frameMat = new THREE.MeshStandardMaterial({ color: 0xc9a96e, roughness: 0.3, metalness: 0.3 });
    const handleMat = new THREE.MeshStandardMaterial({ color: 0xd4a830, roughness: 0.2, metalness: 0.8 });

    rooms.forEach(room => {
      const { x, z, w, d } = room;
      const floorMat = new THREE.MeshStandardMaterial({ color: room.color, roughness: 0.7, metalness: 0.02 });

      // Floor slab
      const floor = new THREE.Mesh(new THREE.BoxGeometry(w, 0.06, d), floorMat);
      floor.position.set(x, 0.03, z); floor.receiveShadow = true;
      floor.userData.roomName = room.name; scene.add(floor);

      // Ceiling slab
      const ceil = new THREE.Mesh(new THREE.BoxGeometry(w, 0.05, d), ceilMat);
      ceil.position.set(x, WALL_H + 0.025, z); scene.add(ceil);

      // Floating room label
      const cvs = document.createElement("canvas");
      cvs.width = 256; cvs.height = 72;
      const ctx = cvs.getContext("2d")!;
      ctx.clearRect(0, 0, 256, 72);
      ctx.font = "bold 20px Inter,sans-serif"; ctx.fillStyle = "#ffffff"; ctx.textAlign = "center";
      ctx.fillText(room.name, 128, 26);
      ctx.font = "15px Inter,sans-serif"; ctx.fillStyle = "rgba(201,169,110,0.95)";
      ctx.fillText(`${room.area} m²`, 128, 50);
      const tex = new THREE.CanvasTexture(cvs);
      const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthTest: false }));
      sprite.position.set(x, WALL_H + 0.7, z); sprite.scale.set(3.6, 1.0, 1); scene.add(sprite);

      // ── SOUTH WALL — door opening ──────────────────────────────────────────
      const doorW = 0.9, doorH = 2.1;
      const sideW = (w - doorW) / 2;
      if (sideW > 0.05) {
        [-1, 1].forEach(s => {
          const seg = new THREE.Mesh(new THREE.BoxGeometry(sideW, WALL_H, WALL_T), wallMat);
          seg.position.set(x + s * (sideW / 2 + doorW / 2), WALL_H / 2, z - d / 2);
          seg.castShadow = seg.receiveShadow = true; scene.add(seg);
        });
        const lintelH = WALL_H - doorH;
        if (lintelH > 0.05) {
          const lintel = new THREE.Mesh(new THREE.BoxGeometry(doorW, lintelH, WALL_T), wallMat);
          lintel.position.set(x, doorH + lintelH / 2, z - d / 2); scene.add(lintel);
        }
        const door = new THREE.Mesh(new THREE.BoxGeometry(doorW - 0.05, doorH - 0.05, 0.04), doorMat);
        door.position.set(x, doorH / 2, z - d / 2); door.castShadow = true; scene.add(door);
        const handle = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.12, 8), handleMat);
        handle.rotation.z = Math.PI / 2;
        handle.position.set(x + doorW / 2 - 0.12, doorH / 2, z - d / 2 + 0.04); scene.add(handle);
      }

      // ── NORTH WALL — solid ─────────────────────────────────────────────────
      const nWall = new THREE.Mesh(new THREE.BoxGeometry(w, WALL_H, WALL_T), wallMat);
      nWall.position.set(x, WALL_H / 2, z + d / 2);
      nWall.castShadow = nWall.receiveShadow = true; scene.add(nWall);

      // ── WEST WALL — window ─────────────────────────────────────────────────
      const winW = Math.min(d * 0.45, 1.4), winH = 1.0, winY = WALL_H * 0.55;
      const wSide = (d - winW) / 2;
      if (wSide > 0.05) {
        [-1, 1].forEach(s => {
          const seg = new THREE.Mesh(new THREE.BoxGeometry(WALL_T, WALL_H, wSide), wallMat);
          seg.position.set(x - w / 2, WALL_H / 2, z + s * (wSide / 2 + winW / 2));
          seg.castShadow = seg.receiveShadow = true; scene.add(seg);
        });
        const below = new THREE.Mesh(new THREE.BoxGeometry(WALL_T, winY - winH / 2, winW), wallMat);
        below.position.set(x - w / 2, (winY - winH / 2) / 2, z); scene.add(below);
        const above = new THREE.Mesh(new THREE.BoxGeometry(WALL_T, WALL_H - winY - winH / 2, winW), wallMat);
        above.position.set(x - w / 2, winY + winH / 2 + (WALL_H - winY - winH / 2) / 2, z); scene.add(above);
        const glass = new THREE.Mesh(new THREE.BoxGeometry(0.04, winH, winW), glassMat);
        glass.position.set(x - w / 2, winY, z); scene.add(glass);
        const frame = new THREE.Mesh(new THREE.BoxGeometry(0.07, winH + 0.1, winW + 0.1), frameMat);
        frame.position.set(x - w / 2, winY, z); scene.add(frame);
        const crossbar = new THREE.Mesh(new THREE.BoxGeometry(0.07, 0.05, winW + 0.1), frameMat);
        crossbar.position.set(x - w / 2, winY, z); scene.add(crossbar);
      } else {
        const wWall = new THREE.Mesh(new THREE.BoxGeometry(WALL_T, WALL_H, d), wallMat);
        wWall.position.set(x - w / 2, WALL_H / 2, z);
        wWall.castShadow = wWall.receiveShadow = true; scene.add(wWall);
      }

      // ── EAST WALL — solid ──────────────────────────────────────────────────
      const eWall = new THREE.Mesh(new THREE.BoxGeometry(WALL_T, WALL_H, d), wallMat);
      eWall.position.set(x + w / 2, WALL_H / 2, z);
      eWall.castShadow = eWall.receiveShadow = true; scene.add(eWall);

      // Room point light + bulb
      const ptLight = new THREE.PointLight(0xfff8f0, 0.9, w * 3.5);
      ptLight.position.set(x, WALL_H - 0.3, z); scene.add(ptLight);
      const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.1, 8, 8),
        new THREE.MeshStandardMaterial({ color: 0xfff8f0, emissive: 0xfff8f0, emissiveIntensity: 3 }));
      bulb.position.set(x, WALL_H - 0.15, z); scene.add(bulb);

      addFurniture(scene, room);
    });

    // Raycaster hover
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    const onMM = (e: MouseEvent) => {
      const rect = el.getBoundingClientRect();
      mouse.x = ((e.clientX - rect.left) / W) * 2 - 1;
      mouse.y = -((e.clientY - rect.top) / H) * 2 + 1;
      raycaster.setFromCamera(mouse, camera);
      const hit = raycaster.intersectObjects(scene.children, true).find(h => h.object.userData?.roomName);
      setHoveredRoom(hit ? hit.object.userData.roomName : "");
    };
    el.addEventListener("mousemove", onMM);

    // Orbit
    let drag = false, px = 0, py = 0;
    let theta = 0.5, phi = 0.52, radius = 16;
    let tTheta = theta, tPhi = phi, tRadius = radius;
    const onMD = (e: MouseEvent) => { drag = true; px = e.clientX; py = e.clientY; };
    const onMU = () => { drag = false; };
    const onDrag = (e: MouseEvent) => {
      if (!drag || stateRef.current?.touring) return;
      tTheta -= (e.clientX - px) * 0.005;
      tPhi = Math.max(0.1, Math.min(Math.PI / 2 - 0.05, tPhi - (e.clientY - py) * 0.005));
      px = e.clientX; py = e.clientY;
    };
    const onWheel = (e: WheelEvent) => { tRadius = Math.max(5, Math.min(40, tRadius + e.deltaY * 0.02)); };
    el.addEventListener("mousedown", onMD); el.addEventListener("mouseup", onMU);
    el.addEventListener("mousemove", onDrag); el.addEventListener("wheel", onWheel, { passive: true });

    stateRef.current = { renderer, scene, camera, animId: 0, theta, phi, radius, tTheta, tPhi, tRadius, touring: autoTour, tourT: 0, tourIdx: 0 };

    const animate = () => {
      const id = requestAnimationFrame(animate);
      stateRef.current!.animId = id;
      const s = stateRef.current!;
      if (s.touring) {
        s.tourT += 0.005;
        const idx = Math.floor(s.tourT / (Math.PI * 0.5)) % rooms.length;
        s.tourIdx = idx;
        const rm = rooms[idx];
        const tx = rm.x + Math.cos(s.tourT * 0.5) * 8;
        const tz = rm.z + Math.sin(s.tourT * 0.5) * 8;
        camera.position.x += (tx - camera.position.x) * 0.02;
        camera.position.y += (3.5 + Math.sin(s.tourT * 0.3) - camera.position.y) * 0.02;
        camera.position.z += (tz - camera.position.z) * 0.02;
        camera.lookAt(rm.x, 1.2, rm.z);
        setHoveredRoom(rm.name);
      } else {
        s.theta += (tTheta - s.theta) * 0.08; s.phi += (tPhi - s.phi) * 0.08; s.radius += (tRadius - s.radius) * 0.08;
        camera.position.set(s.radius * Math.sin(s.theta) * Math.cos(s.phi), s.radius * Math.sin(s.phi), s.radius * Math.cos(s.theta) * Math.cos(s.phi));
        camera.lookAt(0, 1, 0);
      }
      s.tTheta = tTheta; s.tPhi = tPhi; s.tRadius = tRadius;
      renderer.render(scene, camera);
    };
    animate();

    const onResize = () => { const nw = el.clientWidth, nh = el.clientHeight; camera.aspect = nw / nh; camera.updateProjectionMatrix(); renderer.setSize(nw, nh); };
    window.addEventListener("resize", onResize);

    return () => {
      cancelAnimationFrame(stateRef.current?.animId || 0);
      el.removeEventListener("mousemove", onMM); el.removeEventListener("mousedown", onMD);
      el.removeEventListener("mouseup", onMU); el.removeEventListener("mousemove", onDrag);
      el.removeEventListener("wheel", onWheel); window.removeEventListener("resize", onResize);
      renderer.dispose();
      if (el.contains(renderer.domElement)) el.removeChild(renderer.domElement);
    };
  }, [rooms, autoTour]);

  const toggleTour = useCallback(() => { setIsPlaying(p => { if (stateRef.current) stateRef.current.touring = !p; return !p; }); }, []);

  const startRec = useCallback(() => {
    if (!mountRef.current || isRec) return;
    const canvas = mountRef.current.querySelector("canvas") as HTMLCanvasElement;
    if (!canvas) return;
    const stream = canvas.captureStream(30);
    const mr = new MediaRecorder(stream, { mimeType: "video/webm;codecs=vp9" });
    chunksRef.current = [];
    mr.ondataavailable = e => { if (e.data.size > 0) chunksRef.current.push(e.data); };
    mr.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: "video/webm" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a"); a.href = url; a.download = "archiguide-3d.webm"; a.click();
      URL.revokeObjectURL(url); setIsRec(false); setRecTime(0);
      if (timerRef.current) clearInterval(timerRef.current);
    };
    mr.start(); recRef.current = mr; setIsRec(true); setRecTime(0);
    if (stateRef.current) stateRef.current.touring = true; setIsPlaying(true);
    timerRef.current = setInterval(() => setRecTime(t => t + 1), 1000);
  }, [isRec]);

  const stopRec = useCallback(() => { recRef.current?.stop(); if (timerRef.current) clearInterval(timerRef.current); }, []);

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <div ref={mountRef} style={{ width: "100%", height: "100%", cursor: isPlaying ? "default" : "grab" }} />
      {hoveredRoom && (
        <div style={{ position: "absolute", top: 14, left: "50%", transform: "translateX(-50%)", background: "rgba(0,0,0,0.75)", backdropFilter: "blur(10px)", color: "white", padding: "6px 20px", borderRadius: 999, fontSize: 14, fontWeight: 600, pointerEvents: "none", border: "1px solid rgba(201,169,110,0.5)" }}>
          📍 {hoveredRoom}
        </div>
      )}
      {isRec && (
        <div style={{ position: "absolute", top: 14, left: 14, background: "rgba(235,87,87,0.9)", color: "white", padding: "6px 14px", borderRadius: 999, fontSize: 13, fontWeight: 700, display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{ width: 8, height: 8, borderRadius: "50%", background: "white" }} />
          REC {Math.floor(recTime / 60).toString().padStart(2, "0")}:{(recTime % 60).toString().padStart(2, "0")}
        </div>
      )}
      {isPlaying && (
        <div style={{ position: "absolute", bottom: 56, left: "50%", transform: "translateX(-50%)", display: "flex", gap: 6 }}>
          {rooms.map((_, i) => (<div key={i} style={{ width: stateRef.current?.tourIdx === i ? 22 : 8, height: 8, borderRadius: 4, background: stateRef.current?.tourIdx === i ? "var(--accent)" : "rgba(255,255,255,0.3)", transition: "all 0.3s ease" }} />))}
        </div>
      )}
      <div style={{ position: "absolute", bottom: 14, right: 14, display: "flex", gap: 8, flexDirection: "column", alignItems: "flex-end" }}>
        <button onClick={toggleTour} style={{ background: isPlaying ? "rgba(201,169,110,0.9)" : "rgba(0,0,0,0.65)", backdropFilter: "blur(8px)", border: "1px solid rgba(201,169,110,0.4)", color: "white", borderRadius: 10, padding: "9px 18px", cursor: "pointer", fontSize: 13, fontWeight: 600 }}>
          {isPlaying ? "⏸ Pause" : "▶ Visite guidée"}
        </button>
        {!isRec
          ? <button onClick={startRec} style={{ background: "rgba(0,0,0,0.65)", backdropFilter: "blur(8px)", border: "1px solid rgba(235,87,87,0.5)", color: "white", borderRadius: 10, padding: "9px 18px", cursor: "pointer", fontSize: 13, fontWeight: 600 }}>🔴 Enregistrer</button>
          : <button onClick={stopRec} style={{ background: "rgba(235,87,87,0.85)", border: "none", color: "white", borderRadius: 10, padding: "9px 18px", cursor: "pointer", fontSize: 13, fontWeight: 600 }}>⏹ Arrêter</button>
        }
      </div>
      {!isPlaying && !isRec && (
        <div style={{ position: "absolute", bottom: 14, left: 14, background: "rgba(0,0,0,0.55)", color: "rgba(255,255,255,0.65)", padding: "7px 14px", borderRadius: 10, fontSize: 11 }}>
          🖱 Glisser pour tourner · Molette pour zoomer
        </div>
      )}
    </div>
  );
}
