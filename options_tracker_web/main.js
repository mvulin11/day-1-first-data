const OPTIONS_MULTIPLIER = 100.0;
const ACTION_VALUES = new Set(["BTO", "STO", "STC", "BTC"]);
const OPTION_TYPES = new Set(["C", "P"]);

function $(sel) { return document.querySelector(sel); }
function $all(sel) { return Array.from(document.querySelectorAll(sel)); }

function fmtMoney(v) { return (v < 0 ? "-" : "") + "$" + Math.abs(v).toFixed(2); }
function fmtDate(d) { const t = new Date(d); return isNaN(t) ? "" : t.toISOString().slice(0,10); }
function fmtDateTime(d) {
  const t = new Date(d);
  if (isNaN(t)) return "";
  const pad = (n) => String(n).padStart(2, "0");
  return `${t.getFullYear()}-${pad(t.getMonth()+1)}-${pad(t.getDate())} ${pad(t.getHours())}:${pad(t.getMinutes())}:${pad(t.getSeconds())}`;
}

function nowLocalDateTimeInput() {
  const t = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${t.getFullYear()}-${pad(t.getMonth()+1)}-${pad(t.getDate())}T${pad(t.getHours())}:${pad(t.getMinutes())}`;
}

function loadTrades() {
  try {
    const raw = localStorage.getItem("options_trades");
    if (!raw) return [];
    const arr = JSON.parse(raw);
    return arr.map((r) => ({...r, strike: Number(r.strike), quantity: Number(r.quantity), price: Number(r.price), fees: Number(r.fees)}));
  } catch { return []; }
}

function saveTrades(trades) {
  localStorage.setItem("options_trades", JSON.stringify(trades));
}

function nextTradeId(trades) {
  if (!trades.length) return 1;
  return Math.max(...trades.map(t => Number(t.id)||0)) + 1;
}

function legKey(row) {
  return [row.symbol, row.expiry, Number(row.strike), row.option_type.toUpperCase()].join("|");
}

function isOpen(action) { return action === "BTO" || action === "STO"; }
function isClose(action) { return action === "BTC" || action === "STC"; }
function sideForAction(action) { return (action === "BTO" || action === "STC") ? "LONG" : "SHORT"; }

function computePL(trades) {
  const sorted = [...trades].sort((a, b) => new Date(a.trade_datetime) - new Date(b.trade_datetime));
  const openLots = new Map(); // key: symbol|expiry|strike|type|side -> array of {id, qty, price, fees}
  const realized = [];

  for (const r of sorted) {
    const action = String(r.action).toUpperCase();
    if (!ACTION_VALUES.has(action)) continue;
    const side = sideForAction(action);
    const key = `${legKey(r)}|${side}`;
    const qty = Number(r.quantity)||0;
    const price = Number(r.price)||0;
    const fees = Number(r.fees)||0;

    if (isOpen(action)) {
      const lots = openLots.get(key) || [];
      lots.push({ id: Number(r.id)||-1, qty, price, fees });
      openLots.set(key, lots);
    } else if (isClose(action)) {
      const lots = openLots.get(key) || [];
      let toClose = qty;
      while (toClose > 0 && lots.length) {
        const lot = lots[0];
        const matched = Math.min(toClose, lot.qty);
        const plPer = (side === "LONG") ? (price - lot.price) : (lot.price - price);
        const openFeeAlloc = lot.fees * (matched / (lot.qty || matched));
        const closeFeeAlloc = fees * (matched / (qty || matched));
        const realizedAmt = (plPer * matched * OPTIONS_MULTIPLIER) - openFeeAlloc - closeFeeAlloc;
        realized.push({
          symbol: r.symbol,
          expiry: r.expiry,
          strike: Number(r.strike),
          option_type: r.option_type,
          side,
          quantity: matched,
          realized_pl: realizedAmt,
          open_price: lot.price,
          close_price: price,
          open_fees: openFeeAlloc,
          close_fees: closeFeeAlloc,
          open_ids: [lot.id],
          close_id: Number(r.id)||-1,
        });
        lot.qty -= matched;
        toClose -= matched;
        if (lot.qty === 0) lots.shift();
      }
      openLots.set(key, lots);
    }
  }

  // Build open positions
  const openPositions = [];
  for (const [key, lots] of openLots.entries()) {
    const [symbol, expiry, strikeStr, optType, side] = key.split("|");
    const totalQty = lots.reduce((s, l) => s + l.qty, 0);
    if (!totalQty) continue;
    const totalCost = lots.reduce((s, l) => s + l.qty * l.price, 0);
    const totalFees = lots.reduce((s, l) => s + l.fees, 0);
    openPositions.push({
      symbol,
      expiry,
      strike: Number(strikeStr),
      option_type: optType,
      side,
      open_quantity: totalQty,
      average_cost: totalCost / totalQty,
      total_fees: totalFees,
    });
  }

  const totalRealized = realized.reduce((s, r) => s + Number(r.realized_pl)||0, 0);
  return { realized, openPositions, totalRealized };
}

function computeUnrealized(openPositions, marks) {
  const key = (r) => [r.symbol, r.expiry, Number(r.strike), r.option_type, r.side].join("|");
  const markMap = new Map(marks.map(m => [key(m), Number(m.mark)]));
  return openPositions.map((p) => {
    const m = markMap.get(key(p));
    const mark = Number.isFinite(m) ? m : p.average_cost;
    const diff = p.side === "LONG" ? (mark - p.average_cost) : (p.average_cost - mark);
    return { ...p, mark, unrealized_pl: diff * p.open_quantity * OPTIONS_MULTIPLIER };
  });
}

function renderTable(container, columns, rows, opts = {}) {
  const el = typeof container === "string" ? $(container) : container;
  if (!el) return;
  if (!rows || !rows.length) {
    el.innerHTML = '<div class="empty">No data</div>';
    return;
  }
  const ths = columns.map(c => `<th>${c.label}</th>`).join("");
  const trs = rows.map(r => `<tr>${columns.map(c => `<td>${c.format ? c.format(r[c.key], r) : (r[c.key] ?? "")}</td>`).join("")}</tr>`).join("");
  el.innerHTML = `<table><thead><tr>${ths}</tr></thead><tbody>${trs}</tbody></table>`;
}

function exportCSV(trades) {
  const cols = ["id","group_id","symbol","expiry","strike","option_type","action","quantity","price","fees","trade_datetime","note"];
  const escape = (v) => {
    if (v == null) return "";
    const s = String(v);
    if (/[",\n]/.test(s)) return '"' + s.replace(/"/g, '""') + '"';
    return s;
  };
  const header = cols.join(",");
  const lines = trades.map(t => cols.map(c => escape(t[c])).join(","));
  return [header, ...lines].join("\n");
}

function parseCSV(text) {
  // Minimal CSV parser handling quotes
  const rows = [];
  const re = /(,|\n|\r|^)(?:"([^"]*(?:""[^"]*)*)"|([^",\n\r]*))/g;
  let match, row = [];
  text = text.replace(/\r\n/g, "\n");
  while ((match = re.exec(text))) {
    const delim = match[1];
    if (delim.length && delim !== ',') { rows.push(row); row = []; }
    let val = match[2] ? match[2].replace(/""/g, '"') : match[3];
    row.push(val);
  }
  if (row.length) rows.push(row);
  return rows;
}

function rowsToTrades(rows) {
  const header = rows[0] || [];
  const idx = Object.fromEntries(header.map((h, i) => [h, i]));
  return rows.slice(1).filter(r => r.length).map(r => ({
    id: Number(r[idx.id])||null,
    group_id: r[idx.group_id] ? Number(r[idx.group_id]) : null,
    symbol: r[idx.symbol],
    expiry: r[idx.expiry],
    strike: Number(r[idx.strike])||0,
    option_type: r[idx.option_type],
    action: r[idx.action],
    quantity: Number(r[idx.quantity])||0,
    price: Number(r[idx.price])||0,
    fees: Number(r[idx.fees])||0,
    trade_datetime: r[idx.trade_datetime],
    note: r[idx.note] || "",
  }));
}

function setActiveTab(name) {
  $all('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === name));
  $all('.tab').forEach(s => s.classList.toggle('active', s.id === `tab-${name}`));
}

function refresh() {
  const trades = loadTrades();
  $("#metric-trade-count").textContent = String(trades.length);

  // Trades table
  renderTable("#trades-table", [
    { key: 'id', label: 'ID' },
    { key: 'group_id', label: 'Group' },
    { key: 'symbol', label: 'Symbol' },
    { key: 'expiry', label: 'Expiry' },
    { key: 'strike', label: 'Strike' },
    { key: 'option_type', label: 'Type' },
    { key: 'action', label: 'Action' },
    { key: 'quantity', label: 'Qty' },
    { key: 'price', label: 'Price' },
    { key: 'fees', label: 'Fees' },
    { key: 'trade_datetime', label: 'Time', format: v => fmtDateTime(v) },
    { key: 'note', label: 'Note' },
  ], trades);

  const { realized, openPositions, totalRealized } = computePL(trades);
  $("#metric-realized").textContent = fmtMoney(totalRealized);
  $("#metric-open-contracts").textContent = String(openPositions.reduce((s, p) => s + p.open_quantity, 0));

  renderTable("#realized-table", [
    { key: 'symbol', label: 'Symbol' },
    { key: 'expiry', label: 'Expiry' },
    { key: 'strike', label: 'Strike' },
    { key: 'option_type', label: 'Type' },
    { key: 'side', label: 'Side' },
    { key: 'quantity', label: 'Qty' },
    { key: 'open_price', label: 'Open Px' },
    { key: 'close_price', label: 'Close Px' },
    { key: 'open_fees', label: 'Open Fees' },
    { key: 'close_fees', label: 'Close Fees' },
    { key: 'realized_pl', label: 'Realized', format: v => fmtMoney(Number(v)||0) },
  ], realized.map(r => ({...r, expiry: fmtDate(r.expiry)})));

  renderTable("#open-table", [
    { key: 'symbol', label: 'Symbol' },
    { key: 'expiry', label: 'Expiry' },
    { key: 'strike', label: 'Strike' },
    { key: 'option_type', label: 'Type' },
    { key: 'side', label: 'Side' },
    { key: 'open_quantity', label: 'Qty' },
    { key: 'average_cost', label: 'Avg Cost' },
    { key: 'total_fees', label: 'Fees' },
  ], openPositions.map(r => ({...r, expiry: fmtDate(r.expiry)})));

  // Marks editor
  const marksContainer = $("#marks-table");
  marksContainer.innerHTML = '';
  if (openPositions.length) {
    const table = document.createElement('table');
    const thead = document.createElement('thead');
    thead.innerHTML = '<tr><th>Symbol</th><th>Expiry</th><th>Strike</th><th>Type</th><th>Side</th><th>Qty</th><th>Avg Cost</th><th>Mark</th><th>Unrealized</th></tr>';
    table.appendChild(thead);
    const tbody = document.createElement('tbody');
    const marks = [];
    openPositions.forEach((p, idx) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${p.symbol}</td><td>${fmtDate(p.expiry)}</td><td>${p.strike.toFixed(2)}</td><td>${p.option_type}</td><td>${p.side}</td><td>${p.open_quantity}</td><td>${p.average_cost.toFixed(2)}</td>`;
      const tdMark = document.createElement('td');
      const input = document.createElement('input');
      input.type = 'number'; input.step = '0.01'; input.min = '0'; input.value = p.average_cost.toFixed(2); input.dataset.idx = String(idx);
      tdMark.appendChild(input);
      tr.appendChild(tdMark);
      const tdUnreal = document.createElement('td');
      tdUnreal.textContent = '$0.00';
      tr.appendChild(tdUnreal);
      tbody.appendChild(tr);
      marks.push({ symbol: p.symbol, expiry: p.expiry, strike: p.strike, option_type: p.option_type, side: p.side, mark: Number(input.value) });
      input.addEventListener('input', () => {
        marks[Number(input.dataset.idx)].mark = Number(input.value);
        updateUnrealized(openPositions, marks, tbody);
      });
    });
    table.appendChild(tbody);
    marksContainer.appendChild(table);
    updateUnrealized(openPositions, marks, tbody);
  }
}

