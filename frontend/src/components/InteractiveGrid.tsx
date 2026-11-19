import React from 'react';

const CELL = 32;          // same size as the panel's old grid lines
const REACH = 140;        // how far from the cursor cells react (px)
const PULL = 4;           // most a cell leans towards the cursor (px)

/**
 * The sign-in panel's grid: only the cells near the cursor light up and lean towards it (with a short fading trail).
 * Nothing moves while the cursor is outside the panel. Still for reduced motion.
 */
export const InteractiveGrid: React.FC = () => {
  const ref = React.useRef<HTMLCanvasElement>(null);

  React.useEffect(() => {
    const canvas = ref.current;
    const host = canvas?.parentElement;
    const ctx = canvas?.getContext('2d');
    if (!canvas || !host || !ctx) return;
    const still = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
    let w = 0, h = 0, cols = 0, rows = 0;
    let glow = new Float32Array(0);
    const pointer = { x: 0, y: 0, inside: false };
    let frame = 0;
    let last = 0;

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = host.clientWidth;
      h = host.clientHeight;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      cols = Math.ceil(w / CELL) + 1;
      rows = Math.ceil(h / CELL) + 1;
      glow = new Float32Array(cols * rows);
      draw(performance.now());
    };

    const draw = (t: number) => {
      ctx.clearRect(0, 0, w, h);
      if (pointer.inside && !still) {
        const g = ctx.createRadialGradient(pointer.x, pointer.y, 0, pointer.x, pointer.y, 200);
        g.addColorStop(0, 'rgba(70,182,151,0.18)');
        g.addColorStop(1, 'rgba(70,182,151,0)');
        ctx.fillStyle = g;
        ctx.fillRect(0, 0, w, h);
      }
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const i = r * cols + c;
          const cx = c * CELL + CELL / 2;
          const cy = r * CELL + CELL / 2;
          let dx = 0, dy = 0, target = 0;
          if (pointer.inside && !still) {
            const ex = pointer.x - cx, ey = pointer.y - cy;
            const d = Math.hypot(ex, ey);
            if (d < REACH) {
              const k = 1 - d / REACH;
              target = k * k;
              if (d > 0.5) {
                dx = (ex / d) * PULL * k;
                dy = (ey / d) * PULL * k;
              }
            }
          }
          glow[i] = Math.max(target, glow[i] * 0.92);  // fade = the trail
          const a = glow[i];
          const x = c * CELL + dx, y = r * CELL + dy;
          if (a > 0.01) {
            ctx.fillStyle = `rgba(70,182,151,${0.12 * a})`;
            ctx.fillRect(x + 1, y + 1, CELL - 2, CELL - 2);
          }
          ctx.strokeStyle = `rgba(255,255,255,${0.04 + 0.22 * a})`;
          ctx.lineWidth = 1;
          ctx.strokeRect(x + 0.5, y + 0.5, CELL, CELL);
        }
      }
    };

    const fading = () => glow.some((a) => a > 0.01);
    const loop = (t: number) => {
      frame = 0;
      if (t - last >= 16) {
        last = t;
        draw(t);
      }
      if (pointer.inside || fading()) frame = requestAnimationFrame(loop);  // stop once everything is still
    };
    const wake = () => { if (!frame) frame = requestAnimationFrame(loop); };

    const move = (e: PointerEvent) => {
      if (e.pointerType === 'touch') return;
      const box = host.getBoundingClientRect();
      pointer.x = e.clientX - box.left;
      pointer.y = e.clientY - box.top;
      pointer.inside = true;
      wake();
    };
    const leave = () => { pointer.inside = false; wake(); };

    const observer = new ResizeObserver(resize);
    observer.observe(host);
    resize();
    if (!still) {
      host.addEventListener('pointermove', move);
      host.addEventListener('pointerleave', leave);
    }
    return () => {
      observer.disconnect();
      cancelAnimationFrame(frame);
      host.removeEventListener('pointermove', move);
      host.removeEventListener('pointerleave', leave);
    };
  }, []);

  return <canvas ref={ref} aria-hidden className="pointer-events-none absolute inset-0" />;
};
