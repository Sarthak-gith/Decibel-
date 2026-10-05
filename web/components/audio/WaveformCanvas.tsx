"use client";

import React, { useEffect, useRef } from "react";

interface WaveformCanvasProps {
  analyser: AnalyserNode | null;
  threat: boolean;
}

export default function WaveformCanvas({ analyser, threat }: WaveformCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationId: number;

    const draw = () => {
      animationId = requestAnimationFrame(draw);
      const width = canvas.width;
      const height = canvas.height;

      ctx.fillStyle = "rgb(10, 10, 10)"; // Dark architectural background
      ctx.fillRect(0, 0, width, height);
      ctx.lineWidth = 2;
      ctx.strokeStyle = threat ? "rgb(239, 68, 68)" : "rgb(34, 197, 94)"; // Tailwind red-500 / green-500
      ctx.beginPath();

      if (!analyser) {
        // Idle flat line
        ctx.moveTo(0, height / 2);
        ctx.lineTo(width, height / 2);
        ctx.stroke();
        return;
      }

      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      analyser.getByteTimeDomainData(dataArray);

      const sliceWidth = (width * 1.0) / bufferLength;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0;
        const y = v * (height / 2);

        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
        x += sliceWidth;
      }

      ctx.lineTo(width, height / 2);
      ctx.stroke();
    };

    draw();

    return () => {
      cancelAnimationFrame(animationId);
    };
  }, [analyser, threat]);

  return (
    <canvas
      ref={canvasRef}
      width={800}
      height={150}
      className="w-full h-full rounded-lg border border-zinc-800 shadow-lg"
    />
  );
}