function updateUnrealized(openPositions, marks, tbody) {
  const rows = computeUnrealized(openPositions, marks);
  let total = 0;
  Array.from(tbody.children).forEach((tr, i) => {
    const unreal = rows[i]?.unrealized_pl || 0;
    tr.lastChild.textContent = fmtMoney(unreal);
    total += unreal;
  });
  $("#metric-unrealized").textContent = fmtMoney(total);
}

function resetForm() {
  $("#edit_id").value = '';
  $("#submit-btn").textContent = 'Add Trade';
  $("#trade-form").reset();
  $("#trade_datetime").value = nowLocalDateTimeInput();
}

function loadIntoForm(t) {
  $("#edit_id").value = t.id || '';
  $("#symbol").value = t.symbol || '';
  $("#option_type").value = t.option_type || 'C';
  $("#strike").value = t.strike;
  $("#expiry").value = t.expiry;
  $("#action").value = t.action || 'BTO';
  $("#quantity").value = t.quantity || 1;
  $("#price").value = t.price || 0;
  $("#fees").value = t.fees || 0;
  $("#group_id").value = t.group_id ?? '';
  $("#trade_datetime").value = t.trade_datetime?.slice(0,16) || nowLocalDateTimeInput();
  $("#note").value = t.note || '';
  $("#submit-btn").textContent = 'Update Trade';
}

