"use client";
import { useState, useRef, useEffect } from "react";

interface Room {
  name: string;
  area: number;
  windows?: number;
  x?: number;
  z?: number;
  w?: number;
  d?: number;
}

interface Props {
  rooms: Room[];
  floorPlanImage?: string;
  onSave: (rooms: Room[]) => void;
  onCancel: () => void;
}

export default function RoomLayoutEditor({ rooms, floorPlanImage, onSave, onCancel }: Props) {
  const [currentRoomIndex, setCurrentRoomIndex] = useState(0);
  const [placedRooms, setPlacedRooms] = useState<Room[]>([]);
  const [imageDimensions, setImageDimensions] = useState({ width: 600, height: 600 });
  const canvasRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);

  const currentRoom = rooms[currentRoomIndex];
  const isComplete = currentRoomIndex >= rooms.length;

  // Load image and get its dimensions
  useEffect(() => {
    if (!floorPlanImage) return;
    
    const img = new Image();
    img.onload = () => {
      setImageDimensions({ width: img.width, height: img.height });
    };
    img.src = floorPlanImage;
  }, [floorPlanImage]);

  const handleCanvasClick = (e: React.MouseEvent) => {
    if (isComplete) return;
    
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    // Get click position relative to canvas
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;
    
    // Calculate room dimensions based on area
    // Scale based on image size - assume image represents ~15m x 15m space
    const imageArea = 15 * 15; // m²
    const pixelsPerSqM = (rect.width * rect.height) / imageArea;
    const roomPixels = currentRoom.area * pixelsPerSqM;
    
    // Aspect ratio based on room type
    let aspectRatio = 1.0;
    if (currentRoom.area > 25) aspectRatio = 1.5;
    else if (currentRoom.area > 15) aspectRatio = 1.3;
    else if (currentRoom.area < 8) aspectRatio = 0.8;
    
    const width = Math.sqrt(roomPixels * aspectRatio);
    const depth = Math.sqrt(roomPixels / aspectRatio);
    
    const newRoom = {
      ...currentRoom,
      x: clickX,
      z: clickY,
      w: width,
      d: depth,
    };
    
    setPlacedRooms([...placedRooms, newRoom]);
    setCurrentRoomIndex(currentRoomIndex + 1);
  };

  const handleUndo = () => {
    if (placedRooms.length === 0) return;
    setPlacedRooms(placedRooms.slice(0, -1));
    setCurrentRoomIndex(currentRoomIndex - 1);
  };

  const handleSave = () => {
    if (!canvasRef.current) return;
    
    const rect = canvasRef.current.getBoundingClientRect();
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    
    // Scale: assume canvas represents 15m x 15m space
    const scaleX = 15 / rect.width;
    const scaleY = 15 / rect.height;
    
    const worldRooms = placedRooms.map(r => ({
      ...r,
      x: ((r.x || 0) - centerX) * scaleX,
      z: ((r.z || 0) - centerY) * scaleY,
      w: (r.w || 60) * scaleX,
      d: (r.d || 60) * scaleY,
    }));
    
    onSave(worldRooms);
  };

  return (
    <div style={{ 
      position: "fixed", 
      inset: 0, 
      background: "rgba(0,0,0,0.92)", 
      zIndex: 1000,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: 20,
    }}>
      <div style={{
        background: "var(--surface)",
        borderRadius: "var(--radius-lg)",
        maxWidth: 1400,
        width: "100%",
        maxHeight: "95vh",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}>
        {/* Header */}
        <div style={{ 
          padding: "20px 24px", 
          borderBottom: "1px solid var(--border)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}>
          <div>
            <h2 style={{ fontSize: 20, fontWeight: 700, color: "var(--text-primary)", marginBottom: 4 }}>
              📍 Positionnement des pièces
            </h2>
            {!isComplete ? (
              <p style={{ fontSize: 15, color: "var(--accent)", fontWeight: 600 }}>
                Cliquez sur le plan pour placer : <strong>{currentRoom?.name}</strong> ({currentRoom?.area}m²)
              </p>
            ) : (
              <p style={{ fontSize: 15, color: "#4ade80", fontWeight: 600 }}>
                ✓ Toutes les pièces sont placées !
              </p>
            )}
          </div>
          <button onClick={onCancel} style={{
            background: "transparent",
            border: "none",
            fontSize: 28,
            color: "var(--text-secondary)",
            cursor: "pointer",
            padding: 8,
            lineHeight: 1,
          }}>
            ×
          </button>
        </div>

        {/* Main content */}
        <div style={{ 
          display: "grid", 
          gridTemplateColumns: "1fr 300px",
          gap: 24,
          padding: 24,
          flex: 1,
          overflow: "auto",
        }}>
          
          {/* Canvas area */}
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div style={{ 
              fontSize: 14, 
              color: "var(--text-primary)",
              background: "var(--accent-light)",
              padding: "12px 16px",
              borderRadius: "var(--radius)",
              border: "2px solid var(--accent)",
              fontWeight: 500,
            }}>
              💡 <strong>Cliquez sur le plan</strong> à l'endroit exact où vous voulez placer chaque pièce
            </div>
            
            <div
              ref={canvasRef}
              onClick={handleCanvasClick}
              style={{
                position: "relative",
                width: "100%",
                aspectRatio: `${imageDimensions.width} / ${imageDimensions.height}`,
                maxHeight: "calc(95vh - 250px)",
                background: floorPlanImage ? `url(${floorPlanImage})` : "var(--bg-secondary)",
                backgroundSize: "100% 100%",
                backgroundPosition: "center",
                backgroundRepeat: "no-repeat",
                borderRadius: "var(--radius-lg)",
                border: isComplete ? "4px solid #4ade80" : "4px solid var(--accent)",
                cursor: isComplete ? "default" : "crosshair",
                overflow: "hidden",
                boxShadow: "0 8px 32px rgba(0,0,0,0.3)",
              }}
            >
              {/* Placed rooms */}
              {placedRooms.map((room, i) => (
                <div
                  key={i}
                  style={{
                    position: "absolute",
                    left: (room.x || 0) - (room.w || 60) / 2,
                    top: (room.z || 0) - (room.d || 60) / 2,
                    width: room.w || 60,
                    height: room.d || 60,
                    background: "rgba(74,222,128,0.35)",
                    border: "3px solid #4ade80",
                    borderRadius: 10,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    pointerEvents: "none",
                    boxShadow: "0 4px 16px rgba(74,222,128,0.4)",
                  }}
                >
                  <div style={{ 
                    background: "rgba(0,0,0,0.85)", 
                    padding: "8px 12px", 
                    borderRadius: 8,
                    color: "#fff",
                    fontSize: 12,
                    fontWeight: 700,
                    textAlign: "center",
                    lineHeight: 1.4,
                    border: "1px solid rgba(74,222,128,0.5)",
                  }}>
                    <div>{room.name}</div>
                    <div style={{ fontSize: 10, opacity: 0.9, marginTop: 3 }}>{room.area}m²</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Room list sidebar */}
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div style={{ 
              fontSize: 14, 
              fontWeight: 700, 
              color: "var(--text-primary)",
              padding: "12px 14px",
              background: "var(--bg-secondary)",
              borderRadius: "var(--radius)",
              border: "1px solid var(--border)",
            }}>
              🏠 Pièces ({placedRooms.length}/{rooms.length})
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8, maxHeight: "calc(95vh - 350px)", overflowY: "auto" }}>
              {rooms.map((room, i) => {
                const isPlaced = i < placedRooms.length;
                const isCurrent = i === currentRoomIndex;
                
                return (
                  <div
                    key={i}
                    style={{
                      padding: "14px 16px",
                      background: isCurrent ? "var(--accent-light)" : isPlaced ? "rgba(74,222,128,0.12)" : "var(--bg-secondary)",
                      border: `2px solid ${isCurrent ? "var(--accent)" : isPlaced ? "#4ade80" : "var(--border)"}`,
                      borderRadius: "var(--radius-lg)",
                      fontSize: 13,
                      opacity: isPlaced && !isCurrent ? 0.6 : 1,
                      transition: "all 0.2s ease",
                    }}
                  >
                    <div style={{ 
                      display: "flex", 
                      alignItems: "center", 
                      gap: 10,
                      marginBottom: 6,
                    }}>
                      {isPlaced && <span style={{ color: "#4ade80", fontSize: 18 }}>✓</span>}
                      {isCurrent && <span style={{ color: "var(--accent)", fontSize: 18 }}>👉</span>}
                      <span style={{ fontWeight: 700, color: "var(--text-primary)", flex: 1, fontSize: 14 }}>
                        {room.name}
                      </span>
                    </div>
                    <div style={{ fontSize: 12, color: "var(--text-secondary)", paddingLeft: isCurrent || isPlaced ? 28 : 0 }}>
                      {room.area}m²
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Footer actions */}
        <div style={{
          padding: "18px 24px",
          borderTop: "1px solid var(--border)",
          display: "flex",
          gap: 12,
          justifyContent: "space-between",
          background: "var(--bg-secondary)",
        }}>
          <button 
            onClick={handleUndo} 
            disabled={placedRooms.length === 0}
            className="btn btn-ghost" 
            style={{ fontSize: 15, opacity: placedRooms.length === 0 ? 0.4 : 1, cursor: placedRooms.length === 0 ? "not-allowed" : "pointer" }}
          >
            ← Annuler la dernière
          </button>
          <div style={{ display: "flex", gap: 12 }}>
            <button onClick={onCancel} className="btn btn-ghost" style={{ fontSize: 15 }}>
              Annuler
            </button>
            <button 
              onClick={handleSave} 
              disabled={!isComplete}
              className="btn btn-primary" 
              style={{ fontSize: 15, opacity: isComplete ? 1 : 0.5, cursor: isComplete ? "pointer" : "not-allowed" }}
            >
              ✓ Appliquer le positionnement
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
