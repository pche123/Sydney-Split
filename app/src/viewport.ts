// Pan and zoom for the SVG map: mouse drag, wheel, one-finger pan, two-finger pinch, and buttons.

export class Viewport {
  vb: number[];
  moved = false;                       // true if the last pointer gesture was a drag (so it isn't a tap)
  private pts = new Map<number, { x: number; y: number }>();
  private start: { vb: number[]; x: number; y: number; dist: number } | null = null;

  constructor(private svg: SVGSVGElement, private W: number, private H: number, private onChange: () => void) {
    this.vb = [0, 0, W, H];
    svg.addEventListener("pointerdown", (e) => this.down(e));
    window.addEventListener("pointermove", (e) => this.move(e));
    window.addEventListener("pointerup", (e) => this.up(e));
    window.addEventListener("pointercancel", (e) => this.up(e));
    svg.addEventListener("wheel", (e) => { e.preventDefault(); this.zoom(e.deltaY > 0 ? 1.15 : 1 / 1.15, e.clientX, e.clientY); }, { passive: false });
    window.addEventListener("resize", () => { this.fit(); this.apply(); });
  }

  get dragging() { return this.pts.size > 0 && this.moved; }

  private snapshot() {
    const p = [...this.pts.values()];
    const cx = p.reduce((s, q) => s + q.x, 0) / p.length, cy = p.reduce((s, q) => s + q.y, 0) / p.length;
    const dist = p.length > 1 ? Math.hypot(p[0].x - p[1].x, p[0].y - p[1].y) : 0;
    this.start = { vb: this.vb.slice(), x: cx, y: cy, dist };
  }
  private down(e: PointerEvent) {
    this.pts.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (this.pts.size === 1) this.moved = false;
    this.snapshot();
    this.svg.classList.add("dragging");
  }
  private move(e: PointerEvent) {
    if (!this.pts.has(e.pointerId) || !this.start) return;
    this.pts.set(e.pointerId, { x: e.clientX, y: e.clientY });
    const p = [...this.pts.values()];
    const cx = p.reduce((s, q) => s + q.x, 0) / p.length, cy = p.reduce((s, q) => s + q.y, 0) / p.length;
    const r = this.svg.getBoundingClientRect(), s0 = this.start;
    let w = s0.vb[2], h = s0.vb[3];
    if (p.length > 1 && s0.dist > 0) {               // pinch: scale around the start midpoint
      const f = s0.dist / Math.max(Math.hypot(p[0].x - p[1].x, p[0].y - p[1].y), 1);
      w = Math.min(Math.max(s0.vb[2] * f, this.W / 14), this.W * 1.3); h = w * s0.vb[3] / s0.vb[2];
    }
    const k0 = s0.vb[2] / r.width, k = w / r.width;
    const ax = s0.vb[0] + (s0.x - r.left) * k0, ay = s0.vb[1] + (s0.y - r.top) * k0;   // map point under the start midpoint
    if (Math.abs(cx - s0.x) + Math.abs(cy - s0.y) > 4 || p.length > 1) this.moved = true;
    this.vb = [ax - (cx - r.left) * k, ay - (cy - r.top) * k, w, h];
    this.apply();
  }
  private up(e: PointerEvent) {
    if (!this.pts.delete(e.pointerId)) return;
    if (this.pts.size) this.snapshot(); else { this.start = null; this.svg.classList.remove("dragging"); }
  }

  zoom(f: number, cx?: number, cy?: number) {
    const r = this.svg.getBoundingClientRect();
    const px = cx === undefined ? 0.5 : (cx - r.left) / r.width, py = cy === undefined ? 0.5 : (cy - r.top) / r.height;
    const nw = Math.min(Math.max(this.vb[2] * f, this.W / 14), this.W * 1.3), nh = nw * this.vb[3] / this.vb[2];
    this.vb = [this.vb[0] + (this.vb[2] - nw) * px, this.vb[1] + (this.vb[3] - nh) * py, nw, nh];
    this.apply();
  }
  /** Show the whole city, keeping the map's aspect ratio. */
  fit() {
    const ar = this.svg.clientHeight / Math.max(this.svg.clientWidth, 1);
    if (this.H / this.W > ar) { const w = this.H / ar; this.vb = [-(w - this.W) / 2, 0, w, this.H]; }
    else { const h = this.W * ar; this.vb = [0, -(h - this.H) / 2, this.W, h]; }
  }
  /** Centre on a point, showing a window `width` map-units wide. */
  focus(x: number, y: number, width: number) {
    const h = width * this.vb[3] / this.vb[2];
    this.vb = [x - width / 2, y - h / 2, width, h];
    this.apply();
  }
  apply() {
    this.svg.setAttribute("viewBox", this.vb.map((v) => v.toFixed(1)).join(" "));
    this.onChange();
  }
}
