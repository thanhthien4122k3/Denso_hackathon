"use strict";

(function () {
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));

  /* ================================================================ helpers */
  function h(tag, props, children) {
    const n = document.createElement(tag);
    if (props) for (const k in props) {
      const v = props[k];
      if (v === undefined || v === null) continue;
      if (k === "text") n.textContent = v;
      else if (k === "class") n.className = v;
      else if (k === "html") n.innerHTML = v;
      else if (k === "value") n.value = v;
      else if (k === "style") n.setAttribute("style", v);
      else if (k === "checked" || k === "disabled" || k === "selected" || k === "readonly" || k === "required") { if (v) n.setAttribute(k, ""); }
      else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
      else n.setAttribute(k, v);
    }
    if (children !== undefined) (Array.isArray(children) ? children : [children]).forEach((c) => {
      if (c === null || c === undefined) return;
      n.appendChild(typeof c === "string" || typeof c === "number" ? document.createTextNode(c) : c);
    });
    return n;
  }

  async function api(path, opts) {
    const resp = await fetch(path, opts);
    let body = null;
    try { body = await resp.json(); } catch (e) {}
    if (!resp.ok) {
      let msg;
      if (body && body.detail) msg = typeof body.detail === "string" ? body.detail : "Dữ liệu không hợp lệ.";
      else msg = (body && body.message) || ("Lỗi " + resp.status);
      const err = new Error(msg); err.status = resp.status; throw err;
    }
    return body;
  }

  function toast(msg, type) {
    const t = $("#toast");
    t.textContent = msg; t.className = "toast visible " + (type || "success");
    clearTimeout(t._timer); t._timer = setTimeout(() => { t.className = "toast"; }, 4200);
  }

  function openModal(title, bodyNode) {
    $("#modal-title").textContent = title;
    const b = $("#modal-body"); b.textContent = ""; b.appendChild(bodyNode);
    $("#modal").classList.remove("hidden");
  }
  function closeModal() { $("#modal").classList.add("hidden"); }
  $("#modal-close").addEventListener("click", closeModal);
  $("#modal").addEventListener("click", (e) => { if (e.target.id === "modal") closeModal(); });

  function uuid() {
    if (typeof crypto !== "undefined" && crypto.randomUUID) { try { return crypto.randomUUID(); } catch (e) {} }
    if (typeof crypto !== "undefined" && crypto.getRandomValues) {
      const b = crypto.getRandomValues(new Uint8Array(16));
      b[6] = (b[6] & 0x0f) | 0x40; b[8] = (b[8] & 0x3f) | 0x80;
      const hex = Array.from(b, x => x.toString(16).padStart(2, "0")).join("");
      return hex.slice(0, 8) + "-" + hex.slice(8, 12) + "-" + hex.slice(12, 16) + "-" + hex.slice(16, 20) + "-" + hex.slice(20);
    }
    return "xxxxxxxx-xxxx-4xxx-yxxx-" + String(Date.now()).slice(-12);
  }

  function iso(v) { return v ? new Date(v).toISOString() : null; }
  function fmt(v) { if (!v) return ""; const d = new Date(v); return isNaN(d) ? String(v) : d.toLocaleString("vi-VN"); }
  function fmtDate(v) { if (!v) return ""; const d = new Date(v); return isNaN(d) ? String(v) : d.toLocaleDateString("vi-VN"); }

  const ICONS = {
    dashboard: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    operations: '<path d="M9 3h6v4H9z"/><path d="M6 4H5a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2h-1"/><path d="M3 12h18"/>',
    incidents: '<path d="M12 3l9 16H3z"/><path d="M12 10v4"/><path d="M12 17h.01"/>',
    tasks: '<path d="M3 5h18"/><path d="M3 12h18"/><path d="M3 19h12"/><path d="M9 3l2 2-2 2"/>',
    map: '<circle cx="6" cy="6" r="2.5"/><circle cx="18" cy="6" r="2.5"/><circle cx="12" cy="18" r="2.5"/><path d="M8.2 7.5l2.6 8.2M15.8 7.5l-2.6 8.2M8 5h8"/>',
    analysis: '<path d="M3 21h18"/><path d="M6 16l4-4 4 3 5-7"/>',
    scenarios: '<path d="M9 3h6M10 3v5.5L4.5 18a2 2 0 0 0 1.8 3h11.4a2 2 0 0 0 1.8-3L14 8.5V3"/><path d="M8 15h8"/>',
    catalog: '<path d="M21 8l-9-5-9 5v8l9 5 9-5z"/><path d="M3 8l9 5 9-5"/><path d="M12 13v8"/>',
    system: '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v7c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>',
    survey: '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-.8.4-1 1-1 1.7"/><path d="M12 17h.01"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    check: '<path d="M4 12l5 5L20 6"/>',
    alert: '<path d="M12 3l9 16H3z"/><path d="M12 10v4"/><path d="M12 17h.01"/>',
    empty: '<path d="M4 8h16v11a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z"/><path d="M4 8l2-4h12l2 4"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    database: '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v7c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>',
  };
  function icon(name, cls) {
    const s = h("span", { class: "icon " + (cls || ""), "aria-hidden": "true" });
    s.innerHTML = '<svg viewBox="0 0 24 24">' + (ICONS[name] || "") + "</svg>";
    return s;
  }

  /* ======================================================= ui primitives */
  function spinner() { return h("div", { class: "loading" }, [h("div", { class: "spinner" }), "Đang tải..."]); }
  function emptyBox(ic, title, desc, action) {
    return h("div", { class: "state" }, [
      h("div", { class: "state-icon" }, [icon(ic || "empty")]),
      h("div", { class: "state-title", text: title || "Không có dữ liệu" }),
      desc ? h("div", { class: "state-desc", text: desc }) : null,
      action || null,
    ]);
  }
  function errorBox(message, onRetry) {
    return h("div", { class: "state" }, [
      h("div", { class: "state-icon" }, [icon("alert")]),
      h("div", { class: "state-title", text: "Không tải được dữ liệu" }),
      h("div", { class: "state-desc", text: message }),
      onRetry ? h("button", { class: "btn btn-secondary btn-sm", text: "Thử lại", onclick: onRetry }) : null,
    ]);
  }

  function badge(text, kind) { return h("span", { class: "badge badge-" + kind, text: text }); }
  function statusBadge(s) {
    const map = { OPEN: ["Sự cố mở", "red"], INVESTIGATING: ["Đang điều tra", "amber"], MITIGATING: ["Đang xử lý", "blue"], RESOLVED: ["Đã giải quyết", "green"], TODO: ["Cần làm", "gray"], IN_PROGRESS: ["Đang làm", "blue"], DONE: ["Hoàn thành", "green"], DISMISSED: ["Đã bỏ qua", "gray"] };
    const m = map[s] || [s, "gray"];
    return badge(m[0], m[1]);
  }
  const SEVERITY = { LOW: ["Thấp", "gray"], MEDIUM: ["Trung bình", "blue"], HIGH: ["Cao", "amber"], CRITICAL: ["Nghiêm trọng", "red"] };
  function severityBadge(s) { const m = SEVERITY[s] || [s, "gray"]; return badge(m[0], m[1]); }
  const INC_TYPE = { MACHINE_STOP: "Máy dừng", QUALITY: "Chất lượng", MATERIAL_SHORTAGE: "Thiếu vật tư", DATA_DELAY: "Chậm dữ liệu", OTHER: "Khác" };
  function typeLabel(t) { return INC_TYPE[t] || t; }
  const IMPACT_TYPE = { DIRECT: ["Trực tiếp", "red"], INDIRECT: ["Gián tiếp", "amber"], RISK: ["Rủi ro tiềm năng", "gray"], OBSERVED: ["Đã quan sát", "green"], ESTIMATED: ["Ước tính", "blue"] };

  function simBadge(r) { return r && r.is_simulated ? h("span", { class: "badge badge-sim", text: "Mô phỏng" }) : null; }

  function renderTable(container, columns, rows, actionFor, onRowClick) {
    container.textContent = "";
    const table = h("table");
    const thead = h("thead");
    const trh = h("tr");
    columns.forEach((c) => trh.appendChild(h("th", { text: c.label })));
    if (actionFor) trh.appendChild(h("th", {}));
    thead.appendChild(trh); table.appendChild(thead);
    const tbody = h("tbody");
    rows.forEach((row) => {
      const tr = h("tr", { class: onRowClick ? "clickable" : "" });
      if (onRowClick) tr.addEventListener("click", () => onRowClick(row));
      columns.forEach((c) => {
        const td = h("td");
        const val = c.render ? c.render(row) : row[c.key];
        if (c.cell === "html") td.innerHTML = val == null ? "" : String(val);
        else if (val instanceof Node) td.appendChild(val);
        else td.textContent = val == null ? "" : String(val);
        if (c.sub) td.appendChild(h("div", { class: "cell-sub", text: c.sub(row) }));
        tr.appendChild(td);
      });
      if (actionFor) tr.appendChild(actionFor(row));
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    container.appendChild(table);
  }

  function pagination(el, page, totalPages, onPage) {
    el.textContent = "";
    el.appendChild(h("button", { class: "btn btn-sm btn-secondary", text: "Trước", disabled: page <= 1, onclick: () => onPage(page - 1) }));
    el.appendChild(h("span", { class: "info", text: "Trang " + page + "/" + Math.max(totalPages, 1) }));
    el.appendChild(h("button", { class: "btn btn-sm btn-secondary", text: "Sau", disabled: page >= totalPages, onclick: () => onPage(page + 1) }));
  }

  /* searchable select */
  function combo(opts, placeholder) {
    const wrap = h("div", { class: "combo" });
    const input = h("input", { class: "combo-input", placeholder: placeholder || "Tìm..." });
    const list = h("div", { class: "combo-list" });
    wrap.appendChild(input); wrap.appendChild(list);
    let selected = null;
    function render(filter) {
      list.textContent = "";
      const f = (filter || "").toLowerCase();
      opts.filter((o) => !f || o.label.toLowerCase().includes(f) || (o.code || "").toLowerCase().includes(f))
        .slice(0, 60).forEach((o) => {
          list.appendChild(h("div", { class: "combo-option" + (selected && selected.value === o.value ? " sel" : ""), onclick: () => {
            selected = o; input.value = o.label; list.textContent = ""; wrap.classList.remove("open");
          } }, [h("span", { class: "co-code", text: o.code || "" }), o.label]));
        });
    }
    input.addEventListener("focus", () => { wrap.classList.add("open"); render(input.value); });
    input.addEventListener("input", () => { selected = null; wrap.classList.add("open"); render(input.value); });
    document.addEventListener("click", (e) => { if (!wrap.contains(e.target)) wrap.classList.remove("open"); });
    return {
      el: wrap, input,
      getValue: () => selected ? selected.value : null,
      setValue: (v) => { selected = opts.find((o) => o.value === v) || null; input.value = selected ? selected.label : ""; },
      clear: () => { selected = null; input.value = ""; },
    };
  }

  /* form builder with group support */
  function formBuilder(fields, onSubmit, initial) {
    const form = h("form", { class: "grid grid-2" });
    const controls = {};
    let lastGroup = null, fs = null;
    fields.forEach((f) => {
      if (f.group && f.group !== lastGroup) {
        fs = h("fieldset", { class: "fieldset", style: "grid-column: span 2;" });
        fs.appendChild(h("legend", { text: f.group }));
        fs.appendChild(h("div", { class: "grid grid-2" }));
        form.appendChild(fs);
        lastGroup = f.group;
      }
      if (!f.name) return;
      let control;
      if (f.type === "select") control = selectInput(f.name, f.options || [], initial && initial[f.name]);
      else if (f.type === "checkbox") control = h("input", { name: f.name, type: "checkbox", checked: initial ? !!initial[f.name] : !!f.default });
      else if (f.type === "textarea") { control = h("textarea", { name: f.name, rows: 3 }); control.value = (initial && initial[f.name]) || ""; }
      else control = h("input", { name: f.name, value: (initial && initial[f.name]) || "", type: f.type === "number" ? "number" : (f.type === "date" ? "date" : (f.type === "datetime" ? "datetime-local" : "text")), inputmode: f.type === "number" ? "numeric" : undefined, min: f.type === "number" && f.min !== undefined ? f.min : undefined, placeholder: f.placeholder || "" });
      controls[f.name] = control;
      const fieldEl = field(f.label, control, f.required, f.hint);
      if (fs) fs.querySelector(".grid").appendChild(fieldEl);
      else form.appendChild(fieldEl);
    });
    const actions = h("div", { class: "toolbar", style: "grid-column: span 2; margin-top: 8px;" });
    const submit = h("button", { type: "submit", class: "btn btn-primary", text: "Lưu" });
    const cancel = h("button", { type: "button", class: "btn btn-secondary", text: "Hủy", onclick: closeModal });
    actions.appendChild(submit); actions.appendChild(cancel);
    form.appendChild(actions);
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const data = {};
      fields.forEach((f) => {
        if (!f.name) return;
        const c = controls[f.name];
        let v = c.type === "checkbox" ? c.checked : (c.value === "" ? null : c.value);
        if ((f.type === "number" || f.name === "assigned_department_id") && v !== null) v = Number(v);
        data[f.name] = v;
      });
      onSubmit(data, submit);
    });
    return { form, setSubmitting: (flag) => { submit.disabled = flag; submit.textContent = flag ? "Đang lưu..." : "Lưu"; } };
  }
  function field(label, control, required, hint) {
    const w = h("div", { class: "field" });
    w.appendChild(h("label", { text: label + (required ? " *" : "") }));
    w.appendChild(control);
    if (hint) w.appendChild(h("div", { class: "hint", text: hint }));
    return w;
  }
  function selectInput(name, options, value) {
    const s = h("select", { name });
    s.appendChild(h("option", { value: "", text: "-- Chọn --" }));
    options.forEach((o) => s.appendChild(h("option", { value: o.value, text: o.label, selected: String(o.value) === String(value) })));
    return s;
  }

  /* ============================================================ catalog */
  let CATALOG_KEYS = null;
  async function loadCatalogKeys() {
    if (CATALOG_KEYS) return CATALOG_KEYS;
    const d = await api("/api/catalog/keys");
    CATALOG_KEYS = d.data;
    return CATALOG_KEYS;
  }
  async function loadOptions(key) {
    const d = await api("/api/catalog/" + key + "?page_size=100");
    return d.data.items.map((r) => ({ value: r.id, label: r.name, code: r.code }));
  }
  const CATALOG_EXTRA = {
    department: [], shift: [],
    line: [{ name: "department_id", label: "Bộ phận", type: "select", optionsKey: "department" }],
    process: [{ name: "line_id", label: "Chuyền", type: "select", optionsKey: "line" }],
    machine: [{ name: "department_id", label: "Bộ phận", type: "select", optionsKey: "department" }],
    material: [{ name: "unit", label: "Đơn vị tính" }, { name: "department_id", label: "Bộ phận", type: "select", optionsKey: "department" }],
    product: [{ name: "department_id", label: "Bộ phận", type: "select", optionsKey: "department" }],
    order: [{ name: "product_id", label: "Sản phẩm", type: "select", optionsKey: "product" }, { name: "status", label: "Trạng thái" }],
    lot: [{ name: "production_order_id", label: "Lệnh sản xuất", type: "select", optionsKey: "order" }],
  };

  async function renderCatalog() {
    const v = $("#view");
    v.textContent = "";
    v.appendChild(h("div", { class: "section-head" }, [h("div", {}, [h("h2", { text: "Danh mục sản xuất" }), h("div", { class: "desc", text: "Bộ phận, chuyền, công đoạn, máy, vật tư, sản phẩm, lệnh và lot." })])]));
    const keys = await loadCatalogKeys();
    const tabs = h("div", { class: "tabs" });
    const card = h("div", { class: "card" });
    v.appendChild(h("div", { class: "card" }, [tabs, card]));
    const state = { key: "department", page: 1, tp: 1 };
    function selectKey(k) { state.key = k; state.page = 1; renderList(); }
    async function renderList() {
      card.textContent = "";
      const toolbar = h("div", { class: "toolbar" });
      const search = h("input", { placeholder: "Tìm theo mã hoặc tên..." });
      const listWrap = h("div");
      const pag = h("div", { class: "pagination" });
      toolbar.appendChild(h("div", { class: "search-box" }, [icon("search"), search]));
      toolbar.appendChild(h("div", { class: "spacer" }));
      toolbar.appendChild(h("button", { class: "btn btn-primary", text: "Thêm mới", onclick: () => openCatalogForm(null) }));
      card.appendChild(toolbar); card.appendChild(listWrap); card.appendChild(pag);
      let timer;
      search.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(() => { state.page = 1; load(); }, 350); });
      async function load() {
        listWrap.textContent = ""; listWrap.appendChild(spinner());
        try {
          const d = await api("/api/catalog/" + state.key + "?page=" + state.page + "&page_size=20&search=" + encodeURIComponent(search.value));
          listWrap.textContent = "";
          if (!d.data.items.length) { listWrap.appendChild(emptyBox("catalog", "Chưa có " + (keys.find(k => k.key === state.key) || {}).label, "Bấm 'Thêm mới' để khai báo.", h("button", { class: "btn btn-primary btn-sm", text: "Thêm mới", onclick: () => openCatalogForm(null) }))); return; }
          renderTable(listWrap, [
            { key: "code", label: "Mã" }, { key: "name", label: "Tên" },
            { key: "active", label: "Trạng thái", render: (r) => r.active ? badge("Hoạt động", "green") : badge("Đã ngừng", "gray") },
            { key: "is_simulated", label: "Loại", render: (r) => r.is_simulated ? badge("Mô phỏng", "amber") : badge("Thực", "green") },
          ], d.data.items, (row) => h("td", {}, [
            h("button", { class: "btn btn-sm btn-secondary", text: "Sửa", onclick: (e) => { e.stopPropagation(); openCatalogForm(row); } }),
            row.active ? h("button", { class: "btn btn-sm btn-ghost", text: "Ngừng", onclick: (e) => { e.stopPropagation(); deactivate(row); } }) : null,
          ]));
          state.tp = d.data.pagination.total_pages;
          pagination(pag, state.page, state.tp, (p) => { state.page = p; load(); });
        } catch (e) { listWrap.textContent = ""; listWrap.appendChild(errorBox(e.message, load)); }
      }
      async function deactivate(row) {
        if (!confirm("Ngừng sử dụng '" + row.code + "'?")) return;
        try { await api("/api/catalog/" + state.key + "/" + row.id + "/deactivate", { method: "POST" }); toast("Đã ngừng sử dụng."); load(); }
        catch (e) { toast(e.message, "error"); }
      }
      load();
    }
    async function openCatalogForm(row) {
      const extra = CATALOG_EXTRA[state.key] || [];
      const fields = [
        { name: "code", label: "Mã", required: true, placeholder: "VD: ASSY-01" },
        { name: "name", label: "Tên", required: true },
        { name: "description", label: "Mô tả", type: "textarea" },
      ];
      for (const f of extra) {
        if (f.optionsKey) fields.push({ name: f.name, label: f.label, type: "select", options: await loadOptions(f.optionsKey) });
        else fields.push({ name: f.name, label: f.label });
      }
      fields.push({ name: "active", label: "Đang hoạt động", type: "checkbox", default: true });
      fields.push({ name: "is_simulated", label: "Dữ liệu mô phỏng", type: "checkbox" });
      const fb = formBuilder(fields, async (data, s) => {
        fb.setSubmitting(true);
        try {
          if (row) await api("/api/catalog/" + state.key + "/" + row.id, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
          else await api("/api/catalog/" + state.key, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
          closeModal(); toast("Đã lưu."); renderList();
        } catch (e) { toast(e.message, "error"); fb.setSubmitting(false); }
      }, row || { active: true });
      openModal((row ? "Sửa " : "Thêm ") + (keys.find(k => k.key === state.key) || {}).label, fb.form);
    }
    keys.forEach((k) => tabs.appendChild(h("button", { class: k.key === state.key ? "active" : "", text: k.label, onclick: (e) => { $$("button", tabs).forEach(b => b.classList.remove("active")); e.target.classList.add("active"); selectKey(k.key); } })));
    renderList();
  }

  /* ============================================================ system */
  async function renderSystem() {
    const v = $("#view");
    v.textContent = "";
    v.appendChild(h("div", { class: "section-head" }, [h("div", {}, [h("h2", { text: "Nguồn dữ liệu & ánh xạ" }), h("div", { class: "desc", text: "Khai báo hệ thống nguồn, dataset, trường và luồng. Chỉ là metadata, chưa kết nối thật." })])]));
    const tabs = h("div", { class: "tabs" });
    const body = h("div");
    v.appendChild(h("div", { class: "card" }, [tabs, body]));
    const views = { sources: viewSources, datasets: viewDatasets, fields: viewFields, flows: viewFlows };
    const labels = { sources: "Hệ thống nguồn", datasets: "Dataset", fields: "Trường dữ liệu", flows: "Luồng dữ liệu" };
    let active = "sources";
    function setView(k) { active = k; $$("button", tabs).forEach(b => b.classList.toggle("active", b.dataset.v === k)); body.textContent = ""; views[k](body); }
    Object.keys(views).forEach((k) => tabs.appendChild(h("button", { "data-v": k, class: k === active ? "active" : "", text: labels[k], onclick: () => setView(k) })));
    setView(active);
  }
  async function viewSources(body) {
    const toolbar = h("div", { class: "toolbar" }); const listWrap = h("div"); const pag = h("div", { class: "pagination" });
    toolbar.appendChild(h("button", { class: "btn btn-primary", text: "Thêm nguồn", onclick: () => sourceForm(null) }));
    body.appendChild(toolbar); body.appendChild(listWrap); body.appendChild(pag);
    const st = { page: 1, tp: 1 };
    async function load() {
      listWrap.textContent = ""; listWrap.appendChild(spinner());
      try {
        const d = await api("/api/system/sources?page=" + st.page + "&page_size=20");
        listWrap.textContent = "";
        if (!d.data.items.length) { listWrap.appendChild(emptyBox("system", "Chưa khai báo nguồn dữ liệu", "Khai báo MES/ERP/PLC hoặc nguồn nhập liệu.", h("button", { class: "btn btn-primary btn-sm", text: "Thêm nguồn", onclick: () => sourceForm(null) }))); return; }
        renderTable(listWrap, [
          { key: "code", label: "Mã" }, { key: "name", label: "Tên" }, { key: "source_type", label: "Loại" },
          { key: "collection_method", label: "Thu thập" },
          { key: "confirmed", label: "Trạng thái", render: (r) => r.confirmed ? badge("Đã tích hợp", "green") : badge("Đã khai báo", "gray") },
          { key: "is_simulated", label: "Loại", render: (r) => r.is_simulated ? badge("Mô phỏng", "amber") : null },
        ], d.data.items, (row) => h("td", {}, [
          h("button", { class: "btn btn-sm btn-secondary", text: "Sửa", onclick: () => sourceForm(row) }),
          h("button", { class: "btn btn-sm btn-ghost", text: "Xóa", onclick: () => { if (confirm("Xóa nguồn?")) api("/api/system/sources/" + row.id, { method: "DELETE" }).then(() => { toast("Đã xóa."); load(); }).catch(e => toast(e.message, "error")); } }),
        ]));
        st.tp = d.data.pagination.total_pages; pagination(pag, st.page, st.tp, (p) => { st.page = p; load(); });
      } catch (e) { listWrap.textContent = ""; listWrap.appendChild(errorBox(e.message, load)); }
    }
    async function sourceForm(row) {
      const depts = await loadOptions("department");
      const fields = [
        { name: "code", label: "Mã", required: true }, { name: "name", label: "Tên", required: true },
        { name: "source_type", label: "Loại nguồn (MES/ERP/PLC/APP/Excel/API)", required: true },
        { name: "collection_method", label: "Phương thức thu thập" },
        { name: "owner_department_id", label: "Bộ phận sở hữu", type: "select", options: depts },
        { name: "location_metadata", label: "Vị trí lưu trữ (metadata)", type: "textarea" },
        { name: "confirmed", label: "Đã tích hợp thật", type: "checkbox", hint: "Bỏ tích nếu chỉ mới khai báo metadata." },
        { name: "is_simulated", label: "Mô phỏng", type: "checkbox" },
      ];
      const fb = formBuilder(fields, async (data, s) => {
        fb.setSubmitting(true);
        try { await api(row ? "/api/system/sources/" + row.id : "/api/system/sources", { method: row ? "PUT" : "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) }); closeModal(); toast("Đã lưu."); load(); }
        catch (e) { toast(e.message, "error"); fb.setSubmitting(false); }
      }, row);
      openModal(row ? "Sửa nguồn" : "Thêm nguồn", fb.form);
    }
    load();
  }
  async function viewDatasets(body) {
    const toolbar = h("div", { class: "toolbar" }); const listWrap = h("div"); const pag = h("div", { class: "pagination" });
    toolbar.appendChild(h("button", { class: "btn btn-primary", text: "Thêm dataset", onclick: () => datasetForm(null) }));
    body.appendChild(toolbar); body.appendChild(listWrap); body.appendChild(pag);
    const st = { page: 1, tp: 1 };
    async function load() {
      listWrap.textContent = ""; listWrap.appendChild(spinner());
      try {
        const d = await api("/api/system/datasets?page=" + st.page + "&page_size=20");
        listWrap.textContent = "";
        if (!d.data.items.length) { listWrap.appendChild(emptyBox("database", "Chưa có dataset", "Khai báo dataset để mô tả dữ liệu từ các hệ thống.", h("button", { class: "btn btn-primary btn-sm", text: "Thêm dataset", onclick: () => datasetForm(null) }))); return; }
        renderTable(listWrap, [
          { key: "code", label: "Mã" }, { key: "name", label: "Tên" },
          { key: "generation_unit", label: "Đơn vị phát sinh" }, { key: "update_schedule", label: "Lịch cập nhật" },
          { key: "confirmed", label: "Trạng thái", render: (r) => r.confirmed ? badge("Đã xác nhận", "green") : badge("Chưa xác nhận", "gray") },
        ], d.data.items, (row) => h("td", {}, [
          h("button", { class: "btn btn-sm btn-secondary", text: "Sửa", onclick: () => datasetForm(row) }),
          h("button", { class: "btn btn-sm btn-ghost", text: "Xóa", onclick: () => { if (confirm("Xóa?")) api("/api/system/datasets/" + row.id, { method: "DELETE" }).then(() => { toast("Đã xóa."); load(); }).catch(e => toast(e.message, "error")); } }),
        ]));
        st.tp = d.data.pagination.total_pages; pagination(pag, st.page, st.tp, (p) => { st.page = p; load(); });
      } catch (e) { listWrap.textContent = ""; listWrap.appendChild(errorBox(e.message, load)); }
    }
    async function datasetForm(row) {
      const srcs = (await api("/api/system/sources?page_size=100")).data.items.map(r => ({ value: r.id, label: r.code, code: r.code }));
      const depts = await loadOptions("department");
      const fields = [
        { name: "code", label: "Mã", required: true }, { name: "name", label: "Tên", required: true },
        { name: "source_id", label: "Hệ thống nguồn", type: "select", options: srcs },
        { name: "dataset_type", label: "Loại (table/file/endpoint)" },
        { name: "collection_method", label: "Phương thức thu thập" },
        { name: "generation_unit", label: "Đơn vị phát sinh", placeholder: "per_pcs / per_lot / per_event" },
        { name: "update_schedule", label: "Lịch cập nhật", placeholder: "realtime / per_shift / daily / batch / manual" },
        { name: "event_time_field", label: "Trường thời gian sự kiện" },
        { name: "timezone", label: "Múi giờ" },
        { name: "owner_department_id", label: "Bộ phận sở hữu", type: "select", options: depts },
        { name: "confirmed", label: "Đã xác nhận", type: "checkbox" },
        { name: "is_simulated", label: "Mô phỏng", type: "checkbox" },
      ];
      const fb = formBuilder(fields, async (data, s) => {
        fb.setSubmitting(true);
        try { await api(row ? "/api/system/datasets/" + row.id : "/api/system/datasets", { method: row ? "PUT" : "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) }); closeModal(); toast("Đã lưu."); load(); }
        catch (e) { toast(e.message, "error"); fb.setSubmitting(false); }
      }, row);
      openModal(row ? "Sửa dataset" : "Thêm dataset", fb.form);
    }
    load();
  }
  async function viewFields(body) {
    const toolbar = h("div", { class: "toolbar" }); const listWrap = h("div");
    const datasets = (await api("/api/system/datasets?page_size=100")).data.items;
    const sel = selectInput("ds", datasets.map(r => ({ value: r.id, label: r.code })), datasets[0] && datasets[0].id);
    toolbar.appendChild(field("Dataset", sel));
    toolbar.appendChild(h("button", { class: "btn btn-primary", text: "Thêm trường", onclick: () => fieldForm(sel.value) }));
    body.appendChild(toolbar); body.appendChild(listWrap);
    async function load() {
      listWrap.textContent = "";
      if (!sel.value) { listWrap.appendChild(emptyBox("database", "Chưa có dataset", "Hãy khai báo dataset trước.")); return; }
      const d = await api("/api/system/datasets/" + sel.value + "/fields");
      if (!d.data.length) { listWrap.appendChild(emptyBox("database", "Chưa có trường dữ liệu", "Khai báo trường (cột) của dataset, đặc biệt là khóa liên kết.")); return; }
      renderTable(listWrap, [
        { key: "code", label: "Mã trường" }, { key: "name", label: "Tên" }, { key: "data_type", label: "Kiểu" },
        { key: "is_key", label: "Khóa liên kết", render: (r) => r.is_key ? badge("Khóa", "blue") : null },
      ], d.data, (row) => h("td", {}, [h("button", { class: "btn btn-sm btn-ghost", text: "Xóa", onclick: () => { if (confirm("Xóa trường?")) api("/api/system/fields/" + row.id, { method: "DELETE" }).then(() => { toast("Đã xóa."); load(); }).catch(e => toast(e.message, "error")); } })]));
    }
    sel.addEventListener("change", load);
    async function fieldForm(datasetId) {
      const fields = [
        { name: "code", label: "Mã trường", required: true }, { name: "name", label: "Tên", required: true },
        { name: "data_type", label: "Kiểu dữ liệu" },
        { name: "is_key", label: "Là khóa liên kết", type: "checkbox" },
      ];
      const fb = formBuilder(fields, async (data, s) => {
        fb.setSubmitting(true);
        try { await api("/api/system/fields", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...data, dataset_id: Number(datasetId) }) }); closeModal(); toast("Đã lưu."); load(); }
        catch (e) { toast(e.message, "error"); fb.setSubmitting(false); }
      });
      openModal("Thêm trường", fb.form);
    }
    load();
  }
  async function viewFlows(body) {
    const toolbar = h("div", { class: "toolbar" }); const listWrap = h("div");
    toolbar.appendChild(h("button", { class: "btn btn-primary", text: "Thêm luồng", onclick: () => flowForm(null) }));
    body.appendChild(toolbar); body.appendChild(listWrap);
    async function load() {
      const d = await api("/api/system/flows?page_size=50");
      if (!d.data.items.length) { listWrap.appendChild(emptyBox("database", "Chưa có luồng dữ liệu", "Nối dataset nguồn với dataset đích.")); return; }
      renderTable(listWrap, [
        { key: "code", label: "Mã" }, { key: "name", label: "Tên" },
        { key: "source_dataset_id", label: "Dataset nguồn" }, { key: "target_dataset_id", label: "Dataset đích" },
      ], d.data.items, (row) => h("td", {}, [h("button", { class: "btn btn-sm btn-ghost", text: "Xóa", onclick: () => { if (confirm("Xóa?")) api("/api/system/flows/" + row.id, { method: "DELETE" }).then(() => { toast("Đã xóa."); load(); }).catch(e => toast(e.message, "error")); } })]));
    }
    async function flowForm(row) {
      const datasets = (await api("/api/system/datasets?page_size=100")).data.items;
      const opts = datasets.map(r => ({ value: r.id, label: r.code, code: r.code }));
      const fields = [
        { name: "code", label: "Mã", required: true }, { name: "name", label: "Tên", required: true },
        { name: "source_dataset_id", label: "Dataset nguồn", type: "select", options: opts, required: true },
        { name: "target_dataset_id", label: "Dataset đích", type: "select", options: opts, required: true },
        { name: "description", label: "Mô tả", type: "textarea" },
      ];
      const fb = formBuilder(fields, async (data, s) => {
        fb.setSubmitting(true);
        try { await api("/api/system/flows", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) }); closeModal(); toast("Đã lưu."); load(); }
        catch (e) { toast(e.message, "error"); fb.setSubmitting(false); }
      }, row);
      openModal("Thêm luồng dữ liệu", fb.form);
    }
    load();
  }

  /* ============================================================ operations */
  async function renderOperations() {
    const v = $("#view");
    v.textContent = "";
    v.appendChild(h("div", { class: "section-head" }, [h("div", {}, [h("h2", { text: "Ghi nhận dữ liệu" }), h("div", { class: "desc", text: "Nhập sản lượng, trạng thái máy, dừng máy, QC và vật tư." })])]));
    const tabs = h("div", { class: "tabs" });
    const body = h("div");
    v.appendChild(h("div", { class: "card" }, [tabs, body]));
    const views = { production: viewProduction, states: viewStates, downtimes: viewDowntimes, qc: viewQc, material: viewMaterial };
    const labels = { production: "Sản lượng", states: "Trạng thái máy", downtimes: "Dừng máy", qc: "QC", material: "Vật tư" };
    let active = "production";
    function setView(k) { active = k; $$("button", tabs).forEach(b => b.classList.toggle("active", b.dataset.v === k)); body.textContent = ""; views[k](body); }
    Object.keys(views).forEach((k) => tabs.appendChild(h("button", { "data-v": k, class: k === active ? "active" : "", text: labels[k], onclick: () => setView(k) })));
    setView(active);
  }

  function productionForm(onSaved) {
    const form = h("form", { class: "grid grid-2" });
    const ctrl = {};
    function f(label, name, type, required) {
      let c;
      if (name === "shift") c = selectInput(name, ["CA_1", "CA_2", "CA_3"].map(x => ({ value: x, label: x })));
      else if (type === "textarea") c = h("textarea", { name, rows: 2 });
      else c = h("input", { name, type, inputmode: type === "number" ? "numeric" : undefined, min: type === "number" ? 0 : undefined });
      ctrl[name] = c; form.appendChild(field(label, c, required));
    }
    f("Ngày sản xuất", "production_date", "date", true);
    f("Ca sản xuất", "shift", "select", true);
    f("Mã chuyền", "line_code", "text", true);
    f("Mã công đoạn", "process_code", "text", true);
    f("Mã sản phẩm", "product_code", "text", true);
    f("Mã lot", "lot_code", "text", true);
    f("Số lượng đạt (pcs)", "good_quantity", "number", true);
    f("Số lượng lỗi (pcs)", "defect_quantity", "number", true);
    f("Người nhập", "operator_name", "text", true);
    f("Ghi chú", "note", "textarea", false);

    const summary = h("div", { class: "message info", style: "grid-column: span 2;" });
    function upd() {
      const g = Number(ctrl.good_quantity.value) || 0, d = Number(ctrl.defect_quantity.value) || 0;
      const total = g + d, rate = total ? (d / total * 100) : 0;
      summary.textContent = "Tổng sản lượng: " + total + " pcs  •  Tỷ lệ lỗi: " + (total ? rate.toFixed(2) : "0") + "%";
      summary.className = "message visible info";
    }
    ctrl.good_quantity.addEventListener("input", upd); ctrl.defect_quantity.addEventListener("input", upd);
    const actions = h("div", { class: "toolbar", style: "grid-column: span 2;" });
    const submit = h("button", { type: "submit", class: "btn btn-primary", text: "Gửi dữ liệu" });
    const reset = h("button", { type: "button", class: "btn btn-secondary", text: "Nhập mới", onclick: () => { form.reset(); draftId = uuid(); upd(); } });
    actions.appendChild(submit); actions.appendChild(reset);
    form.appendChild(summary); form.appendChild(actions);
    let draftId = uuid();
    form.addEventListener("input", () => { draftId = uuid(); });
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const good = Number(ctrl.good_quantity.value) || 0, defect = Number(ctrl.defect_quantity.value) || 0;
      if (!ctrl.production_date.value || !ctrl.shift.value) { toast("Vui lòng nhập đầy đủ các trường bắt buộc.", "error"); return; }
      if (good + defect <= 0) { toast("Tổng sản lượng phải lớn hơn 0.", "error"); return; }
      const payload = { request_id: draftId, production_date: ctrl.production_date.value, shift: ctrl.shift.value, line_code: ctrl.line_code.value.trim(), process_code: ctrl.process_code.value.trim(), product_code: ctrl.product_code.value.trim(), lot_code: ctrl.lot_code.value.trim(), good_quantity: good, defect_quantity: defect, operator_name: ctrl.operator_name.value.trim(), note: ctrl.note.value.trim() || null };
      submit.disabled = true; submit.textContent = "Đang gửi...";
      try {
        const r = await api("/api/production-records", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
        toast("Đã lưu bản ghi #" + r.data.id); form.reset(); draftId = uuid(); upd();
        if (onSaved) onSaved();
      } catch (err) { toast(err.message, "error"); }
      submit.disabled = false; submit.textContent = "Gửi dữ liệu";
    });
    return form;
  }

  function viewProduction(body) {
    body.appendChild(productionForm());
    const head = h("div", { class: "card-title", style: "margin-top:16px;" }, [h("span", { text: "Bản ghi gần nhất" })]);
    const listWrap = h("div");
    body.appendChild(h("div", { class: "card" }, [head, listWrap]));
    api("/api/production-records?page_size=10").then(d => renderTable(listWrap, [
      { key: "id", label: "ID" }, { key: "production_date", label: "Ngày" }, { key: "shift", label: "Ca" },
      { key: "line_code", label: "Chuyền" }, { key: "process_code", label: "Công đoạn" }, { key: "lot_code", label: "Lot" },
      { key: "good_quantity", label: "Đạt" }, { key: "defect_quantity", label: "Lỗi" },
    ], d.data.items)).catch(() => {});
  }

  async function viewStates(body) {
    const toolbar = h("div", { class: "toolbar" }); const listWrap = h("div");
    toolbar.appendChild(h("button", { class: "btn btn-primary", text: "Ghi nhận trạng thái", onclick: () => stateForm(null) }));
    body.appendChild(toolbar); body.appendChild(listWrap);
    async function load() {
      listWrap.textContent = ""; listWrap.appendChild(spinner());
      try {
        const d = await api("/api/operations/machine-states?page_size=20");
        listWrap.textContent = "";
        if (!d.data.items.length) { listWrap.appendChild(emptyBox("operations", "Chưa có dữ liệu trạng thái máy", "Ghi nhận trạng thái RUNNING/STOPPED/... để theo dõi máy dừng.")); return; }
        renderTable(listWrap, [
          { key: "machine_id", label: "Máy" }, { key: "event_time", label: "Thời điểm sự kiện", render: (r) => fmt(r.event_time) },
          { key: "state", label: "Trạng thái", render: (r) => { const m = { RUNNING: ["Đang chạy", "green"], STOPPED: ["Đã dừng", "red"], MAINTENANCE: ["Bảo trì", "amber"], UNKNOWN: ["Không rõ", "gray"] }[r.state]; return badge(m[0], m[1]); } },
          { key: "error_code", label: "Mã lỗi" }, { key: "is_simulated", label: "Loại", render: (r) => r.is_simulated ? badge("Mô phỏng", "amber") : null },
        ], d.data.items);
      } catch (e) { listWrap.textContent = ""; listWrap.appendChild(errorBox(e.message, load)); }
    }
    async function stateForm(row) {
      const machines = await loadOptions("machine");
      const fields = [
        { name: "machine_id", label: "Máy", type: "select", options: machines, required: true },
        { name: "event_time", label: "Thời điểm sự kiện", type: "datetime", required: true },
        { name: "state", label: "Trạng thái", type: "select", options: ["RUNNING", "STOPPED", "MAINTENANCE", "UNKNOWN"].map(x => ({ value: x, label: x })), required: true },
        { name: "error_code", label: "Mã lỗi (nếu có)" }, { name: "note", label: "Ghi chú" },
      ];
      const fb = formBuilder(fields, async (data, s) => {
        fb.setSubmitting(true);
        try { await api("/api/operations/machine-states", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...data, event_time: iso(data.event_time) }) }); closeModal(); toast("Đã ghi nhận."); load(); }
        catch (e) { toast(e.message, "error"); fb.setSubmitting(false); }
      });
      openModal("Ghi nhận trạng thái máy", fb.form);
    }
    load();
  }

  async function viewDowntimes(body) {
    const toolbar = h("div", { class: "toolbar" }); const listWrap = h("div");
    toolbar.appendChild(h("button", { class: "btn btn-primary", text: "Ghi nhận dừng máy", onclick: () => downtimeForm() }));
    body.appendChild(toolbar); body.appendChild(listWrap);
    async function load() {
      listWrap.textContent = ""; listWrap.appendChild(spinner());
      try {
        const d = await api("/api/operations/downtimes?page_size=20");
        listWrap.textContent = "";
        if (!d.data.items.length) { listWrap.appendChild(emptyBox("operations", "Chưa có dữ liệu dừng máy", "Ghi nhận khoảng dừng kèm lý do/mã lỗi.")); return; }
        renderTable(listWrap, [
          { key: "machine_id", label: "Máy" }, { key: "start_time", label: "Bắt đầu", render: (r) => fmt(r.start_time) },
          { key: "end_time", label: "Kết thúc", render: (r) => r.end_time ? fmt(r.end_time) : badge("Đang dừng", "red") },
          { key: "reason", label: "Lý do" }, { key: "error_code", label: "Mã lỗi" },
        ], d.data.items);
      } catch (e) { listWrap.textContent = ""; listWrap.appendChild(errorBox(e.message, load)); }
    }
    async function downtimeForm() {
      const machines = await loadOptions("machine");
      const fields = [
        { name: "machine_id", label: "Máy", type: "select", options: machines, required: true },
        { name: "start_time", label: "Bắt đầu", type: "datetime", required: true },
        { name: "end_time", label: "Kết thúc (bỏ trống nếu đang dừng)", type: "datetime" },
        { name: "reason", label: "Lý do" }, { name: "error_code", label: "Mã lỗi" }, { name: "operator_name", label: "Người ghi nhận" },
      ];
      const fb = formBuilder(fields, async (data, s) => {
        fb.setSubmitting(true);
        try { await api("/api/operations/downtimes", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...data, start_time: iso(data.start_time), end_time: data.end_time ? iso(data.end_time) : null }) }); closeModal(); toast("Đã ghi nhận."); load(); }
        catch (e) { toast(e.message, "error"); fb.setSubmitting(false); }
      });
      openModal("Ghi nhận dừng máy", fb.form);
    }
    load();
  }

  async function viewQc(body) {
    const toolbar = h("div", { class: "toolbar" }); const listWrap = h("div");
    toolbar.appendChild(h("button", { class: "btn btn-primary", text: "Ghi nhận QC", onclick: () => qcForm() }));
    body.appendChild(toolbar); body.appendChild(listWrap);
    async function load() {
      listWrap.textContent = ""; listWrap.appendChild(spinner());
      try {
        const d = await api("/api/operations/qc?page_size=20");
        listWrap.textContent = "";
        if (!d.data.items.length) { listWrap.appendChild(emptyBox("operations", "Chưa có kết quả QC", "Ghi nhận kết quả kiểm tra chất lượng theo lot.")); return; }
        renderTable(listWrap, [
          { key: "lot_id", label: "Lot" }, { key: "check_time", label: "Thời điểm", render: (r) => fmt(r.check_time) },
          { key: "inspected_qty", label: "Kiểm tra" }, { key: "defect_qty", label: "Lỗi" },
          { key: "defect_type", label: "Loại lỗi" },
          { key: "result", label: "Kết quả", render: (r) => { const m = { PASS: ["Đạt", "green"], FAIL: ["Không đạt", "red"], HOLD: ["Tạm giữ", "amber"] }[r.result]; return badge(m[0], m[1]); } },
        ], d.data.items);
      } catch (e) { listWrap.textContent = ""; listWrap.appendChild(errorBox(e.message, load)); }
    }
    async function qcForm() {
      const lots = await loadOptions("lot"), products = await loadOptions("product"), procs = await loadOptions("process");
      const fields = [
        { name: "lot_id", label: "Lot", type: "select", options: lots, required: true },
        { name: "product_id", label: "Sản phẩm", type: "select", options: products },
        { name: "process_id", label: "Công đoạn", type: "select", options: procs },
        { name: "check_time", label: "Thời điểm kiểm tra", type: "datetime", required: true },
        { name: "inspected_qty", label: "Số lượng kiểm tra", type: "number", min: 0, required: true },
        { name: "defect_qty", label: "Số lượng lỗi", type: "number", min: 0, required: true },
        { name: "defect_type", label: "Loại lỗi" },
        { name: "result", label: "Kết quả", type: "select", options: ["PASS", "FAIL", "HOLD"].map(x => ({ value: x, label: x })), required: true },
        { name: "note", label: "Ghi chú" },
      ];
      const fb = formBuilder(fields, async (data, s) => {
        fb.setSubmitting(true);
        try { await api("/api/operations/qc", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...data, check_time: iso(data.check_time) }) }); closeModal(); toast("Đã ghi nhận."); load(); }
        catch (e) { toast(e.message, "error"); fb.setSubmitting(false); }
      });
      openModal("Ghi nhận kết quả QC", fb.form);
    }
    load();
  }

  async function viewMaterial(body) {
    const toolbar = h("div", { class: "toolbar" }); const listWrap = h("div");
    toolbar.appendChild(h("button", { class: "btn btn-primary", text: "Ghi nhận vật tư", onclick: () => matForm() }));
    body.appendChild(toolbar); body.appendChild(listWrap);
    async function load() {
      listWrap.textContent = ""; listWrap.appendChild(spinner());
      try {
        const d = await api("/api/operations/material?page_size=20");
        listWrap.textContent = "";
        if (!d.data.items.length) { listWrap.appendChild(emptyBox("operations", "Chưa có dữ liệu vật tư", "Ghi nhận số lượng vật tư khả dụng.")); return; }
        renderTable(listWrap, [
          { key: "material_id", label: "Vật tư" }, { key: "recorded_at", label: "Thời điểm", render: (r) => fmt(r.recorded_at) },
          { key: "available_qty", label: "Khả dụng" }, { key: "unit", label: "Đơn vị" }, { key: "scope", label: "Phạm vi" },
        ], d.data.items);
      } catch (e) { listWrap.textContent = ""; listWrap.appendChild(errorBox(e.message, load)); }
    }
    async function matForm() {
      const materials = await loadOptions("material");
      const fields = [
        { name: "material_id", label: "Vật tư", type: "select", options: materials, required: true },
        { name: "recorded_at", label: "Thời điểm ghi nhận", type: "datetime", required: true },
        { name: "available_qty", label: "Số lượng khả dụng", type: "number", min: 0, required: true },
        { name: "unit", label: "Đơn vị tính" }, { name: "scope", label: "Phạm vi kho/chuyền" },
      ];
      const fb = formBuilder(fields, async (data, s) => {
        fb.setSubmitting(true);
        try { await api("/api/operations/material", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...data, recorded_at: iso(data.recorded_at) }) }); closeModal(); toast("Đã ghi nhận."); load(); }
        catch (e) { toast(e.message, "error"); fb.setSubmitting(false); }
      });
      openModal("Ghi nhận tình trạng vật tư", fb.form);
    }
    load();
  }

  /* ============================================================ incidents */
  async function renderIncidents(params) {
    const v = $("#view");
    v.textContent = "";
    if (params.parts[1]) { renderIncidentDetail(params.parts[1]); return; }
    v.appendChild(h("div", { class: "section-head" }, [h("div", {}, [h("h2", { text: "Sự cố" }), h("div", { class: "desc", text: "Tạo và xử lý sự cố theo một luồng liền mạch." })])]));
    const card = h("div", { class: "card" });
    v.appendChild(card);
    const toolbar = h("div", { class: "toolbar" });
    const search = h("input", { placeholder: "Tìm theo mã hoặc tiêu đề..." });
    const statusSel = selectInput("status", ["OPEN", "INVESTIGATING", "MITIGATING", "RESOLVED"].map(x => ({ value: x, label: { OPEN: "Đang mở", INVESTIGATING: "Đang điều tra", MITIGATING: "Đang xử lý", RESOLVED: "Đã giải quyết" }[x] })));
    const typeSel = selectInput("type", ["MACHINE_STOP", "QUALITY", "MATERIAL_SHORTAGE", "DATA_DELAY", "OTHER"].map(x => ({ value: x, label: typeLabel(x) })));
    const listWrap = h("div"); const pag = h("div", { class: "pagination" });
    toolbar.appendChild(h("div", { class: "search-box", style: "min-width:200px;" }, [icon("search"), search]));
    toolbar.appendChild(field("Trạng thái", statusSel));
    toolbar.appendChild(field("Loại", typeSel));
    toolbar.appendChild(h("div", { class: "spacer" }));
    toolbar.appendChild(h("button", { class: "btn btn-primary", text: "Tạo sự cố", onclick: () => incidentForm(null) }));
    card.appendChild(toolbar); card.appendChild(listWrap); card.appendChild(pag);
    const st = { page: 1, tp: 1 };
    let timer;
    search.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(() => { st.page = 1; load(); }, 350); });
    statusSel.addEventListener("change", () => { st.page = 1; load(); });
    typeSel.addEventListener("change", () => { st.page = 1; load(); });
    async function load() {
      listWrap.textContent = ""; listWrap.appendChild(spinner());
      try {
        const q = new URLSearchParams({ page: st.page, page_size: 15 });
        if (statusSel.value) q.set("status", statusSel.value);
        if (typeSel.value) q.set("incident_type", typeSel.value);
        if (search.value) q.set("search", search.value);
        const d = await api("/api/incidents?" + q);
        listWrap.textContent = "";
        if (!d.data.items.length) { listWrap.appendChild(emptyBox("incidents", "Không có sự cố", "Tạo sự cố đầu tiên hoặc nạp kịch bản mô phỏng.", h("button", { class: "btn btn-primary btn-sm", text: "Tạo sự cố", onclick: () => incidentForm(null) }))); return; }
        renderTable(listWrap, [
          { key: "code", label: "Mã" }, { key: "title", label: "Tiêu đề" },
          { key: "incident_type", label: "Loại", render: (r) => typeLabel(r.incident_type) },
          { key: "severity", label: "Mức độ", render: (r) => severityBadge(r.severity) },
          { key: "status", label: "Trạng thái", render: (r) => statusBadge(r.status) },
          { key: "is_simulated", label: "", render: (r) => simBadge(r) },
        ], d.data.items, (row) => h("td", {}, [
          h("button", { class: "btn btn-sm btn-secondary", text: "Mở", onclick: (e) => { e.stopPropagation(); navigate("incidents/" + row.id); } }),
        ]), (row) => navigate("incidents/" + row.id));
        st.tp = d.data.pagination.total_pages; pagination(pag, st.page, st.tp, (p) => { st.page = p; load(); });
      } catch (e) { listWrap.textContent = ""; listWrap.appendChild(errorBox(e.message, load)); }
    }
    async function incidentForm(row) {
      const depts = await loadOptions("department");
      const fields = [
        { group: "Thông tin chung" },
        { name: "code", label: "Mã sự cố", required: true }, { name: "title", label: "Tiêu đề", required: true },
        { name: "incident_type", label: "Loại sự cố", type: "select", options: ["MACHINE_STOP", "QUALITY", "MATERIAL_SHORTAGE", "DATA_DELAY", "OTHER"].map(x => ({ value: x, label: typeLabel(x) })), required: true },
        { name: "severity", label: "Mức nghiêm trọng", type: "select", options: ["LOW", "MEDIUM", "HIGH", "CRITICAL"].map(x => ({ value: x, label: (SEVERITY[x] || [x])[0] })) },
        { group: "Đối tượng & thời gian" },
        { name: "source_object_type", label: "Loại đối tượng", type: "select", options: ["machine", "lot", "material", "process", "product", "dataset", "line", "order"].map(x => ({ value: x, label: x })) },
        { name: "source_object_id", label: "ID đối tượng", type: "number", hint: "Nhập ID của máy/lot/vật tư (xem ở Bản đồ liên kết)." },
        { name: "start_time", label: "Bắt đầu", type: "datetime" }, { name: "end_time", label: "Kết thúc", type: "datetime" },
        { group: "Xử lý" },
        { name: "assigned_department_id", label: "Bộ phận phụ trách", type: "select", options: depts },
        { name: "description", label: "Mô tả quan sát (triệu chứng)", type: "textarea" },
      ];
      const fb = formBuilder(fields, async (data, s) => {
        fb.setSubmitting(true);
        try {
          const payload = { ...data, request_id: uuid(), start_time: data.start_time ? iso(data.start_time) : null, end_time: data.end_time ? iso(data.end_time) : null };
          await api("/api/incidents", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
          closeModal(); toast("Đã tạo sự cố."); load();
        } catch (e) { toast(e.message, "error"); fb.setSubmitting(false); }
      });
      openModal("Tạo sự cố", fb.form);
    }
    load();
  }

  async function renderIncidentDetail(id) {
    const v = $("#view");
    v.textContent = "";
    v.appendChild(spinner());
    let inc, causes, links, runs;
    try {
      inc = (await api("/api/incidents/" + id)).data;
      causes = (await api("/api/incidents/" + id + "/causes")).data;
      links = (await api("/api/incidents/" + id + "/links")).data;
      runs = (await api("/api/analysis/runs?page_size=50")).data.items.filter(r => r.source_type === "INCIDENT" && r.source_id === Number(id));
    } catch (e) { v.textContent = ""; v.appendChild(errorBox(e.message, () => renderIncidentDetail(id))); return; }
    v.textContent = "";

    const back = h("button", { class: "btn btn-ghost btn-sm", text: "← Danh sách sự cố", onclick: () => navigate("incidents") });
    v.appendChild(back);

    const steps = ["Tạo", "Bằng chứng", "Phân tích", "Công việc", "Giải quyết"];
    const stepper = h("div", { class: "tabs", style: "margin-top:12px;" });
    steps.forEach((s, i) => stepper.appendChild(h("button", { text: (i + 1) + ". " + s, disabled: true })));
    v.appendChild(stepper);

    const grid = h("div", { class: "detail-grid" });
    const left = h("div");
    const right = h("div");
    grid.appendChild(left); grid.appendChild(right);
    v.appendChild(grid);

    // left: summary + evidence + causes + impacts
    left.appendChild(h("div", { class: "card" }, [
      h("div", { class: "card-title" }, [h("span", { text: inc.code + " — " + inc.title }), simBadge(inc)]),
      h("div", { class: "kv-list" }, [
        kv("Loại", typeLabel(inc.incident_type)), kv("Mức độ", null, severityBadge(inc.severity)),
        kv("Trạng thái", null, statusBadge(inc.status)),
        kv("Bắt đầu", inc.start_time ? fmt(inc.start_time) : "—"),
        kv("Đối tượng", inc.source_object_type ? (inc.source_object_type + " #" + inc.source_object_id) : "—"),
        kv("Bộ phận", inc.assigned_department_id ? ("#" + inc.assigned_department_id) : "—"),
      ]),
      inc.description ? h("div", { class: "explain", style: "margin-top:12px;" }, [h("h4", { text: "Quan sát (triệu chứng)" }), h("div", { text: inc.description })]) : null,
    ]));

    // causes
    const causeCard = h("div", { class: "card" });
    causeCard.appendChild(h("div", { class: "card-title" }, [h("span", { text: "Nguyên nhân" })]));
    const causeWrap = h("div");
    function renderCauses() {
      causeWrap.textContent = "";
      if (!causes.length) causeWrap.appendChild(emptyBox("survey", "Chưa có nguyên nhân", "Giả thuyết sẽ xuất hiện sau khi chạy phân tích; nguyên nhân xác nhận do bạn ghi."));
      causes.forEach((c) => causeWrap.appendChild(h("div", { class: "explain" }, [
        h("div", {}, [c.kind === "CONFIRMED" ? badge("Đã xác nhận", "green") : badge("Giả thuyết", "amber"), c.rule_id ? h("span", { style: "font-size:12px;color:var(--c-text-faint);margin-left:8px;", text: "rule " + c.rule_id }) : null]),
        h("div", { text: c.content, style: "margin-top:6px;" }),
        c.evidence ? h("div", { class: "cell-sub", text: "Bằng chứng: " + c.evidence }) : null,
        (c.kind === "CONFIRMED" && c.confirmed_by) ? h("div", { class: "cell-sub", text: "Xác nhận bởi: " + c.confirmed_by }) : null,
      ])));
    }
    renderCauses(); causeCard.appendChild(causeWrap);
    left.appendChild(causeCard);

    // links (evidence)
    const linkCard = h("div", { class: "card" });
    linkCard.appendChild(h("div", { class: "card-title" }, [h("span", { text: "Bằng chứng (bản ghi vận hành)" })]));
    const linkWrap = h("div");
    if (!links.length) linkWrap.appendChild(h("p", { class: "cell-sub", text: "Chưa liên kết bản ghi vận hành nào." }));
    else links.forEach((l) => linkWrap.appendChild(h("div", { class: "explain" }, [h("div", { text: l.source_type + " #" + l.source_id })])));
    linkCard.appendChild(linkWrap);
    left.appendChild(linkCard);

    // right: actions + run analysis + history
    const actCard = h("div", { class: "card" });
    actCard.appendChild(h("div", { class: "card-title" }, [h("span", { text: "Thao tác" })]));
    const statusRow = h("div", { class: "toolbar" });
    const newStatus = selectInput("newstatus", ["OPEN", "INVESTIGATING", "MITIGATING", "RESOLVED"].map(x => ({ value: x, label: { OPEN: "Mở", INVESTIGATING: "Điều tra", MITIGATING: "Xử lý", RESOLVED: "Giải quyết" }[x] })), inc.status);
    statusRow.appendChild(field("Chuyển trạng thái", newStatus));
    statusRow.appendChild(h("button", { class: "btn btn-secondary", text: "Cập nhật", onclick: async () => {
      try { await api("/api/incidents/" + id, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status: newStatus.value }) }); toast("Đã cập nhật trạng thái."); renderIncidentDetail(id); }
      catch (e) { toast(e.message, "error"); }
    } }));
    actCard.appendChild(statusRow);
    actCard.appendChild(h("button", { class: "btn btn-primary", style: "width:100%;", text: "Chạy phân tích tác động", onclick: () => navigate("analysis?incident=" + id) }));
    if (runs.length) {
      actCard.appendChild(h("h4", { text: "Đã phân tích " + runs.length + " lần", style: "margin:12px 0 6px;" }));
      runs.slice(0, 5).forEach((r) => actCard.appendChild(h("button", { class: "btn btn-ghost btn-sm", style: "width:100%;text-align:left;", text: "Xem phân tích #" + r.id + " — " + fmt(r.run_at), onclick: () => navigate("analysis?run=" + r.id) })));
    }
    right.appendChild(actCard);
  }
  function kv(k, v, node) {
    return h("div", { class: "kv-row" }, [h("span", { class: "k", text: k }), node ? node : h("span", { text: v })]);
  }

  /* ============================================================ map */
  async function renderMap() {
    const v = $("#view");
    v.textContent = "";
    v.appendChild(h("div", { class: "section-head" }, [h("div", {}, [h("h2", { text: "Bản đồ liên kết" }), h("div", { class: "desc", text: "Xem quan hệ giữa máy, công đoạn, vật tư, sản phẩm và dữ liệu." })])]));
    const card = h("div", { class: "card" });
    v.appendChild(card);
    const meta = await api("/api/graph/meta");
    const toolbar = h("div", { class: "graph-toolbar" });
    const modeSel = selectInput("mode", [{ value: "business", label: "Nghiệp vụ sản xuất" }, { value: "system", label: "Logic hệ thống" }, { value: "combined", label: "Kết hợp hai lớp" }]);
    const search = h("input", { placeholder: "Tìm node theo mã/tên..." });
    const depthSel = selectInput("depth", [1, 2, 3].map(x => ({ value: x, label: x + " bước" })), 2);
    toolbar.appendChild(field("Chế độ", modeSel));
    toolbar.appendChild(field("Độ sâu", depthSel));
    toolbar.appendChild(h("div", { class: "search-box", style: "min-width:200px;" }, [icon("search"), search]));
    toolbar.appendChild(h("div", { class: "spacer" }));
    toolbar.appendChild(h("button", { class: "btn btn-secondary btn-sm", text: "Fit view", onclick: () => draw() }));
    toolbar.appendChild(h("button", { class: "btn btn-secondary btn-sm", text: "Toàn bộ", onclick: () => draw() }));
    toolbar.appendChild(h("button", { class: "btn btn-secondary btn-sm", text: "Thêm quan hệ", onclick: () => edgeForm() }));
    card.appendChild(toolbar);

    const legend = h("div", { class: "legend" });
    const kinds = { production_dependency: ["Phụ thuộc sản xuất", "prod", "solid"], data_flow: ["Luồng dữ liệu", "data", "solid"], data_mapping: ["Ánh xạ dữ liệu–nghiệp vụ", "map", "dashed"], department_responsibility: ["Trách nhiệm bộ phận", "dept", "dotted"] };
    Object.keys(kinds).forEach((k) => legend.appendChild(h("span", { class: "lg" }, [h("span", { class: "swatch " + kinds[k][1] }), kinds[k][0]])));
    card.appendChild(legend);

    const wrap = h("div", { class: "graph-wrap" });
    card.appendChild(wrap);
    const detail = h("div", { class: "card" });
    v.appendChild(detail);

    let graphData = null;
    async function loadGraph() {
      wrap.textContent = ""; wrap.appendChild(spinner());
      try {
        const d = await api("/api/graph/map");
        graphData = d.data;
        draw();
      } catch (e) { wrap.textContent = ""; wrap.appendChild(errorBox(e.message, loadGraph)); }
    }
    function draw() {
      if (!graphData) return;
      wrap.textContent = "";
      let nodes = graphData.nodes, edges = graphData.edges;
      const mode = modeSel.value;
      const businessTypes = ["department", "line", "process", "machine", "material", "product", "order", "lot", "shift"];
      const systemTypes = ["source", "dataset", "field"];
      if (mode === "business") { nodes = nodes.filter(n => businessTypes.includes(n.type)); edges = edges.filter(e => businessTypes.includes(e.source_type) && businessTypes.includes(e.target_type)); }
      else if (mode === "system") { nodes = nodes.filter(n => systemTypes.includes(n.type)); edges = edges.filter(e => systemTypes.includes(e.source_type) && systemTypes.includes(e.target_type)); }
      if (search.value) {
        const q = search.value.toLowerCase();
        const matched = nodes.filter(n => n.name.toLowerCase().includes(q) || (n.code || "").toLowerCase().includes(q));
        const ids = new Set(matched.map(n => n.type + ":" + n.id));
        edges = edges.filter(e => ids.has(e.source_type + ":" + e.source_id) || ids.has(e.target_type + ":" + e.target_id));
        const edgeIds = new Set();
        edges.forEach(e => { edgeIds.add(e.source_type + ":" + e.source_id); edgeIds.add(e.target_type + ":" + e.target_id); });
        nodes = nodes.filter(n => edgeIds.has(n.type + ":" + n.id));
      }
      if (!nodes.length) { wrap.appendChild(emptyBox("map", "Không có dữ liệu để vẽ", "Thêm danh mục, thiết lập quan hệ hoặc nạp dữ liệu mô phỏng.")); return; }
      drawGraph(wrap, nodes, edges, (n) => onNodeClick(n, edges));
    }
    function onNodeClick(node, edges) {
      detail.textContent = "";
      const rels = edges.filter(e => (e.source_type === node.type && e.source_id === node.id) || (e.target_type === node.type && e.target_id === node.id));
      detail.appendChild(h("div", { class: "card-title" }, [h("span", { text: node.name + " (" + node.type + ")" }), node.is_simulated ? badge("Mô phỏng", "amber") : null]));
      if (!rels.length) { detail.appendChild(h("p", { class: "cell-sub", text: "Không có quan hệ nào." })); return; }
      const ul = h("ul", { class: "path-list" });
      rels.forEach(e => {
        const dir = e.source_type === node.type ? "→" : "←";
        const other = e.source_type === node.type ? (e.target_type + " #" + e.target_id) : (e.source_type + " #" + e.source_id);
        ul.appendChild(h("li", {}, [h("div", { text: dir + " " + other }), h("div", { class: "hop", text: kinds[e.kind][0] + (e.label ? " — " + e.label : "") })]));
      });
      detail.appendChild(ul);
    }
    async function edgeForm() {
      const nodeOpts = graphData ? graphData.nodes.map(n => ({ value: n.type + ":" + n.id, label: n.name + " (" + n.type + ")", code: n.type })) : [];
      if (!nodeOpts.length) { toast("Chưa có node để liên kết.", "error"); return; }
      const fields = [
        { name: "source", label: "Node nguồn", type: "select", options: nodeOpts, required: true },
        { name: "target", label: "Node đích", type: "select", options: nodeOpts, required: true },
        { name: "kind", label: "Loại quan hệ", type: "select", options: Object.keys(kinds).map(k => ({ value: k, label: kinds[k][0] })), required: true },
        { name: "label", label: "Mô tả quan hệ" },
      ];
      const fb = formBuilder(fields, async (data, s) => {
        fb.setSubmitting(true);
        try {
          const [st, si] = data.source.split(":"); const [tt, ti] = data.target.split(":");
          await api("/api/graph/edges", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ source_type: st, source_id: Number(si), target_type: tt, target_id: Number(ti), kind: data.kind, label: data.label || null }) });
          closeModal(); toast("Đã thêm quan hệ."); loadGraph();
        } catch (e) { toast(e.message, "error"); fb.setSubmitting(false); }
      });
      openModal("Thêm quan hệ", fb.form);
    }
    modeSel.addEventListener("change", draw);
    depthSel.addEventListener("change", draw);
    let t; search.addEventListener("input", () => { clearTimeout(t); t = setTimeout(draw, 300); });
    loadGraph();
  }

  function drawGraph(wrap, nodes, edges, onNodeClick) {
    const byType = {};
    nodes.forEach(n => { (byType[n.type] = byType[n.type] || []).push(n); });
    const order = ["department", "machine", "material", "line", "process", "product", "order", "lot", "shift", "source", "dataset", "field"];
    const types = order.filter(t => byType[t]);
    const colW = 140, rowH = 74, padX = 70, padY = 40;
    const pos = {};
    types.forEach((t, ci) => byType[t].forEach((n, ri) => { pos[n.type + ":" + n.id] = { x: padX + ci * colW, y: padY + ri * rowH }; }));
    const W = padX * 2 + types.length * colW;
    const H = padY * 2 + Math.max.apply(null, types.map(t => byType[t].length), [1]) * rowH;
    const svg = hNS("svg", { class: "graph-svg", width: W, height: H });
    edges.forEach(e => {
      const a = pos[e.source_type + ":" + e.source_id], b = pos[e.target_type + ":" + e.target_id];
      if (!a || !b) return;
      const kindCls = { production_dependency: "prod", data_flow: "data", data_mapping: "map", department_responsibility: "dept" }[e.kind] || "";
      const line = hNS("line", { class: "edge-line " + kindCls, x1: a.x + 60, y1: a.y + 22, x2: b.x + 60, y2: b.y + 22 });
      line.setAttribute("marker-end", "url(#arrow)");
      svg.appendChild(line);
    });
    const defs = hNS("defs", {});
    const marker = hNS("marker", { id: "arrow", viewBox: "0 0 10 10", refX: 9, refY: 5, markerWidth: 7, markerHeight: 7, orient: "auto" });
    marker.appendChild(hNS("path", { d: "M0,0 L10,5 L0,10 z", fill: "#8a93a0" }));
    defs.appendChild(marker); svg.appendChild(defs);
    nodes.forEach(n => {
      const p = pos[n.type + ":" + n.id];
      const g = hNS("g", { class: "node" });
      const r = hNS("rect", { x: p.x, y: p.y, width: 120, height: 44, rx: 6, fill: n.is_simulated ? "#fff3e0" : "#ffffff", stroke: "#c9ced6" });
      r.addEventListener("click", () => onNodeClick(n));
      const t = hNS("text", { x: p.x + 60, y: p.y + 19, "text-anchor": "middle", fill: "#1f2933", "font-weight": "600" });
      t.textContent = (n.name || "").length > 15 ? (n.name || "").slice(0, 15) + "…" : (n.name || "");
      const s2 = hNS("text", { x: p.x + 60, y: p.y + 34, "text-anchor": "middle", fill: "#8a93a0" });
      s2.textContent = n.type;
      g.appendChild(r); g.appendChild(t); g.appendChild(s2);
      svg.appendChild(g);
    });
    wrap.appendChild(svg);
  }
  function hNS(tag, attrs) {
    const n = document.createElementNS("http://www.w3.org/2000/svg", tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    return n;
  }

  /* ============================================================ analysis */
  async function renderAnalysis(params) {
    const v = $("#view");
    v.textContent = "";
    v.appendChild(h("div", { class: "section-head" }, [h("div", {}, [h("h2", { text: "Phân tích tác động" }), h("div", { class: "desc", text: "Chạy phân tích và đọc kết quả kèm giải thích." })])]));
    const inputCard = h("div", { class: "card" });
    const resultCard = h("div", { class: "card" });
    const histCard = h("div", { class: "card" });
    v.appendChild(inputCard); v.appendChild(resultCard); v.appendChild(histCard);

    inputCard.appendChild(h("div", { class: "card-title" }, [h("span", { text: "Đầu vào" })]));
    const form = h("div", { class: "grid grid-4" });
    const incSel = selectInput("incident", []);
    const dur = h("input", { name: "duration", type: "number", min: 0, placeholder: "phút" });
    const rate = h("input", { name: "rate", type: "number", min: 0, placeholder: "pcs/phút" });
    const maxd = h("input", { name: "max_depth", type: "number", min: 1, value: "3" });
    form.appendChild(field("Sự cố", incSel));
    form.appendChild(field("Thời lượng dừng (phút, tùy chọn)", dur));
    form.appendChild(field("Tốc độ (pcs/phút, tùy chọn)", rate));
    form.appendChild(field("Số bước lan truyền", maxd));
    inputCard.appendChild(form);
    inputCard.appendChild(h("button", { class: "btn btn-primary", text: "Chạy phân tích", onclick: () => runAnalysis() }));

    const incidents = await api("/api/incidents?page_size=100");
    incSel.appendChild(h("option", { value: "", text: "-- Chọn sự cố --" }));
    incidents.data.items.forEach(i => incSel.appendChild(h("option", { value: i.id, text: i.code + " — " + i.title })));

    const qInc = params.params.get("incident"), qRun = params.params.get("run");
    if (qRun) viewRun(Number(qRun));
    else if (qInc) { incSel.value = qInc; runAnalysis(); }
    loadHistory();
  }
  function runAnalysis() {
    const incSel = $("#view select[name='incident']");
    const id = incSel.value;
    if (!id) { toast("Chọn một sự cố trước.", "error"); return; }
    const dur = $("#view input[name='duration']").value;
    const rate = $("#view input[name='rate']").value;
    const maxd = $("#view input[name='max_depth']").value || "3";
    api("/api/analysis/run", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ incident_id: Number(id), max_depth: Number(maxd), duration_minutes: dur ? Number(dur) : null, rate_per_minute: rate ? Number(rate) : null }) })
      .then(d => renderAnalysisResult(d.data)).catch(e => toast(e.message, "error"));
  }
  function renderAnalysisResult(r) {
    const box = $("#view .card:nth-child(2)");
    box.textContent = "";
    box.appendChild(h("div", { class: "card-title" }, [h("span", { text: "Kết quả phân tích" }), h("span", { class: "sub", text: "Quy tắc " + (r.rules || []).join(", ") + " — phiên bản " + r.rule_version })]));
    if (r.quantification && r.quantification.available) box.appendChild(h("div", { class: "message visible info", text: "Định lượng: " + r.quantification.formula + " = " + r.quantification.lost_quantity + " pcs" }));
    else if (r.quantification) box.appendChild(h("div", { class: "message visible warn", text: r.quantification.message }));

    const impacts = r.impacts || [], hypotheses = r.hypotheses || [], actions = r.actions || [];
    box.appendChild(h("h3", { text: "Ảnh hưởng (" + impacts.length + ")" }));
    const impWrap = h("div");
    if (!impacts.length) impWrap.appendChild(h("p", { class: "cell-sub", text: "Không phát hiện ảnh hưởng lan truyền nào trong giới hạn đã đặt." }));
    else impacts.forEach(i => {
      const m = IMPACT_TYPE[i.impact_type] || [i.impact_type, "gray"];
      const ex = h("div", { class: "explain", style: "display:none;" }, [
        h("div", { class: "kv" }, [h("span", { text: "Bằng chứng: " + (i.evidence || "—") }), i.rule_id ? h("span", { text: "Quy tắc: " + i.rule_id }) : null]),
        i.path && i.path.length ? h("div", { class: "hop", style: "margin-top:8px;", text: i.path.map(s => s.from_type + "#" + s.from_id + " → " + s.to_type + "#" + s.to_id).join("  ›  ") }) : null,
        i.missing_info ? h("div", { class: "cell-sub", style: "margin-top:4px;", text: "Dữ liệu còn thiếu: " + i.missing_info }) : null,
      ]);
      const row = h("div", { class: "explain" }, [
        h("div", { style: "display:flex;gap:8px;align-items:center;" }, [badge(m[0], m[1]), h("strong", { text: i.node_name }), h("span", { class: "cell-sub", text: i.node_type }), h("button", { class: "btn btn-ghost btn-sm", text: "Vì sao?", onclick: () => { ex.style.display = ex.style.display === "none" ? "block" : "none"; } })]),
        ex,
      ]);
      impWrap.appendChild(row);
    });
    box.appendChild(impWrap);

    box.appendChild(h("h3", { text: "Giả thuyết nguyên nhân (" + hypotheses.length + ")" }));
    const hypWrap = h("div");
    if (!hypotheses.length) hypWrap.appendChild(h("p", { class: "cell-sub", text: "Chưa đủ dữ liệu để tạo giả thuyết." }));
    else hypotheses.forEach(hh => hypWrap.appendChild(h("div", { class: "explain" }, [
      h("div", {}, [badge("Giả thuyết", "amber"), h("span", { class: "cell-sub", style: "margin-left:8px;", text: "rule " + hh.rule_id + " · ưu tiên " + hh.priority })]),
      h("div", { text: hh.content, style: "margin-top:6px;font-weight:600;" }),
      hh.evidence ? h("div", { class: "cell-sub", text: "Bằng chứng: " + hh.evidence }) : null,
      hh.check_more ? h("div", { class: "cell-sub", text: "Cần kiểm tra thêm: " + hh.check_more }) : null,
    ])));
    box.appendChild(hypWrap);

    box.appendChild(h("h3", { text: "Hành động đề xuất (" + actions.length + ")" }));
    const actWrap = h("div");
    if (!actions.length) actWrap.appendChild(h("p", { class: "cell-sub", text: "Không có hành động đề xuất." }));
    else actions.forEach(a => actWrap.appendChild(h("div", { class: "explain" }, [
      h("div", { style: "display:flex;justify-content:space-between;gap:8px;align-items:center;" }, [h("div", {}, [h("div", { text: a.action }), h("div", { class: "cell-sub", text: a.department_name + " · ưu tiên " + a.priority })])]),
    ])));
    box.appendChild(actWrap);
    box.appendChild(h("div", { class: "message visible warn", text: "Đây là đề xuất từ quy tắc (không phải xác suất, không phải nguyên nhân đã xác nhận)." }));
  }
  async function loadHistory() {
    const wrap = $("#view .card:nth-child(3)");
    if (!wrap) return;
    wrap.textContent = ""; wrap.appendChild(h("div", { class: "card-title" }, [h("span", { text: "Lịch sử phân tích" })]));
    const d = await api("/api/analysis/runs?page_size=10");
    const list = h("div");
    if (!d.data.items.length) list.appendChild(h("p", { class: "cell-sub", text: "Chưa có lần phân tích nào." }));
    else d.data.items.forEach(r => list.appendChild(h("div", { class: "explain", style: "display:flex;justify-content:space-between;align-items:center;" }, [
      h("span", { text: "#" + r.id + " — " + r.source_type + " " + r.source_id + " · " + fmt(r.run_at) }),
      h("button", { class: "btn btn-ghost btn-sm", text: "Xem", onclick: () => viewRun(r.id) }),
    ])));
    wrap.appendChild(list);
  }
  async function viewRun(id) {
    const d = await api("/api/analysis/runs/" + id);
    const r = { rules: [], rule_version: d.data.run.rule_version, quantification: { available: false }, impacts: d.data.impacts.map(i => ({ node_name: i.node_name, node_type: i.node_type, impact_type: i.impact_type, path: i.path, evidence: i.evidence, rule_id: i.rule_id, missing_info: i.missing_info })), hypotheses: d.data.hypotheses.map(hh => ({ content: hh.content, rule_id: hh.rule_id, priority: hh.priority, check_more: hh.check_more, evidence: hh.evidence })), actions: d.data.actions.map(a => ({ department_name: a.department_name, action: a.action, priority: a.priority })) };
    renderAnalysisResult(r);
  }

  /* ============================================================ tasks */
  async function renderTasks() {
    const v = $("#view");
    v.textContent = "";
    v.appendChild(h("div", { class: "section-head" }, [h("div", {}, [h("h2", { text: "Công việc theo bộ phận" }), h("div", { class: "desc", text: "Theo dõi việc cần làm của từng bộ phận." })])]));
    const card = h("div", { class: "card" });
    v.appendChild(card);
    const toolbar = h("div", { class: "toolbar" });
    const deptSel = selectInput("dept", []);
    const statusSel = selectInput("status", ["TODO", "IN_PROGRESS", "DONE", "DISMISSED"].map(x => ({ value: x, label: { TODO: "Cần làm", IN_PROGRESS: "Đang làm", DONE: "Hoàn thành", DISMISSED: "Đã bỏ qua" }[x] })));
    const listWrap = h("div"); const pag = h("div", { class: "pagination" });
    toolbar.appendChild(field("Bộ phận", deptSel)); toolbar.appendChild(field("Trạng thái", statusSel));
    toolbar.appendChild(h("div", { class: "spacer" }));
    toolbar.appendChild(h("button", { class: "btn btn-primary", text: "Tạo công việc", onclick: () => taskForm(null) }));
    card.appendChild(toolbar); card.appendChild(listWrap); card.appendChild(pag);
    loadOptions("department").then(opts => { opts.forEach(o => deptSel.appendChild(h("option", { value: o.value, text: o.label }))); });
    const st = { page: 1, tp: 1 };
    async function load() {
      listWrap.textContent = ""; listWrap.appendChild(spinner());
      try {
        const q = new URLSearchParams({ page: st.page, page_size: 20 });
        if (deptSel.value) q.set("department_id", deptSel.value);
        if (statusSel.value) q.set("status", statusSel.value);
        const d = await api("/api/tasks?" + q);
        listWrap.textContent = "";
        if (!d.data.items.length) { listWrap.appendChild(emptyBox("tasks", "Không có công việc", "Công việc được tạo từ đề xuất phân tích hoặc thêm thủ công.")); return; }
        renderTable(listWrap, [
          { key: "title", label: "Công việc" }, { key: "department_id", label: "Bộ phận" },
          { key: "priority", label: "Ưu tiên" }, { key: "status", label: "Trạng thái", render: (r) => statusBadge(r.status) },
          { key: "source_incident_id", label: "Sự cố", render: (r) => r.source_incident_id ? ("#" + r.source_incident_id) : "—" },
        ], d.data.items, (row) => h("td", {}, [h("select", { onchange: (e) => setStatus(row.id, e.target.value) }, [
          h("option", { value: "TODO", selected: row.status === "TODO", text: "Cần làm" }),
          h("option", { value: "IN_PROGRESS", selected: row.status === "IN_PROGRESS", text: "Đang làm" }),
          h("option", { value: "DONE", selected: row.status === "DONE", text: "Hoàn thành" }),
          h("option", { value: "DISMISSED", selected: row.status === "DISMISSED", text: "Bỏ qua" }),
        ])]));
        st.tp = d.data.pagination.total_pages; pagination(pag, st.page, st.tp, (p) => { st.page = p; load(); });
      } catch (e) { listWrap.textContent = ""; listWrap.appendChild(errorBox(e.message, load)); }
    }
    async function setStatus(id, status) { try { await api("/api/tasks/" + id + "/status", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status }) }); toast("Đã cập nhật."); load(); } catch (e) { toast(e.message, "error"); } }
    async function taskForm(row) {
      const depts = await loadOptions("department");
      const fields = [
        { name: "title", label: "Việc cần làm", required: true },
        { name: "department_id", label: "Bộ phận phụ trách", type: "select", options: depts },
        { name: "description", label: "Lý do / mô tả", type: "textarea" },
        { name: "priority", label: "Mức ưu tiên", type: "select", options: ["LOW", "MEDIUM", "HIGH", "CRITICAL"].map(x => ({ value: x, label: (SEVERITY[x] || [x])[0] })) },
      ];
      const fb = formBuilder(fields, async (data, s) => {
        fb.setSubmitting(true);
        try { await api("/api/tasks", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) }); closeModal(); toast("Đã tạo."); load(); }
        catch (e) { toast(e.message, "error"); fb.setSubmitting(false); }
      });
      openModal("Tạo công việc", fb.form);
    }
    deptSel.addEventListener("change", () => { st.page = 1; load(); });
    statusSel.addEventListener("change", () => { st.page = 1; load(); });
    load();
  }

  /* ============================================================ scenarios */
  async function renderScenarios() {
    const v = $("#view");
    v.textContent = "";
    v.appendChild(h("div", { class: "section-head" }, [h("div", {}, [h("h2", { text: "Kịch bản mô phỏng" }), h("div", { class: "desc", text: "Thử 3 tình huống với dữ liệu mô phỏng (tách khỏi dữ liệu vận hành)." })])]));
    const card = h("div", { class: "card" });
    v.appendChild(card);
    card.appendChild(h("div", { class: "message visible warn", text: "Dữ liệu mô phỏng — chưa xác nhận bởi Denso. Không trộn với dữ liệu vận hành." }));
    const toolbar = h("div", { class: "toolbar" });
    toolbar.appendChild(h("button", { class: "btn btn-primary", text: "Nạp dữ liệu mô phỏng", onclick: loadDemo }));
    const st = h("span", { class: "cell-sub" });
    toolbar.appendChild(st);
    card.appendChild(toolbar);
    const list = h("div", { class: "grid grid-3" });
    const info = await api("/api/scenarios");
    info.data.forEach(s => list.appendChild(h("div", { class: "card" }, [
      h("div", { class: "card-title" }, [h("span", { text: s.title.replace(/^Kịch bản \d: /, "") }), badge("Mô phỏng", "amber")]),
      h("p", { class: "cell-sub", text: "Sự cố: " + s.incident_code }),
      h("p", { text: s.expected, style: "font-size:13px;" }),
      h("p", { class: "cell-sub", text: "Giới hạn: " + s.limits }),
      h("button", { class: "btn btn-secondary btn-sm", text: "Chạy kịch bản này", onclick: () => analyzeByCode(s.incident_code) }),
    ])));
    card.appendChild(list);
    const status = await api("/api/scenarios/status");
    st.textContent = status.data.loaded ? "Đã nạp." : "Chưa nạp.";
  }
  async function loadDemo() {
    try { const d = await api("/api/scenarios/load", { method: "POST" }); toast(d.data.message); renderScenarios(); }
    catch (e) { toast(e.message, "error"); }
  }
  async function analyzeByCode(code) {
    const d = await api("/api/incidents?page_size=100");
    const inc = d.data.items.find(i => i.code === code);
    if (!inc) { toast("Chưa nạp dữ liệu mô phỏng hoặc không thấy sự cố " + code + ".", "error"); return; }
    navigate("analysis?incident=" + inc.id);
  }

  /* ============================================================ survey */
  async function renderSurvey() {
    const v = $("#view");
    v.textContent = "";
    v.appendChild(h("div", { class: "section-head" }, [h("div", {}, [h("h2", { text: "Khảo sát & xác nhận" }), h("div", { class: "desc", text: "Theo dõi các thông tin cần xác nhận với nhà máy." })])]));
    const groups = await api("/api/survey/groups");
    const items = await api("/api/survey");
    const byGroup = {};
    items.data.forEach(i => { (byGroup[i.group_code] = byGroup[i.group_code] || []).push(i); });
    groups.data.forEach(g => {
      const card = h("div", { class: "card" });
      const confirmed = (byGroup[g.code] || []).filter(x => x.status === "CONFIRMED").length;
      const total = (byGroup[g.code] || []).length;
      card.appendChild(h("div", { class: "card-title" }, [h("span", { text: g.name }), h("span", { class: "cell-sub", text: confirmed + "/" + total + " đã xác nhận" })]));
      (byGroup[g.code] || []).forEach(item => {
        const row = h("div", { style: "border-bottom:1px solid var(--c-border); padding:10px 0;" });
        row.appendChild(h("p", { text: item.question, style: "font-weight:600; margin:0 0 4px;" }));
        row.appendChild(h("p", { class: "cell-sub", text: item.answer ? ("Trả lời: " + item.answer + (item.provided_by ? " — " + item.provided_by : "")) : "Chưa trả lời" }));
        row.appendChild(h("div", { style: "margin-top:4px;" }, [statusBadge(item.status === "CONFIRMED" ? "DONE" : "TODO"), h("button", { class: "btn btn-ghost btn-sm", style: "margin-left:8px;", text: item.answer ? "Sửa" : "Trả lời", onclick: () => surveyForm(item) })]));
        card.appendChild(row);
      });
      v.appendChild(card);
    });
  }
  function surveyForm(item) {
    const fields = [
      { name: "answer", label: "Câu trả lời", type: "textarea" },
      { name: "provided_by", label: "Người cung cấp" },
      { name: "status", label: "Trạng thái", type: "select", options: [{ value: "UNCONFIRMED", label: "Chưa xác nhận" }, { value: "CONFIRMED", label: "Đã xác nhận" }] },
      { name: "note", label: "Ghi chú", type: "textarea" },
    ];
    const fb = formBuilder(fields, async (data, s) => {
      fb.setSubmitting(true);
      try { await api("/api/survey/" + item.id, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) }); closeModal(); toast("Đã lưu."); renderSurvey(); }
      catch (e) { toast(e.message, "error"); fb.setSubmitting(false); }
    }, item);
    openModal("Trả lời khảo sát", fb.form);
  }

  /* ============================================================ dashboard */
  let dataMode = localStorage.getItem("d3.mode") || "operations";
  async function renderDashboard() {
    const v = $("#view");
    v.textContent = "";
    v.appendChild(spinner());
    let d;
    try { d = await api("/api/dashboard?simulated=" + (dataMode === "simulation")); } catch (e) { v.textContent = ""; v.appendChild(errorBox(e.message, renderDashboard)); return; }
    v.textContent = "";
    const s = d.data;

    // first-use checklist
    if (!s.has_data) {
      const card = h("div", { class: "card" });
      card.appendChild(h("div", { class: "card-title" }, [h("span", { text: "Bắt đầu thiết lập" }), h("span", { class: "sub", text: "Làm theo thứ tự để hệ thống hoạt động đầy đủ" })]));
      const cl = h("div", { class: "checklist" });
      s.checklist.forEach(step => cl.appendChild(h("div", { class: "check-item" + (step.done ? " done" : "") }, [
        h("div", { class: "check-dot", html: step.done ? '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="3"><path d="M4 12l5 5L20 6"/></svg>' : "" }),
        h("div", { class: "check-body" }, [h("div", { class: "check-title", text: step.title }), h("div", { class: "check-desc", text: step.description })]),
        h("button", { class: "btn btn-secondary btn-sm", text: step.done ? "Xem" : "Mở", onclick: () => navigate(step.route) }),
      ])));
      card.appendChild(cl);
      card.appendChild(h("div", { class: "toolbar", style: "margin-top:12px;" }, [
        h("button", { class: "btn btn-outline", text: "Khám phá bằng dữ liệu mô phỏng", onclick: () => navigate("scenarios") }),
      ]));
      v.appendChild(card);
      return;
    }

    // top bar: mode + last updated + actions
    const top = h("div", { class: "card" });
    const topRow = h("div", { class: "toolbar" });
    topRow.appendChild(h("span", { class: "cell-sub" }, [icon("clock", "icon"), " Cập nhật gần nhất: " + (s.last_updated ? fmt(s.last_updated) : "—")]));
    topRow.appendChild(h("div", { class: "spacer" }));
    topRow.appendChild(h("button", { class: "btn btn-primary", text: "Ghi nhận dữ liệu", onclick: () => navigate("operations") }));
    topRow.appendChild(h("button", { class: "btn btn-outline", text: "Báo cáo sự cố", onclick: () => navigate("incidents") }));
    top.appendChild(topRow);
    v.appendChild(top);

    if (dataMode === "simulation") v.appendChild(h("div", { class: "message visible warn", text: "Đang xem dữ liệu mô phỏng (chưa xác nhận bởi Denso)." }));

    // metrics
    const m = s.metrics;
    const incidents = s.incidents || [];
    const tasks = s.tasks || [];

    const metrics = h("div", { class: "metrics" });
    metrics.appendChild(metric("Sự cố chưa đóng", m.open_incidents, "sự cố", m.open_incidents > 0 ? "danger" : "neutral", "incidents"));
    metrics.appendChild(metric("Công việc cần xử lý", m.todo_tasks, "việc", "neutral", "tasks"));
    metrics.appendChild(metric("Máy đang dừng", m.machines_stopped, "máy", m.machines_stopped === null ? "empty" : (m.machines_stopped > 0 ? "danger" : "success"), "operations"));
    metrics.appendChild(metric("Sản lượng đạt", m.good_qty, "pcs", m.good_qty === null ? "empty" : "neutral", "operations"));
    metrics.appendChild(metric("Tỷ lệ lỗi sản lượng", m.defect_rate === null ? null : (m.defect_rate.toFixed(2) + "%"), m.defect_rate === null ? "" : "pcs", m.defect_rate === null ? "empty" : (m.defect_rate > 5 ? "warn" : "success"), "operations"));
    v.appendChild(metrics);

    const grid = h("div", { class: "detail-grid" });
    const left = h("div"); const right = h("div");
    grid.appendChild(left); grid.appendChild(right);

    // incidents
    const incCard = h("div", { class: "card" });
    incCard.appendChild(h("div", { class: "card-title" }, [h("span", { text: "Sự cố cần chú ý" }), h("button", { class: "btn btn-ghost btn-sm", text: "Xem tất cả", onclick: () => navigate("incidents") })]));
    if (!incidents.length) incCard.appendChild(emptyBox("incidents", "Không có sự cố đang mở", dataMode === "simulation" ? "Chưa có sự cố mô phỏng nào." : "Tốt — không có sự cố nào đang mở."));
    else {
      const wrap = h("div");
      renderTable(wrap, [
        { key: "code", label: "Mã" }, { key: "title", label: "Tiêu đề" }, { key: "severity", label: "Mức", render: (r) => severityBadge(r.severity) },
        { key: "department_name", label: "Bộ phận" }, 
        { key: "impact", label: "Tác động", render: (r) => r.affected_count != null ? badge(`${r.affected_count} entity, ${r.task_count} tasks`, "blue") : "—" },
        { key: "start_time", label: "Bắt đầu", render: (r) => r.start_time ? fmtDate(r.start_time) : "—" },
      ], incidents, null, (row) => navigate("incidents/" + row.id));
      incCard.appendChild(wrap);
    }
    left.appendChild(incCard);

    // tasks
    const tCard = h("div", { class: "card" });
    tCard.appendChild(h("div", { class: "card-title" }, [h("span", { text: "Công việc cần xử lý" }), h("button", { class: "btn btn-ghost btn-sm", text: "Xem tất cả", onclick: () => navigate("tasks") })]));
    if (!tasks.length) tCard.appendChild(emptyBox("tasks", "Không có công việc tồn đọng", "Công việc được tạo từ đề xuất phân tích."));
    else {
      const wrap = h("div");
      renderTable(wrap, [{ key: "title", label: "Công việc" }, { key: "department_name", label: "Bộ phận" }, { key: "priority", label: "Ưu tiên" }], tasks, null, () => navigate("tasks"));
      tCard.appendChild(wrap);
    }
    left.appendChild(tCard);

    // freshness
    const fCard = h("div", { class: "card" });
    fCard.appendChild(h("div", { class: "card-title" }, [h("span", { text: "Độ mới dữ liệu" }), h("button", { class: "btn btn-ghost btn-sm", text: "Cấu hình", onclick: () => navigate("system") })]));
    const fresh = (s.data_freshness || []).filter(ds => dataMode === "simulation" ? !!ds.is_simulated : !ds.is_simulated);
    if (!fresh.length) fCard.appendChild(emptyBox("database", "Chưa khai báo dataset", "Khai báo dataset để theo dõi độ mới dữ liệu."));
    else {
      const fw = h("div", { class: "freshness" });
      fresh.forEach(ds => {
        const m2 = { OK: ["Đã cập nhật", "green"], STALE: ["Dữ liệu chậm", "amber"], NO_DATA: ["Chưa có dữ liệu", "gray"], UNKNOWN: ["Chưa đánh giá", "gray"] }[ds.status];
        fw.appendChild(h("div", { class: "fresh-row" }, [
          h("div", { class: "fresh-name" }, [ds.name, h("span", { class: "sub", text: ds.code + " · " + (ds.update_schedule || "lịch chưa đặt") })]),
          badge(m2[0], m2[1]),
        ]));
      });
      fCard.appendChild(fw);
    }
    right.appendChild(fCard);

    // setup status
    const sCard = h("div", { class: "card" });
    sCard.appendChild(h("div", { class: "card-title" }, [h("span", { text: "Tình trạng thiết lập" }), h("button", { class: "btn btn-ghost btn-sm", text: "Thiết lập", onclick: () => navigate("catalog") })]));
    const st2 = h("div", { class: "freshness" });
    st2.appendChild(h("div", { class: "fresh-row" }, [h("div", { class: "fresh-name" }, ["Danh mục", h("span", { class: "sub", text: "bộ phận, chuyền, công đoạn, máy, vật tư, sản phẩm" })]), badge(s.setup.departments + " bộ phận", "gray")]));
    st2.appendChild(h("div", { class: "fresh-row" }, [h("div", { class: "fresh-name" }, ["Liên kết", h("span", { class: "sub", text: "quan hệ trong đồ thị" })]), badge(s.setup.edges + " cạnh", "gray")]));
    st2.appendChild(h("div", { class: "fresh-row" }, [h("div", { class: "fresh-name" }, ["Nguồn dữ liệu", h("span", { class: "sub", text: "hệ thống nguồn và dataset" })]), badge(s.setup.sources + " nguồn", "gray")]));
    sCard.appendChild(st2);
    right.appendChild(sCard);

    v.appendChild(grid);
  }
  function metric(label, value, unit, kind, route) {
    const el = h("a", { class: "metric m-" + kind, href: "#/" + route });
    const showValue = value === null || value === undefined ? "Chưa có dữ liệu" : (typeof value === "number" ? value.toLocaleString("vi-VN") : String(value));
    el.appendChild(h("div", { class: "m-label", text: label }));
    el.appendChild(h("div", { class: "m-value" }, [showValue, value !== null && value !== undefined && unit ? h("span", { class: "m-unit", text: unit }) : null]));
    el.appendChild(h("div", { class: "m-meta", text: "Bấm để xem chi tiết" }));
    return el;
  }

  /* ============================================================ router */
  const ROUTES = {
    dashboard: { title: "Trung tâm vận hành", group: "Tổng quan", icon: "dashboard", render: renderDashboard },
    operations: { title: "Ghi nhận dữ liệu", group: "Vận hành", icon: "operations", render: renderOperations },
    incidents: { title: "Sự cố", group: "Vận hành", icon: "incidents", render: renderIncidents },
    tasks: { title: "Công việc theo bộ phận", group: "Vận hành", icon: "tasks", render: renderTasks },
    map: { title: "Bản đồ liên kết", group: "Phân tích", icon: "map", render: renderMap },
    analysis: { title: "Phân tích tác động", group: "Phân tích", icon: "analysis", render: renderAnalysis },
    scenarios: { title: "Kịch bản mô phỏng", group: "Phân tích", icon: "scenarios", render: renderScenarios },
    catalog: { title: "Danh mục sản xuất", group: "Thiết lập dữ liệu", icon: "catalog", render: renderCatalog },
    system: { title: "Nguồn dữ liệu & ánh xạ", group: "Thiết lập dữ liệu", icon: "system", render: renderSystem },
    survey: { title: "Khảo sát & xác nhận", group: "Thiết lập dữ liệu", icon: "survey", render: renderSurvey },
  };

  function buildSidebar() {
    const wrap = $("#sidebar-groups");
    wrap.textContent = "";
    const groups = {};
    Object.keys(ROUTES).forEach(r => { const g = ROUTES[r].group; (groups[g] = groups[g] || []).push(r); });
    Object.keys(groups).forEach(g => {
      const grp = h("div", { class: "nav-group" });
      grp.appendChild(h("div", { class: "nav-group-title", text: g }));
      groups[g].forEach(r => {
        const a = h("button", { class: "nav-item", "data-route": r, onclick: () => navigate(r) }, [icon(ROUTES[r].icon), h("span", { class: "nav-label", text: ROUTES[r].title })]);
        grp.appendChild(a);
      });
      wrap.appendChild(grp);
    });
  }

  function parseHash() {
    const raw = location.hash.replace(/^#\/?/, "");
    const [pathPart, queryPart] = raw.split("?");
    const parts = pathPart.split("/").filter(Boolean);
    const params = new URLSearchParams(queryPart || "");
    return { parts, params };
  }

  function navigate(path) {
    location.hash = "#/" + path;
  }
  function renderRoute() {
    const { parts, params } = parseHash();
    const route = parts[0] || "dashboard";
    const cfg = ROUTES[route];
    $("#page-title").textContent = cfg ? cfg.title : "Trung tâm vận hành";
    $$(".nav-item").forEach(a => a.classList.toggle("active", a.dataset.route === route));
    $("#sidebar").classList.remove("open");
    removeBackdrop();
    const render = cfg ? cfg.render : renderDashboard;
    render({ parts, params });
  }

  /* header controls */
  $("#nav-toggle").addEventListener("click", () => { $("#sidebar").classList.toggle("open"); toggleBackdrop(); });
  $("#collapse-toggle").addEventListener("click", () => { document.body.classList.toggle("sidebar-collapsed"); });
  $("#header-record").addEventListener("click", () => navigate("operations"));
  $("#header-incident").addEventListener("click", () => navigate("incidents"));
  function setMode(mode) {
    dataMode = mode; localStorage.setItem("d3.mode", mode);
    $$(".mode-btn").forEach(b => b.classList.toggle("active", b.dataset.mode === mode));
    if (parseHash().parts[0] === "dashboard") renderDashboard();
  }
  $$(".mode-btn").forEach(b => b.addEventListener("click", () => setMode(b.dataset.mode)));
  setMode(dataMode);

  function toggleBackdrop() {
    removeBackdrop();
    if ($("#sidebar").classList.contains("open")) {
      const bd = h("div", { class: "sidebar-backdrop", onclick: () => { $("#sidebar").classList.remove("open"); removeBackdrop(); } });
      document.body.appendChild(bd);
    }
  }
  function removeBackdrop() { const bd = $(".sidebar-backdrop"); if (bd) bd.remove(); }

  window.addEventListener("hashchange", renderRoute);
  buildSidebar();
  renderRoute();
})();
