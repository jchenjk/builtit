const { useState, useEffect, useRef, useMemo, useCallback } = React;
const API_BASE = window.__API_BASE__ ?? (location.protocol === "file:" ? "http://localhost:8000" : "");
async function apiListProjects() {
  const r = await fetch(`${API_BASE}/api/projects`);
  if (!r.ok) throw new Error(`Failed to load projects: ${r.status}`);
  return (await r.json()).projects;
}
async function apiGenerate(projectId, parameters) {
  const r = await fetch(`${API_BASE}/api/projects/${projectId}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ parameters })
  });
  if (!r.ok) throw new Error(`Failed to generate: ${r.status}`);
  return await r.json();
}
function ThreeViewer({ parts, bbox }) {
  const mountRef = useRef(null);
  const stateRef = useRef({});
  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;
    const width = mount.clientWidth;
    const height = mount.clientHeight;
    const scene = new THREE.Scene();
    scene.background = null;
    const camera = new THREE.PerspectiveCamera(40, width / height, 1, 5e3);
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(width, height);
    mount.innerHTML = "";
    mount.appendChild(renderer.domElement);
    scene.add(new THREE.AmbientLight(16777215, 0.7));
    const dir = new THREE.DirectionalLight(16777215, 0.7);
    dir.position.set(80, 120, 100);
    scene.add(dir);
    const group = new THREE.Group();
    scene.add(group);
    const ground = new THREE.Mesh(
      new THREE.PlaneGeometry(2e3, 2e3),
      new THREE.MeshLambertMaterial({ color: 15525594 })
    );
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.1;
    scene.add(ground);
    stateRef.current = { scene, camera, renderer, group, mount };
    let isDown = false, lastX = 0, lastY = 0, theta = Math.PI / 4, phi = Math.PI / 5, dist = 200;
    function updateCamera() {
      const cx = (bbox?.min[0] + bbox?.max[0]) / 2 || 0;
      const cy = (bbox?.min[2] + bbox?.max[2]) / 2 || 0;
      const cz = (bbox?.min[1] + bbox?.max[1]) / 2 || 0;
      camera.position.set(
        cx + dist * Math.cos(phi) * Math.sin(theta),
        cy + dist * Math.sin(phi),
        cz + dist * Math.cos(phi) * Math.cos(theta)
      );
      camera.lookAt(cx, cy, cz);
    }
    stateRef.current.updateCamera = () => updateCamera();
    function onDown(e) {
      isDown = true;
      lastX = e.clientX;
      lastY = e.clientY;
    }
    function onUp() {
      isDown = false;
    }
    function onMove(e) {
      if (!isDown) return;
      theta -= (e.clientX - lastX) * 0.01;
      phi = Math.max(0.05, Math.min(Math.PI / 2 - 0.05, phi + (e.clientY - lastY) * 5e-3));
      lastX = e.clientX;
      lastY = e.clientY;
      updateCamera();
    }
    function onWheel(e) {
      e.preventDefault();
      dist *= 1 + e.deltaY * 1e-3;
      dist = Math.max(40, Math.min(1200, dist));
      updateCamera();
    }
    renderer.domElement.addEventListener("mousedown", onDown);
    window.addEventListener("mouseup", onUp);
    window.addEventListener("mousemove", onMove);
    renderer.domElement.addEventListener("wheel", onWheel, { passive: false });
    let raf;
    const tick = () => {
      renderer.render(scene, camera);
      raf = requestAnimationFrame(tick);
    };
    tick();
    function onResize() {
      const w = mount.clientWidth, h = mount.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    }
    window.addEventListener("resize", onResize);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("mouseup", onUp);
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("resize", onResize);
      renderer.dispose();
      mount.innerHTML = "";
    };
  }, []);
  useEffect(() => {
    const s = stateRef.current;
    if (!s.group) return;
    while (s.group.children.length) s.group.remove(s.group.children[0]);
    const center = bbox ? [
      (bbox.min[0] + bbox.max[0]) / 2,
      (bbox.min[1] + bbox.max[1]) / 2,
      (bbox.min[2] + bbox.max[2]) / 2
    ] : [0, 0, 0];
    (parts || []).forEach((p) => {
      const geom = new THREE.BoxGeometry(p.dx, p.dz, p.dy);
      const mat = new THREE.MeshLambertMaterial({ color: p.color || "#c69c6d" });
      const mesh = new THREE.Mesh(geom, mat);
      mesh.position.set(
        p.x + p.dx / 2 - center[0],
        p.z + p.dz / 2 - center[2],
        p.y + p.dy / 2 - center[1]
      );
      const edges = new THREE.LineSegments(
        new THREE.EdgesGeometry(geom),
        new THREE.LineBasicMaterial({ color: 4863264, linewidth: 1, transparent: true, opacity: 0.5 })
      );
      mesh.add(edges);
      s.group.add(mesh);
    });
    const span = bbox ? Math.max(
      bbox.max[0] - bbox.min[0],
      bbox.max[1] - bbox.min[1],
      bbox.max[2] - bbox.min[2]
    ) : 100;
    s.dist = span * 1.6;
    if (s.updateCamera) {
      s.dist = Math.max(80, span * 1.6);
    }
    if (s.updateCamera) s.updateCamera();
  }, [parts, bbox]);
  return /* @__PURE__ */ React.createElement("div", { ref: mountRef, className: "three-canvas" });
}
function NumberInput({ label, value, onChange, min, max, step, unit }) {
  return /* @__PURE__ */ React.createElement("label", { className: "block" }, /* @__PURE__ */ React.createElement("div", { className: "text-xs font-semibold text-stone-600 mb-1 uppercase tracking-wide" }, label), /* @__PURE__ */ React.createElement("div", { className: "flex items-center gap-2" }, /* @__PURE__ */ React.createElement(
    "input",
    {
      type: "range",
      min,
      max,
      step: step || 1,
      value,
      onChange: (e) => onChange(Number(e.target.value)),
      className: "flex-1 accent-orange-700"
    }
  ), /* @__PURE__ */ React.createElement(
    "input",
    {
      type: "number",
      value,
      min,
      max,
      step: step || 1,
      onChange: (e) => onChange(Number(e.target.value)),
      className: "w-20 px-2 py-1 border border-stone-300 rounded text-sm"
    }
  ), /* @__PURE__ */ React.createElement("span", { className: "text-xs text-stone-500 w-6" }, unit)));
}
function BoolInput({ label, value, onChange }) {
  return /* @__PURE__ */ React.createElement("label", { className: "flex items-center gap-2 select-none" }, /* @__PURE__ */ React.createElement(
    "input",
    {
      type: "checkbox",
      checked: !!value,
      onChange: (e) => onChange(e.target.checked),
      className: "w-4 h-4 accent-orange-700"
    }
  ), /* @__PURE__ */ React.createElement("span", { className: "text-sm text-stone-700" }, label));
}
function ParamForm({ schema, values, onChange }) {
  return /* @__PURE__ */ React.createElement("div", { className: "space-y-4" }, schema.parameters.map((p) => {
    if (p.kind === "boolean") {
      return /* @__PURE__ */ React.createElement(
        BoolInput,
        {
          key: p.key,
          label: p.label,
          value: values[p.key],
          onChange: (v) => onChange(p.key, v)
        }
      );
    }
    return /* @__PURE__ */ React.createElement("div", { key: p.key }, /* @__PURE__ */ React.createElement(
      NumberInput,
      {
        label: p.label,
        value: values[p.key],
        onChange: (v) => onChange(p.key, v),
        min: p.min,
        max: p.max,
        step: p.step,
        unit: p.unit
      }
    ), p.help && /* @__PURE__ */ React.createElement("div", { className: "text-xs text-stone-500 mt-1" }, p.help));
  }));
}
function ShoppingList({ data }) {
  if (!data) return null;
  const [quotes, setQuotes] = useState(null);
  const [liveState, setLiveState] = useState("idle");
  const [liveEnabled, setLiveEnabled] = useState(null);
  const [zip, setZip] = useState("");
  useEffect(() => {
    setQuotes(null);
    setLiveState("idle");
    fetch(`${API_BASE}/api/prices/status`).then((r) => r.json()).then((d) => setLiveEnabled(d.live_enabled)).catch(() => setLiveEnabled(false));
  }, [data]);
  const fetchLive = async () => {
    setLiveState("loading");
    try {
      const ids = [...new Set(data.lines.map((l) => l.catalog_id))];
      const body = { catalog_ids: ids };
      if (/^\d{5}$/.test(zip)) body.zip_code = zip;
      const r = await fetch(`${API_BASE}/api/prices/live`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const d = await r.json();
      const map = {};
      d.quotes.forEach((q) => {
        map[q.catalog_id] = q;
      });
      setQuotes(map);
      setLiveState("done");
    } catch (e) {
      setLiveState("error");
    }
  };
  const grouped = useMemo(() => {
    const g = { lumber: [], panel: [], hardware: [] };
    data.lines.forEach((l) => g[l.kind] && g[l.kind].push(l));
    return g;
  }, [data]);
  const priceFor = (l) => {
    const q = quotes?.[l.catalog_id];
    return q ? q.price : l.unit_price;
  };
  const liveTotal = useMemo(() => {
    if (!quotes) return null;
    return data.lines.reduce((s, l) => s + priceFor(l) * l.qty, 0);
  }, [quotes, data]);
  const anyLive = quotes && Object.values(quotes).some((q) => q.fetched_live);
  const Section = ({ title, lines }) => lines.length ? /* @__PURE__ */ React.createElement("div", { className: "mb-4" }, /* @__PURE__ */ React.createElement("div", { className: "text-xs font-semibold uppercase tracking-wide text-stone-500 mb-2" }, title), /* @__PURE__ */ React.createElement("div", { className: "divide-y divide-stone-200 border border-stone-200 rounded-lg bg-white" }, lines.map((l, i) => {
    const q = quotes?.[l.catalog_id];
    const unit = priceFor(l);
    const isLive = q?.fetched_live;
    return /* @__PURE__ */ React.createElement("div", { key: i, className: "p-3 flex items-start justify-between gap-3" }, /* @__PURE__ */ React.createElement("div", { className: "flex-1 min-w-0" }, /* @__PURE__ */ React.createElement("div", { className: "font-medium text-stone-800 text-sm flex items-center gap-2" }, l.name, isLive && /* @__PURE__ */ React.createElement("span", { className: "text-[10px] px-1.5 py-0.5 rounded-full bg-orange-100 text-orange-700 font-semibold uppercase tracking-wide" }, "live")), /* @__PURE__ */ React.createElement("div", { className: "text-xs text-stone-500 mt-0.5" }, l.vendor, " \xB7 ", l.details?.notes || `${l.qty} \xD7 $${unit.toFixed(2)}`, isLive && q.link && /* @__PURE__ */ React.createElement(React.Fragment, null, " \xB7 ", /* @__PURE__ */ React.createElement("a", { href: q.link, target: "_blank", rel: "noreferrer", className: "text-orange-600 hover:underline" }, "view item \u2197"))), isLive && q.title && q.title !== l.name && /* @__PURE__ */ React.createElement("div", { className: "text-[11px] text-stone-400 mt-0.5 truncate" }, "matched: ", q.title)), /* @__PURE__ */ React.createElement("div", { className: "text-right" }, /* @__PURE__ */ React.createElement("div", { className: "text-sm font-semibold num text-stone-800" }, "$", (unit * l.qty).toFixed(2)), /* @__PURE__ */ React.createElement("div", { className: "text-xs text-stone-500 num" }, "qty ", l.qty)));
  }))) : null;
  return /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("div", { className: "mb-4 p-3 rounded-lg border border-orange-200 bg-orange-50 flex flex-wrap items-center gap-2" }, /* @__PURE__ */ React.createElement("div", { className: "text-xs text-orange-800 flex-1 min-w-[180px]" }, liveEnabled === false ? "Live pricing not configured on this server \u2014 showing catalog estimates." : "Pull today's Home Depot prices for this shopping list."), /* @__PURE__ */ React.createElement(
    "input",
    {
      value: zip,
      onChange: (e) => setZip(e.target.value.replace(/\D/g, "").slice(0, 5)),
      placeholder: "ZIP (optional)",
      disabled: liveEnabled === false,
      className: "w-28 px-2 py-1.5 text-xs rounded border border-orange-200 bg-white disabled:opacity-50"
    }
  ), /* @__PURE__ */ React.createElement(
    "button",
    {
      onClick: fetchLive,
      disabled: liveState === "loading" || liveEnabled === false,
      className: "px-3 py-1.5 text-xs font-semibold rounded bg-orange-600 text-white hover:bg-orange-700 disabled:opacity-50"
    },
    liveState === "loading" ? "Fetching\u2026" : "Get live prices"
  ), liveState === "error" && /* @__PURE__ */ React.createElement("div", { className: "w-full text-xs text-red-600" }, "Couldn't fetch live prices \u2014 showing estimates."), liveState === "done" && !anyLive && /* @__PURE__ */ React.createElement("div", { className: "w-full text-xs text-orange-700" }, "Live lookup unavailable right now \u2014 showing catalog estimates.")), /* @__PURE__ */ React.createElement(Section, { title: "Lumber", lines: grouped.lumber }), /* @__PURE__ */ React.createElement(Section, { title: "Sheet goods", lines: grouped.panel }), /* @__PURE__ */ React.createElement(Section, { title: "Hardware & finish", lines: grouped.hardware }), /* @__PURE__ */ React.createElement("div", { className: "mt-6 p-4 rounded-lg bg-stone-900 text-white flex items-baseline justify-between" }, /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("div", { className: "text-xs uppercase tracking-wide opacity-70" }, anyLive ? "Total (live prices)" : "Estimated total"), /* @__PURE__ */ React.createElement("div", { className: "text-xs opacity-60 mt-1" }, anyLive ? "Live Home Depot prices; items without a match use catalog estimates. Tax not included." : "Tax not included. Prices reflect typical Home Depot stock.")), /* @__PURE__ */ React.createElement("div", { className: "text-3xl font-bold num" }, "$", (liveTotal ?? data.total_cost).toFixed(2))));
}
function CutDiagrams({ diagrams }) {
  if (!diagrams || diagrams.length === 0) return null;
  return /* @__PURE__ */ React.createElement("div", { className: "space-y-4" }, diagrams.map((d, i) => /* @__PURE__ */ React.createElement("details", { key: i, className: "border border-stone-200 rounded-lg bg-white overflow-hidden", open: i === 0 }, /* @__PURE__ */ React.createElement("summary", { className: "p-3 bg-stone-50 hover:bg-stone-100 flex items-center justify-between" }, /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("div", { className: "font-medium text-sm text-stone-800" }, d.stock_name), /* @__PURE__ */ React.createElement("div", { className: "text-xs text-stone-500" }, d.pieces.length, " board(s)")), /* @__PURE__ */ React.createElement("div", { className: "text-stone-400 text-xs" }, "click to expand")), /* @__PURE__ */ React.createElement("div", { className: "p-3 space-y-3" }, d.pieces.map((piece, j) => {
    const total = d.stock_length_in;
    const cuts = piece.cuts;
    return /* @__PURE__ */ React.createElement("div", { key: j }, /* @__PURE__ */ React.createElement("div", { className: "text-xs font-semibold text-stone-600 mb-1" }, "Board #", piece.stock_index, " \u2014 ", total, '" stock, ', piece.leftover_in, '" leftover'), /* @__PURE__ */ React.createElement("div", { className: "flex h-8 rounded overflow-hidden border border-stone-300 bg-stone-100" }, cuts.map((c, k) => {
      const colors = ["#c97b4f", "#c69c6d", "#a87b4f", "#d6b48a", "#8b5a2b"];
      return /* @__PURE__ */ React.createElement(
        "div",
        {
          key: k,
          style: { width: `${c.length_in / total * 100}%`, background: colors[k % colors.length] },
          className: "flex items-center justify-center text-white text-xs font-medium border-r border-stone-50/40"
        },
        c.length_in,
        '"'
      );
    }), /* @__PURE__ */ React.createElement(
      "div",
      {
        style: { width: `${piece.leftover_in / total * 100}%` },
        className: "bg-stone-200 flex items-center justify-center text-stone-500 text-xs"
      },
      "waste"
    )), /* @__PURE__ */ React.createElement("div", { className: "flex flex-wrap gap-x-3 mt-1 text-xs text-stone-500" }, cuts.map((c, k) => /* @__PURE__ */ React.createElement("span", { key: k }, "\u2022 ", c.name))));
  })))));
}
function Instructions({ data }) {
  if (!data) return null;
  const hours = (data.estimated_total_minutes / 60).toFixed(1);
  return /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("div", { className: "grid grid-cols-2 gap-3 mb-5" }, /* @__PURE__ */ React.createElement("div", { className: "bg-white border border-stone-200 rounded-lg p-3" }, /* @__PURE__ */ React.createElement("div", { className: "text-xs uppercase tracking-wide text-stone-500" }, "Estimated time"), /* @__PURE__ */ React.createElement("div", { className: "text-2xl font-bold mt-0.5 num text-stone-800" }, hours, " ", /* @__PURE__ */ React.createElement("span", { className: "text-sm font-normal text-stone-500" }, "hours"))), /* @__PURE__ */ React.createElement("div", { className: "bg-white border border-stone-200 rounded-lg p-3" }, /* @__PURE__ */ React.createElement("div", { className: "text-xs uppercase tracking-wide text-stone-500" }, "Steps"), /* @__PURE__ */ React.createElement("div", { className: "text-2xl font-bold mt-0.5 num text-stone-800" }, data.steps.length))), /* @__PURE__ */ React.createElement("div", { className: "mb-5" }, /* @__PURE__ */ React.createElement("div", { className: "text-xs uppercase tracking-wide font-semibold text-stone-600 mb-2" }, "Tools you'll need"), /* @__PURE__ */ React.createElement("ul", { className: "grid grid-cols-1 sm:grid-cols-2 gap-1 text-sm text-stone-700" }, data.tools.map((t, i) => /* @__PURE__ */ React.createElement("li", { key: i, className: "flex gap-2" }, /* @__PURE__ */ React.createElement("span", { className: "text-orange-700" }, "\u2022"), t)))), /* @__PURE__ */ React.createElement("div", { className: "space-y-3" }, data.steps.map((s) => /* @__PURE__ */ React.createElement("div", { key: s.step, className: "bg-white border border-stone-200 rounded-lg p-4 flex gap-4" }, /* @__PURE__ */ React.createElement("div", { className: "step-num w-9 h-9 rounded-full flex items-center justify-center font-bold flex-shrink-0" }, s.step), /* @__PURE__ */ React.createElement("div", { className: "flex-1 min-w-0" }, /* @__PURE__ */ React.createElement("div", { className: "flex items-center justify-between gap-2 mb-1" }, /* @__PURE__ */ React.createElement("h4", { className: "font-semibold text-stone-800" }, s.title), /* @__PURE__ */ React.createElement("span", { className: "text-xs text-stone-500 num flex-shrink-0" }, "~", s.estimated_minutes, " min")), /* @__PURE__ */ React.createElement("p", { className: "text-sm text-stone-600 leading-relaxed" }, s.body))))), data.tips && data.tips.length > 0 && /* @__PURE__ */ React.createElement("div", { className: "mt-6 p-4 bg-amber-50 border border-amber-200 rounded-lg" }, /* @__PURE__ */ React.createElement("div", { className: "text-xs uppercase tracking-wide font-semibold text-amber-800 mb-2" }, "Pro tips"), /* @__PURE__ */ React.createElement("ul", { className: "space-y-1 text-sm text-amber-900" }, data.tips.map((t, i) => /* @__PURE__ */ React.createElement("li", { key: i }, "\u2022 ", t)))), /* @__PURE__ */ React.createElement("div", { className: "mt-6 p-4 bg-red-50 border border-red-200 rounded-lg" }, /* @__PURE__ */ React.createElement("div", { className: "text-xs uppercase tracking-wide font-semibold text-red-800 mb-2" }, "Safety"), /* @__PURE__ */ React.createElement("ul", { className: "space-y-1 text-sm text-red-900" }, data.safety.map((s, i) => /* @__PURE__ */ React.createElement("li", { key: i }, "\u2022 ", s)))));
}
function App() {
  const [projects, setProjects] = useState([]);
  const [selected, setSelected] = useState(null);
  const [params, setParams] = useState({});
  const [build, setBuild] = useState(null);
  const [tab, setTab] = useState("model");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);
  useEffect(() => {
    apiListProjects().then((ps) => {
      setProjects(ps);
      const first = ps[0];
      if (first) {
        setSelected(first);
        const def = {};
        first.parameters.forEach((p) => def[p.key] = p.default);
        setParams(def);
      }
    }).catch((e) => setErr(e.message));
  }, []);
  useEffect(() => {
    if (!selected) return;
    const t = setTimeout(() => {
      setLoading(true);
      apiGenerate(selected.id, params).then((d) => {
        setBuild(d);
        setLoading(false);
        setErr(null);
      }).catch((e) => {
        setErr(e.message);
        setLoading(false);
      });
    }, 200);
    return () => clearTimeout(t);
  }, [selected, params]);
  const onPickProject = (p) => {
    setSelected(p);
    const def = {};
    p.parameters.forEach((x) => def[x.key] = x.default);
    setParams(def);
    setBuild(null);
  };
  return /* @__PURE__ */ React.createElement("div", { className: "min-h-screen" }, /* @__PURE__ */ React.createElement("header", { className: "bg-stone-900 text-white" }, /* @__PURE__ */ React.createElement("div", { className: "max-w-7xl mx-auto px-6 py-5 flex items-center justify-between" }, /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("div", { className: "flex items-center gap-2" }, /* @__PURE__ */ React.createElement("div", { className: "w-8 h-8 rounded bg-orange-600 flex items-center justify-center font-bold" }, "B"), /* @__PURE__ */ React.createElement("h1", { className: "text-xl font-bold tracking-tight" }, "Builtit")), /* @__PURE__ */ React.createElement("p", { className: "text-xs text-stone-400 mt-1" }, "DIY carpentry, designed for beginners. Pick a project, tweak the dimensions, build it.")), /* @__PURE__ */ React.createElement("div", { className: "text-right text-xs text-stone-400" }, /* @__PURE__ */ React.createElement("div", null, "API: ", /* @__PURE__ */ React.createElement("span", { className: err ? "text-red-400" : "text-green-400" }, err ? "offline" : "connected")), /* @__PURE__ */ React.createElement("div", null, API_BASE)))), err && /* @__PURE__ */ React.createElement("div", { className: "bg-red-50 border-b border-red-200 px-6 py-3 text-sm text-red-800" }, /* @__PURE__ */ React.createElement("strong", null, "Could not reach the backend."), " Make sure the FastAPI server is running on ", API_BASE, ". (", err, ")"), /* @__PURE__ */ React.createElement("div", { className: "max-w-7xl mx-auto px-6 py-6" }, /* @__PURE__ */ React.createElement("div", { className: "grid grid-cols-1 md:grid-cols-3 gap-3 mb-6" }, projects.map((p) => /* @__PURE__ */ React.createElement(
    "button",
    {
      key: p.id,
      onClick: () => onPickProject(p),
      className: `text-left p-4 rounded-xl border-2 transition-all ${selected?.id === p.id ? "border-orange-600 bg-orange-50 shadow-sm" : "border-stone-200 bg-white hover:border-stone-400"}`
    },
    /* @__PURE__ */ React.createElement("div", { className: "flex items-start justify-between gap-2" }, /* @__PURE__ */ React.createElement("div", null, /* @__PURE__ */ React.createElement("div", { className: "font-bold text-stone-800" }, p.name), /* @__PURE__ */ React.createElement("div", { className: "text-xs text-stone-500 mt-0.5" }, p.difficulty, " \xB7 ~", p.estimated_time_hours, "h")), selected?.id === p.id && /* @__PURE__ */ React.createElement("div", { className: "text-orange-600 text-xs font-semibold" }, "SELECTED")),
    /* @__PURE__ */ React.createElement("div", { className: "text-sm text-stone-600 mt-2 leading-snug" }, p.description)
  ))), selected && /* @__PURE__ */ React.createElement("div", { className: "grid grid-cols-1 lg:grid-cols-12 gap-6" }, /* @__PURE__ */ React.createElement("aside", { className: "lg:col-span-3 bg-white p-5 rounded-xl border border-stone-200 h-fit sticky top-4" }, /* @__PURE__ */ React.createElement("h3", { className: "font-bold text-stone-800 mb-1" }, selected.name), /* @__PURE__ */ React.createElement("p", { className: "text-xs text-stone-500 mb-4" }, "Adjust to fit your space. Numbers update live."), /* @__PURE__ */ React.createElement(
    ParamForm,
    {
      schema: selected,
      values: params,
      onChange: (k, v) => setParams((s) => ({ ...s, [k]: v }))
    }
  )), /* @__PURE__ */ React.createElement("main", { className: "lg:col-span-9" }, /* @__PURE__ */ React.createElement("div", { className: "flex gap-1 mb-4 bg-stone-200 p-1 rounded-lg w-fit" }, [
    ["model", "3D Model"],
    ["shopping", "Shopping List"],
    ["cuts", "Cut Diagrams"],
    ["instructions", "Instructions"]
  ].map(([k, label]) => /* @__PURE__ */ React.createElement(
    "button",
    {
      key: k,
      onClick: () => setTab(k),
      className: `px-4 py-2 rounded-md text-sm font-medium transition ${tab === k ? "bg-white text-stone-900 shadow-sm" : "text-stone-600 hover:text-stone-900"}`
    },
    label
  ))), /* @__PURE__ */ React.createElement("div", { className: "relative" }, loading && /* @__PURE__ */ React.createElement("div", { className: "absolute top-2 right-2 z-10 bg-white/80 backdrop-blur px-2 py-1 rounded text-xs text-stone-600" }, "recalculating\u2026"), tab === "model" && build && /* @__PURE__ */ React.createElement("div", { className: "bg-white p-4 rounded-xl border border-stone-200" }, /* @__PURE__ */ React.createElement(ThreeViewer, { parts: build.model_3d.parts, bbox: build.model_3d.bbox }), /* @__PURE__ */ React.createElement("div", { className: "text-xs text-stone-500 mt-2 text-center" }, "drag to rotate \xB7 scroll to zoom \xB7 ", build.model_3d.parts.length, " parts")), tab === "shopping" && build && /* @__PURE__ */ React.createElement("div", { className: "bg-stone-50 p-4 rounded-xl border border-stone-200" }, /* @__PURE__ */ React.createElement(ShoppingList, { data: build.shopping_list })), tab === "cuts" && build && /* @__PURE__ */ React.createElement("div", { className: "bg-stone-50 p-4 rounded-xl border border-stone-200" }, /* @__PURE__ */ React.createElement("p", { className: "text-sm text-stone-600 mb-3" }, "Each row shows how cuts pack onto a single stock board. Mark these layouts on your lumber before you start cutting \u2014 it saves a trip back to the store."), /* @__PURE__ */ React.createElement(CutDiagrams, { diagrams: build.shopping_list.cut_diagrams })), tab === "instructions" && build && /* @__PURE__ */ React.createElement("div", { className: "bg-stone-50 p-4 rounded-xl border border-stone-200" }, /* @__PURE__ */ React.createElement(Instructions, { data: build.instructions })), !build && !err && /* @__PURE__ */ React.createElement("div", { className: "bg-white p-12 rounded-xl border border-stone-200 text-center text-stone-500" }, "Loading your build\u2026"))))), /* @__PURE__ */ React.createElement("footer", { className: "max-w-7xl mx-auto px-6 py-8 text-xs text-stone-500" }, "Built with FastAPI, React, and Three.js. Prices are illustrative \u2014 wire in a live data source for production."));
}
ReactDOM.createRoot(document.getElementById("root")).render(/* @__PURE__ */ React.createElement(App, null));
