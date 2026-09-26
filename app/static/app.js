"use strict";

(function () {
  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

  // ---------- helpers ----------
  function h(tag, props, children) {
    const node = document.createElement(tag);
    if (props) {
      for (const k in props) {
        const v = props[k];
        if (v === undefined || v === null) continue;
        if (k === "text") node.textContent = v;
        else if (k === "class") node.className = v;
        else if (k === "html") node.innerHTML = v; // chỉ dùng cho nội dung tĩnh tin cậy
        else if (k === "value") node.value = v;
        else if (k === "style") node.setAttribute("style", v);
        else if (k === "checked" || k === "disabled" || k === "selected" || k === "readonly" || k === "required") { if (v) node.setAttribute(k, ""); }
        else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
        else node.setAttribute(k, v);
      }
    }
    if (children !== undefined) {
      (Array.isArray(children) ? children : [children]).forEach((c) => {
        if (c === null || c === undefined) return;
        node.appendChild(typeof c === "string" || typeof c === "number" ? document.createTextNode(c) : c);
      });
    }
    return node;
  }

  async function api(path, opts) {
    const resp = await fetch(path, opts);
    let body = null;
    try { body = await resp.json(); } catch (e) { /* ignore */ }
    if (!resp.ok) {
      const msg = body && body.detail ? (typeof body.detail === "string" ? body.detail : "Dữ liệu không hợp lệ.") : (body && body.message) || ("Lỗi " + resp.status);
      const err = new Error(msg);
      err.status = resp.status;
      throw err;
    }
    return body;
  }

  function toast(msg, type) {
    const t = $("#toast");
    t.textContent = msg;
    t.className = "toast visible " + (type || "success");
    clearTimeout(t._timer);
    t._timer = setTimeout(() => { t.className = "toast"; }, 4000);
  }

  function showMsg(el, msg, type) {
    el.textContent = msg;
    el.className = "message visible " + (type || "info");
  }
  function hideMsg(el) { el.className = "message"; }

  function openModal(title, bodyNode) {
    $("#modal-title").textContent = title;
    const body = $("#modal-body");
    body.textContent = "";
    body.appendChild(bodyNode);
    $("#modal").classList.remove("hidden");
  }
  function closeModal() { $("#modal").classList.add("hidden"); }
  $("#modal-close").addEventListener("click", closeModal);
  $("#modal").addEventListener("click", (e) => { if (e.target.id === "modal") closeModal(); });

  function field(label, control, required) {
    const wrap = h("div", { class: "field" });
    wrap.appendChild(h("label", { text: label + (required ? " *" : "") }));
    wrap.appendChild(control);
    return wrap;
  }
  function textInput(name, value, type) {
    const i = h("input", { name, value: value || "", type: type || "text" });
    return i;
  }
  function selectInput(name, options, value) {
    const s = h("select", { name });
    s.appendChild(h("option", { value: "", text: "-- Chọn --" }));
    options.forEach((o) => s.appendChild(h("option", { value: o.value, text: o.label, selected: String(o.value) === String(value) })));
    return s;
  }
  function checkbox(name, checked) {
    return h("input", { name, type: "checkbox", checked: !!checked });
  }

  function formBuilder(fields, onSubmit, initial) {
    const form = h("form", { class: "grid grid-2" });
    const controls = {};
    fields.forEach((f) => {
      let control;
      if (f.type === "select") control = selectInput(f.name, f.options || [], initial && initial[f.name]);
      else if (f.type === "checkbox") control = checkbox(f.name, initial ? !!initial[f.name] : f.default === true);
      else if (f.type === "textarea") { control = h("textarea", { name, rows: 2 }); control.value = (initial && initial[f.name]) || ""; }
      else control = textInput(f.name, initial && initial[f.name], f.type === "number" ? "number" : (f.type === "date" ? "date" : (f.type === "datetime" ? "datetime-local" : "text")));
      controls[f.name] = control;
      form.appendChild(field(f.label, control, f.required));
    });
    const actions = h("div", { class: "grid grid-2", style: "grid-column: span 2;" });
    const submit = h("button", { type: "submit", class: "btn btn-primary", text: "Lưu" });
    const cancel = h("button", { type: "button", class: "btn btn-secondary", text: "Hủy", onclick: closeModal });
    actions.appendChild(submit);
    actions.appendChild(cancel);
    form.appendChild(actions);
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const data = {};
      fields.forEach((f) => {
        const c = controls[f.name];
        let v = c.type === "checkbox" ? c.checked : (c.value === "" ? null : c.value);
        if (f.type === "number" && v !== null) v = Number(v);
        data[f.name] = v;
      });
      onSubmit(data, submit);
    });
    return { form, setSubmitting: (flag) => { submit.disabled = flag; submit.textContent = flag ? "Đang lưu..." : "Lưu"; } };
  }

  function renderTable(container, columns, rows, actionFor) {
    container.textContent = "";
    if (!rows || rows.length === 0) {
      container.appendChild(h("p", { class: "empty", text: "Không có dữ liệu." }));
      return;
    }
    const table = h("table");
    const thead = h("thead");
    const trHead = h("tr");
    columns.forEach((c) => trHead.appendChild(h("th", { text: c.label })));
    if (actionFor) trHead.appendChild(h("th", { text: "" }));
    thead.appendChild(trHead);
    table.appendChild(thead);
    const tbody = h("tbody");
    rows.forEach((row) => {
      const tr = h("tr");
      columns.forEach((c) => {
        const td = h("td");
        const val = c.render ? c.render(row) : row[c.key];
        if (c.cell === "html") td.innerHTML = val == null ? "" : String(val);
        else td.textContent = val == null ? "" : String(val);
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

  function statusBadge(status) {
    const map = { OPEN: "badge-red", RESOLVED: "badge-green", INVESTIGATING: "badge-amber", MITIGATING: "badge-blue", TODO: "badge-gray", IN_PROGRESS: "badge-blue", DONE: "badge-green", DISMISSED: "badge-gray" };
    return h("span", { class: "badge " + (map[status] || "badge-gray"), text: status });
  }
  function boolBadge(v) {
    return v ? h("span", { class: "badge badge-amber", text: "Mô phỏng" }) : h("span", { class: "badge badge-green", text: "Thực" });
  }

  // ---------- navigation ----------
  const sections = ["dashboard", "catalog", "system", "operations", "incidents", "map", "analysis", "tasks", "scenarios", "survey"];
  const current = { page: {} };

  function navigate(name) {
    sections.forEach((s) => {
      $("#section-" + s).classList.toggle("active", s === name);
      $('.sidebar a[data-section="' + s + '"]').classList.toggle("active", s === name);
    });
    $("#sidebar").classList.remove("open");
    const render = { dashboard: renderDashboard, catalog: renderCatalog, system: renderSystem, operations: renderOperations, incidents: renderIncidents, map: renderMap, analysis: renderAnalysis, tasks: renderTasks, scenarios: renderScenarios, survey: renderSurvey }[name];
    if (render) render();
  }
  $$(".sidebar a").forEach((a) => a.addEventListener("click", (e) => { e.preventDefault(); navigate(a.dataset.section); }));
  $("#nav-toggle").addEventListener("click", () => $("#sidebar").classList.toggle("open"));

  // ---------- catalog ----------
  const CATALOG_KEYS = [];
  async function loadCatalogKeys() {
    if (CATALOG_KEYS.length) return CATALOG_KEYS;
    const d = await api("/api/catalog/keys");
    d.data.forEach((k) => CATALOG_KEYS.push(k));
    return CATALOG_KEYS;
  }

  async function loadOptions(key) {
    const d = await api("/api/catalog/" + key + "?page_size=100");
    return d.data.items.map((r) => ({ value: r.id, label: r.code + " - " + r.name }));
  }

  const CATALOG_EXTRA = {
    department: [],
    line: [{ name: "department_id", label: "Bộ phận", type: "select", optionsKey: "department" }],
    process: [{ name: "line_id", label: "Chuyền", type: "select", optionsKey: "line" }],
    machine: [{ name: "department_id", label: "Bộ phận", type: "select", optionsKey: "department" }],
    material: [{ name: "unit", label: "Đơn vị tính", type: "text" }, { name: "department_id", label: "Bộ phận", type: "select", optionsKey: "department" }],
    product: [{ name: "department_id", label: "Bộ phận", type: "select", optionsKey: "department" }],
    order: [{ name: "product_id", label: "Sản phẩm", type: "select", optionsKey: "product" }, { name: "status", label: "Trạng thái", type: "text" }],
    lot: [{ name: "production_order_id", label: "Lệnh sản xuất", type: "select", optionsKey: "order" }],
    shift: [],
  };

  async function renderCatalog() {
    const sec = $("#section-catalog");
    sec.textContent = "";
    const keys = await loadCatalogKeys();
    const tabs = h("div", { class: "tabs" });
    const listWrap = h("div");
    const pag = h("div", { class: "pagination" });
    const msg = h("div", { class: "message" });
    sec.appendChild(h("div", { class: "card" }, [
      h("h2", { text: "Danh mục nghiệp vụ sản xuất" }),
      tabs, h("div", { class: "toolbar" }, [h("button", { class: "btn btn-primary", text: "+ Thêm mới", onclick: () => openCatalogForm(null) })]),
      listWrap, pag, msg,
    ]));

    const state = { key: "department", page: 1, totalPages: 1 };
    function selectKey(key) { state.key = key; state.page = 1; loadList(); }
    async function loadList() {
      hideMsg(msg);
      const d = await api("/api/catalog/" + state.key + "?page=" + state.page + "&page_size=15");
      const columns = [
        { key: "id", label: "ID" }, { key: "code", label: "Mã" }, { key: "name", label: "Tên" },
        { key: "active", label: "Trạng thái", render: (r) => (r.active ? "Hoạt động" : "Ngừng") },
        { key: "is_simulated", label: "Loại", render: (r) => r.is_simulated ? "Mô phỏng" : "Thực" },
      ];
      renderTable(listWrap, columns, d.data.items, (row) => h("td", {}, [
        h("button", { class: "btn btn-sm btn-secondary", text: "Sửa", onclick: () => openCatalogForm(row) }),
        h("button", { class: "btn btn-sm btn-link", text: "Ngừng", onclick: () => deactivate(row) }),
      ]));
      state.totalPages = d.data.pagination.total_pages;
      pagination(pag, state.page, state.totalPages, (p) => { state.page = p; loadList(); });
    }
    async function deactivate(row) {
      if (!confirm("Ngừng sử dụng '" + row.code + "'?")) return;
      try { await api("/api/catalog/" + state.key + "/" + row.id + "/deactivate", { method: "POST" }); toast("Đã ngừng sử dụng."); loadList(); }
      catch (e) { toast(e.message, "error"); }
    }
    async function openCatalogForm(row) {
      const extra = CATALOG_EXTRA[state.key] || [];
      const fields = [
        { name: "code", label: "Mã", required: true },
        { name: "name", label: "Tên", required: true },
        { name: "description", label: "Mô tả", type: "textarea" },
        { name: "active", label: "Đang hoạt động", type: "checkbox", default: true },
        { name: "is_simulated", label: "Dữ liệu mô phỏng", type: "checkbox" },
      ];
      for (const f of extra) {
        if (f.optionsKey) { const opts = await loadOptions(f.optionsKey); fields.push({ name: f.name, label: f.label, type: "select", options: opts }); }
        else fields.push({ name: f.name, label: f.label, type: f.type || "text" });
      }
      const initial = row || { active: true };
      const fb = formBuilder(fields, async (data, submit) => {
        fb.setSubmitting(true);
        try {
          if (row) await api("/api/catalog/" + state.key + "/" + row.id, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
          else await api("/api/catalog/" + state.key, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
          closeModal(); toast("Đã lưu."); loadList();
        } catch (e) { toast(e.message, "error"); fb.setSubmitting(false); }
      }, initial);
      openModal((row ? "Sửa " : "Thêm ") + (keys.find(k => k.key === state.key) || {}).label, fb.form);
    }
    keys.forEach((k) => tabs.appendChild(h("button", { class: k.key === state.key ? "active" : "", text: k.label, onclick: (e) => { $$("button", tabs).forEach(b => b.classList.remove("active")); e.target.classList.add("active"); selectKey(k.key); } })));
    loadList();
  }

  // ---------- system ----------
  async function renderSystem() {
    const sec = $("#section-system");
    sec.textContent = "";
    const tabs = h("div", { class: "tabs" });
    const body = h("div");
    sec.appendChild(h("div", { class: "card" }, [h("h2", { text: "Nguồn dữ liệu & liên kết hệ thống" }), tabs, body]));

    const views = { sources: viewSources, datasets: viewDatasets, fields: viewFields, flows: viewFlows };
    let active = "sources";
    function setView(k) {
      active = k; $$("button", tabs).forEach(b => b.classList.toggle("active", b.dataset.v === k));
      body.textContent = ""; views[k](body);
    }
    Object.keys(views).forEach((k) => tabs.appendChild(h("button", { "data-v": k, class: k === active ? "active" : "", text: { sources: "Hệ thống nguồn", datasets: "Dataset", fields: "Trường dữ liệu", flows: "Luồng dữ liệu" }[k], onclick: () => setView(k) })));
    setView(active);
  }

  async function viewSources(body) {
    const pag = h("div", { class: "pagination" }); const listWrap = h("div"); const msg = h("div", { class: "message" });
    body.appendChild(h("div", { class: "toolbar" }, [h("button", { class: "btn btn-primary", text: "+ Thêm nguồn", onclick: () => sourceForm(null) })]));
    body.appendChild(listWrap); body.appendChild(pag); body.appendChild(msg);
    const state = { page: 1, tp: 1 };
    async function load() {
      hideMsg(msg);
      const d = await api("/api/system/sources?page=" + state.page + "&page_size=15");
      renderTable(listWrap, [
        { key: "code", label: "Mã" }, { key: "name", label: "Tên" }, { key: "source_type", label: "Loại" },
        { key: "collection_method", label: "Thu thập" }, { key: "confirmed", label: "Xác nhận", render: (r) => r.confirmed ? "Đã xác nhận" : "Chưa xác nhận" },
        { key: "is_simulated", label: "Loại", render: boolBadge },
      ], d.data.items, (row) => h("td", {}, [
        h("button", { class: "btn btn-sm btn-secondary", text: "Sửa", onclick: () => sourceForm(row) }),
        h("button", { class: "btn btn-sm btn-link", text: "Xóa", onclick: () => del("/api/system/sources/" + row.id, load) }),
      ]));
      state.tp = d.data.pagination.total_pages;
      pagination(pag, state.page, state.tp, (p) => { state.page = p; load(); });
    }
    async function del(url, cb) { if (!confirm("Xóa?")) return; try { await api(url, { method: "DELETE" }); toast("Đã xóa."); cb(); } catch (e) { toast(e.message, "error"); } }
    async function sourceForm(row) {
      const deptOpts = await loadOptions("department");
      const fields = [
        { name: "code", label: "Mã", required: true }, { name: "name", label: "Tên", required: true },
        { name: "source_type", label: "Loại nguồn (MES/ERP/PLC/...)", required: true },
        { name: "collection_method", label: "Phương thức thu thập" },
        { name: "owner_department_id", label: "Bộ phận sở hữu", type: "select", options: deptOpts },
        { name: "location_metadata", label: "Vị trí lưu trữ (metadata)", type: "textarea" },
        { name: "confirmed", label: "Đã xác nhận", type: "checkbox" },
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
    const pag = h("div", { class: "pagination" }); const listWrap = h("div"); const msg = h("div", { class: "message" });
    body.appendChild(h("div", { class: "toolbar" }, [h("button", { class: "btn btn-primary", text: "+ Thêm dataset", onclick: () => datasetForm(null) })]));
    body.appendChild(listWrap); body.appendChild(pag); body.appendChild(msg);
    const state = { page: 1, tp: 1 };
    async function load() {
      hideMsg(msg);
      const d = await api("/api/system/datasets?page=" + state.page + "&page_size=15");
      renderTable(listWrap, [
        { key: "code", label: "Mã" }, { key: "name", label: "Tên" },
        { key: "generation_unit", label: "Đơn vị phát sinh" }, { key: "update_schedule", label: "Lịch cập nhật" },
        { key: "confirmed", label: "Xác nhận", render: (r) => r.confirmed ? "Đã xác nhận" : "Chưa" },
      ], d.data.items, (row) => h("td", {}, [
        h("button", { class: "btn btn-sm btn-secondary", text: "Sửa", onclick: () => datasetForm(row) }),
        h("button", { class: "btn btn-sm btn-link", text: "Xóa", onclick: () => { if (confirm("Xóa?")) api("/api/system/datasets/" + row.id, { method: "DELETE" }).then(() => { toast("Đã xóa."); load(); }).catch(e => toast(e.message, "error")); } }),
      ]));
      state.tp = d.data.pagination.total_pages;
      pagination(pag, state.page, state.tp, (p) => { state.page = p; load(); });
    }
    async function datasetForm(row) {
      const srcOpts = (await api("/api/system/sources?page_size=100")).data.items.map(r => ({ value: r.id, label: r.code }));
      const deptOpts = await loadOptions("department");
      const fields = [
        { name: "code", label: "Mã", required: true }, { name: "name", label: "Tên", required: true },
        { name: "source_id", label: "Hệ thống nguồn", type: "select", options: srcOpts },
        { name: "dataset_type", label: "Loại (table/file/endpoint)" },
        { name: "collection_method", label: "Phương thức thu thập" },
        { name: "generation_unit", label: "Đơn vị phát sinh (per_pcs/per_lot/per_event)" },
        { name: "update_schedule", label: "Lịch cập nhật (realtime/per_shift/daily/batch/manual)" },
        { name: "event_time_field", label: "Trường thời gian sự kiện" },
        { name: "timezone", label: "Múi giờ" },
        { name: "owner_department_id", label: "Bộ phận sở hữu", type: "select", options: deptOpts },
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
    const ds = h("div", { class: "toolbar" }); const listWrap = h("div");
    body.appendChild(ds); body.appendChild(listWrap);
    const datasets = (await api("/api/system/datasets?page_size=100")).data.items;
    const sel = selectInput("ds", datasets.map(r => ({ value: r.id, label: r.code })), datasets[0] && datasets[0].id);
    ds.appendChild(field("Dataset", sel));
    ds.appendChild(h("button", { class: "btn btn-primary", text: "+ Thêm trường", onclick: () => fieldForm(sel.value) }));
    async function load() {
      if (!sel.value) { listWrap.textContent = ""; listWrap.appendChild(h("p", { class: "empty", text: "Chưa có dataset." })); return; }
      const d = await api("/api/system/datasets/" + sel.value + "/fields");
      renderTable(listWrap, [
        { key: "code", label: "Mã trường" }, { key: "name", label: "Tên" }, { key: "data_type", label: "Kiểu" },
        { key: "is_key", label: "Khóa", render: (r) => r.is_key ? "Khóa" : "" },
      ], d.data, (row) => h("td", {}, [
        h("button", { class: "btn btn-sm btn-link", text: "Xóa", onclick: () => { if (confirm("Xóa trường?")) api("/api/system/fields/" + row.id, { method: "DELETE" }).then(() => { toast("Đã xóa."); load(); }).catch(e => toast(e.message, "error")); } }),
      ]));
    }
    sel.addEventListener("change", load);
    async function fieldForm(datasetId) {
      const fields = [
        { name: "code", label: "Mã trường", required: true }, { name: "name", label: "Tên", required: true },
        { name: "data_type", label: "Kiểu dữ liệu" }, { name: "is_key", label: "Là khóa liên kết", type: "checkbox" },
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
    const listWrap = h("div"); const msg = h("div", { class: "message" });
    body.appendChild(h("div", { class: "toolbar" }, [h("button", { class: "btn btn-primary", text: "+ Thêm luồng", onclick: () => flowForm(null) })]));
    body.appendChild(listWrap); body.appendChild(msg);
    async function load() {
      hideMsg(msg);
      const d = await api("/api/system/flows?page_size=50");
      renderTable(listWrap, [
        { key: "code", label: "Mã" }, { key: "name", label: "Tên" },
        { key: "source_dataset_id", label: "Nguồn" }, { key: "target_dataset_id", label: "Đích" },
      ], d.data.items, (row) => h("td", {}, [
        h("button", { class: "btn btn-sm btn-link", text: "Xóa", onclick: () => { if (confirm("Xóa?")) api("/api/system/flows/" + row.id, { method: "DELETE" }).then(() => { toast("Đã xóa."); load(); }).catch(e => toast(e.message, "error")); } }),
      ]));
    }
    async function flowForm(row) {
      const datasets = (await api("/api/system/datasets?page_size=100")).data.items;
      const opts = datasets.map(r => ({ value: r.id, label: r.code }));
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

  // ---------- operations ----------
  async function renderOperations() {
    const sec = $("#section-operations");
    sec.textContent = "";
    const tabs = h("div", { class: "tabs" });
    const body = h("div");
    sec.appendChild(h("div", { class: "card" }, [h("h2", { text: "Ghi nhận vận hành" }), tabs, body]));
    const views = { production: viewProduction, states: viewStates, downtimes: viewDowntimes, qc: viewQc, material: viewMaterial };
    const labels = { production: "Sản lượng", states: "Trạng thái máy", downtimes: "Dừng máy", qc: "Kết quả QC", material: "Vật tư" };
    let active = "production";
    function setView(k) { active = k; $$("button", tabs).forEach(b => b.classList.toggle("active", b.dataset.v === k)); body.textContent = ""; views[k](body); }
    Object.keys(views).forEach((k) => tabs.appendChild(h("button", { "data-v": k, class: k === active ? "active" : "", text: labels[k], onclick: () => setView(k) })));
    setView(active);
  }

  function productionForm() {
    const form = h("form", { class: "grid grid-2" });
    const fields = [
      ["production_date", "Ngày sản xuất", "date"], ["shift", "Ca sản xuất", "shift"],
      ["line_code", "Mã chuyền", "text"], ["process_code", "Mã công đoạn", "text"],
      ["product_code", "Mã sản phẩm", "text"], ["lot_code", "Mã lot", "text"],
      ["good_quantity", "Số lượng đạt", "number"], ["defect_quantity", "Số lượng lỗi", "number"],
      ["operator_name", "Người nhập", "text"], ["note", "Ghi chú", "textarea"],
    ];
    const ctrl = {};
    fields.forEach(([name, label, type]) => {
      let c;
      if (name === "shift") c = selectInput(name, ["CA_1", "CA_2", "CA_3"].map(x => ({ value: x, label: x })));
      else if (type === "textarea") c = h("textarea", { name, rows: 2 });
      else c = h("input", { name, type, inputmode: type === "number" ? "numeric" : undefined, min: type === "number" ? 0 : undefined });
      ctrl[name] = c;
      form.appendChild(field(label, c, name !== "note"));
    });
    const summary = h("div", { class: "message info", style: "grid-column: span 2;" });
    function upd() {
      const g = Number(ctrl.good_quantity.value) || 0, d = Number(ctrl.defect_quantity.value) || 0;
      const total = g + d, rate = total ? (d / total * 100) : 0;
      summary.textContent = "Tổng: " + total + "  |  Tỷ lệ lỗi: " + (total ? rate.toFixed(2) : "0") + "%";
      summary.className = "message visible info";
    }
    ctrl.good_quantity.addEventListener("input", upd); ctrl.defect_quantity.addEventListener("input", upd);
    const actions = h("div", { class: "grid grid-2", style: "grid-column: span 2;" });
    const submit = h("button", { type: "submit", class: "btn btn-primary", text: "Gửi dữ liệu" });
    const reset = h("button", { type: "button", class: "btn btn-secondary", text: "Nhập mới", onclick: () => form.reset() });
    actions.appendChild(submit); actions.appendChild(reset);
    form.appendChild(summary); form.appendChild(actions);
    let draftId = uuid();
    form.addEventListener("input", () => { draftId = uuid(); });
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const good = Number(ctrl.good_quantity.value) || 0, defect = Number(ctrl.defect_quantity.value) || 0;
      if (good + defect <= 0) { toast("Tổng sản lượng phải lớn hơn 0.", "error"); return; }
      const payload = {
        request_id: draftId, production_date: ctrl.production_date.value, shift: ctrl.shift.value,
        line_code: ctrl.line_code.value.trim(), process_code: ctrl.process_code.value.trim(),
        product_code: ctrl.product_code.value.trim(), lot_code: ctrl.lot_code.value.trim(),
        good_quantity: good, defect_quantity: defect,
        operator_name: ctrl.operator_name.value.trim(), note: ctrl.note.value.trim() || null,
      };
      submit.disabled = true; submit.textContent = "Đang gửi...";
      try {
        const r = await api("/api/production-records", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
        toast("Đã lưu bản ghi ID " + r.data.id); form.reset(); draftId = uuid();
      } catch (err) { toast(err.message, "error"); }
      submit.disabled = false; submit.textContent = "Gửi dữ liệu";
    });
    return form;
  }

  function viewProduction(body) {
    body.appendChild(productionForm());
    const listWrap = h("div"); body.appendChild(h("h3", { text: "Bản ghi gần nhất" })); body.appendChild(listWrap);
    api("/api/production-records?page_size=10").then(d => renderTable(listWrap, [
      { key: "id", label: "ID" }, { key: "production_date", label: "Ngày" }, { key: "shift", label: "Ca" },
      { key: "line_code", label: "Chuyền" }, { key: "process_code", label: "Công đoạn" }, { key: "lot_code", label: "Lot" },
      { key: "good_quantity", label: "Đạt" }, { key: "defect_quantity", label: "Lỗi" },
    ], d.data.items)).catch(e => {});
  }

  async function viewStates(body) {
    const listWrap = h("div"); const msg = h("div", { class: "message" });
    body.appendChild(h("div", { class: "toolbar" }, [h("button", { class: "btn btn-primary", text: "+ Ghi nhận trạng thái", onclick: () => stateForm(null) })]));
    body.appendChild(listWrap); body.appendChild(msg);
    async function load() {
      hideMsg(msg);
      const d = await api("/api/operations/machine-states?page_size=20");
      renderTable(listWrap, [
        { key: "id", label: "ID" }, { key: "machine_id", label: "Máy" }, { key: "event_time", label: "Thời điểm", render: (r) => fmt(r.event_time) },
        { key: "state", label: "Trạng thái" }, { key: "error_code", label: "Mã lỗi" }, { key: "is_simulated", label: "Loại", render: boolBadge },
      ], d.data.items);
    }
    async function stateForm(row) {
      const machines = await loadOptions("machine");
      const fields = [
        { name: "machine_id", label: "Máy", type: "select", options: machines, required: true },
        { name: "event_time", label: "Thời điểm sự kiện", type: "datetime", required: true },
        { name: "state", label: "Trạng thái", type: "select", options: ["RUNNING", "STOPPED", "MAINTENANCE", "UNKNOWN"].map(x => ({ value: x, label: x })), required: true },
        { name: "error_code", label: "Mã lỗi" }, { name: "note", label: "Ghi chú" },
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
    const listWrap = h("div");
    body.appendChild(h("div", { class: "toolbar" }, [h("button", { class: "btn btn-primary", text: "+ Ghi nhận dừng máy", onclick: () => downtimeForm() })]));
    body.appendChild(listWrap);
    async function load() {
      const d = await api("/api/operations/downtimes?page_size=20");
      renderTable(listWrap, [
        { key: "id", label: "ID" }, { key: "machine_id", label: "Máy" }, { key: "start_time", label: "Bắt đầu", render: (r) => fmt(r.start_time) },
        { key: "end_time", label: "Kết thúc", render: (r) => r.end_time ? fmt(r.end_time) : "Đang dừng" },
        { key: "reason", label: "Lý do" }, { key: "error_code", label: "Mã lỗi" },
      ], d.data.items);
    }
    async function downtimeForm() {
      const machines = await loadOptions("machine");
      const fields = [
        { name: "machine_id", label: "Máy", type: "select", options: machines, required: true },
        { name: "start_time", label: "Bắt đầu", type: "datetime", required: true },
        { name: "end_time", label: "Kết thúc (để trống nếu đang dừng)", type: "datetime" },
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
    const listWrap = h("div");
    body.appendChild(h("div", { class: "toolbar" }, [h("button", { class: "btn btn-primary", text: "+ Ghi nhận QC", onclick: () => qcForm() })]));
    body.appendChild(listWrap);
    async function load() {
      const d = await api("/api/operations/qc?page_size=20");
      renderTable(listWrap, [
        { key: "id", label: "ID" }, { key: "lot_id", label: "Lot" }, { key: "check_time", label: "Thời điểm", render: (r) => fmt(r.check_time) },
        { key: "inspected_qty", label: "Kiểm tra" }, { key: "defect_qty", label: "Lỗi" }, { key: "result", label: "Kết quả", render: (r) => r.result },
      ], d.data.items);
    }
    async function qcForm() {
      const lots = await loadOptions("lot"), products = await loadOptions("product"), procs = await loadOptions("process");
      const fields = [
        { name: "lot_id", label: "Lot", type: "select", options: lots, required: true },
        { name: "product_id", label: "Sản phẩm", type: "select", options: products },
        { name: "process_id", label: "Công đoạn", type: "select", options: procs },
        { name: "check_time", label: "Thời điểm kiểm tra", type: "datetime", required: true },
        { name: "inspected_qty", label: "Số lượng kiểm tra", type: "number", required: true },
        { name: "defect_qty", label: "Số lượng lỗi", type: "number", required: true },
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
    const listWrap = h("div");
    body.appendChild(h("div", { class: "toolbar" }, [h("button", { class: "btn btn-primary", text: "+ Ghi nhận vật tư", onclick: () => matForm() })]));
    body.appendChild(listWrap);
    async function load() {
      const d = await api("/api/operations/material?page_size=20");
      renderTable(listWrap, [
        { key: "id", label: "ID" }, { key: "material_id", label: "Vật tư" }, { key: "recorded_at", label: "Thời điểm", render: (r) => fmt(r.recorded_at) },
        { key: "available_qty", label: "Khả dụng" }, { key: "unit", label: "Đơn vị" }, { key: "scope", label: "Phạm vi" },
      ], d.data.items);
    }
    async function matForm() {
      const materials = await loadOptions("material");
      const fields = [
        { name: "material_id", label: "Vật tư", type: "select", options: materials, required: true },
        { name: "recorded_at", label: "Thời điểm ghi nhận", type: "datetime", required: true },
        { name: "available_qty", label: "Số lượng khả dụng", type: "number", required: true },
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

  function iso(v) { return v ? new Date(v).toISOString() : null; }
  function fmt(v) { if (!v) return ""; const d = new Date(v); return isNaN(d) ? String(v) : d.toLocaleString("vi-VN"); }

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

  // ---------- incidents ----------
  async function renderIncidents() {
    const sec = $("#section-incidents");
    sec.textContent = "";
    const filters = h("div", { class: "toolbar" });
    const listWrap = h("div"); const pag = h("div", { class: "pagination" }); const msg = h("div", { class: "message" });
    const statusSel = selectInput("status", ["OPEN", "INVESTIGATING", "MITIGATING", "RESOLVED"].map(x => ({ value: x, label: x })));
    const typeSel = selectInput("type", ["MACHINE_STOP", "QUALITY", "MATERIAL_SHORTAGE", "DATA_DELAY", "OTHER"].map(x => ({ value: x, label: x })));
    filters.appendChild(field("Trạng thái", statusSel));
    filters.appendChild(field("Loại", typeSel));
    filters.appendChild(h("button", { class: "btn btn-secondary", text: "Lọc", onclick: () => { state.page = 1; load(); } }));
    filters.appendChild(h("button", { class: "btn btn-primary", text: "+ Tạo sự cố", onclick: () => incidentForm(null) }));
    sec.appendChild(h("div", { class: "card" }, [h("h2", { text: "Quản lý sự cố" }), filters, listWrap, pag, msg]));
    const state = { page: 1, tp: 1 };
    async function load() {
      hideMsg(msg);
      const q = new URLSearchParams({ page: state.page, page_size: 15 });
      if (statusSel.value) q.set("status", statusSel.value);
      if (typeSel.value) q.set("incident_type", typeSel.value);
      const d = await api("/api/incidents?" + q);
      renderTable(listWrap, [
        { key: "code", label: "Mã" }, { key: "title", label: "Tiêu đề" }, { key: "incident_type", label: "Loại" },
        { key: "severity", label: "Mức", render: (r) => r.severity }, { key: "status", label: "Trạng thái", render: (r) => statusBadge(r.status) },
        { key: "is_simulated", label: "Loại", render: boolBadge },
      ], d.data.items, (row) => h("td", {}, [
        h("button", { class: "btn btn-sm btn-secondary", text: "Chi tiết", onclick: () => incidentDetail(row.id) }),
        h("button", { class: "btn btn-sm btn-primary", text: "Phân tích", onclick: () => { navigate("analysis"); setTimeout(() => runIncidentAnalysis(row.id), 50); } }),
      ]));
      state.tp = d.data.pagination.total_pages;
      pagination(pag, state.page, state.tp, (p) => { state.page = p; load(); });
    }
    async function incidentForm(row) {
      const depts = await loadOptions("department");
      const fields = [
        { name: "code", label: "Mã sự cố", required: true }, { name: "title", label: "Tiêu đề", required: true },
        { name: "incident_type", label: "Loại", type: "select", options: ["MACHINE_STOP", "QUALITY", "MATERIAL_SHORTAGE", "DATA_DELAY", "OTHER"].map(x => ({ value: x, label: x })), required: true },
        { name: "severity", label: "Mức nghiêm trọng", type: "select", options: ["LOW", "MEDIUM", "HIGH", "CRITICAL"].map(x => ({ value: x, label: x })) },
        { name: "source_object_type", label: "Loại đối tượng phát sinh", type: "select", options: ["machine", "lot", "material", "process", "product", "dataset", "line", "order"].map(x => ({ value: x, label: x })) },
        { name: "source_object_id", label: "ID đối tượng phát sinh", type: "number" },
        { name: "start_time", label: "Bắt đầu", type: "datetime" }, { name: "end_time", label: "Kết thúc", type: "datetime" },
        { name: "assigned_department_id", label: "Bộ phận phụ trách", type: "select", options: depts },
        { name: "status", label: "Trạng thái", type: "select", options: ["OPEN", "INVESTIGATING", "MITIGATING", "RESOLVED"].map(x => ({ value: x, label: x })) },
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
    async function incidentDetail(id) {
      const d = await api("/api/incidents/" + id);
      const inc = d.data;
      const causes = await api("/api/incidents/" + id + "/causes");
      const box = h("div");
      box.appendChild(h("h3", { text: inc.code + " - " + inc.title }));
      box.appendChild(h("p", { text: inc.description || "" }));
      box.appendChild(h("p", { text: "Loại: " + inc.incident_type + " | Trạng thái: " + inc.status + " | Mức: " + inc.severity }));
      box.appendChild(h("h3", { text: "Nguyên nhân" }));
      const causeWrap = h("div");
      box.appendChild(causeWrap);
      function renderCauses() {
        causeWrap.textContent = "";
        causes.data.forEach((c) => causeWrap.appendChild(h("p", { text: (c.kind === "CONFIRMED" ? "[Đã xác nhận] " : "[Giả thuyết] ") + c.content + (c.confirmed_by ? " — " + c.confirmed_by : "") })));
      }
      renderCauses();
      const cf = h("div", { class: "grid grid-2" });
      const content = textInput("content");
      const kind = selectInput("kind", [{ value: "HYPOTHESIS", label: "Giả thuyết" }, { value: "CONFIRMED", label: "Đã xác nhận" }]);
      const confirmBy = textInput("confirmed_by");
      cf.appendChild(field("Nội dung", content)); cf.appendChild(field("Loại", kind));
      cf.appendChild(field("Người xác nhận (nếu CONFIRMED)", confirmBy));
      const addBtn = h("button", { class: "btn btn-primary", text: "Thêm nguyên nhân", onclick: async () => {
        try { await api("/api/incidents/" + id + "/causes", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ content: content.value, kind: kind.value, confirmed_by: confirmBy.value || null }) }); content.value = ""; const c2 = await api("/api/incidents/" + id + "/causes"); causes.data = c2.data; renderCauses(); toast("Đã thêm."); }
        catch (e) { toast(e.message, "error"); }
      } });
      cf.appendChild(addBtn);
      box.appendChild(cf);
      openModal("Chi tiết sự cố", box);
    }
    load();
  }

  // ---------- map ----------
  async function renderMap() {
    const sec = $("#section-map");
    sec.textContent = "";
    const filters = h("div", { class: "toolbar" });
    const wrap = h("div", { class: "graph-wrap" });
    const detail = h("div", { class: "card" });
    sec.appendChild(h("div", { class: "card" }, [h("h2", { text: "Bản đồ liên kết hai lớp" }), filters, wrap]));
    sec.appendChild(detail);

    const meta = await api("/api/graph/meta");
    const typeSel = selectInput("type", meta.data.node_types.map(t => ({ value: t.type, label: t.label })));
    filters.appendChild(field("Loại node", typeSel));
    filters.appendChild(h("button", { class: "btn btn-secondary", text: "Vẽ toàn bộ", onclick: () => draw() }));
    filters.appendChild(h("button", { class: "btn btn-secondary", text: "Vẽ loại đã chọn", onclick: () => draw(typeSel.value) }));

    const kindColor = { production_dependency: "prod", data_flow: "data", data_mapping: "map", department_responsibility: "dept" };
    const legend = h("div", { class: "graph-legend" });
    meta.data.edge_kinds.forEach(k => legend.appendChild(h("span", { text: k.label + " (" + k.kind + ")" })));
    filters.appendChild(legend);

    let selectedType = null;
    async function draw(type) {
      selectedType = type || null;
      wrap.textContent = "";
      const d = await api("/api/graph/map" + (type ? "?types=" + type : ""));
      const nodes = d.data.nodes, edges = d.data.edges;
      if (!nodes.length) { wrap.appendChild(h("p", { class: "empty", text: "Chưa có node. Hãy thêm danh mục hoặc nạp dữ liệu demo." })); return; }
      drawGraph(wrap, nodes, edges, onNodeClick);
    }
    function onNodeClick(node) {
      detail.textContent = "";
      const edges = api("/api/graph/map").then(d => d.data.edges.filter(e => (e.source_type === node.type && e.source_id === node.id) || (e.target_type === node.type && e.target_id === node.id)));
      edges.then(rels => {
        detail.appendChild(h("h2", { text: "Node: " + node.name + " (" + node.type + ")" }));
        const ul = h("ul", { class: "path-list" });
        rels.forEach(e => ul.appendChild(h("li", {}, [h("div", { text: e.source_type + "#" + e.source_id + " -> " + e.target_type + "#" + e.target_id }), h("div", { class: "hop", text: e.kind + (e.label ? " — " + e.label : "") })])));
        if (!rels.length) detail.appendChild(h("p", { text: "Không có quan hệ nào." }));
        detail.appendChild(ul);
      });
    }
    draw();
  }

  function drawGraph(wrap, nodes, edges, onNodeClick) {
    const byType = {};
    nodes.forEach(n => { (byType[n.type] = byType[n.type] || []).push(n); });
    const order = ["department", "machine", "material", "line", "process", "product", "order", "lot", "shift", "source", "dataset", "field"];
    const types = order.filter(t => byType[t]);
    const colW = 130, rowH = 70, padX = 70, padY = 40;
    const pos = {};
    types.forEach((t, ci) => {
      byType[t].forEach((n, ri) => {
        pos[n.type + ":" + n.id] = { x: padX + ci * colW, y: padY + ri * rowH };
      });
    });
    const W = padX * 2 + types.length * colW;
    const H = padY * 2 + Math.max.apply(null, types.map(t => byType[t].length)) * rowH;
    const svg = hNS("svg", { class: "graph-svg", width: W, height: H, xmlns: "http://www.w3.org/2000/svg" });
    edges.forEach(e => {
      const a = pos[e.source_type + ":" + e.source_id], b = pos[e.target_type + ":" + e.target_id];
      if (!a || !b) return;
      svg.appendChild(hNS("line", { class: "edge-line " + ({ production_dependency: "prod", data_flow: "data", data_mapping: "map", department_responsibility: "dept" }[e.kind] || ""), x1: a.x + 55, y1: a.y + 20, x2: b.x + 55, y2: b.y + 20 }));
    });
    nodes.forEach(n => {
      const p = pos[n.type + ":" + n.id];
      const g = hNS("g", { class: "node" });
      const r = hNS("rect", { x: p.x, y: p.y, width: 110, height: 40, rx: 6, fill: n.is_simulated ? "#fff3e0" : "#eaf2fd", stroke: "#b9c0ca" });
      r.addEventListener("click", () => onNodeClick(n));
      const t = hNS("text", { x: p.x + 55, y: p.y + 17, "text-anchor": "middle", fill: "#1f2933" });
      t.textContent = n.name.length > 14 ? n.name.slice(0, 14) + "…" : n.name;
      const s = hNS("text", { x: p.x + 55, y: p.y + 32, "text-anchor": "middle", fill: "#6b7280" });
      s.textContent = n.type;
      g.appendChild(r); g.appendChild(t); g.appendChild(s);
      svg.appendChild(g);
    });
    wrap.appendChild(svg);
  }
  function hNS(tag, attrs) {
    const n = document.createElementNS("http://www.w3.org/2000/svg", tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    return n;
  }

  // ---------- analysis ----------
  async function renderAnalysis() {
    const sec = $("#section-analysis");
    sec.textContent = "";
    const box = h("div", { class: "card" });
    sec.appendChild(h("div", { class: "card" }, [h("h2", { text: "Phân tích tác động & nguyên nhân" }), h("div", { id: "analysis-form" }), h("div", { id: "analysis-result" })]));
    sec.appendChild(h("div", { class: "card" }, [h("h2", { text: "Lịch sử phân tích" }), h("div", { id: "analysis-history" })]));

    const formWrap = $("#analysis-form");
    const incSel = selectInput("incident", []);
    const dur = textInput("duration", "", "number");
    const rate = textInput("rate", "", "number");
    const maxd = textInput("max_depth", "3", "number");
    formWrap.appendChild(h("div", { class: "grid grid-4" }, [
      field("Sự cố", incSel), field("Thời lượng dừng (phút, tùy chọn)", dur),
      field("Tốc độ (pcs/phút, tùy chọn)", rate), field("Số bước lan truyền", maxd),
    ]));
    formWrap.appendChild(h("button", { class: "btn btn-primary", text: "Chạy phân tích", onclick: () => runIncidentAnalysis(incSel.value) }));

    const incidents = await api("/api/incidents?page_size=100");
    incSel.textContent = "";
    incSel.appendChild(h("option", { value: "", text: "-- Chọn --" }));
    incidents.data.items.forEach(i => incSel.appendChild(h("option", { value: i.id, text: i.code + " - " + i.title })));

    loadHistory();
  }

  function runIncidentAnalysis(id) {
    if (!id) { toast("Chọn một sự cố trước.", "error"); return; }
    const dur = $("#analysis-form input[name='duration']").value;
    const rate = $("#analysis-form input[name='rate']").value;
    const maxd = $("#analysis-form input[name='max_depth']").value || "3";
    api("/api/analysis/run", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ incident_id: Number(id), max_depth: Number(maxd), duration_minutes: dur ? Number(dur) : null, rate_per_minute: rate ? Number(rate) : null }) })
      .then(d => renderAnalysisResult(d.data))
      .catch(e => toast(e.message, "error"));
  }

  function renderAnalysisResult(r) {
    const box = $("#analysis-result");
    box.textContent = "";
    box.appendChild(h("h3", { text: "Kết quả (quy tắc: " + r.rules.join(", ") + ", phiên bản " + r.rule_version + ")" }));
    if (r.quantification && r.quantification.available) box.appendChild(h("div", { class: "message visible info", text: "Định lượng: " + r.quantification.formula + " = " + r.quantification.lost_quantity + " pcs" }));
    else if (r.quantification) box.appendChild(h("div", { class: "message visible warn", text: r.quantification.message }));

    box.appendChild(h("h3", { text: "Ảnh hưởng lan truyền" }));
    const impWrap = h("div");
    const impCols = [
      { key: "node_name", label: "Đối tượng" }, { key: "node_type", label: "Loại" },
      { key: "impact_type", label: "Mức", render: (i) => i.impact_type },
    ];
    renderTable(impWrap, impCols, r.impacts);
    box.appendChild(impWrap);

    box.appendChild(h("h3", { text: "Đường lan truyền (dạng chữ)" }));
    const paths = h("ul", { class: "path-list" });
    r.impacts.forEach(i => {
      if (!i.path || !i.path.length) return;
      const hop = i.path.map(s => s.from_type + "#" + s.from_id + " → " + s.to_type + "#" + s.to_id + " (" + s.kind + ")").join("  ›  ");
      paths.appendChild(h("li", {}, [h("div", { text: i.node_name + " [" + i.impact_type + "]" }), h("div", { class: "hop", text: hop })]));
    });
    box.appendChild(paths);

    box.appendChild(h("h3", { text: "Giả thuyết nguyên nhân" }));
    const hypWrap = h("div");
    r.hypotheses.forEach(hh => hypWrap.appendChild(h("p", { text: hh.content + " (rule " + hh.rule_id + ", " + hh.priority + ") — Cần kiểm tra: " + hh.check_more })));
    if (!r.hypotheses.length) hypWrap.appendChild(h("p", { class: "empty", text: "Chưa đủ dữ liệu để tạo giả thuyết." }));
    box.appendChild(hypWrap);

    box.appendChild(h("h3", { text: "Hành động đề xuất" }));
    const actWrap = h("div");
    r.actions.forEach(a => actWrap.appendChild(h("p", { text: a.department_name + ": " + a.action + " (" + a.priority + ")" })));
    box.appendChild(actWrap);
    box.appendChild(h("div", { class: "message visible warn", text: "Kết quả là đề xuất dựa trên quy tắc demo; nguyên nhân chưa được xác nhận trừ khi người dùng xác nhận riêng." }));
    loadHistory();
  }

  async function loadHistory() {
    const wrap = $("#analysis-history");
    if (!wrap) return;
    const d = await api("/api/analysis/runs?page_size=10");
    renderTable(wrap, [
      { key: "id", label: "ID" }, { key: "source_type", label: "Nguồn" }, { key: "source_id", label: "Đối tượng" },
      { key: "rule_version", label: "Quy tắc" }, { key: "run_at", label: "Thời điểm", render: (r) => fmt(r.run_at) },
    ], d.data.items, (row) => h("td", {}, [
      h("button", { class: "btn btn-sm btn-secondary", text: "Xem", onclick: () => viewRun(row.id) }),
    ]));
  }
  async function viewRun(id) {
    const d = await api("/api/analysis/runs/" + id);
    const r = { rules: [], rule_version: d.data.run.rule_version, quantification: { available: false }, impacts: d.data.impacts.map(i => ({ node_name: i.node_name, node_type: i.node_type, impact_type: i.impact_type, path: i.path })), hypotheses: d.data.hypotheses.map(hh => ({ content: hh.content, rule_id: hh.rule_id, priority: hh.priority, check_more: hh.check_more })), actions: d.data.actions.map(a => ({ department_name: a.department_name, action: a.action, priority: a.priority })) };
    renderAnalysisResult(r);
    navigate("analysis");
  }

  // ---------- tasks ----------
  async function renderTasks() {
    const sec = $("#section-tasks");
    sec.textContent = "";
    const listWrap = h("div"); const pag = h("div", { class: "pagination" });
    sec.appendChild(h("div", { class: "card" }, [h("h2", { text: "Hành động theo bộ phận" }), h("div", { class: "toolbar" }, [h("button", { class: "btn btn-primary", text: "+ Tạo công việc", onclick: () => taskForm(null) })]), listWrap, pag]));
    const state = { page: 1, tp: 1 };
    async function load() {
      const d = await api("/api/tasks?page=" + state.page + "&page_size=15");
      renderTable(listWrap, [
        { key: "id", label: "ID" }, { key: "title", label: "Công việc" }, { key: "department_id", label: "Bộ phận" },
        { key: "priority", label: "Ưu tiên" }, { key: "status", label: "Trạng thái", render: (r) => statusBadge(r.status) },
      ], d.data.items, (row) => h("td", {}, [
        h("select", { onchange: (e) => setTaskStatus(row.id, e.target.value) }, [
          h("option", { value: "TODO", selected: row.status === "TODO", text: "TODO" }),
          h("option", { value: "IN_PROGRESS", selected: row.status === "IN_PROGRESS", text: "IN_PROGRESS" }),
          h("option", { value: "DONE", selected: row.status === "DONE", text: "DONE" }),
          h("option", { value: "DISMISSED", selected: row.status === "DISMISSED", text: "DISMISSED" }),
        ]),
      ]));
      state.tp = d.data.pagination.total_pages;
      pagination(pag, state.page, state.tp, (p) => { state.page = p; load(); });
    }
    async function setTaskStatus(id, status) { try { await api("/api/tasks/" + id + "/status", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status }) }); toast("Đã cập nhật."); } catch (e) { toast(e.message, "error"); } }
    async function taskForm(row) {
      const depts = await loadOptions("department");
      const fields = [
        { name: "title", label: "Công việc", required: true },
        { name: "department_id", label: "Bộ phận", type: "select", options: depts },
        { name: "description", label: "Mô tả", type: "textarea" },
        { name: "priority", label: "Ưu tiên" },
      ];
      const fb = formBuilder(fields, async (data, s) => {
        fb.setSubmitting(true);
        try { await api("/api/tasks", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) }); closeModal(); toast("Đã tạo."); load(); }
        catch (e) { toast(e.message, "error"); fb.setSubmitting(false); }
      });
      openModal("Tạo công việc", fb.form);
    }
    load();
  }

  // ---------- scenarios ----------
  async function renderScenarios() {
    const sec = $("#section-scenarios");
    sec.textContent = "";
    const card = h("div", { class: "card" });
    sec.appendChild(h("div", { class: "card" }, [
      h("h2", { text: "Kịch bản mô phỏng" }),
      h("div", { class: "message visible warn", text: "Dữ liệu mô phỏng — chưa xác nhận bởi Denso." }),
      h("div", { class: "toolbar" }, [
        h("button", { class: "btn btn-primary", text: "Nạp dữ liệu demo", onclick: loadDemo }),
        h("span", { id: "scenario-status", class: "info" }),
      ]),
      card,
    ]));
    const list = h("div");
    const info = await api("/api/scenarios");
    info.data.forEach(s => list.appendChild(h("div", { class: "card" }, [
      h("h3", { text: s.title }),
      h("p", { text: "Sự cố: " + s.incident_code }),
      h("p", { text: "Kết quả dự kiến: " + s.expected }),
      h("p", { text: "Giới hạn: " + s.limits }),
      h("button", { class: "btn btn-secondary", text: "Chạy phân tích kịch bản này", onclick: () => analyzeByCode(s.incident_code) }),
    ])));
    card.appendChild(list);

    // What-if
    card.appendChild(h("h3", { text: "Phân tích What-if (giả định)" }));
    const what = h("div", { class: "grid grid-4" });
    const wt = selectInput("wt_type", ["MACHINE_STOP", "QUALITY", "MATERIAL_SHORTAGE", "DATA_DELAY"].map(x => ({ value: x, label: x })));
    const wst = selectInput("wt_stype", ["machine", "lot", "material", "process", "product", "dataset"].map(x => ({ value: x, label: x })));
    const wid = textInput("wt_id", "", "number");
    what.appendChild(field("Loại sự cố", wt)); what.appendChild(field("Loại node", wst)); what.appendChild(field("Node ID", wid));
    what.appendChild(h("button", { class: "btn btn-secondary", text: "Chạy what-if", onclick: () => {
      api("/api/analysis/whatif", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ incident_type: wt.value, source_type: wst.value, source_id: wid.value ? Number(wid.value) : null }) })
        .then(d => renderAnalysisResult(d.data)).catch(e => toast(e.message, "error"));
    } }));
    card.appendChild(what);

    const st = await api("/api/scenarios/status");
    $("#scenario-status").textContent = st.data.loaded ? "Đã nạp demo." : "Chưa nạp demo.";
  }
  async function loadDemo() {
    try { const d = await api("/api/scenarios/load", { method: "POST" }); toast(d.data.message); $("#scenario-status").textContent = "Đã nạp demo."; }
    catch (e) { toast(e.message, "error"); }
  }
  async function analyzeByCode(code) {
    const d = await api("/api/incidents?page_size=100");
    const inc = d.data.items.find(i => i.code === code);
    if (!inc) { toast("Chưa nạp demo hoặc không tìm thấy sự cố " + code, "error"); return; }
    navigate("analysis");
    setTimeout(() => runIncidentAnalysis(inc.id), 50);
  }

  // ---------- survey ----------
  async function renderSurvey() {
    const sec = $("#section-survey");
    sec.textContent = "";
    const groups = await api("/api/survey/groups");
    const items = await api("/api/survey");
    const byGroup = {};
    items.data.forEach(i => { (byGroup[i.group_code] = byGroup[i.group_code] || []).push(i); });
    groups.data.forEach(g => {
      const card = h("div", { class: "card" });
      card.appendChild(h("h2", { text: g.code + ". " + g.name }));
      const list = (byGroup[g.code] || []);
      list.forEach(item => {
        const row = h("div", { style: "border-bottom:1px solid #eee; padding:8px 0;" });
        row.appendChild(h("p", { text: item.question, style: "font-weight:600; margin:0 0 6px;" }));
        row.appendChild(h("p", { text: (item.answer ? "Trả lời: " + item.answer : "Chưa trả lời") + (item.provided_by ? " — " + item.provided_by : ""), style: "margin:0;" }));
        row.appendChild(statusBadge(item.status));
        const editBtn = h("button", { class: "btn btn-sm btn-secondary", style: "margin-left:8px;", text: "Trả lời", onclick: () => surveyForm(item) });
        row.appendChild(editBtn);
        card.appendChild(row);
      });
      sec.appendChild(card);
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

  // ---------- dashboard ----------
  async function renderDashboard() {
    const sec = $("#section-dashboard");
    sec.textContent = "";
    const d = await api("/api/dashboard");
    const s = d.data;
    const card = h("div", { class: "card" });
    card.appendChild(h("h2", { text: "Tổng quan" }));
    const stats = h("div", { class: "stat-grid" });
    const addStat = (label, num) => stats.appendChild(h("div", { class: "stat" }, [h("div", { class: "num", text: num }), h("div", { class: "lbl", text: label })]));
    addStat("Bản ghi sản lượng", s.production_records);
    addStat("Sự cố (đang mở)", s.incidents.open + "/" + s.incidents.total);
    addStat("Công việc TODO", s.tasks.todo + "/" + s.tasks.total);
    addStat("Hệ thống nguồn", s.sources);
    addStat("Dataset", s.datasets);
    addStat("Cạnh đồ thị", s.graph_edges);
    addStat("Lần phân tích", s.analysis_runs);
    card.appendChild(stats);

    const cat = h("div", { class: "stat-grid" });
    Object.keys(s.catalog).forEach(k => cat.appendChild(h("div", { class: "stat" }, [h("div", { class: "num", text: s.catalog[k].total }), h("div", { class: "lbl", text: k })])));
    card.appendChild(h("h3", { text: "Danh mục (tổng / mô phỏng)" }));
    card.appendChild(cat);

    sec.appendChild(card);

    const inc = await api("/api/incidents?status=OPEN&page_size=5");
    const incCard = h("div", { class: "card" });
    incCard.appendChild(h("h2", { text: "Sự cố đang mở" }));
    const incWrap = h("div");
    renderTable(incWrap, [{ key: "code", label: "Mã" }, { key: "title", label: "Tiêu đề" }, { key: "incident_type", label: "Loại" }, { key: "is_simulated", label: "Loại", render: boolBadge }], inc.data.items);
    incCard.appendChild(incWrap);
    sec.appendChild(incCard);

    const tasks = await api("/api/tasks?status=TODO&page_size=5");
    const tCard = h("div", { class: "card" });
    tCard.appendChild(h("h2", { text: "Công việc TODO" }));
    const tWrap = h("div");
    renderTable(tWrap, [{ key: "title", label: "Công việc" }, { key: "priority", label: "Ưu tiên" }], tasks.data.items);
    tCard.appendChild(tWrap);
    sec.appendChild(tCard);
  }

  // ---------- init ----------
  navigate("dashboard");
})();