function init() {
  // Tabs
  $all('.tab-btn').forEach(btn => btn.addEventListener('click', () => setActiveTab(btn.dataset.tab)));

  // Defaults
  $("#trade_datetime").value = nowLocalDateTimeInput();

  // Form submit
  $("#trade-form").addEventListener('submit', (e) => {
    e.preventDefault();
    const trades = loadTrades();
    const idInput = $("#edit_id").value;
    const row = {
      id: idInput ? Number(idInput) : nextTradeId(trades),
      group_id: $("#group_id").value ? Number($("#group_id").value) : null,
      symbol: $("#symbol").value.trim().toUpperCase(),
      expiry: $("#expiry").value,
      strike: Number($("#strike").value),
      option_type: $("#option_type").value,
      action: $("#action").value,
      quantity: Number($("#quantity").value),
      price: Number($("#price").value),
      fees: Number($("#fees").value),
      trade_datetime: $("#trade_datetime").value.replace('T', ' ') + ":00",
      note: $("#note").value || '',
    };
    if (!ACTION_VALUES.has(row.action) || !OPTION_TYPES.has(row.option_type)) return;
    let updated;
    if (idInput) { updated = trades.filter(t => t.id !== Number(idInput)); }
    else { updated = trades; }
    updated.push(row);
    updated.sort((a,b) => new Date(a.trade_datetime) - new Date(b.trade_datetime));
    saveTrades(updated);
    resetForm();
    refresh();
    setActiveTab('trades');
  });

  $("#cancel-edit").addEventListener('click', () => resetForm());

  // Load for edit
  $("#load-for-edit").addEventListener('click', () => {
    const id = Number($("#edit-trade-id").value);
    if (!id) return;
    const t = loadTrades().find(x => x.id === id);
    if (!t) { alert('Trade ID not found'); return; }
    loadIntoForm(t);
    setActiveTab('add');
  });

  // Delete
  $("#delete-trade").addEventListener('click', () => {
    const id = Number($("#edit-trade-id").value);
    if (!id) return;
    const trades = loadTrades().filter(t => t.id !== id);
    saveTrades(trades);
    refresh();
  });

  // Export CSV
  $("#export-csv").addEventListener('click', () => {
    const csv = exportCSV(loadTrades());
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'trades.csv'; a.click();
    URL.revokeObjectURL(url);
  });

  // Import CSV
  $("#import-csv").addEventListener('change', async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    const rows = parseCSV(text);
    const incoming = rowsToTrades(rows);
    const existing = loadTrades();
    let startId = existing.length ? Math.max(...existing.map(t => t.id||0)) + 1 : 1;
    const normalized = incoming.map(r => ({ ...r, id: startId++ }));
    const merged = existing.concat(normalized).sort((a,b) => new Date(a.trade_datetime) - new Date(b.trade_datetime));
    saveTrades(merged);
    e.target.value = '';
    refresh();
  });

  refresh();
}

document.addEventListener('DOMContentLoaded', init);