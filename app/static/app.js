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
    if (resp.status === 401) {
      const msg = (body && body.message) || "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.";
      if (path !== "/api/auth/login") showLogin();
      const err = new Error(msg); err.status = 401; throw err;
    }
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

  /* Vòng đời trang: mỗi lần render tạo một context có version bất biến.
     Continuation chỉ được cập nhật DOM khi version của nó vẫn là version hiện
     tại. Hàm render phải capture context ở đầu và dùng ctx.isCurrent(). */
  let pageVersion = 0;
  let activePageCtx = null;
  function createPageContext() {
    const version = ++pageVersion;
    return { isCurrent: () => version === pageVersion };
  }

  let modalDirty = false;
  let modalOpener = null;

  function openModal(title, bodyNode) {
    $("#modal-title").textContent = title;
    const b = $("#modal-body"); b.textContent = ""; b.appendChild(bodyNode);
    $("#modal").classList.remove("hidden");
    modalDirty = false;
    modalOpener = document.activeElement || null;
    const first = $("#modal").querySelector("input, select, textarea, button");
    if (first) first.focus();
  }
  function closeModal() {
    $("#modal").classList.add("hidden");
    $("#modal-body").textContent = "";
    if (modalOpener && typeof modalOpener.focus === "function") modalOpener.focus();
    modalOpener = null;
    modalDirty = false;
  }
  function markModalDirty() { modalDirty = true; }
  function confirmDiscard() {
    if (modalDirty && !window.confirm("Có thay đổi chưa lưu. Bỏ thay đổi?")) return false;
    return true;
  }
  function requestCloseModal() {
    if (!confirmDiscard()) return;
    closeModal();
  }
  $("#modal-close").addEventListener("click", requestCloseModal);
  $("#modal").addEventListener("click", (e) => { if (e.target.id === "modal") requestCloseModal(); });
  document.addEventListener("keydown", (e) => {
    if ($("#modal").classList.contains("hidden")) return;
    if (e.key === "Escape") { e.preventDefault(); requestCloseModal(); return; }
    if (e.key === "Tab") {
      const focusables = Array.from($("#modal").querySelectorAll("input, select, textarea, button, a[href]"))
        .filter((el) => !el.disabled && el.offsetParent !== null);
      if (!focusables.length) return;
      const first = focusables[0], last = focusables[focusables.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });

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

  // Giá trị datetime-local (không có múi giờ) được hiểu là giờ Việt Nam (+07:00),
  // bất kể múi giờ của trình duyệt; dữ liệu mẫu theo +07:00.
  function iso(v) {
    if (!v) return null;
    const s = String(v);
    if (!/(Z|[+-]\d{2}:?\d{2})$/i.test(s)) return new Date(s + "+07:00").toISOString();
    return new Date(s).toISOString();
  }
  const VN_TZ = "Asia/Ho_Chi_Minh";
  function fmt(v) { if (!v) return ""; const d = new Date(v); return isNaN(d) ? String(v) : d.toLocaleString("vi-VN", { timeZone: VN_TZ }); }
  function fmtDate(v) { if (!v) return ""; const d = new Date(v); return isNaN(d) ? String(v) : d.toLocaleDateString("vi-VN", { timeZone: VN_TZ }); }

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
    users: '<circle cx="9" cy="8" r="3.5"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/><circle cx="17" cy="9" r="2.5"/><path d="M16 14c2.8 0 5 2.2 5 5"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    check: '<path d="M4 12l5 5L20 6"/>',
    alert: '<path d="M12 3l9 16H3z"/><path d="M12 10v4"/><path d="M12 17h.01"/>',
    empty: '<path d="M4 8h16v11a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z"/><path d="M4 8l2-4h12l2 4"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    database: '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v7c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>',
    matrix: '<rect x="3" y="3" width="8" height="8" rx="1"/><rect x="13" y="3" width="8" height="8" rx="1"/><rect x="3" y="13" width="8" height="8" rx="1"/><rect x="13" y="13" width="8" height="8" rx="1"/>',
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
    const wrap = h("div", { class: "table-wrap" });
    wrap.appendChild(table);
    container.appendChild(wrap);
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
    let lastGroup = null, fs = null, groupInner = null;
    fields.forEach((f) => {
      // Chỉ có group, không có name => tiêu đề nhóm, không tạo input/payload.
      if (f.group && !f.name) {
        fs = h("fieldset", { class: "fieldset" });
        fs.appendChild(h("legend", { text: f.group }));
        groupInner = h("div", { class: "grid grid-2" });
        fs.appendChild(groupInner);
        form.appendChild(fs);
        lastGroup = f.group;
        return;
      }
      if (f.group && f.group !== lastGroup) {
        fs = h("fieldset", { class: "fieldset" });
        fs.appendChild(h("legend", { text: f.group }));
        groupInner = h("div", { class: "grid grid-2" });
        fs.appendChild(groupInner);
        form.appendChild(fs);
        lastGroup = f.group;
      }
      const hasInit = initial && initial[f.name] !== undefined && initial[f.name] !== null;
      const initVal = hasInit ? initial[f.name] : (f.default !== undefined ? f.default : "");
      let control;
      if (f.type === "select") control = selectInput(f.name, f.options || [], initVal);
      else if (f.type === "checkbox") {
        control = h("input", { name: f.name, type: "checkbox" });
        control.checked = !!(hasInit ? initial[f.name] : f.default);
      } else if (f.type === "textarea") {
        control = h("textarea", { name: f.name, rows: f.rows || 3 });
        control.value = initVal === null || initVal === undefined ? "" : String(initVal);
      } else {
        const inputType = f.type === "number" ? "number"
          : (f.type === "date" ? "date"
          : (f.type === "datetime" ? "datetime-local"
          : (f.type === "password" ? "password" : "text")));
        control = h("input", { name: f.name, type: inputType });
        if (f.type === "number") control.setAttribute("inputmode", "numeric");
        control.value = initVal === null || initVal === undefined ? "" : String(initVal);
        if (f.required) control.setAttribute("required", "");
        if (f.min !== undefined) control.setAttribute("min", f.min);
        if (f.max !== undefined) control.setAttribute("max", f.max);
        if (f.step !== undefined) control.setAttribute("step", f.step);
        if (f.placeholder) control.setAttribute("placeholder", f.placeholder);
        if (f.autocomplete !== undefined) control.setAttribute("autocomplete", f.autocomplete);
      }
      controls[f.name] = control;
      const fieldEl = field(f.label, control, f.required, f.hint);
      if (groupInner) groupInner.appendChild(fieldEl);
      else form.appendChild(fieldEl);
    });
    const actions = h("div", { class: "toolbar form-actions" });
    const submit = h("button", { type: "submit", class: "btn btn-primary", text: "Lưu" });
    const cancel = h("button", { type: "button", class: "btn btn-secondary", text: "Hủy", onclick: requestCloseModal });
    actions.appendChild(submit); actions.appendChild(cancel);
    form.appendChild(actions);
    form.addEventListener("input", markModalDirty);
    form.addEventListener("change", markModalDirty);
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const data = {};
      let firstInvalid = null;
      fields.forEach((f) => {
        if (!f.name) return;
        const c = controls[f.name];
        let v = c.type === "checkbox" ? c.checked : (c.value === "" ? null : c.value);
        if (f.type === "number" && v !== null && v !== "") v = Number(v);
        data[f.name] = v;
        const errEl = c.closest(".field") ? c.closest(".field").querySelector(".field-error") : null;
        if (errEl) errEl.textContent = "";
        let invalid = false;
        if (f.required && (v === null || v === "")) invalid = true;
        if (f.type === "number" && v !== null && v !== "" && (isNaN(v) || (f.min !== undefined && v < f.min) || (f.max !== undefined && v > f.max))) invalid = true;
        if (invalid) {
          if (errEl) errEl.textContent = "Giá trị không hợp lệ.";
          c.classList.add("invalid");
          if (!firstInvalid) firstInvalid = c;
        } else {
          c.classList.remove("invalid");
        }
      });
      if (firstInvalid) { firstInvalid.focus(); return; }
      onSubmit(data, submit);
    });
    return { form, setSubmitting: (flag) => { submit.disabled = flag; submit.textContent = flag ? "Đang lưu..." : "Lưu"; } };
  }
  function field(label, control, required, hint) {
    const w = h("div", { class: "field" });
    if (!control.id) control.id = "fld-" + Math.random().toString(36).slice(2, 10);
    w.appendChild(h("label", { for: control.id, text: label + (required ? " *" : "") }));
    w.appendChild(control);
    w.appendChild(h("div", { class: "field-error" }));
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
    return d.data.items.map((r) => ({ value: r.id, label: (r.code ? r.code + " — " : "") + r.name, code: r.code }));
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
    const ctx = activePageCtx;
    const v = $("#view");
    v.textContent = "";
    v.appendChild(h("div", { class: "section-head" }, [h("div", {}, [h("h2", { text: "Danh mục sản xuất" }), h("div", { class: "desc", text: "Bộ phận, chuyền, công đoạn, máy, vật tư, sản phẩm, lệnh và lot." })])]));
    const keys = await loadCatalogKeys();
    if (!ctx.isCurrent()) return;
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
    let tabToken = 0;
    function setView(k) { active = k; const t = ++tabToken; $$("button", tabs).forEach(b => b.classList.toggle("active", b.dataset.v === k)); body.textContent = ""; views[k](body, t, () => t === tabToken); }
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
  async function viewFields(body, token, isActive) {
    const ctx = activePageCtx;
    const toolbar = h("div", { class: "toolbar" }); const listWrap = h("div");
    const datasets = (await api("/api/system/datasets?page_size=100")).data.items;
    if (!ctx.isCurrent() || (isActive && !isActive())) return;
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
    const ctx = activePageCtx;
    function loadRecent() {
      listWrap.textContent = ""; listWrap.appendChild(spinner());
      api("/api/production-records?page_size=10").then(d => {
        if (!ctx.isCurrent()) return;
        listWrap.textContent = "";
        renderTable(listWrap, [
          { key: "id", label: "ID" }, { key: "production_date", label: "Ngày" }, { key: "shift", label: "Ca" },
          { key: "line_code", label: "Chuyền" }, { key: "process_code", label: "Công đoạn" }, { key: "lot_code", label: "Lot" },
          { key: "good_quantity", label: "Đạt" }, { key: "defect_quantity", label: "Lỗi" },
        ], d.data.items);
      }).catch((e) => {
        if (!ctx.isCurrent()) return;
        listWrap.textContent = "";
        listWrap.appendChild(errorBox(e.message, loadRecent));
      });
    }
    body.appendChild(productionForm(loadRecent));
    const head = h("div", { class: "card-title", style: "margin-top:16px;" }, [h("span", { text: "Bản ghi gần nhất" })]);
    const listWrap = h("div");
    body.appendChild(h("div", { class: "card" }, [head, listWrap]));
    loadRecent();
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
        try { await api("/api/operations/machine-states", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...data, event_time: iso(data.event_time), is_simulated: dataMode === "simulation" }) }); closeModal(); toast("Đã ghi nhận."); load(); }
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
        try { await api("/api/operations/downtimes", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...data, start_time: iso(data.start_time), end_time: data.end_time ? iso(data.end_time) : null, is_simulated: dataMode === "simulation" }) }); closeModal(); toast("Đã ghi nhận."); load(); }
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
        try { await api("/api/operations/qc", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...data, check_time: iso(data.check_time), is_simulated: dataMode === "simulation" }) }); closeModal(); toast("Đã ghi nhận."); load(); }
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
        try { await api("/api/operations/material", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...data, recorded_at: iso(data.recorded_at), is_simulated: dataMode === "simulation" }) }); closeModal(); toast("Đã ghi nhận."); load(); }
        catch (e) { toast(e.message, "error"); fb.setSubmitting(false); }
      });
      openModal("Ghi nhận tình trạng vật tư", fb.form);
    }
    load();
  }

  /* ============================================================ incidents */
  let incidentFormOpener = null;
  async function renderIncidents(params) {
    const ctx = activePageCtx;
    const v = $("#view");
    v.textContent = "";
    if (params.parts[1]) { renderIncidentDetail(params.parts[1]); return; }
    v.appendChild(h("div", { class: "section-head" }, [h("div", {}, [h("h2", { text: "Sự cố" }), h("div", { class: "desc", text: "Tạo và xử lý sự cố theo một luồng liền mạch." })])]));
    const card = h("div", { class: "card" });
    v.appendChild(card);
    const toolbar = h("div", { class: "toolbar" });
    const saved = pageState.incidents || {};
    const search = h("input", { placeholder: "Tìm theo mã hoặc tiêu đề..." });
    search.value = saved.search || "";
    const statusSel = selectInput("status", ["OPEN", "INVESTIGATING", "MITIGATING", "RESOLVED"].map(x => ({ value: x, label: { OPEN: "Đang mở", INVESTIGATING: "Đang điều tra", MITIGATING: "Đang xử lý", RESOLVED: "Đã giải quyết" }[x] })), saved.status || "");
    const typeSel = selectInput("type", ["MACHINE_STOP", "QUALITY", "MATERIAL_SHORTAGE", "DATA_DELAY", "OTHER"].map(x => ({ value: x, label: typeLabel(x) })), saved.type || "");
    // Áp dụng filter từ URL (ví dụ dashboard trỏ đến sự cố chưa đóng).
    const qStatus = params.params.get("status");
    if (qStatus && ["OPEN", "INVESTIGATING", "MITIGATING", "RESOLVED"].includes(qStatus)) statusSel.value = qStatus;
    const listWrap = h("div"); const pag = h("div", { class: "pagination" });
    toolbar.appendChild(h("div", { class: "search-box", style: "min-width:200px;" }, [icon("search"), search]));
    toolbar.appendChild(field("Trạng thái", statusSel));
    toolbar.appendChild(field("Loại", typeSel));
    toolbar.appendChild(h("div", { class: "spacer" }));
    toolbar.appendChild(h("button", { class: "btn btn-primary", text: "Tạo sự cố", onclick: () => incidentForm(null) }));
    card.appendChild(toolbar); card.appendChild(listWrap); card.appendChild(pag);
    const st = { page: saved.page || 1, tp: 1 };
    let loadSeq = 0;
    let timer;
    function persist() { pageState.incidents = { page: st.page, search: search.value, status: statusSel.value, type: typeSel.value }; }
    search.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(() => { st.page = 1; load(); }, 350); });
    statusSel.addEventListener("change", () => { st.page = 1; load(); });
    typeSel.addEventListener("change", () => { st.page = 1; load(); });
    async function load() {
      const mySeq = ++loadSeq;
      listWrap.textContent = ""; listWrap.appendChild(spinner());
      try {
        const q = new URLSearchParams({ page: st.page, page_size: 15 });
        if (statusSel.value) q.set("status", statusSel.value);
        if (typeSel.value) q.set("incident_type", typeSel.value);
        if (search.value) q.set("search", search.value);
        const d = await api("/api/incidents?" + q);
        if (!ctx.isCurrent() || mySeq !== loadSeq) return;
        listWrap.textContent = "";
        pag.textContent = "";
        if (!d.data.items.length) {
          const hasFilter = statusSel.value || typeSel.value || search.value;
          if (hasFilter) listWrap.appendChild(emptyBox("search", "Không có kết quả phù hợp", "Thử thay đổi bộ lọc hoặc xóa bộ lọc.",
            h("button", { class: "btn btn-secondary btn-sm", text: "Xóa bộ lọc", onclick: () => { search.value = ""; statusSel.value = ""; typeSel.value = ""; st.page = 1; load(); } })));
          else listWrap.appendChild(emptyBox("incidents", "Không có sự cố", "Tạo sự cố đầu tiên hoặc nạp kịch bản mô phỏng.", h("button", { class: "btn btn-primary btn-sm", text: "Tạo sự cố", onclick: () => incidentForm(null) })));
          persist();
          return;
        }
        renderTable(listWrap, [
          { key: "code", label: "Mã" }, { key: "title", label: "Tiêu đề" },
          { key: "incident_type", label: "Loại", render: (r) => typeLabel(r.incident_type) },
          { key: "severity", label: "Mức độ", render: (r) => severityBadge(r.severity) },
          { key: "status", label: "Trạng thái", render: (r) => statusBadge(r.status) },
          { key: "is_simulated", label: "", render: (r) => simBadge(r) },
        ], d.data.items, (row) => h("td", {}, [
          h("button", { class: "btn btn-sm btn-secondary", text: "Mở", onclick: (e) => { e.stopPropagation(); navigate("incidents/" + row.id); } }),
        ]), (row) => navigate("incidents/" + row.id));
        st.tp = d.data.pagination.total_pages;
        pagination(pag, st.page, st.tp, (p) => { st.page = p; load(); });
        persist();
      } catch (e) {
        if (!ctx.isCurrent() || mySeq !== loadSeq) return;
        listWrap.textContent = ""; listWrap.appendChild(errorBox(e.message, load));
      }
    }
    async function incidentForm(row) {
      let depts = [];
      try {
        depts = await loadOptions("department");
      } catch (e) {
        toast("Không tải được danh sách bộ phận: " + (e && e.message ? e.message : "lỗi mạng"), "error");
        return;
      }
      // Idempotency key ổn định cho một lần nhập; giữ nguyên khi retry.
      const formRequestId = uuid();
      const fields = [
        { group: "Thông tin chung" },
        { name: "code", label: "Mã sự cố", required: true }, { name: "title", label: "Tiêu đề", required: true },
        { name: "incident_type", label: "Loại sự cố", type: "select", options: ["MACHINE_STOP", "QUALITY", "MATERIAL_SHORTAGE", "DATA_DELAY", "OTHER"].map(x => ({ value: x, label: typeLabel(x) })), required: true },
        { name: "severity", label: "Mức nghiêm trọng", type: "select", options: ["LOW", "MEDIUM", "HIGH", "CRITICAL"].map(x => ({ value: x, label: (SEVERITY[x] || [x])[0] })) },
        { group: "Đối tượng & thời gian" },
        { name: "source_object_type", label: "Loại đối tượng", type: "select", options: ["machine", "lot", "material", "process", "product", "dataset", "line", "order"].map(x => ({ value: x, label: x })) },
        { name: "source_object_id", label: "ID đối tượng", type: "number", min: 1, hint: "Nhập ID của máy/lot/vật tư (xem ở Bản đồ liên kết)." },
        { name: "start_time", label: "Bắt đầu", type: "datetime" }, { name: "end_time", label: "Kết thúc", type: "datetime" },
        { group: "Xử lý" },
        { name: "assigned_department_id", label: "Bộ phận phụ trách", type: "select", options: depts },
        { name: "description", label: "Mô tả quan sát (triệu chứng)", type: "textarea" },
      ];
      const fb = formBuilder(fields, async (data, s) => {
        fb.setSubmitting(true);
        try {
          const payload = { ...data, request_id: formRequestId, start_time: data.start_time ? iso(data.start_time) : null, end_time: data.end_time ? iso(data.end_time) : null, is_simulated: dataMode === "simulation" };
          const resp = await api("/api/incidents", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
          closeModal(); toast(resp.message || "Đã tạo sự cố."); load();
        } catch (e) { toast(e.message, "error"); fb.setSubmitting(false); }
      });
      openModal("Tạo sự cố", fb.form);
    }
    incidentFormOpener = () => incidentForm(null);
    load();
    if (params.params.get("new") === "1") {
      incidentForm(null);
      history.replaceState(null, "", "#/incidents");
    }
  }

  async function renderIncidentDetail(id) {
    const ctx = activePageCtx;
    const v = $("#view");
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

    // Thông tin chính + thao tác (hiển thị sớm).
    const summaryCard = h("div", { class: "card" });
    left.appendChild(summaryCard);
    const actCard = h("div", { class: "card" });
    right.appendChild(actCard);

    let inc;
    try {
      inc = (await api("/api/incidents/" + id)).data;
      if (!ctx.isCurrent()) return;
      summaryCard.appendChild(h("div", { class: "card-title" }, [h("span", { text: inc.code + " — " + inc.title }), simBadge(inc)]));
      const rootCauseLabels = { UNKNOWN: "Chưa xác định", HYPOTHESIS: "Giả thuyết", CONFIRMED: "Đã xác nhận" };
      const kvList = h("div", { class: "kv-list" });
      summaryCard.appendChild(kvList);
      const objRow = kv("Đối tượng", inc.source_object_type ? (inc.source_object_type + " #" + inc.source_object_id) : "—");
      const deptRow = kv("Bộ phận", inc.assigned_department_id ? ("#" + inc.assigned_department_id) : "—");
      const rows = [
        kv("Loại", typeLabel(inc.incident_type)), kv("Mức độ", null, severityBadge(inc.severity)),
        kv("Trạng thái", null, statusBadge(inc.status)),
        kv("Bắt đầu", inc.start_time ? fmt(inc.start_time) : "—"),
        objRow, deptRow,
      ];
      if (inc.recovered_at) rows.push(kv("Khôi phục lúc", fmt(inc.recovered_at)));
      if (inc.recovered_by) rows.push(kv("Người xác nhận khôi phục", inc.recovered_by));
      if (inc.closed_at) rows.push(kv("Đóng hồ sơ lúc", fmt(inc.closed_at)));
      if (inc.closed_by) rows.push(kv("Người đóng", inc.closed_by));
      if (inc.resolution_summary) rows.push(kv("Tóm tắt xử lý", inc.resolution_summary));
      rows.push(kv("Trạng thái nguyên nhân", rootCauseLabels[inc.root_cause_status] || inc.root_cause_status || "Chưa xác định"));
      rows.forEach((r) => kvList.appendChild(r));
      if (inc.source_object_type && inc.source_object_id) {
        loadOptions(inc.source_object_type).then((opts) => {
          const o = opts.find((x) => x.value === Number(inc.source_object_id));
          if (o) objRow.lastChild.textContent = o.label;
        }).catch(() => {});
      }
      if (inc.assigned_department_id) {
        loadOptions("department").then((opts) => {
          const o = opts.find((x) => x.value === Number(inc.assigned_department_id));
          if (o) deptRow.lastChild.textContent = o.label;
        }).catch(() => {});
      }
      if (inc.description) summaryCard.appendChild(h("div", { class: "explain", style: "margin-top:12px;" }, [h("h4", { text: "Quan sát (triệu chứng)" }), h("div", { text: inc.description })]));
      renderActionCard(actCard, inc, id);
    } catch (e) {
      if (!ctx.isCurrent()) return;
      summaryCard.appendChild(errorBox(e.message, () => renderIncidentDetail(id)));
      return;
    }

    // Các khu vực phụ tải song song; lỗi một phần không che thông tin chính.
    loadContextSection(left, id, inc);
    loadCausesSection(left, id);
    loadLinksSection(left, id);
    loadHistorySection(left, id);
    loadRunsSection(actCard, id);
  }

  function asyncSection(card, title, fetcher, renderer) {
    const ctx = activePageCtx;
    card.appendChild(h("div", { class: "card-title" }, [h("span", { text: title })]));
    const body = h("div");
    card.appendChild(body);
    function run() {
      body.textContent = ""; body.appendChild(spinner());
      fetcher()
        .then((d) => { if (!ctx.isCurrent()) return; body.textContent = ""; renderer(body, d); })
        .catch((e) => { if (!ctx.isCurrent()) return; body.textContent = ""; body.appendChild(errorBox(e.message, run)); });
    }
    run();
  }

  function renderActionCard(actCard, inc, id) {
    actCard.appendChild(h("div", { class: "card-title" }, [h("span", { text: "Thao tác" })]));
    const statusRow = h("div", { class: "toolbar" });
    const newStatus = selectInput("newstatus", ["OPEN", "INVESTIGATING", "MITIGATING"].map(x => ({ value: x, label: { OPEN: "Mở", INVESTIGATING: "Điều tra", MITIGATING: "Xử lý" }[x] })), inc.status);
    statusRow.appendChild(field("Chuyển trạng thái", newStatus));
    statusRow.appendChild(h("button", { class: "btn btn-secondary", text: "Cập nhật", onclick: async () => {
      try { await api("/api/incidents/" + id, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status: newStatus.value }) }); toast("Đã cập nhật trạng thái."); renderIncidentDetail(id); }
      catch (e) { toast(e.message, "error"); }
    } }));
    actCard.appendChild(statusRow);
    const canResolve = userHasRole("COORDINATOR") || userHasRole("ADMIN");
    if (inc.status === "RESOLVED") {
      actCard.appendChild(h("div", { class: "message visible success", text: "Hồ sơ đã đóng" }));
    } else if (canResolve) {
      actCard.appendChild(h("button", { class: "btn btn-outline", style: "width:100%;margin-top:8px;", text: "Xác nhận khôi phục", onclick: () => recoverIncident(id) }));
      actCard.appendChild(h("button", { class: "btn btn-primary", style: "width:100%;margin-top:8px;", text: "Đóng hồ sơ", onclick: () => closeIncident(id) }));
    } else {
      actCard.appendChild(h("p", { class: "cell-sub", text: "Cần tài khoản điều phối để xác nhận khôi phục/đóng hồ sơ" }));
    }
    actCard.appendChild(h("button", { class: "btn btn-primary", style: "width:100%;margin-top:8px;", text: "Chạy phân tích tác động", onclick: () => navigate("analysis?incident=" + id) }));
  }

  function loadContextSection(left, id, inc) {
    const card = h("div", { class: "card" });
    left.appendChild(card);
    asyncSection(card, "Bối cảnh sản xuất",
      () => api("/api/incidents/" + id + "/context").then(d => d.data),
      (body, ctxData) => renderContextContent(body, id, ctxData));
  }
  function loadCausesSection(left, id) {
    const card = h("div", { class: "card" });
    left.appendChild(card);
    asyncSection(card, "Nguyên nhân",
      () => api("/api/incidents/" + id + "/causes").then(d => d.data),
      (body, causes) => {
        if (!causes.length) { body.appendChild(emptyBox("survey", "Chưa có nguyên nhân", "Giả thuyết sẽ xuất hiện sau khi chạy phân tích; nguyên nhân xác nhận do bạn ghi.")); return; }
        causes.forEach((c) => body.appendChild(h("div", { class: "explain" }, [
          h("div", {}, [c.kind === "CONFIRMED" ? badge("Đã xác nhận", "green") : badge("Giả thuyết", "amber"), c.rule_id ? h("span", { style: "font-size:12px;color:var(--c-text-faint);margin-left:8px;", text: "rule " + c.rule_id }) : null]),
          h("div", { text: c.content, style: "margin-top:6px;" }),
          c.evidence ? h("div", { class: "cell-sub", text: "Bằng chứng: " + c.evidence }) : null,
          (c.kind === "CONFIRMED" && c.confirmed_by) ? h("div", { class: "cell-sub", text: "Xác nhận bởi: " + c.confirmed_by }) : null,
        ])));
      });
  }
  function loadLinksSection(left, id) {
    const card = h("div", { class: "card" });
    left.appendChild(card);
    asyncSection(card, "Bằng chứng (bản ghi vận hành)",
      () => api("/api/incidents/" + id + "/links").then(d => d.data),
      (body, links) => {
        if (!links.length) { body.appendChild(h("p", { class: "cell-sub", text: "Chưa liên kết bản ghi vận hành nào." })); return; }
        links.forEach((l) => body.appendChild(h("div", { class: "explain" }, [h("div", { text: l.source_type + " #" + l.source_id })])));
      });
  }
  const HISTORY_ACTIONS = {
    CREATED: "Tạo sự cố", UPDATED: "Cập nhật", RECOVERED: "Xác nhận khôi phục",
    CLOSED: "Đóng hồ sơ", CAUSE_HYPOTHESIS: "Thêm nguyên nhân", CAUSE_CONFIRMED: "Xác nhận nguyên nhân",
    CAUSE_UPDATED: "Cập nhật nguyên nhân", CONTEXT_VERIFIED: "Xác minh bối cảnh",
  };
  function loadHistorySection(left, id) {
    const card = h("div", { class: "card" });
    left.appendChild(card);
    asyncSection(card, "Dòng thời gian",
      () => api("/api/incidents/" + id + "/history").then(d => d.data),
      (body, entries) => {
        if (!entries.length) { body.appendChild(h("p", { class: "cell-sub", text: "Chưa có hoạt động nào." })); return; }
        entries.forEach((e) => {
          const detail = e.detail || {};
          const note = e.action === "RECOVERED" ? detail.note : (e.action === "CLOSED" ? detail.resolution_summary : null);
          body.appendChild(h("div", { class: "explain", style: "margin-bottom:8px;" }, [
            h("div", { class: "cell-sub", text: fmt(e.changed_at) + (e.changed_by ? " · " + e.changed_by : "") }),
            h("div", { text: HISTORY_ACTIONS[e.action] || e.action, style: "margin-top:4px;" }),
            note ? h("div", { class: "cell-sub", text: note }) : null,
          ]));
        });
      });
  }
  function loadRunsSection(actCard, id) {
    const wrap = h("div", { style: "margin-top:12px;" });
    actCard.appendChild(wrap);
    asyncSectionWrap(wrap, "Đã phân tích",
      () => api("/api/analysis/runs?source_type=INCIDENT&source_id=" + id + "&page_size=10").then(d => d.data.items),
      (body, runs) => {
        if (!runs.length) { body.appendChild(h("p", { class: "cell-sub", text: "Chưa có lần phân tích nào." })); return; }
        runs.forEach((r) => body.appendChild(h("button", { class: "btn btn-ghost btn-sm", style: "width:100%;text-align:left;", text: "Xem phân tích #" + r.id + " — " + fmt(r.run_at), onclick: () => navigate("analysis?run=" + r.id) })));
      });
  }
  function asyncSectionWrap(wrap, title, fetcher, renderer) {
    const ctx = activePageCtx;
    wrap.appendChild(h("h4", { text: title, style: "margin:0 0 6px;" }));
    const body = h("div");
    wrap.appendChild(body);
    function run() {
      body.textContent = ""; body.appendChild(spinner());
      fetcher()
        .then((d) => { if (!ctx.isCurrent()) return; body.textContent = ""; renderer(body, d); })
        .catch((e) => { if (!ctx.isCurrent()) return; body.textContent = ""; body.appendChild(errorBox(e.message, run)); });
    }
    run();
  }

  function kv(k, v, node) {
    return h("div", { class: "kv-row" }, [h("span", { class: "k", text: k }), node ? node : h("span", { text: v })]);
  }

  const CTX_STATUS = { MATCHED: ["Đã xác định", "green"], AMBIGUOUS: ["Mơ hồ — cần xác minh", "amber"], NOT_FOUND: ["Chưa xác định", "gray"], CONFIRMED: ["Đã xác minh", "green"], NEEDS_REVIEW: ["Cần kiểm tra lại", "red"] };

  function renderContextContent(body, id, ctxData) {
    const status = ctxData.status || "NOT_FOUND";
    body.appendChild(h("div", { style: "margin-bottom:8px;" }, [badge(CTX_STATUS[status][0], CTX_STATUS[status][1])]));
    const candidates = ctxData.candidates || [];
    if (!candidates.length) {
      body.appendChild(h("p", { class: "cell-sub", text: "Chưa xác định được lô/công đoạn tại thời điểm xảy ra sự cố." }));
    } else {
      const tbl = h("div");
      renderTable(tbl, [
        { key: "lot_code", label: "Lô" }, { key: "process_code", label: "Công đoạn" },
        { key: "started_at", label: "Bắt đầu", render: (r) => fmt(r.started_at) },
        { key: "ended_at", label: "Kết thúc", render: (r) => r.ended_at ? fmt(r.ended_at) : badge("Đang chạy", "green") },
      ], candidates);
      body.appendChild(tbl);
    }
    if (ctxData.verification && ctxData.verification.status === "CONFIRMED") {
      const vr = ctxData.verification;
      body.appendChild(h("div", { class: "explain", style: "margin-top:8px;" }, [
        h("div", { class: "cell-sub", text: "Đã xác minh bởi #" + vr.decided_by + " lúc " + fmt(vr.decided_at) }),
        vr.reason ? h("div", { class: "cell-sub", text: "Lý do: " + vr.reason }) : null,
      ]));
    }
    if (status === "AMBIGUOUS" && userHasRole("COORDINATOR")) {
      body.appendChild(renderVerifyForm(id, candidates));
    }
  }

  function renderVerifyForm(id, candidates) {
    const wrap = h("div", { class: "verify-form", style: "margin-top:8px;border-top:1px solid var(--c-border);padding-top:8px;" });
    wrap.appendChild(h("h4", { text: "Xác minh bối cảnh" }));
    const sel = h("select");
    sel.appendChild(h("option", { value: "", text: "-- Chọn bối cảnh --" }));
    candidates.forEach(c => sel.appendChild(h("option", { value: c.operation_id, text: c.lot_code + " / " + c.process_code + " (" + c.operation_id + ")" })));
    const reason = h("input", { placeholder: "Lý do xác minh (bắt buộc)" });
    wrap.appendChild(h("label", { class: "field", html: "<span>Bối cảnh</span>" }));
    wrap.appendChild(sel);
    wrap.appendChild(h("label", { class: "field", html: "<span>Lý do</span>" }));
    wrap.appendChild(reason);
    const btn = h("button", { class: "btn btn-primary btn-sm", text: "Xác minh", onclick: async () => {
      if (!sel.value) { toast("Chọn một bối cảnh.", "error"); return; }
      if (!reason.value.trim()) { toast("Nhập lý do xác minh.", "error"); return; }
      btn.disabled = true;
      try {
        await api("/api/incidents/" + id + "/context/verify", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ operation_ids: [Number(sel.value)], reason: reason.value }) });
        toast("Đã xác minh bối cảnh."); renderIncidentDetail(id);
      } catch (e) { toast(e.message, "error"); btn.disabled = false; }
    } });
    wrap.appendChild(btn);
    return wrap;
  }

  function recoverIncident(id) {
    const fields = [
      { name: "recovered_at", label: "Thời điểm khôi phục", type: "datetime", required: true },
      { name: "note", label: "Ghi chú", type: "textarea" },
    ];
    const fb = formBuilder(fields, async (data, s) => {
      fb.setSubmitting(true);
      try {
        await api("/api/incidents/" + id + "/recover", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ recovered_at: data.recovered_at ? iso(data.recovered_at) : null, note: data.note || null }) });
        closeModal(); toast("Đã xác nhận khôi phục."); renderIncidentDetail(id);
      } catch (e) { toast(e.message, "error"); fb.setSubmitting(false); }
    });
    openModal("Xác nhận khôi phục", fb.form);
  }

  function closeIncident(id) {
    const fields = [
      { name: "resolution_summary", label: "Tóm tắt kết quả xử lý", type: "textarea", required: true },
      { name: "root_cause_status", label: "Trạng thái nguyên nhân", type: "select", options: [{ value: "UNKNOWN", label: "Chưa xác định" }, { value: "HYPOTHESIS", label: "Giả thuyết" }, { value: "CONFIRMED", label: "Đã xác nhận" }] },
    ];
    const fb = formBuilder(fields, async (data, s) => {
      fb.setSubmitting(true);
      try {
        await api("/api/incidents/" + id + "/close", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ resolution_summary: data.resolution_summary, root_cause_status: data.root_cause_status || "UNKNOWN" }) });
        closeModal(); toast("Đã đóng hồ sơ."); renderIncidentDetail(id);
      } catch (e) { toast(e.message, "error"); fb.setSubmitting(false); }
    });
    openModal("Đóng hồ sơ", fb.form);
  }

  /* ============================================================ map */
  const NODE_COLORS = {
    department: ["#e3f2fd", "#1e88e5"], material: ["#fff3e0", "#f57c00"],
    machine: ["#fce4ec", "#d81b60"], process: ["#e8f5e9", "#2e7d32"],
    line: ["#f3e5f5", "#8e24aa"], product: ["#fff8e1", "#f9a825"],
    order: ["#e0f7fa", "#00838f"], lot: ["#f1f8e9", "#558b2f"],
    shift: ["#efebe9", "#6d4c41"], source: ["#eceff1", "#546e7a"],
    dataset: ["#e8eaf6", "#3949ab"], field: ["#f5f5f5", "#757575"],
  };
  const NODE_LABELS = {
    department: "Bộ phận", material: "Vật tư", machine: "Máy", process: "Công đoạn",
    line: "Chuyền", product: "Sản phẩm", order: "Lệnh sản xuất", lot: "Lot", shift: "Ca sản xuất",
    source: "Hệ thống nguồn", dataset: "Dataset", field: "Trường dữ liệu",
  };
  const EDGE_LABELS = {
    production_dependency: "Phụ thuộc sản xuất", data_flow: "Luồng dữ liệu",
    data_mapping: "Ánh xạ dữ liệu–nghiệp vụ", department_responsibility: "Trách nhiệm bộ phận",
  };
  const EDGE_STYLE = {
    production_dependency: { color: "#c62828", dash: null, width: 2.5 },
    data_flow: { color: "#1d4f91", dash: null, width: 2 },
    data_mapping: { color: "#6a1b9a", dash: "6 3", width: 2.6 },
    department_responsibility: { color: "#b45309", dash: "2 2", width: 1.6 },
  };
  const TYPE_LANE = {
    department: "department", material: "material", machine: "machine", process: "process", line: "line",
    product: "output", order: "output", lot: "output", shift: "output",
    source: "source", dataset: "dataset", field: "field",
  };
  const LANE_LABELS = {
    department: "Bộ phận", material: "Vật tư", machine: "Máy", process: "Công đoạn", line: "Chuyền",
    output: "Sản phẩm · Lệnh · Lot · Ca", source: "Hệ thống nguồn", dataset: "Dataset", field: "Trường dữ liệu",
  };
  const BUSINESS_TYPES = ["department", "line", "process", "machine", "material", "product", "order", "lot", "shift"];
  const SYSTEM_TYPES = ["source", "dataset", "field"];
  const BUSINESS_LANES = ["department", "material", "machine", "process", "line", "output"];
  const SYSTEM_LANES = ["source", "dataset", "field"];
  const IMPACT_LABEL = { DIRECT: "Trực tiếp", INDIRECT: "Gián tiếp", RISK: "Rủi ro", OBSERVED: "Đã quan sát", ESTIMATED: "Ước tính" };
  const IMPACT_COLOR = { DIRECT: "#c62828", INDIRECT: "#b45309", RISK: "#8a93a0", OBSERVED: "#1a7f3c", ESTIMATED: "#1d4f91" };
  const NODE_W = 150, NODE_H = 64, LANE_W = 178;

  const nkey = (t, i) => t + ":" + i;
  function trunc(s, n) { s = s || ""; return s.length > n ? s.slice(0, n - 1) + "…" : s; }
  function edgePath(a, b) {
    const dx = b.x - a.x || 1;
    const bend = Math.min(Math.abs(dx) * 0.4, 70) || 24;
    const s = dx >= 0 ? 1 : -1;
    return "M " + a.x + " " + a.y + " C " + (a.x + s * bend) + " " + a.y + ", " + (b.x - s * bend) + " " + b.y + ", " + b.x + " " + b.y;
  }

  const EDGE_MEANING = {
    production_dependency: (s, t) => t + " phụ thuộc vào " + s + " theo quan hệ đã khai báo.",
    data_flow: (s, t) => "Dữ liệu được truyền từ " + s + " sang " + t + ".",
    data_mapping: (s, t) => "Dữ liệu " + s + " được liên kết với đối tượng " + t + ".",
    department_responsibility: (s, t) => "Bộ phận " + s + " phụ trách đối tượng " + t + ".",
  };

  async function renderMap() {
    const ctx = activePageCtx;
    const v = $("#view");
    v.textContent = "";
    v.appendChild(h("div", { class: "section-head" }, [h("div", {}, [h("h2", { text: "Bản đồ liên kết" }), h("div", { class: "desc", text: "Chọn một máy hoặc công đoạn để xem quan hệ và ý nghĩa từng liên kết." })])]));

    let meta = { node: {}, edge: {} };
    try {
      const m = await api("/api/graph/meta");
      m.data.node_types.forEach(t => { meta.node[t.type] = t.label; });
      m.data.edge_kinds.forEach(k => { meta.edge[k.kind] = k.label; });
    } catch (e) { /* meta chỉ là nhãn phụ */ }
    if (!ctx.isCurrent()) return;

    const nodeLabel = (t) => meta.node[t] || NODE_LABELS[t] || t;
    const edgeLabel = (k) => meta.edge[k] || EDGE_LABELS[k] || k;

    let graphData = { nodes: [], edges: [] };
    let fullGraphData = { nodes: [], edges: [] };
    let focusKey = null;          // đối tượng đang tập trung
    let selectedEdge = null;
    let impactNodes = {};
    let impactEdges = new Set();
    let impactSourceKey = null;
    let contentBox = { w: 400, h: 300 };
    let listMode = false;
    let incident = null;
    let showAll = false;
    const view = { x: 0, y: 0, w: 0, h: 0 };

    // ---- khung chọn phạm vi (góc nhìn, phạm vi liên kết, tìm kiếm) ----
    const scope = h("div", { class: "card" });
    const toolbar = h("div", { class: "graph-toolbar" });
    const modeSel = selectInput("mode", [
      { value: "process", label: "Quy trình sản xuất" },
      { value: "data", label: "Nguồn dữ liệu" },
      { value: "incident", label: "Theo sự cố" },
      { value: "combined", label: "Kết hợp (nâng cao)" },
    ], "process");
    const depthSel = selectInput("depth", [1, 2, 3].map(x => ({ value: x, label: x === 1 ? "Trực tiếp" : ("Thêm " + (x - 1) + " bước") })), 1);
    const search = h("input", { placeholder: "Tìm máy/công đoạn theo mã hoặc tên..." });
    const searchList = h("div", { class: "search-results" });
    const searchBox = h("div", { class: "search-box", style: "min-width:220px;" });
    searchBox.appendChild(icon("search")); searchBox.appendChild(search); searchBox.appendChild(searchList);
    // Bộ chọn cho góc nhìn "Theo sự cố".
    const incSel = selectInput("incident", []);
    const runSel = selectInput("run", []);
    toolbar.appendChild(field("Góc nhìn", modeSel));
    toolbar.appendChild(field("Phạm vi liên kết", depthSel));
    toolbar.appendChild(searchBox);
    toolbar.appendChild(h("div", { class: "spacer" }));
    toolbar.appendChild(h("button", { class: "btn btn-secondary btn-sm", text: "+", title: "Phóng to", onclick: () => zoomBy(1.25) }));
    toolbar.appendChild(h("button", { class: "btn btn-secondary btn-sm", text: "−", title: "Thu nhỏ", onclick: () => zoomBy(0.8) }));
    toolbar.appendChild(h("button", { class: "btn btn-secondary btn-sm", text: "Vừa khung", onclick: fitView }));
    toolbar.appendChild(h("button", { class: "btn btn-secondary btn-sm", text: "Bỏ chọn", onclick: deselect }));
    toolbar.appendChild(h("button", { class: "btn btn-secondary btn-sm", text: listMode ? "Sơ đồ" : "Danh sách", onclick: () => { listMode = !listMode; draw(); } }));
    scope.appendChild(toolbar);
    // Dòng tóm tắt ngắn.
    const summary = h("div", { class: "graph-summary cell-sub" });
    scope.appendChild(summary);
    v.appendChild(scope);

    // Bảng chọn sự cố (chỉ hiện ở góc nhìn "Theo sự cố").
    const incidentCard = h("div", { class: "card", style: "display:none;" });
    const incidentToolbar = h("div", { class: "toolbar" });
    incidentToolbar.appendChild(field("Sự cố", incSel));
    incidentToolbar.appendChild(field("Lần phân tích", runSel));
    const runBtn = h("button", { class: "btn btn-primary btn-sm", text: "Chạy phân tích", onclick: runAnalysisForIncident });
    incidentToolbar.appendChild(runBtn);
    incidentCard.appendChild(incidentToolbar);
    const incidentInfo = h("div", { class: "cell-sub" });
    incidentCard.appendChild(incidentInfo);
    v.appendChild(incidentCard);

    // ---- vùng sơ đồ chính + bảng giải thích bên phải ----
    const main = h("div", { class: "graph-layout" });
    const wrap = h("div", { class: "graph-wrap" });
    const tip = h("div", { class: "graph-tooltip" });
    main.appendChild(wrap);
    const detail = h("div", { class: "card graph-detail" });
    main.appendChild(detail);
    v.appendChild(main);

    v.appendChild(buildLegend());

    function buildLegend() {
      const frame = h("details", { class: "legend-frame" });
      frame.appendChild(h("summary", { text: "Cách đọc bản đồ" }));
      const read = h("div", { class: "read" });
      read.appendChild(h("div", { text: "• Mũi tên chỉ chiều quan hệ đã khai báo, không phải chiều lan truyền sự cố." }));
      read.appendChild(h("div", { text: "• Nét liền đậm: phụ thuộc sản xuất. Nét liền xanh: luồng dữ liệu. Nét đứt tím: ánh xạ dữ liệu–nghiệp vụ. Nét chấm cam: trách nhiệm bộ phận." }));
      read.appendChild(h("div", { text: "• Node nền nhạt + viền nét đứt: dữ liệu mô phỏng (chưa xác nhận bởi Denso)." }));
      frame.appendChild(read);
      const legend = h("div", { class: "legend" });
      Object.keys(NODE_COLORS).forEach(t => {
        const c = NODE_COLORS[t];
        legend.appendChild(h("span", { class: "lg" }, [h("span", { class: "swatch", style: "background:" + c[0] + ";border-color:" + c[1] + ";" }), nodeLabel(t)]));
      });
      Object.keys(EDGE_STYLE).forEach(k => {
        const s = EDGE_STYLE[k];
        const line = h("span", { class: "swatch-line", style: "border-color:" + s.color + ";" + (s.dash === "5 4" || s.dash === "6 3" ? "border-top-style:dashed;" : s.dash === "2 2" ? "border-top-style:dotted;" : "") });
        legend.appendChild(h("span", { class: "lg" }, [line, edgeLabel(k)]));
      });
      frame.appendChild(legend);
      return frame;
    }

    async function loadGraph() {
      wrap.textContent = ""; wrap.appendChild(spinner());
      try {
        const d = await api("/api/graph/map");
        if (!ctx.isCurrent()) return;
        graphData = d.data;
        fullGraphData = d.data;
        draw();
      } catch (e) {
        if (!ctx.isCurrent()) return;
        wrap.textContent = ""; wrap.appendChild(errorBox(e.message, loadGraph));
      }
    }
    async function loadIncidents() {
      try {
        const d = await api("/api/incidents?page_size=100");
        incSel.textContent = "";
        incSel.appendChild(h("option", { value: "", text: "-- Chọn sự cố --" }));
        d.data.items.forEach(i => incSel.appendChild(h("option", { value: i.id, text: i.code + " — " + i.title })));
      } catch (e) { /* không chặn bản đồ */ }
    }

    function modeIs(m) { return modeSel.value === m; }

    function filteredData() {
      let nodes = fullGraphData.nodes.slice(), edges = fullGraphData.edges.slice();
      if (modeIs("process")) {
        nodes = nodes.filter(n => BUSINESS_TYPES.includes(n.type));
        edges = edges.filter(e => BUSINESS_TYPES.includes(e.source_type) && BUSINESS_TYPES.includes(e.target_type));
      } else if (modeIs("data")) {
        nodes = nodes.filter(n => SYSTEM_TYPES.includes(n.type));
        edges = edges.filter(e => SYSTEM_TYPES.includes(e.source_type) && SYSTEM_TYPES.includes(e.target_type));
      } else if (modeIs("incident")) {
        const keys = new Set(Object.keys(impactNodes));
        if (impactSourceKey) keys.add(impactSourceKey);
        edges.forEach(e => {
          const ek = e.source_type + ":" + e.source_id + "->" + e.target_type + ":" + e.target_id;
          if (impactEdges.has(ek)) { keys.add(nkey(e.source_type, e.source_id)); keys.add(nkey(e.target_type, e.target_id)); }
        });
        nodes = nodes.filter(n => keys.has(nkey(n.type, n.id)));
        edges = edges.filter(e => keys.has(nkey(e.source_type, e.source_id)) && keys.has(nkey(e.target_type, e.target_id)));
        return { nodes, edges };
      }
      // Giới hạn theo đối tượng trung tâm + phạm vi liên kết (client-side cho đồ thị nhỏ).
      if (focusKey) {
        const inScope = neighborSet(fullGraphData, focusKey, Number(depthSel.value) || 1);
        nodes = nodes.filter(n => inScope.has(nkey(n.type, n.id)));
        edges = edges.filter(e => inScope.has(nkey(e.source_type, e.source_id)) && inScope.has(nkey(e.target_type, e.target_id)));
      }
      return { nodes, edges };
    }

    // Thứ tự công đoạn theo quan hệ phụ thuộc (không theo tên).
    function processOrder(nodes, edges) {
      const procNodes = nodes.filter(n => n.type === "process");
      const keys = new Set(procNodes.map(n => nkey(n.type, n.id)));
      const adj = {}, indeg = {};
      keys.forEach(k => { adj[k] = []; indeg[k] = 0; });
      edges.forEach(e => {
        if (e.kind === "production_dependency" && e.source_type === "process" && e.target_type === "process") {
          const s = nkey(e.source_type, e.source_id), t = nkey(e.target_type, e.target_id);
          if (keys.has(s) && keys.has(t)) { adj[s].push(t); indeg[t]++; }
        }
      });
      const order = [];
      const q = Array.from(keys).filter(k => indeg[k] === 0).sort((a, b) => a.localeCompare(b));
      while (q.length) {
        const k = q.shift(); order.push(k);
        adj[k].sort((a, b) => a.localeCompare(b));
        adj[k].forEach(m => { if (--indeg[m] === 0) q.push(m); });
      }
      return order.length ? order : Array.from(keys);
    }

    function computeLayout(nodes, edges) {
      const pos = {};
      const colW = 230, rowH = 96;
      const order = processOrder(nodes, edges);
      const idx = {}; order.forEach((k, i) => idx[k] = i);
      const nCol = Math.max(order.length, 1);
      const byType = {};
      nodes.forEach(n => { (byType[n.type] = byType[n.type] || []).push(n); });
      (byType.process || []).forEach(n => { const i = idx[nkey(n.type, n.id)] != null ? idx[nkey(n.type, n.id)] : 0; pos[nkey(n.type, n.id)] = { x: 90 + i * colW, y: 150 }; });
      // Máy gắn dưới công đoạn liên quan.
      (byType.machine || []).forEach(n => {
        const e = edges.find(ed => ed.source_type === "machine" && ed.source_id === n.id && ed.target_type === "process");
        const i = e ? (idx[nkey("process", e.target_id)] != null ? idx[nkey("process", e.target_id)] : 0) : 0;
        pos[nkey(n.type, n.id)] = { x: 90 + i * colW, y: 270 };
      });
      // Vật tư bên trái.
      (byType.material || []).forEach((n, i) => { pos[nkey(n.type, n.id)] = { x: 90 - colW, y: 150 + i * rowH }; });
      // Sản phẩm/lệnh/lô bên phải.
      (["product", "order", "lot"].forEach(t => (byType[t] || []).forEach((n, i) => { pos[nkey(n.type, n.id)] = { x: 90 + nCol * colW, y: 130 + i * rowH }; })));
      // Chuyền ở trên, bộ phận ở góc.
      (byType.line || []).forEach((n, i) => { pos[nkey(n.type, n.id)] = { x: 90 + (nCol / 2) * colW, y: 40 }; });
      (byType.department || []).forEach((n, i) => { pos[nkey(n.type, n.id)] = { x: 90 + (nCol + 1) * colW, y: 40 + i * 70 }; });
      // Lớp hệ thống ở vùng riêng phía dưới.
      (["source", "dataset", "field"].forEach(t => (byType[t] || []).forEach((n, i) => { pos[nkey(n.type, n.id)] = { x: 90 + i * colW, y: 400 }; })));
      const w = Math.max(90 + (nCol + 2) * colW, 500);
      const h = 470;
      return { pos, w, h };
    }

    function showTip(ev, text) {
      tip.textContent = text; tip.classList.add("visible");
      const r = wrap.getBoundingClientRect();
      tip.style.left = (ev.clientX - r.left + 12) + "px";
      tip.style.top = (ev.clientY - r.top + 12) + "px";
    }
    function hideTip() { tip.classList.remove("visible"); }

    function applyView() { const svg = wrap.querySelector("svg"); if (svg) svg.setAttribute("viewBox", view.x + " " + view.y + " " + view.w + " " + view.h); }

    function draw() {
      wrap.textContent = ""; wrap.appendChild(tip);
      updateSummary();
      if (modeIs("incident")) {
        if (!incident) {
          wrap.appendChild(emptyBox("incidents", "Chọn một sự cố", "Chọn sự cố ở khung phía trên để xem ảnh hưởng đã phân tích."));
          detail.textContent = "";
          return;
        }
      } else if (!focusKey && !showAll && !(impactNodes && Object.keys(impactNodes).length)) {
        wrap.appendChild(emptyBox("search", "Chọn một máy hoặc công đoạn để bắt đầu",
          "Tìm theo mã/tên ở ô tìm kiếm để tập trung vào đối tượng đó và các liên kết trực tiếp.",
          h("button", { class: "btn btn-primary btn-sm", text: "Xem tổng quan toàn chuyền", onclick: () => { showAll = true; focusKey = null; draw(); } })));
        detail.textContent = "";
        return;
      }
      const { nodes, edges } = filteredData();
      if (!nodes.length) {
        wrap.appendChild(emptyBox("map", "Không có dữ liệu để vẽ", "Nạp dữ liệu mô phỏng hoặc thêm danh mục/quan hệ."));
        return;
      }
      const layout = computeLayout(nodes, edges);
      contentBox = { w: layout.w, h: layout.h };
      if (view.w <= 0) { view.x = 0; view.y = 0; view.w = layout.w; view.h = layout.h; }

      if (listMode) { renderListMode(wrap, nodes, edges); return; }

      const svg = hNS("svg", { class: "graph-svg", viewBox: view.x + " " + view.y + " " + view.w + " " + view.h });
      const defs = hNS("defs", {});
      Object.keys(EDGE_STYLE).forEach(k => {
        const mk = hNS("marker", { id: "arrow-" + k, viewBox: "0 0 10 10", refX: 9, refY: 5, markerWidth: 6, markerHeight: 6, orient: "auto" });
        mk.appendChild(hNS("path", { d: "M0,0 L10,5 L0,10 z", fill: EDGE_STYLE[k].color }));
        defs.appendChild(mk);
      });
      svg.appendChild(defs);

      const pos = layout.pos;
      const nodeById = {};
      nodes.forEach(n => { nodeById[nkey(n.type, n.id)] = n; });
      edges.forEach(e => {
        const a = pos[nkey(e.source_type, e.source_id)], b = pos[nkey(e.target_type, e.target_id)];
        if (!a || !b) return;
        const st = EDGE_STYLE[e.kind] || EDGE_STYLE.production_dependency;
        const d = edgePath(a, b);
        const p = hNS("path", { class: "graph-edge", d: d, fill: "none", stroke: st.color, "stroke-width": st.width, "stroke-dasharray": st.dash || "none", "marker-end": "url(#arrow-" + e.kind + ")" });
        const src = nodeById[nkey(e.source_type, e.source_id)] || {};
        const tgt = nodeById[nkey(e.target_type, e.target_id)] || {};
        const edgeText = (EDGE_MEANING[e.kind] || (() => ""))((src.name || src.code || "?"), (tgt.name || tgt.code || "?")) + (e.label ? " (" + e.label + ")" : "");
        const ek = e.source_type + ":" + e.source_id + "->" + e.target_type + ":" + e.target_id;
        if (impactEdges.has(ek)) { p.setAttribute("stroke-width", "4"); p.setAttribute("stroke", "#c62828"); }
        p.setAttribute("aria-label", edgeText);
        p.addEventListener("mousemove", (ev) => showTip(ev, edgeText));
        p.addEventListener("mouseleave", hideTip);
        p.addEventListener("click", () => selectEdge(e, src, tgt));
        svg.appendChild(p);
      });

      nodes.forEach(n => {
        const p = pos[nkey(n.type, n.id)];
        const g = hNS("g", { class: "graph-node", transform: "translate(" + (p.x - NODE_W / 2) + "," + (p.y - NODE_H / 2) + ")" });
        g.setAttribute("tabindex", "0");
        g.setAttribute("role", "button");
        g.setAttribute("aria-label", nodeLabel(n.type) + " " + (n.name || "") + (n.code ? " (" + n.code + ")" : ""));
        const c = NODE_COLORS[n.type] || ["#fff", "#999"];
        const rect = hNS("rect", { width: NODE_W, height: NODE_H, rx: 8, fill: c[0], stroke: c[1] });
        if (n.is_simulated) rect.setAttribute("stroke-dasharray", "5 4");
        const nameT = hNS("text", { x: NODE_W / 2, y: 26, "text-anchor": "middle", fill: "#1f2933", "font-weight": "600", "font-size": "13" });
        nameT.textContent = trunc(n.name || "", 20);
        const codeT = hNS("text", { x: NODE_W / 2, y: 42, "text-anchor": "middle", fill: "#5b6572", "font-size": "11" });
        codeT.textContent = n.code ? trunc(n.code, 20) : "";
        const typeT = hNS("text", { x: NODE_W / 2, y: 57, "text-anchor": "middle", fill: c[1], "font-size": "10", "font-weight": "600" });
        typeT.textContent = nodeLabel(n.type);
        g.appendChild(rect); g.appendChild(nameT); g.appendChild(codeT); g.appendChild(typeT);
        if (n.is_simulated) {
          const b = hNS("g", { transform: "translate(" + (NODE_W - 12) + ",12)" });
          b.appendChild(hNS("circle", { r: 5, fill: "#b45309" }));
          b.appendChild(hNS("title", {})).textContent = "Dữ liệu mô phỏng";
          g.appendChild(b);
        }
        const key = nkey(n.type, n.id);
        if (impactNodes[key]) { rect.setAttribute("stroke", IMPACT_COLOR[impactNodes[key].impact_type] || "#c62828"); rect.setAttribute("stroke-width", "3"); }
        if (impactSourceKey === key) { rect.setAttribute("stroke-width", "4"); }
        g.addEventListener("click", () => selectNode(key));
        g.addEventListener("keydown", (ev) => { if (ev.key === "Enter") { ev.preventDefault(); selectNode(key); } });
        g.addEventListener("mousemove", (ev) => showTip(ev, nodeLabel(n.type) + ": " + (n.name || "") + (n.code ? " (" + n.code + ")" : "")));
        g.addEventListener("mouseleave", hideTip);
        svg.appendChild(g);
      });

      wrap.appendChild(svg);
      attachPanZoom(svg);
    }

    function renderListMode(container, nodes, edges) {
      container.appendChild(h("h3", { text: "Danh sách liên kết (" + nodes.length + " đối tượng)" }));
      const byType = {};
      nodes.forEach(n => { (byType[n.type] = byType[n.type] || []).push(n); });
      Object.keys(byType).forEach(t => {
        container.appendChild(h("h4", { text: nodeLabel(t) + " (" + byType[t].length + ")" }));
        const ul = h("ul", { class: "path-list" });
        byType[t].forEach(n => {
          const li = h("li", {}, [h("div", { text: (n.name || "") + (n.code ? " (" + n.code + ")" : "") })]);
          const rels = edges.filter(e => (e.source_type === n.type && e.source_id === n.id) || (e.target_type === n.type && e.target_id === n.id));
          rels.forEach(e => {
            const other = (e.source_type === n.type && e.source_id === n.id) ? nodeNameById(e.target_type, e.target_id, nodes) : nodeNameById(e.source_type, e.source_id, nodes);
            li.appendChild(h("div", { class: "cell-sub", text: edgeLabel(e.kind) + " — " + other }));
          });
          li.appendChild(h("button", { class: "btn btn-ghost btn-sm", text: "Xem trên sơ đồ", onclick: () => { listMode = false; focusKey = nkey(n.type, n.id); selectNode(focusKey); } }));
          ul.appendChild(li);
        });
        container.appendChild(ul);
      });
    }
    function nodeNameById(t, id, nodes) {
      const n = nodes.find(x => x.type === t && x.id === id);
      return n ? ((n.name || n.code || "") + " (" + nodeLabel(n.type) + ")") : (t + " #" + id);
    }

    function attachPanZoom(svg) {
      let drag = null;
      svg.addEventListener("pointerdown", (e) => {
        if (e.target === svg) { drag = { x: e.clientX, y: e.clientY, vx: view.x, vy: view.y }; svg.setPointerCapture(e.pointerId); }
      });
      svg.addEventListener("pointermove", (e) => {
        if (!drag) return;
        const rect = svg.getBoundingClientRect();
        const kx = view.w / rect.width;
        view.x = drag.vx - (e.clientX - drag.x) * kx;
        view.y = drag.vy - (e.clientY - drag.y) * kx;
        applyView();
      });
      svg.addEventListener("pointerup", () => { drag = null; });
      svg.addEventListener("pointercancel", () => { drag = null; });
      svg.addEventListener("wheel", (e) => {
        e.preventDefault();
        zoomAt(e.deltaY < 0 ? 1.2 : 0.83, e.clientX, e.clientY);
      }, { passive: false });
    }
    function zoomAt(f, clientX, clientY) {
      const svg = wrap.querySelector("svg"); if (!svg) return;
      const rect = svg.getBoundingClientRect();
      const px = (clientX - rect.left) / rect.width;
      const py = (clientY - rect.top) / rect.height;
      const cx = view.x + px * view.w;
      const cy = view.y + py * view.h;
      const minW = contentBox.w / 4, maxW = contentBox.w * 1.5;
      let newW = view.w / f;
      if (newW < minW) newW = minW;
      if (newW > maxW) newW = maxW;
      const newH = newW * (view.h / view.w);
      view.w = newW; view.h = newH;
      view.x = cx - px * newW;
      view.y = cy - py * newH;
      clampView();
      applyView();
    }
    function zoomBy(f) {
      const svg = wrap.querySelector("svg"); if (!svg) return;
      const rect = svg.getBoundingClientRect();
      zoomAt(f, rect.left + rect.width / 2, rect.top + rect.height / 2);
    }
    function clampView() {
      if (view.w > contentBox.w * 1.5) { view.w = contentBox.w * 1.5; view.h = view.w * (contentBox.h / contentBox.w); }
      if (view.x < -contentBox.w * 0.2) view.x = -contentBox.w * 0.2;
      if (view.y < -contentBox.h * 0.2) view.y = -contentBox.h * 0.2;
      if (view.x > contentBox.w * 1.2) view.x = contentBox.w * 1.2;
      if (view.y > contentBox.h * 1.2) view.y = contentBox.h * 1.2;
    }
    function fitView() {
      view.x = 0; view.y = 0; view.w = contentBox.w; view.h = contentBox.h;
      applyView();
    }
    function deselect() {
      search.value = ""; searchTerm = "";
      focusKey = null; selectedEdge = null; showAll = false; impactNodes = {}; impactEdges = new Set(); impactSourceKey = null;
      detail.textContent = "";
      searchList.textContent = "";
      draw();
    }

    function neighborSet(data, startKey, depth) {
      const adj = {};
      const keys = new Set();
      data.nodes.forEach(n => keys.add(nkey(n.type, n.id)));
      data.edges.forEach(e => {
        const s = nkey(e.source_type, e.source_id), t = nkey(e.target_type, e.target_id);
        if (!keys.has(s) || !keys.has(t)) return;
        (adj[s] = adj[s] || []).push(t);
        (adj[t] = adj[t] || []).push(s);
      });
      const visited = new Set([startKey]);
      let frontier = [startKey];
      for (let i = 0; i < depth; i++) {
        const nxt = [];
        frontier.forEach(n => (adj[n] || []).forEach(m => { if (!visited.has(m)) { visited.add(m); nxt.push(m); } }));
        frontier = nxt;
      }
      return visited;
    }

    function selectNode(nk) {
      focusKey = nk;
      selectedEdge = null;
      showAll = false;
      draw();
      fitView();
      renderDetail(nk);
    }

    function selectEdge(e, src, tgt) {
      selectedEdge = e;
      detail.textContent = "";
      detail.appendChild(h("div", { class: "card-title" }, [h("span", { text: edgeLabel(e.kind) })]));
      detail.appendChild(h("div", { text: (EDGE_MEANING[e.kind] || (() => ""))((src.name || src.code || "?"), (tgt.name || tgt.code || "?")) }));
      detail.appendChild(h("div", { class: "cell-sub", text: "Từ: " + (src.name || "") + (src.code ? " (" + src.code + ")" : "") }));
      detail.appendChild(h("div", { class: "cell-sub", text: "Đến: " + (tgt.name || "") + (tgt.code ? " (" + tgt.code + ")" : "") }));
      if (e.label) detail.appendChild(h("div", { class: "cell-sub", text: "Ghi chú: " + e.label }));
      if (e.description) detail.appendChild(h("div", { class: "cell-sub", text: e.description }));
      detail.appendChild(h("div", { class: "cell-sub", text: "Nguồn xác nhận: " + (e.source_confirmation || "chưa khai báo") }));
      if (e.valid_from) detail.appendChild(h("div", { class: "cell-sub", text: "Hiệu lực từ: " + fmt(e.valid_from) }));
      if (e.valid_to) detail.appendChild(h("div", { class: "cell-sub", text: "Hiệu lực đến: " + fmt(e.valid_to) }));
      detail.appendChild(h("div", { class: "cell-sub", text: "Loại dữ liệu: " + (e.is_simulated ? "Mô phỏng" : "Vận hành") }));
    }

    function nodeById(t, id) { return fullGraphData.nodes.find(n => n.type === t && n.id === id); }

    function renderDetail(nk) {
      detail.textContent = "";
      const parts = nk.split(":"); const nt = parts[0], nid = Number(parts[1]);
      const node = nodeById(nt, nid);
      if (!node) { detail.appendChild(h("p", { class: "cell-sub", text: "Không tìm thấy đối tượng." })); return; }
      detail.appendChild(h("div", { class: "card-title" }, [h("span", { text: (node.name || node.code || "") + " — " + nodeLabel(node.type) }), node.is_simulated ? badge("Mô phỏng", "amber") : null]));
      if (node.code) detail.appendChild(h("div", { class: "cell-sub", text: "Mã: " + node.code }));
      const edges = fullGraphData.edges;
      const dependsOn = edges.filter(e => e.target_type === nt && e.target_id === nid && e.kind === "production_dependency");
      const dependedBy = edges.filter(e => e.source_type === nt && e.source_id === nid && e.kind === "production_dependency");
      const responsible = edges.filter(e => e.target_type === nt && e.target_id === nid && e.kind === "department_responsibility");
      const dataRel = edges.filter(e => (e.source_type === nt && e.source_id === nid || e.target_type === nt && e.target_id === nid) && (e.kind === "data_mapping" || e.kind === "data_flow"));
      if (!dependsOn.length && !dependedBy.length && !responsible.length && !dataRel.length) { detail.appendChild(h("p", { class: "cell-sub", text: "Chưa có liên kết nào." })); return; }
      relGroup(detail, "Phụ thuộc vào", dependsOn, (e) => e.source_type, (e) => e.source_id, node);
      relGroup(detail, "Đối tượng phụ thuộc vào đối tượng này", dependedBy, (e) => e.target_type, (e) => e.target_id, node);
      relGroup(detail, "Bộ phận phụ trách", responsible, (e) => e.source_type, (e) => e.source_id, node);
      relGroup(detail, "Dữ liệu liên quan", dataRel, (e) => (e.source_type === nt && e.source_id === nid) ? e.target_type : e.source_type, (e) => (e.source_type === nt && e.source_id === nid) ? e.target_id : e.source_id, node);
    }

    function relGroup(container, title, edges, otherType, otherId, selected) {
      if (!edges.length) return;
      container.appendChild(h("h4", { text: title + " (" + edges.length + ")", style: "margin-top:12px;" }));
      const ul = h("ul", { class: "path-list" });
      edges.forEach(e => {
        const ot = otherType(e), oi = otherId(e);
        const other = nodeById(ot, oi);
        const src = (e.source_type === selected.type && e.source_id === selected.id) ? selected : other;
        const tgt = (e.target_type === selected.type && e.target_id === selected.id) ? selected : other;
        const meaning = (EDGE_MEANING[e.kind] || (() => ""))((src ? (src.name || src.code || "?") : "?"), (tgt ? (tgt.name || tgt.code || "?") : "?"));
        const li = h("li", {}, [
          h("div", { class: "hop", text: edgeLabel(e.kind) + (e.label ? " — " + e.label : "") }),
          h("div", { text: other ? ((other.name || other.code || "") + " (" + nodeLabel(other.type) + ")") : (ot + " #" + oi) }),
          h("div", { class: "cell-sub", text: meaning }),
          h("button", { class: "btn btn-ghost btn-sm", text: "Xem trên sơ đồ", onclick: () => selectNode(ot + ":" + oi) }),
        ]);
        ul.appendChild(li);
      });
      container.appendChild(ul);
    }

    function updateSummary() {
      if (modeIs("incident")) {
        if (incident) summary.textContent = "Sự cố " + incident.code + " — " + incident.title;
        else summary.textContent = "Chọn một sự cố để xem ảnh hưởng đã phân tích.";
        return;
      }
      if (focusKey) {
        const parts = focusKey.split(":"); const n = nodeById(parts[0], Number(parts[1]));
        if (n) summary.textContent = "Đang xem " + (n.name || n.code || "") + " — " + nodeLabel(n.type) + ", cùng các quan hệ trực tiếp đã khai báo.";
        else summary.textContent = "Chọn một máy hoặc công đoạn để bắt đầu.";
      } else {
        summary.textContent = "Chọn một máy hoặc công đoạn để bắt đầu.";
      }
    }

    function updateSearch() {
      const term = searchTerm;
      searchList.textContent = "";
      if (!term) { searchList.style.display = "none"; return; }
      const matches = fullGraphData.nodes.filter(n => (n.name || "").toLowerCase().includes(term) || (n.code || "").toLowerCase().includes(term)).slice(0, 8);
      if (!matches.length) { searchList.appendChild(h("div", { class: "cell-sub", text: "Không có kết quả." })); searchList.style.display = "block"; return; }
      matches.forEach(n => {
        searchList.appendChild(h("div", { class: "combo-option", onclick: () => { search.value = (n.code || n.name || ""); searchList.textContent = ""; searchList.style.display = "none"; searchTerm = ""; focusKey = nkey(n.type, n.id); draw(); renderDetail(focusKey); } }, [
          h("span", { class: "co-code", text: n.code || "" }), (n.name || "") + " (" + nodeLabel(n.type) + ")",
        ]));
      });
      searchList.style.display = "block";
    }

    // ---- Góc nhìn "Theo sự cố": chỉ đọc, không tự tạo run. ----
    async function loadIncident() {
      const id = incSel.value;
      incident = null; runSel.textContent = ""; impactNodes = {}; impactEdges = new Set(); impactSourceKey = null;
      incidentInfo.textContent = "";
      if (!id) { draw(); return; }
      try {
        const d = await api("/api/incidents/" + id);
        if (!ctx.isCurrent()) return;
        incident = d.data;
        incidentInfo.textContent = "Đối tượng: " + (incident.source_object_type || "?") + " #" + (incident.source_object_id || "?") +
          " · thời điểm " + (incident.start_time ? fmt(incident.start_time) : "?") + " · trạng thái " + incident.status;
        impactSourceKey = incident.source_object_type + ":" + incident.source_object_id;
        const runs = await api("/api/analysis/runs?source_type=INCIDENT&source_id=" + id + "&page_size=20");
        if (!ctx.isCurrent()) return;
        runSel.textContent = "";
        runSel.appendChild(h("option", { value: "", text: "-- Chọn lần phân tích --" }));
        runs.data.items.forEach(r => runSel.appendChild(h("option", { value: r.id, text: "#" + r.id + " — " + fmt(r.run_at) })));
        if (runs.data.items.length) {
          runSel.value = runs.data.items[0].id;
          loadRun(runs.data.items[0].id);
        } else {
          incidentInfo.textContent += " · Chưa có kết quả phân tích cho sự cố này.";
          draw();
        }
      } catch (e) { if (ctx.isCurrent()) toast(e.message, "error"); }
    }

    async function loadRun(runId) {
      impactNodes = {}; impactEdges = new Set();
      try {
        const d = await api("/api/analysis/runs/" + runId);
        if (!ctx.isCurrent()) return;
        const r = d.data;
        (r.impacts || []).forEach(imp => { impactNodes[nkey(imp.node_type, imp.node_id)] = { impact_type: imp.impact_type }; });
        (r.impacts || []).forEach(imp => {
          (imp.path || []).forEach(s => { impactEdges.add(s.from_type + ":" + s.from_id + "->" + s.to_type + ":" + s.to_id); });
        });
        draw();
      } catch (e) { if (ctx.isCurrent()) toast(e.message, "error"); }
    }

    async function runAnalysisForIncident() {
      const id = incSel.value;
      if (!id) { toast("Chọn một sự cố trước.", "error"); return; }
      runBtn.disabled = true; runBtn.textContent = "Đang chạy...";
      try {
        await api("/api/analysis/run", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ incident_id: Number(id), max_depth: Number(depthSel.value) || 2 }) });
        toast("Đã chạy phân tích.");
        await loadIncident();
      } catch (e) { toast(e.message, "error"); }
      runBtn.disabled = false; runBtn.textContent = "Chạy phân tích";
    }

    async function edgeForm() {
      const nodeOpts = fullGraphData.nodes.map(n => ({ value: n.type + ":" + n.id, label: (n.name || n.code || "") + " (" + nodeLabel(n.type) + ")", code: n.type }));
      if (!nodeOpts.length) { toast("Chưa có node để liên kết.", "error"); return; }
      const fields = [
        { name: "kind", label: "Loại quan hệ", type: "select", options: Object.keys(EDGE_STYLE).map(k => ({ value: k, label: edgeLabel(k) })), required: true },
        { name: "source", label: "Từ (đối tượng nguồn)", type: "select", options: nodeOpts, required: true },
        { name: "target", label: "Đến (đối tượng đích)", type: "select", options: nodeOpts, required: true },
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

    let searchTerm = "";
    modeSel.addEventListener("change", () => {
      incidentCard.style.display = modeIs("incident") ? "" : "none";
      if (!modeIs("incident")) { incident = null; incidentInfo.textContent = ""; }
      impactNodes = {}; impactEdges = new Set(); impactSourceKey = null; focusKey = null; detail.textContent = "";
      draw();
      fitView();
    });
    depthSel.addEventListener("change", () => { if (focusKey || modeIs("incident")) { draw(); fitView(); } });
    incSel.addEventListener("change", loadIncident);
    runSel.addEventListener("change", () => { if (runSel.value) loadRun(runSel.value); });
    let t; search.addEventListener("input", () => { clearTimeout(t); t = setTimeout(() => { searchTerm = search.value.trim().toLowerCase(); updateSearch(); }, 250); });
    search.addEventListener("focus", () => { if (search.value) { searchTerm = search.value.trim().toLowerCase(); updateSearch(); } });
    document.addEventListener("click", (e) => { if (!searchBox.contains(e.target)) { searchList.style.display = "none"; } });

    loadIncidents();
    loadGraph();
  }

  function hNS(tag, attrs) {
    const n = document.createElementNS("http://www.w3.org/2000/svg", tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    return n;
  }

  /* ============================================================ analysis */
  async function renderAnalysis(params) {
    const ctx = activePageCtx;
    const v = $("#view");
    v.textContent = "";
    v.appendChild(h("div", { class: "section-head" }, [h("div", {}, [h("h2", { text: "Phân tích tác động" }), h("div", { class: "desc", text: "Chạy phân tích và đọc kết quả kèm giải thích." })])]));
    const inputCard = h("div", { class: "card", id: "analysis-input" });
    const resultCard = h("div", { class: "card", id: "analysis-result" });
    const histCard = h("div", { class: "card", id: "analysis-history" });
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
    const runBtn = h("button", { class: "btn btn-primary", text: "Chạy phân tích", onclick: () => runAnalysis(runBtn) });
    inputCard.appendChild(runBtn);
    inputCard.appendChild(h("div", { class: "cell-sub", text: "Chọn sự cố rồi bấm \"Chạy phân tích\". Mở trang này không tự tạo kết quả mới." }));

    let incOptions = [];
    try {
      const incidents = await api("/api/incidents?page_size=100");
      incOptions = incidents.data.items;
    } catch (e) {
      if (ctx.isCurrent()) toast(e.message, "error");
    }
    incSel.appendChild(h("option", { value: "", text: "-- Chọn sự cố --" }));
    incOptions.forEach(i => incSel.appendChild(h("option", { value: i.id, text: i.code + " — " + i.title })));

    const qInc = params.params.get("incident"), qRun = params.params.get("run");
    if (qRun) viewRun(Number(qRun));
    else if (qInc) incSel.value = qInc;
    loadHistory();
  }
  function runAnalysis(btn) {
    const ctx = activePageCtx;
    const incSel = $("#view select[name='incident']");
    const id = incSel.value;
    if (!id) { toast("Chọn một sự cố trước.", "error"); return; }
    const dur = $("#view input[name='duration']").value;
    const rate = $("#view input[name='rate']").value;
    const maxd = $("#view input[name='max_depth']").value || "3";
    const b = btn || $("#analysis-input button.btn-primary");
    const prev = b.textContent;
    b.disabled = true; b.textContent = "Đang chạy...";
    api("/api/analysis/run", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ incident_id: Number(id), max_depth: Number(maxd), duration_minutes: dur ? Number(dur) : null, rate_per_minute: rate ? Number(rate) : null }) })
      .then(d => {
        if (!ctx.isCurrent()) return;
        renderAnalysisResult(d.data);
        loadHistory();
      })
      .catch(e => { if (ctx.isCurrent()) toast(e.message, "error"); })
      .finally(() => { b.disabled = false; b.textContent = prev; });
  }
  function renderAnalysisResult(r) {
    const box = $("#analysis-result");
    box.textContent = "";
    box.appendChild(h("div", { class: "card-title" }, [h("span", { text: "Kết quả phân tích" }), h("span", { class: "sub", text: "Quy tắc " + (r.rules || []).join(", ") + " — phiên bản " + r.rule_version + (r.run_id ? " · lần chạy #" + r.run_id : "") })]));
    if (r.snapshot_available === false) box.appendChild(h("div", { class: "message visible warn", text: "Lần chạy cũ chưa lưu snapshot đầy đủ; bối cảnh/ước tính có thể không tái hiện được." }));
    if (r.quantification) {
      const q = r.quantification;
      if (q.available) {
        if (q.kind === "QUALITY") {
          box.appendChild(h("div", { class: "explain" }, [
            h("div", { style: "display:flex;gap:8px;align-items:center;flex-wrap:wrap;" }, [badge("Định lượng", "blue"), h("strong", { text: "Tỷ lệ lỗi " + q.defect_rate + "%" })]),
            h("div", { class: "cell-sub", style: "margin-top:4px;", text: q.defect_qty + " / " + q.inspected_qty + " kiểm → ước tính cả lô " + q.lot_qty + " × " + (q.defect_rate / 100) + " = " + q.estimated_defects + " pcs" }),
            q.order_code ? h("div", { class: "cell-sub", text: q.estimated_defects + " ÷ " + q.plan_qty + " (lệnh " + q.order_code + ") = " + q.plan_defect_pct + "% kế hoạch" }) : null,
            (q.materials && q.materials.length) ? h("div", { class: "cell-sub", text: "Vật tư cần truy xuất: " + q.materials.map(m => m.material_code).join(", ") }) : null,
            h("div", { class: "cell-sub", text: "Công thức: " + q.formula }),
            q.assumptions ? h("div", { class: "cell-sub", text: "Giả định: " + q.assumptions }) : null,
          ]));
        } else if (q.kind === "MATERIAL_SHORTAGE") {
          box.appendChild(h("div", { class: "explain" }, [
            h("div", { style: "display:flex;gap:8px;align-items:center;flex-wrap:wrap;" }, [badge("Định lượng", "blue"), h("strong", { text: q.material_code + " còn " + q.available_qty + " pcs, cạn sau " + q.minutes + " phút" })]),
            h("div", { class: "cell-sub", style: "margin-top:4px;", text: q.available_qty + " pcs ÷ " + q.rate_per_minute + " pcs/phút = " + q.minutes + " phút" }),
            q.stockout_time ? h("div", { class: "cell-sub", text: "Thời điểm cạn: " + fmt(q.stockout_time) + " (công đoạn " + q.process_code + ")" }) : null,
            h("div", { class: "cell-sub", text: "Công thức: " + q.formula }),
            q.assumptions ? h("div", { class: "cell-sub", text: "Giả định: " + q.assumptions }) : null,
          ]));
        } else {
          box.appendChild(h("div", { class: "message visible info", text: "Định lượng: " + q.formula + " = " + q.lost_quantity + " pcs" }));
        }
      } else {
        box.appendChild(h("div", { class: "message visible warn", text: q.message || "Chưa đủ dữ liệu để định lượng." }));
      }
    }
    // Bối cảnh sản xuất
    if (r.context) {
      const c = r.context;
      const cs = CTX_STATUS[c.status] || [c.status, "gray"];
      box.appendChild(h("div", { class: "explain" }, [
        h("div", { style: "display:flex;gap:8px;align-items:center;flex-wrap:wrap;" }, [h("strong", { text: "Bối cảnh sản xuất" }), badge(cs[0], cs[1])]),
        c.lot_code ? h("div", { class: "cell-sub", style: "margin-top:4px;", text: "Lô " + c.lot_code + " · công đoạn " + c.process_code + (c.order_code ? " · lệnh " + c.order_code : "") }) : null,
        c.message ? h("div", { class: "cell-sub", style: "margin-top:4px;", text: c.message }) : null,
        (c.status === "AMBIGUOUS" && c.candidates && c.candidates.length) ? h("div", { class: "cell-sub", style: "margin-top:4px;", text: "Có " + c.candidates.length + " bối cảnh phù hợp — cần xác minh (xem trang chi tiết sự cố)." }) : null,
      ]));
    }
    // Ước tính định lượng
    if (r.capacity_estimate) {
      const ce = r.capacity_estimate;
      box.appendChild(h("div", { class: "explain" }, [
        h("div", { style: "display:flex;gap:8px;align-items:center;" }, [badge("Ước tính", "blue"), h("strong", { text: ce.estimated_quantity + " " + (ce.unit || "pcs") + " năng lực có nguy cơ" })]),
        h("div", { class: "cell-sub", style: "margin-top:4px;", text: ce.formula + " = " + ce.duration_minutes + " × " + ce.rate_per_minute }),
        ce.assumptions ? h("div", { class: "cell-sub", text: "Giả định: " + ce.assumptions }) : null,
      ]));
    }
    if (r.buffer_estimate && r.buffer_estimate.available) {
      const be = r.buffer_estimate;
      box.appendChild(h("div", { class: "explain" }, [
        h("div", { style: "display:flex;gap:8px;align-items:center;" }, [badge("Ước tính", "blue"), h("strong", { text: "Công đoạn sau (" + be.downstream_name + ") có nguy cơ cạn hàng sau " + be.depletion_minutes + " phút" })]),
        h("div", { class: "cell-sub", style: "margin-top:4px;", text: "Hàng đệm " + be.buffer_qty + " " + (be.buffer_unit || "") + " ÷ " + be.rate_per_minute + " pcs/phút ≈ " + fmt(be.depletion_time) }),
        h("div", { class: "cell-sub", text: be.assumptions }),
      ]));
    } else if (r.buffer_estimate && r.buffer_estimate.message) {
      box.appendChild(h("div", { class: "explain" }, [h("div", { class: "cell-sub", text: r.buffer_estimate.message })]));
    }
    // Độ nhạy theo thời gian dừng (tính phía client, không gọi API).
    if (r.capacity_estimate && r.capacity_estimate.rate_per_minute) {
      const ce = r.capacity_estimate, be = r.buffer_estimate;
      const durations = [10, 15, 30, 60];
      const sens = h("div", { class: "explain" });
      sens.appendChild(h("div", { style: "display:flex;gap:8px;align-items:center;" }, [badge("Độ nhạy", "blue"), h("strong", { text: "Độ nhạy theo thời gian dừng" })]));
      const tbl = h("table");
      const thead = h("thead"); const trh = h("tr");
      trh.appendChild(h("th", { text: "Thời gian dừng" }));
      trh.appendChild(h("th", { text: "Năng lực có nguy cơ" }));
      if (be && be.available) trh.appendChild(h("th", { text: "Hàng đệm" }));
      thead.appendChild(trh); tbl.appendChild(thead);
      const tbody = h("tbody");
      durations.forEach(d => {
        const tr = h("tr");
        tr.appendChild(h("td", { text: d + " phút" }));
        tr.appendChild(h("td", { text: Math.round(d * ce.rate_per_minute) + " " + (ce.unit || "pcs") }));
        if (be && be.available) {
          tr.appendChild(h("td", { text: d > be.depletion_minutes ? "Cạn sau " + be.depletion_minutes + " phút (trong khi dừng)" : "Chưa cạn (" + be.depletion_minutes + " phút)" }));
        }
        tbody.appendChild(tr);
      });
      tbl.appendChild(tbody);
      sens.appendChild(tbl);
      sens.appendChild(h("div", { class: "cell-sub", text: "Giả định: tốc độ giữ nguyên, không bổ sung hàng đệm, không sản xuất bù." }));
      box.appendChild(sens);
    }
    // Sự cố tương tự
    const related = r.related_past_incidents || [];
    if (related.length) {
      box.appendChild(h("h3", { text: "Sự cố tương tự (" + related.length + ")" }));
      const relWrap = h("div");
      related.forEach(p => relWrap.appendChild(h("div", { class: "explain" }, [
        h("div", { style: "display:flex;gap:8px;align-items:center;" }, [h("strong", { text: p.code }), h("span", { class: "cell-sub", text: "Khớp: " + p.matched_criteria.join(", ") })]),
        h("button", { class: "btn btn-ghost btn-sm", text: "Mở hồ sơ cũ", onclick: () => navigate("incidents/" + p.incident_id) }),
        h("div", { class: "cell-sub", style: "margin-top:4px;", text: "Nguyên nhân cũ chỉ để tham khảo; không tự áp dụng cho sự cố hiện tại." }),
      ])));
      box.appendChild(relWrap);
    }

    const impacts = r.impacts || [], hypotheses = r.hypotheses || [], actions = r.actions || [];
    box.appendChild(h("h3", { text: "Ảnh hưởng (" + impacts.length + ")" }));
    const impWrap = h("div");
    if (!impacts.length) impWrap.appendChild(h("p", { class: "cell-sub", text: "Không phát hiện ảnh hưởng lan truyền nào trong giới hạn đã đặt." }));
    else impacts.forEach(i => {
      const m = IMPACT_TYPE[i.impact_type] || [i.impact_type, "gray"];
      const ex = h("div", { class: "explain", style: "display:none;" }, [
        h("div", { class: "kv" }, [h("span", { text: "Bằng chứng: " + (i.evidence || "—") }), i.rule_id ? h("span", { text: "Quy tắc: " + i.rule_id }) : null]),
        i.evidence_status ? h("div", { class: "cell-sub", text: "Trạng thái bằng chứng: " + i.evidence_status }) : null,
        i.relation_depth ? h("div", { class: "cell-sub", text: "Độ sâu quan hệ: " + i.relation_depth }) : null,
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
      h("div", { style: "display:flex;justify-content:space-between;gap:8px;align-items:center;flex-wrap:wrap;" }, [
        h("div", {}, [h("div", { text: a.action }), h("div", { class: "cell-sub", text: a.department_name + " · ưu tiên " + a.priority })]),
        a.id ? h("button", { class: "btn btn-sm btn-secondary", text: "Tạo công việc", onclick: () => createTaskFromAction(a, r) }) : null,
      ]),
    ])));
    box.appendChild(actWrap);
    box.appendChild(h("div", { class: "message visible warn", text: "Đây là đề xuất từ quy tắc (không phải xác suất, không phải nguyên nhân đã xác nhận)." }));
  }

  async function createTaskFromAction(a, r) {
    try {
      const payload = { analysis_action_id: a.id, title: a.action, department_id: a.department_id || null, source_analysis_run_id: r.run_id || null, source_incident_id: r.incident_id || null, is_simulated: dataMode === "simulation" };
      const d = await api("/api/tasks/from-action", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      const taskId = d.data && d.data.id;
      toast(d.message + (taskId ? " (#" + taskId + ")" : ""));
      if (taskId) {
        if (window.confirm("Đã tạo công việc #" + taskId + ". Mở danh sách công việc?")) navigate("tasks");
      }
    } catch (e) { toast(e.message, "error"); }
  }

  /* ================================================= bảng gợi ý theo bộ phận */
  function renderActionMatrix() {
    const ctx = activePageCtx;
    const v = $("#view");
    v.textContent = "";
    v.appendChild(h("div", { class: "section-head" }, [h("div", {}, [h("h2", { text: "Bảng gợi ý theo bộ phận" }), h("div", { class: "desc", text: "Hành động đề xuất cho 3 tình huống sự cố, xếp theo bộ phận." })])]));
    const card = h("div", { class: "card" });
    v.appendChild(card);
    const PRIORITY = { HIGH: ["Cao", "red"], MEDIUM: ["Trung bình", "amber"], LOW: ["Thấp", "gray"], CRITICAL: ["Nghiêm trọng", "red"] };
    function pBadge(p) { const m = PRIORITY[p] || [p, "gray"]; return badge(m[0], m[1]); }

    async function runForScenario(s) {
      if (!s.incident) return;
      try {
        await api("/api/analysis/run", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ incident_id: s.incident.id, max_depth: 5, duration_minutes: 15 }) });
        toast("Đã chạy phân tích."); load();
      } catch (e) { toast(e.message, "error"); }
    }

    async function load() {
      card.textContent = ""; card.appendChild(spinner());
      try {
        const d = await api("/api/analysis/action-matrix?simulated=" + (dataMode === "simulation"));
        if (!ctx.isCurrent()) return;
        card.textContent = "";
        const m = d.data;
        const scenarios = m.scenarios || [], departments = m.departments || [], cells = m.cells || [];
        if (!scenarios.length || !departments.length) {
          card.appendChild(emptyBox("matrix", "Chưa có dữ liệu", "Chạy phân tích cho các sự cố để xem hành động theo bộ phận."));
          return;
        }
        const cellMap = {};
        cells.forEach(c => { cellMap[c.department + "|" + c.incident_type] = c.actions; });

        const table = h("table");
        const thead = h("thead");
        const trh = h("tr");
        trh.appendChild(h("th", { text: "Bộ phận" }));
        scenarios.forEach(s => {
          trh.appendChild(h("th", {}, [
            h("div", { text: s.label }),
            s.incident ? h("div", { class: "cell-sub", text: s.incident.code }) : h("div", { class: "cell-sub", text: "—" }),
            s.max_priority ? pBadge(s.max_priority) : null,
            (s.incident && !s.run_id) ? h("button", { class: "btn btn-sm btn-primary", text: "Chạy phân tích", onclick: () => runForScenario(s) }) : null,
          ]));
        });
        thead.appendChild(trh); table.appendChild(thead);

        const tbody = h("tbody");
        departments.forEach(dept => {
          const tr = h("tr");
          tr.appendChild(h("td", {}, [h("strong", { text: dept.name }), h("div", { class: "cell-sub", text: dept.code })]));
          scenarios.forEach(s => {
            const td = h("td");
            if (!s.incident) { td.appendChild(h("span", { class: "cell-sub", text: "—" })); tr.appendChild(td); return; }
            const acts = cellMap[dept.code + "|" + s.type] || [];
            if (!acts.length) { td.appendChild(h("span", { class: "cell-sub", text: "—" })); tr.appendChild(td); return; }
            acts.forEach(a => {
              td.appendChild(h("div", { class: "explain", style: "margin-bottom:6px;" }, [
                h("div", {}, [pBadge(a.priority)]),
                h("div", { text: a.action, style: "margin-top:4px;" }),
                a.id ? h("button", { class: "btn btn-sm btn-secondary", text: "Tạo công việc", onclick: () => createTaskFromAction(a, { run_id: s.run_id, incident_id: s.incident ? s.incident.id : null }) }) : null,
              ]));
            });
            tr.appendChild(td);
          });
          tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        const wrap = h("div", { class: "table-wrap" });
        wrap.appendChild(table);
        card.appendChild(wrap);
      } catch (e) {
        if (!ctx.isCurrent()) return;
        card.textContent = "";
        card.appendChild(errorBox(e.message, load));
      }
    }

    load();
  }
  async function loadHistory() {
    const ctx = activePageCtx;
    const wrap = $("#analysis-history");
    if (!wrap) return;
    wrap.textContent = ""; wrap.appendChild(h("div", { class: "card-title" }, [h("span", { text: "Lịch sử phân tích" })]));
    try {
      const d = await api("/api/analysis/runs?page_size=10");
      if (!ctx.isCurrent()) return;
      const list = h("div");
      if (!d.data.items.length) list.appendChild(h("p", { class: "cell-sub", text: "Chưa có lần phân tích nào." }));
      else d.data.items.forEach(r => list.appendChild(h("div", { class: "explain", style: "display:flex;justify-content:space-between;align-items:center;" }, [
        h("span", { text: "#" + r.id + " — " + r.source_type + " " + r.source_id + " · " + fmt(r.run_at) }),
        h("button", { class: "btn btn-ghost btn-sm", text: "Xem", onclick: () => viewRun(r.id) }),
      ])));
      wrap.appendChild(list);
    } catch (e) {
      if (!ctx.isCurrent()) return;
      wrap.appendChild(h("p", { class: "cell-sub", text: "Không tải được lịch sử phân tích." }));
    }
  }
  async function viewRun(id) {
    const ctx = activePageCtx;
    try {
      const d = await api("/api/analysis/runs/" + id);
      if (!ctx.isCurrent()) return;
      renderAnalysisResult(d.data);
    } catch (e) { if (ctx.isCurrent()) toast(e.message, "error"); }
  }

  /* ============================================================ tasks */
  async function renderTasks() {
    const ctx = activePageCtx;
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
    let loadSeq = 0;
    async function load() {
      const mySeq = ++loadSeq;
      listWrap.textContent = ""; listWrap.appendChild(spinner());
      try {
        const q = new URLSearchParams({ page: st.page, page_size: 20 });
        if (deptSel.value) q.set("department_id", deptSel.value);
        if (statusSel.value) q.set("status", statusSel.value);
        const d = await api("/api/tasks?" + q);
        if (!ctx.isCurrent() || mySeq !== loadSeq) return;
        listWrap.textContent = "";
        pag.textContent = "";
        if (!d.data.items.length) {
          if (deptSel.value || statusSel.value) listWrap.appendChild(emptyBox("search", "Không có công việc phù hợp", "Thử thay đổi bộ lọc.",
            h("button", { class: "btn btn-secondary btn-sm", text: "Xóa bộ lọc", onclick: () => { deptSel.value = ""; statusSel.value = ""; st.page = 1; load(); } })));
          else listWrap.appendChild(emptyBox("tasks", "Không có công việc", "Công việc được tạo từ đề xuất phân tích hoặc thêm thủ công."));
          return;
        }
        renderTable(listWrap, [
          { key: "title", label: "Công việc" }, { key: "department_id", label: "Bộ phận" },
          { key: "priority", label: "Ưu tiên" }, { key: "status", label: "Trạng thái", render: (r) => statusBadge(r.status) },
          { key: "source_incident_id", label: "Sự cố", render: (r) => r.source_incident_id ? ("#" + r.source_incident_id) : "—" },
        ], d.data.items, (row) => h("td", {}, [h("select", { onchange: (e) => setStatus(row, e.target) }, [
          h("option", { value: "TODO", selected: row.status === "TODO", text: "Cần làm" }),
          h("option", { value: "IN_PROGRESS", selected: row.status === "IN_PROGRESS", text: "Đang làm" }),
          h("option", { value: "DONE", selected: row.status === "DONE", text: "Hoàn thành" }),
          h("option", { value: "DISMISSED", selected: row.status === "DISMISSED", text: "Bỏ qua" }),
        ])]));
        st.tp = d.data.pagination.total_pages; pagination(pag, st.page, st.tp, (p) => { st.page = p; load(); });
      } catch (e) { if (!ctx.isCurrent() || mySeq !== loadSeq) return; listWrap.textContent = ""; listWrap.appendChild(errorBox(e.message, load)); }
    }
    async function setStatus(row, sel) {
      sel.disabled = true;
      try {
        await api("/api/tasks/" + row.id + "/status", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status: sel.value }) });
        toast("Đã cập nhật."); load();
      } catch (e) {
        sel.value = row.status;
        sel.disabled = false;
        toast(e.message, "error");
      }
    }
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
    const ctx = activePageCtx;
    const v = $("#view");
    v.textContent = "";
    v.appendChild(h("div", { class: "section-head" }, [h("div", {}, [h("h2", { text: "Kịch bản mô phỏng" }), h("div", { class: "desc", text: "Thử tình huống với dữ liệu mô phỏng (tách khỏi dữ liệu vận hành)." })])]));
    const card = h("div", { class: "card" });
    v.appendChild(card);
    card.appendChild(h("div", { class: "message visible warn", text: "Dữ liệu mô phỏng — chưa xác nhận bởi Denso. Không trộn với dữ liệu vận hành." }));
    const toolbar = h("div", { class: "toolbar" });
    toolbar.appendChild(h("button", { class: "btn btn-primary", text: "Nạp dữ liệu mô phỏng", onclick: loadDemo }));
    const st = h("span", { class: "cell-sub" });
    toolbar.appendChild(st);
    card.appendChild(toolbar);

    // Hành động nhanh sau khi nạp.
    const quick = h("div", { class: "explain", style: "margin-bottom:12px;display:none;" });
    quick.appendChild(h("div", { style: "display:flex;gap:12px;align-items:center;flex-wrap:wrap;" }, [
      h("button", { class: "btn btn-primary btn-sm", text: "Xem Bản đồ liên kết", onclick: () => navigate("map") }),
      h("span", { class: "cell-sub", text: "Bước kế tiếp: Ghi nhận máy M10 dừng (Ghi nhận dữ liệu → Trạng thái máy)." }),
    ]));
    card.appendChild(quick);

    const list = h("div", { class: "grid grid-3" });
    const info = await api("/api/scenarios");
    if (!ctx.isCurrent()) return;
    info.data.forEach(s => list.appendChild(h("div", { class: "card" }, [
      h("div", { class: "card-title" }, [h("span", { text: s.title.replace(/^Kịch bản \d: /, "") }), badge("Mô phỏng", "amber")]),
      h("p", { class: "cell-sub", text: "Sự cố: " + s.incident_code }),
      h("p", { text: s.expected, style: "font-size:13px;" }),
      h("p", { class: "cell-sub", text: "Giới hạn: " + s.limits }),
      h("button", { class: "btn btn-secondary btn-sm", text: "Chạy kịch bản này", onclick: () => analyzeByCode(s.incident_code) }),
    ])));
    card.appendChild(list);
    const status = await api("/api/scenarios/d3/status");
    if (!ctx.isCurrent()) return;
    if (status.data.loaded) {
      st.textContent = "Đã nạp.";
      quick.style.display = "";
    } else {
      st.textContent = "Chưa nạp.";
    }
  }
  async function loadDemo() {
    try {
      const d = await api("/api/scenarios/d3/load", { method: "POST" });
      toast(d.data.message);
      if (d.data.credentials && Object.keys(d.data.credentials).length) {
        showCredentialsModal(d.data.credentials);
      }
      renderScenarios();
    } catch (e) { toast(e.message, "error"); }
  }
  function showCredentialsModal(creds) {
    const box = h("div", {});
    box.appendChild(h("p", { text: "Tài khoản demo (mật khẩu chỉ hiện một lần — hãy ghi lại):" }));
    renderTable(box, [
      { key: "username", label: "Tên đăng nhập" },
      { key: "password", label: "Mật khẩu" },
      { key: "roles", label: "Vai trò", render: (r) => (r.roles || []).join(", ") },
    ], Object.keys(creds).map(u => ({ username: u, password: creds[u].password, roles: creds[u].roles })));
    openModal("Tài khoản demo", box);
  }
  async function analyzeByCode(code) {
    const d = await api("/api/incidents?page_size=100");
    const inc = d.data.items.find(i => i.code === code);
    if (!inc) { toast("Chưa nạp dữ liệu mô phỏng hoặc không thấy sự cố " + code + ".", "error"); return; }
    navigate("analysis?incident=" + inc.id);
  }

  /* ============================================================ survey */
  async function renderSurvey() {
    const ctx = activePageCtx;
    const v = $("#view");
    v.textContent = "";
    v.appendChild(h("div", { class: "section-head" }, [h("div", {}, [h("h2", { text: "Khảo sát & xác nhận" }), h("div", { class: "desc", text: "Theo dõi các thông tin cần xác nhận với nhà máy." })])]));
    const groups = await api("/api/survey/groups");
    if (!ctx.isCurrent()) return;
    const items = await api("/api/survey");
    if (!ctx.isCurrent()) return;
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

  /* ============================================================ users (admin) */
  async function renderUsers() {
    const ctx = activePageCtx;
    const v = $("#view");
    v.textContent = "";
    v.appendChild(h("div", { class: "section-head" }, [h("div", {}, [h("h2", { text: "Tài khoản & quyền" }), h("div", { class: "desc", text: "Quản lý tài khoản local và vai trò. Mật khẩu được băm; không lưu dạng văn bản." })])]));
    const card = h("div", { class: "card" });
    v.appendChild(card);
    const toolbar = h("div", { class: "toolbar" });
    const listWrap = h("div");
    toolbar.appendChild(h("button", { class: "btn btn-primary", text: "Tạo tài khoản", onclick: () => userForm() }));
    card.appendChild(toolbar); card.appendChild(listWrap);
    async function load() {
      listWrap.textContent = ""; listWrap.appendChild(spinner());
      try {
        const d = await api("/api/auth/users");
        if (!ctx.isCurrent()) return;
        listWrap.textContent = "";
        if (!d.data.length) { listWrap.appendChild(emptyBox("users", "Chưa có tài khoản", "Tạo tài khoản đầu tiên bằng script hoặc nút bên dưới.")); return; }
        renderTable(listWrap, [
          { key: "username", label: "Tên đăng nhập" }, { key: "display_name", label: "Tên hiển thị" },
          { key: "roles", label: "Vai trò", render: (r) => (r.roles || []).map(x => badge(x, "blue")).reduce((f, b) => { if (f) f.appendChild(document.createTextNode(" ")); f.appendChild(b); return f; }, h("span", {})) },
          { key: "active", label: "Trạng thái", render: (r) => r.active ? badge("Hoạt động", "green") : badge("Đã khóa", "red") },
        ], d.data, (row) => h("td", {}, [
          h("button", { class: "btn btn-sm btn-secondary", text: row.active ? "Khóa" : "Mở khóa", onclick: () => toggleActive(row) }),
        ]));
      } catch (e) { listWrap.textContent = ""; listWrap.appendChild(errorBox(e.message, load)); }
    }
    async function toggleActive(row) {
      try { await api("/api/auth/users/" + row.id + "/active", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ active: !row.active }) }); toast("Đã cập nhật."); load(); }
      catch (e) { toast(e.message, "error"); }
    }
    function userForm() {
      const fields = [
        { name: "username", label: "Tên đăng nhập", required: true },
        { name: "display_name", label: "Tên hiển thị", required: true },
        { name: "password", label: "Mật khẩu", required: true },
        { name: "roles", label: "Vai trò (phân tách bởi dấu phẩy)", hint: "OPERATOR, HANDLER, COORDINATOR, ADMIN" },
      ];
      const fb = formBuilder(fields, async (data, s) => {
        fb.setSubmitting(true);
        try {
          const roles = (data.roles || "").split(",").map(x => x.trim()).filter(Boolean);
          await api("/api/auth/users", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username: data.username, display_name: data.display_name, password: data.password, roles }) });
          closeModal(); toast("Đã tạo tài khoản."); load();
        } catch (e) { toast(e.message, "error"); fb.setSubmitting(false); }
      });
      openModal("Tạo tài khoản", fb.form);
    }
    load();
  }

  /* ============================================================ dashboard */
  const pageState = {};
  let dataMode = localStorage.getItem("d3.mode") || "operations";
  async function renderDashboard() {
    const ctx = activePageCtx;
    const v = $("#view");
    v.textContent = "";
    v.appendChild(spinner());
    let d;
    try { d = await api("/api/dashboard?simulated=" + (dataMode === "simulation")); } catch (e) { if (!ctx.isCurrent()) return; v.textContent = ""; v.appendChild(errorBox(e.message, renderDashboard)); return; }
    if (!ctx.isCurrent()) return;
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
        { key: "department_name", label: "Bộ phận" }, { key: "start_time", label: "Bắt đầu", render: (r) => r.start_time ? fmtDate(r.start_time) : "—" },
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

  /* ============================================================ auth */
  let currentUser = null;

  function showLogin() {
    $("#login-screen").classList.remove("hidden");
    const el = $("#login-error"); el.classList.add("hidden"); el.textContent = "";
  }
  function hideLogin() { $("#login-screen").classList.add("hidden"); }
  function userHasRole(role) { return currentUser && currentUser.roles && currentUser.roles.includes(role); }

  async function initAuth() {
    try {
      const d = await api("/api/auth/me");
      currentUser = d.data;
      $("#user-name").textContent = currentUser.display_name + " · " + (currentUser.roles || []).join(", ");
      hideLogin();
      buildSidebar();
      renderRoute();
    } catch (e) { showLogin(); }
  }

  $("#login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const un = $("#login-username").value.trim();
    const pw = $("#login-password").value;
    const btn = $(".login-submit");
    btn.disabled = true; btn.textContent = "Đang đăng nhập...";
    try {
      const d = await api("/api/auth/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username: un, password: pw }) });
      currentUser = d.data;
      $("#user-name").textContent = currentUser.display_name + " · " + (currentUser.roles || []).join(", ");
      hideLogin();
      buildSidebar();
      renderRoute();
    } catch (err) {
      const el = $("#login-error"); el.textContent = err.message; el.classList.remove("hidden");
    }
    btn.disabled = false; btn.textContent = "Đăng nhập";
  });

  $("#logout-btn").addEventListener("click", async () => {
    try { await api("/api/auth/logout", { method: "POST" }); } catch (e) {}
    currentUser = null;
    $("#user-name").textContent = "";
    showLogin();
  });

  /* ============================================================ router */
  const ROUTES = {
    dashboard: { title: "Trung tâm vận hành", group: "Tổng quan", icon: "dashboard", render: renderDashboard },
    operations: { title: "Ghi nhận dữ liệu", group: "Vận hành", icon: "operations", render: renderOperations },
    incidents: { title: "Sự cố", group: "Vận hành", icon: "incidents", render: renderIncidents },
    tasks: { title: "Công việc theo bộ phận", group: "Vận hành", icon: "tasks", render: renderTasks },
    map: { title: "Bản đồ liên kết", group: "Phân tích", icon: "map", render: renderMap },
    analysis: { title: "Phân tích tác động", group: "Phân tích", icon: "analysis", render: renderAnalysis },
    matrix: { title: "Bảng gợi ý theo bộ phận", group: "Phân tích", icon: "matrix", render: renderActionMatrix },
    scenarios: { title: "Kịch bản mô phỏng", group: "Phân tích", icon: "scenarios", render: renderScenarios },
    catalog: { title: "Danh mục sản xuất", group: "Thiết lập dữ liệu", icon: "catalog", render: renderCatalog },
    system: { title: "Nguồn dữ liệu & ánh xạ", group: "Thiết lập dữ liệu", icon: "system", render: renderSystem },
    survey: { title: "Khảo sát & xác nhận", group: "Thiết lập dữ liệu", icon: "survey", render: renderSurvey },
    users: { title: "Tài khoản & quyền", group: "Thiết lập dữ liệu", icon: "users", render: renderUsers, adminOnly: true },
  };

  function buildSidebar() {
    const wrap = $("#sidebar-groups");
    wrap.textContent = "";
    const groups = {};
    Object.keys(ROUTES).forEach(r => {
      if (ROUTES[r].adminOnly && !userHasRole("ADMIN")) return;
      const g = ROUTES[r].group; (groups[g] = groups[g] || []).push(r);
    });
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

  function currentHash() { return location.hash.replace(/^#\/?/, ""); }

  function navigate(path) {
    if (currentHash() === path) return;
    if (modalDirty && !window.confirm("Có thay đổi chưa lưu trong form. Bỏ thay đổi và chuyển trang?")) return;
    location.hash = "#/" + path;
  }

  function renderNotFound() {
    const v = $("#view");
    v.textContent = "";
    v.appendChild(emptyBox("empty", "Không tìm thấy trang",
      "URL không hợp lệ. Chọn một mục từ menu bên trái.",
      h("button", { class: "btn btn-primary btn-sm", text: "Về trung tâm vận hành", onclick: () => navigate("dashboard") })));
  }

  function renderForbidden() {
    const v = $("#view");
    v.textContent = "";
    v.appendChild(emptyBox("alert", "Không có quyền truy cập",
      "Tài khoản hiện tại không được phép mở trang này.", null));
  }

  function renderRoute() {
    if (!currentUser) { showLogin(); return; }
    const { parts, params } = parseHash();
    const route = parts[0] || "dashboard";
    const cfg = ROUTES[route];
    $("#page-title").textContent = cfg ? cfg.title : "Không tìm thấy trang";
    $$(".nav-item").forEach(a => a.classList.toggle("active", a.dataset.route === route));
    $("#sidebar").classList.remove("open");
    removeBackdrop();
    activePageCtx = createPageContext();
    const pageCtx = activePageCtx;
    const v = $("#view");
    v.textContent = ""; v.appendChild(spinner());
    if (!cfg) { renderNotFound(); return; }
    if (cfg.adminOnly && !userHasRole("ADMIN")) { renderForbidden(); return; }
    try {
      const result = cfg.render({ parts, params });
      if (result && typeof result.then === "function") {
        result.catch((err) => {
          if (!pageCtx.isCurrent()) return;
          if (err && err.status === 401) return;
          v.textContent = "";
          v.appendChild(errorBox((err && err.message) || "Không tải được trang.", () => renderRoute()));
        });
      }
    } catch (err) {
      if (!pageCtx.isCurrent()) return;
      v.textContent = "";
      v.appendChild(errorBox((err && err.message) || "Lỗi khi hiển thị trang.", () => renderRoute()));
    }
  }

  /* header controls */
  $("#nav-toggle").addEventListener("click", () => { $("#sidebar").classList.toggle("open"); toggleBackdrop(); });
  $("#collapse-toggle").addEventListener("click", () => { document.body.classList.toggle("sidebar-collapsed"); });
  $("#header-record").addEventListener("click", () => navigate("operations"));
  $("#header-incident").addEventListener("click", () => {
    const { parts } = parseHash();
    if (parts[0] === "incidents" && !parts[1] && incidentFormOpener) {
      incidentFormOpener();
    } else {
      navigate("incidents?new=1");
    }
  });
  function setMode(mode) {
    dataMode = mode; localStorage.setItem("d3.mode", mode);
    $$(".mode-btn").forEach(b => b.classList.toggle("active", b.dataset.mode === mode));
    const modeLabel = mode === "simulation" ? "Mô phỏng" : "Vận hành";
    $("#mode-label").textContent = modeLabel;
    // Áp dụng lại toàn bộ trang hiện tại (đồng bộ scope/dữ liệu/bộ đếm).
    renderRoute();
  }
  $$(".mode-btn").forEach(b => b.addEventListener("click", () => setMode(b.dataset.mode)));
  const modeLabelBtn = $("#mode-label");
  if (modeLabelBtn) modeLabelBtn.addEventListener("click", () => setMode(dataMode === "simulation" ? "operations" : "simulation"));
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
  window.addEventListener("beforeunload", (e) => {
    if (modalDirty) {
      e.preventDefault();
      e.returnValue = "";
    }
  });
  initAuth();
})();
