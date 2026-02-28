<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DENTAL WHITE — Panel</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; font-family: Arial, sans-serif; }
body { background:#f0f2f5; display:flex; height:100vh; overflow:hidden; }

/* PANEL IZQUIERDO */
#pizq {
  width:280px; min-width:280px; background:#2c3e50;
  color:white; display:flex; flex-direction:column;
  padding:16px; gap:10px; overflow-y:auto;
}
#pizq h2 { font-size:16px; text-align:center; padding:8px 0; }
#usuario-badge {
  background:#27ae60; border-radius:8px;
  padding:8px; text-align:center; font-size:13px; font-weight:bold;
}
#tabla-balance { width:100%; border-collapse:collapse; font-size:12px; }
#tabla-balance th { background:#1a252f; padding:6px 4px; }
#tabla-balance td { padding:5px 4px; text-align:center; border-bottom:1px solid #3d5166; }
#lbl-caja {
  background:#27ae60; border-radius:8px;
  padding:10px; text-align:center; font-size:14px; font-weight:bold;
}
.btn-panel {
  padding:10px; border:none; border-radius:8px;
  font-size:13px; font-weight:bold; cursor:pointer;
  width:100%; transition: opacity .2s;
}
.btn-panel:hover { opacity:.85; }
.leyenda { font-size:11px; text-align:center; color:#aaa; padding:4px 0; }

/* BARRA DE PROGRESO */
#prog-wrap { display:none; }
#prog-bar {
  width:100%; height:8px; background:#1a252f;
  border-radius:4px; overflow:hidden; margin-top:4px;
}
#prog-fill { height:100%; background:#27ae60; width:0%; transition:width .3s; }
#prog-lbl { font-size:11px; color:#aaa; text-align:center; margin-top:3px; }

/* PANEL CENTRAL */
#pcen {
  flex:1; display:flex; flex-direction:column; overflow:hidden;
}
#tabs {
  display:flex; background:#34495e; overflow-x:auto;
  border-bottom:3px solid #27ae60;
}
.tab {
  padding:12px 20px; cursor:pointer; color:#aaa;
  font-size:13px; font-weight:bold; white-space:nowrap;
  transition: all .2s; border-bottom:3px solid transparent;
  margin-bottom:-3px;
}
.tab.activo { color:white; border-bottom-color:#27ae60; background:#2c3e50; }
#buscar-wrap {
  padding:10px 16px; background:white;
  border-bottom:1px solid #ddd;
}
#buscar {
  width:100%; padding:8px 12px; border:2px solid #ddd;
  border-radius:8px; font-size:14px; outline:none;
}
#buscar:focus { border-color:#3498db; }
#tabla-wrap { flex:1; overflow-y:auto; }
table { width:100%; border-collapse:collapse; font-size:13px; }
thead th {
  background:#2c3e50; color:white; padding:10px 8px;
  position:sticky; top:0; cursor:pointer; user-select:none;
}
thead th:hover { background:#3d5166; }
tbody tr { border-bottom:1px solid #eee; cursor:pointer; transition:background .1s; }
tbody tr:hover { background:#f8f9fa !important; }
tbody tr.sel { background:#d5e8ff !important; }
.verde   { background:#c8f0c8 !important; }
.naranja { background:#ffd9a0 !important; }

/* PANEL DERECHO */
#pder {
  width:380px; min-width:380px; background:white;
  display:flex; flex-direction:column; overflow-y:auto;
  border-left:2px solid #ddd; padding:16px; gap:10px;
}
#img-cupon {
  width:100%; height:200px; background:#ecf0f1;
  border-radius:8px; object-fit:contain;
  display:flex; align-items:center; justify-content:center;
  color:#aaa; font-size:13px; overflow:hidden;
}
#img-cupon img { width:100%; height:100%; object-fit:contain; }
.campo-lbl { font-size:11px; font-weight:bold; color:#555; margin-bottom:2px; }
.campo-inp {
  width:100%; padding:8px 10px; border:2px solid #e0e0e0;
  border-radius:6px; font-size:13px; outline:none;
}
.campo-inp:focus { border-color:#3498db; }
select.campo-inp { cursor:pointer; }
.switch-row {
  display:flex; align-items:center; gap:10px;
  padding:6px 0;
}
.switch {
  position:relative; width:48px; height:24px;
}
.switch input { opacity:0; width:0; height:0; }
.slider {
  position:absolute; cursor:pointer;
  top:0; left:0; right:0; bottom:0;
  background:#e74c3c; border-radius:24px;
  transition:.3s;
}
.slider:before {
  content:""; position:absolute;
  height:18px; width:18px; left:3px; bottom:3px;
  background:white; border-radius:50%; transition:.3s;
}
input:checked + .slider { background:#27ae60; }
input:checked + .slider:before { transform:translateX(24px); }
#lbl-estado { font-size:13px; font-weight:bold; }
textarea.campo-inp { resize:vertical; min-height:60px; }
.btn-acc {
  width:100%; padding:10px; border:none; border-radius:8px;
  font-size:13px; font-weight:bold; cursor:pointer;
  transition: opacity .2s;
}
.btn-acc:hover { opacity:.85; }

/* MODAL BALANCE */
#modal-overlay {
  display:none; position:fixed; inset:0;
  background:rgba(0,0,0,.5); z-index:1000;
  align-items:center; justify-content:center;
}
#modal-overlay.show { display:flex; }
#modal {
  background:white; border-radius:12px;
  padding:30px; max-width:600px; width:90%;
  max-height:85vh; overflow-y:auto;
}
#modal h2 { font-size:18px; margin-bottom:16px; color:#2c3e50; }
#modal pre {
  background:#f8f9fa; border-radius:8px;
  padding:16px; font-size:12px; white-space:pre-wrap;
  font-family: monospace; border:1px solid #ddd;
}
.modal-btns { display:flex; gap:10px; margin-top:16px; }
.modal-btns button {
  flex:1; padding:12px; border:none; border-radius:8px;
  font-size:14px; font-weight:bold; cursor:pointer;
}
</style>
</head>
<body>

<!-- PANEL IZQUIERDO -->
<div id="pizq">
  <h2>🦷 DENTAL WHITE</h2>
  <div id="usuario-badge">CARGANDO...</div>

  <table id="tabla-balance">
    <thead><tr><th>PROV</th><th>CANT</th><th>INICIAL</th><th>COBRADO</th></tr></thead>
    <tbody id="bal-body"></tbody>
  </table>

  <div id="lbl-caja">CAJA DEL DÍA: $0</div>

  <div id="prog-wrap">
    <div id="prog-bar"><div id="prog-fill"></div></div>
    <div id="prog-lbl">Procesando...</div>
  </div>

  <!-- Botones -->
  <label style="display:none" id="pdf-label">
    <input type="file" id="pdf-input" accept=".pdf" style="display:none">
    <div class="btn-panel" style="background:#27ae60">📥 SUBIR PDF</div>
  </label>
  <button class="btn-panel" style="background:#27ae60" onclick="document.getElementById('pdf-input').click()">📥 SUBIR PDF</button>
  <input type="file" id="pdf-input" accept=".pdf" style="display:none">

  <button class="btn-panel" style="background:#2980b9" onclick="agregarManual()">➕ AGREGAR</button>
  <button class="btn-panel" style="background:#34495e" onclick="mostrarIniciarMes()">📅 INICIAR MES</button>
  <button class="btn-panel" style="background:#7f8c8d" onclick="mostrarCierre()">📝 CIERRE</button>
  <button class="btn-panel" style="background:#c0392b" onclick="eliminarCliente()">❌ ELIMINAR</button>
  <button class="btn-panel" style="background:#e67e22" onclick="mostrarBalanceDiario()">📊 BALANCE DIARIO</button>

  <div class="leyenda">🟢 Guardado/Pagado &nbsp; 🟠 Cuota vieja</div>
</div>

<!-- PANEL CENTRAL -->
<div id="pcen">
  <div id="tabs"></div>
  <div id="buscar-wrap">
    <input id="buscar" placeholder="🔍 Buscar cliente..." oninput="cargarTabla()">
  </div>
  <div id="tabla-wrap">
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th onclick="ordenarPorN()">N° ↕</th>
          <th>AFILIADO</th>
          <th>MONTO</th>
          <th>CTA</th>
          <th>FECHA</th>
          <th>VISTO</th>
        </tr>
      </thead>
      <tbody id="tabla-body"></tbody>
    </table>
  </div>
</div>

<!-- PANEL DERECHO -->
<div id="pder">
  <div id="img-cupon"><span>Sin imagen</span></div>

  <div><div class="campo-lbl">N° AFILIADO</div>
  <input class="campo-inp" id="e-cta"></div>

  <div><div class="campo-lbl">AFILIADO</div>
  <input class="campo-inp" id="e-nom"></div>

  <div><div class="campo-lbl">MONTO $</div>
  <input class="campo-inp" id="e-mon" type="number"></div>

  <div><div class="campo-lbl">CTA (CUOTA)</div>
  <input class="campo-inp" id="e-cuo"></div>

  <div><div class="campo-lbl">FECHA COBRO</div>
  <input class="campo-inp" id="e-fec"></div>

  <div><div class="campo-lbl">WHATSAPP</div>
  <input class="campo-inp" id="e-tel" type="tel"></div>

  <div><div class="campo-lbl">MÉTODO DE PAGO</div>
  <select class="campo-inp" id="e-pag">
    <option>EFECTIVO</option>
    <option>TRANSFERENCIA</option>
    <option>MERCADO PAGO</option>
    <option>TARJETA</option>
  </select></div>

  <div class="switch-row">
    <label class="switch">
      <input type="checkbox" id="sw-estado" onchange="toggleEstado()">
      <span class="slider"></span>
    </label>
    <span id="lbl-estado" style="color:#e74c3c">PENDIENTE</span>
  </div>

  <div><div class="campo-lbl">COMENTARIO</div>
  <input class="campo-inp" id="e-com"></div>

  <div><div class="campo-lbl">MENSAJE WHATSAPP</div>
  <textarea class="campo-inp" id="e-msg">Hola! Le informamos que su cupón de pago Dental White está disponible. Ante cualquier consulta no dude en contactarnos.</textarea></div>

  <button class="btn-acc" style="background:#27ae60;color:white;font-size:15px;padding:14px"
          onclick="registrarPago()">✅ REGISTRAR PAGO</button>
  <button class="btn-acc" style="background:#f39c12;color:white" onclick="marcarVisto()">👁️ VISTO</button>
  <button class="btn-acc" style="background:#34495e;color:white" onclick="guardarDatos()">💾 GUARDAR CAMBIOS</button>
  <button class="btn-acc" style="background:#2ecc71;color:white" onclick="enviarWA()">🟢 ENVIAR WHATSAPP</button>
</div>

<!-- MODAL -->
<div id="modal-overlay">
  <div id="modal">
    <h2 id="modal-titulo"></h2>
    <pre id="modal-texto"></pre>
    <div class="modal-btns" id="modal-btns"></div>
  </div>
</div>

<script>
// ── ESTADO GLOBAL ───────────────────────────────
let usuario = '', provincias = [], tabActual = '', currId = null;
let ordenN = true, filas = [];

// ── INIT ─────────────────────────────────────────
window.onload = () => {
  usuario   = sessionStorage.getItem('usuario');
  provincias = JSON.parse(sessionStorage.getItem('provincias') || '[]');
  if (!usuario) { window.location = '/'; return; }

  document.getElementById('usuario-badge').textContent = '👤 ' + usuario;

  // Crear tabs
  const tabs = document.getElementById('tabs');
  ['✅ PAGOS HOY', ...provincias].forEach(p => {
    const t = document.createElement('div');
    t.className = 'tab';
    t.textContent = p;
    t.onclick = () => cambiarTab(p);
    tabs.appendChild(t);
  });

  // PDF input
  document.getElementById('pdf-input').onchange = subirPDF;

  cambiarTab('✅ PAGOS HOY');
  cargarBalance();
};

// ── TABS ──────────────────────────────────────────
function cambiarTab(prov) {
  tabActual = prov;
  document.querySelectorAll('.tab').forEach(t => {
    t.classList.toggle('activo', t.textContent === prov);
  });
  document.getElementById('buscar').value = '';
  cargarTabla();
}

// ── TABLA ─────────────────────────────────────────
async function cargarTabla() {
  const buscar = document.getElementById('buscar').value;
  let url, data;

  if (tabActual === '✅ PAGOS HOY') {
    const r = await fetch('/api/cupones/hoy');
    data = await r.json();
    // Filtrar por búsqueda
    if (buscar) data = data.filter(d =>
      (d.nombre||'').toLowerCase().includes(buscar.toLowerCase()));
    // Color: siempre verde en pagos hoy
    data.forEach(d => d.color = 'verde');
  } else {
    const r = await fetch(`/api/cupones?provincia=${encodeURIComponent(tabActual)}&buscar=${encodeURIComponent(buscar)}`);
    data = await r.json();
  }

  filas = data;
  renderTabla(data);
}

function renderTabla(data) {
  const body = document.getElementById('tabla-body');
  body.innerHTML = '';
  data.forEach(r => {
    const tr = document.createElement('tr');
    if (r.color === 'verde')   tr.classList.add('verde');
    if (r.color === 'naranja') tr.classList.add('naranja');
    if (currId === r.id)       tr.classList.add('sel');
    tr.innerHTML = `
      <td>${r.id}</td>
      <td>${r.cuenta||''}</td>
      <td style="text-align:left;padding-left:8px">${r.nombre||''}</td>
      <td>$${(r.monto||0).toLocaleString('es-AR')}</td>
      <td>${r.cta||''}</td>
      <td>${r.fecha_cobro||''}</td>
      <td style="text-align:center;font-size:16px">${r.visto ? '✅' : '🟡'}</td>
    `;
    tr.onclick = () => cargarDetalle(r.id);
    body.appendChild(tr);
  });
}

// ── ORDENAR POR N° ───────────────────────────────
function ordenarPorN() {
  filas.sort((a,b) => {
    const na = parseInt(a.cuenta)||99999;
    const nb = parseInt(b.cuenta)||99999;
    return ordenN ? na-nb : nb-na;
  });
  ordenN = !ordenN;
  renderTabla(filas);
}

// ── DETALLE ───────────────────────────────────────
async function cargarDetalle(id) {
  currId = id;
  const r = await fetch(`/api/cupon/${id}`);
  const d = await r.json();

  document.getElementById('e-cta').value = d.cuenta || '';
  document.getElementById('e-nom').value = d.nombre || '';
  document.getElementById('e-mon').value = d.monto  || '';
  document.getElementById('e-cuo').value = d.cta    || '';
  document.getElementById('e-fec').value = d.fecha_cobro || '';
  document.getElementById('e-tel').value = d.telefono || '';
  document.getElementById('e-com').value = d.comentario || '';
  if (d.medio_pago) document.getElementById('e-pag').value = d.medio_pago;

  // Switch estado
  const pagado = d.estado === 'PAGADO';
  document.getElementById('sw-estado').checked = pagado;
  document.getElementById('lbl-estado').textContent = pagado ? 'PAGADO' : 'PENDIENTE';
  document.getElementById('lbl-estado').style.color  = pagado ? '#27ae60' : '#e74c3c';

  // Imagen
  const imgDiv = document.getElementById('img-cupon');
  if (d.img_path) {
    imgDiv.innerHTML = `<img src="${d.img_path}" alt="cupón">`;
  } else {
    imgDiv.innerHTML = '<span>Sin imagen</span>';
  }

  // Resaltar fila
  document.querySelectorAll('#tabla-body tr').forEach(tr => tr.classList.remove('sel'));
  const trs = document.querySelectorAll('#tabla-body tr');
  trs.forEach(tr => { if (parseInt(tr.cells[0].textContent) === id) tr.classList.add('sel'); });
}

// ── ACCIONES ─────────────────────────────────────
async function registrarPago() {
  if (!currId) return;
  const fd = new FormData();
  fd.append('medio_pago', document.getElementById('e-pag').value);
  fd.append('comentario', document.getElementById('e-com').value);
  await fetch(`/api/cupon/${currId}/pago`, {method:'POST', body:fd});
  cargarTabla(); cargarBalance();
}

async function toggleEstado() {
  if (!currId) return;
  const pagado = document.getElementById('sw-estado').checked;
  document.getElementById('lbl-estado').textContent = pagado ? 'PAGADO' : 'PENDIENTE';
  document.getElementById('lbl-estado').style.color  = pagado ? '#27ae60' : '#e74c3c';

  if (pagado) {
    const fd = new FormData();
    fd.append('medio_pago', document.getElementById('e-pag').value);
    fd.append('comentario', document.getElementById('e-com').value);
    await fetch(`/api/cupon/${currId}/pago`, {method:'POST', body:fd});
  } else {
    await fetch(`/api/cupon/${currId}/impago`, {method:'POST'});
  }
  cargarTabla(); cargarBalance();
}

async function guardarDatos() {
  if (!currId) return;
  const fd = new FormData();
  fd.append('cuenta',      document.getElementById('e-cta').value);
  fd.append('nombre',      document.getElementById('e-nom').value);
  fd.append('monto',       document.getElementById('e-mon').value);
  fd.append('cta',         document.getElementById('e-cuo').value);
  fd.append('fecha_cobro', document.getElementById('e-fec').value);
  fd.append('telefono',    document.getElementById('e-tel').value);
  fd.append('comentario',  document.getElementById('e-com').value);
  await fetch(`/api/cupon/${currId}/guardar`, {method:'POST', body:fd});
  cargarTabla(); cargarBalance();
  alert('✅ Guardado');
}

async function eliminarCliente() {
  if (!currId) return;
  if (!confirm('¿Eliminar este cliente?')) return;
  await fetch(`/api/cupon/${currId}`, {method:'DELETE'});
  currId = null;
  cargarTabla(); cargarBalance();
}

async function agregarManual() {
  if (!tabActual || tabActual === '✅ PAGOS HOY') {
    alert('Seleccioná una provincia primero');
    return;
  }
  const fd = new FormData();
  fd.append('provincia', tabActual);
  await fetch('/api/cupon/agregar', {method:'POST', body:fd});
  cargarTabla();
}

async function marcarVisto() {
  if (!currId) return;
  await fetch(`/api/cupon/${currId}/visto`, {method:'POST'});
  cargarTabla();
}

async function enviarWA() {
  const tel = document.getElementById('e-tel').value.replace(/\D/g,'');
  if (!tel) { alert('Este cliente no tiene número de WhatsApp'); return; }
  const msg = encodeURIComponent(document.getElementById('e-msg').value.trim());

  // Abrir WhatsApp Web con el mensaje
  window.open(`https://web.whatsapp.com/send?phone=549${tel}&text=${msg}`, '_blank');

  // Si hay imagen, abrirla en nueva pestaña para poder guardarla o copiarla
  if (currId) {
    const r = await fetch(`/api/cupon/${currId}`);
    const d = await r.json();
    if (d.img_path) {
      setTimeout(() => {
        window.open(d.img_path, '_blank');
        alert('💡 La imagen del cupón se abrió en una nueva pestaña.\nGuardala o copiala y pegala en WhatsApp.');
      }, 1000);
    }
  }
}

// ── SUBIR PDF ─────────────────────────────────────
async function subirPDF(e) {
  const file = e.target.files[0];
  if (!file) return;
  if (!tabActual || tabActual === '✅ PAGOS HOY') {
    alert('Seleccioná una provincia antes de subir el PDF');
    return;
  }
  const pw = document.getElementById('prog-wrap');
  const pf = document.getElementById('prog-fill');
  const pl = document.getElementById('prog-lbl');
  pw.style.display = 'block';
  pf.style.width = '5%';
  pl.textContent = 'Enviando PDF al servidor...';

  const fd = new FormData();
  fd.append('provincia', tabActual);
  fd.append('archivo', file);

  try {
    // Iniciar la subida en background
    const promesa = fetch('/api/subir_pdf', {method:'POST', body:fd});

    // Esperar 2 segundos para que el servidor arranque a procesar
    await new Promise(r => setTimeout(r, 2000));
    pf.style.width = '15%';
    pl.textContent = 'Procesando... (espere)';

    // Polling: consultar progreso cada 2 segundos
    // Como no tenemos el tarea_id todavía, mostramos animación simple
    let dots = 0;
    const intervalo = setInterval(() => {
      dots = (dots + 1) % 4;
      const barra = Math.min(15 + dots * 5, 85);
      pf.style.width = barra + '%';
      pl.textContent = 'Procesando páginas' + '.'.repeat(dots + 1);
    }, 2000);

    // Esperar que termine
    const r = await promesa;
    clearInterval(intervalo);

    if (!r.ok) {
      const err = await r.json();
      pl.textContent = '❌ Error: ' + (err.detail || 'Error desconocido');
      pf.style.width = '0%';
      console.error(err.detail);
      return;
    }

    const d = await r.json();
    pf.style.width = '100%';
    pl.textContent = `✅ ${d.detectados} cupones en ${d.paginas} páginas`;
    cargarTabla();
    cargarBalance();
    setTimeout(() => { pw.style.display = 'none'; pf.style.width='0%'; }, 5000);

  } catch(err) {
    pl.textContent = '❌ Error al procesar — revisá los logs en Render';
    console.error(err);
  }
  e.target.value = '';
}

// ── BALANCE ───────────────────────────────────────
async function cargarBalance() {
  const r = await fetch(`/api/balance?provincias=${encodeURIComponent(provincias.join(','))}`);
  const data = await r.json();
  const body = document.getElementById('bal-body');
  body.innerHTML = '';
  let totalCobrado = 0;
  data.forEach(d => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${d.provincia.substring(0,6)}</td><td>${d.cant}</td>
      <td>$${(d.inicial||0).toLocaleString('es-AR',{maximumFractionDigits:0})}</td>
      <td>$${(d.cobrado||0).toLocaleString('es-AR',{maximumFractionDigits:0})}</td>`;
    body.appendChild(tr);
    totalCobrado += d.cobrado || 0;
  });
  document.getElementById('lbl-caja').textContent =
    `CAJA DEL DÍA: $${totalCobrado.toLocaleString('es-AR',{maximumFractionDigits:0})}`;
}

// ── BALANCE DIARIO ────────────────────────────────
async function mostrarBalanceDiario() {
  const r = await fetch('/api/balance_diario');
  const d = await r.json();
  if (!d.clientes?.length) { alert('No hay pagos registrados hoy.'); return; }

  const sep  = '='.repeat(60);
  const sep2 = '-'.repeat(60);
  let txt = `${sep}\n   BALANCE DIARIO — DENTAL WHITE\n   Fecha: ${d.fecha}\n${sep}\n`;
  txt += `   Clientes cobrados: ${d.total_clientes}\n`;
  txt += `   Total recaudado:   $${d.total_general.toLocaleString('es-AR',{maximumFractionDigits:0})}\n`;
  txt += `${sep2}\n   DESGLOSE POR MÉTODO:\n`;
  txt += `   💵 Efectivo:       $${d.total_efectivo.toLocaleString('es-AR',{maximumFractionDigits:0})}\n`;
  txt += `   🏦 Transferencia:  $${d.total_transfer.toLocaleString('es-AR',{maximumFractionDigits:0})}\n`;
  txt += `   📱 Mercado Pago:   $${d.total_mp.toLocaleString('es-AR',{maximumFractionDigits:0})}\n`;
  txt += `   💳 Tarjeta:        $${d.total_tarjeta.toLocaleString('es-AR',{maximumFractionDigits:0})}\n`;
  txt += `${sep}\n   DETALLE POR CLIENTE:\n${sep2}\n`;

  let provAct = '';
  d.clientes.forEach(c => {
    if (c.provincia !== provAct) {
      provAct = c.provincia;
      txt += `\n  ── ${provAct.toUpperCase()} ──\n`;
    }
    const multi = c.multi ? '  ⭐ MULTI-CUOTA' : '';
    txt += `  • ${(c.nombre||'').padEnd(35)} Cuota(s): ${c.cuotas_str||'-'}   $${c.total.toLocaleString('es-AR',{maximumFractionDigits:0})}${multi}\n`;
    if (c.comentario) txt += `    Nota: ${c.comentario}\n`;
  });
  txt += `\n${sep}`;

  abrirModal('📊 BALANCE DIARIO', txt, [
    {txt:'Cerrar', color:'#7f8c8d', fn:'cerrarModal()'}
  ]);
}

// ── INICIAR MES ───────────────────────────────────
async function mostrarIniciarMes() {
  const r = await fetch(`/api/iniciar_mes/preview?provincias=${encodeURIComponent(provincias.join(','))}`);
  const data = await r.json();

  const sep = '='.repeat(60);
  let txt = `${sep}\n   BALANCE INICIAL DEL MES — DENTAL WHITE\n${sep}\n`;
  let totCli=0, totCup=0, totMonto=0;
  data.forEach(d => {
    txt += `\n  ── ${d.provincia.toUpperCase()} ──\n`;
    txt += `     Clientes:    ${d.clientes}\n`;
    txt += `     Cupones:     ${d.cupones}\n`;
    txt += `     A recaudar:  $${d.monto.toLocaleString('es-AR',{maximumFractionDigits:0})}\n`;
    totCli += d.clientes; totCup += d.cupones; totMonto += d.monto;
  });
  txt += `\n${'-'.repeat(60)}\n   TOTALES:\n`;
  txt += `   Clientes:    ${totCli}\n`;
  txt += `   Cupones:     ${totCup}\n`;
  txt += `   A recaudar:  $${totMonto.toLocaleString('es-AR',{maximumFractionDigits:0})}\n${sep}`;

  abrirModal('📅 BALANCE INICIO DE MES', txt, [
    {txt:'Cerrar', color:'#27ae60', fn:'cerrarModal()'}
  ]);
}

// ── CIERRE ────────────────────────────────────────
async function mostrarCierre() {
  const r = await fetch(`/api/cierre?provincias=${encodeURIComponent(provincias.join(','))}`);
  const d = await r.json();

  const sep = '='.repeat(60);
  const hoy = new Date().toLocaleDateString('es-AR');
  let txt = `${sep}\n   CIERRE DE MES — DENTAL WHITE\n   Fecha: ${hoy}\n${sep}\n`;

  let totCob=0, totPend=0, totCliCob=0, totCliPend=0;
  d.provincias.forEach(p => {
    txt += `\n  ── ${p.provincia.toUpperCase()} ──\n`;
    txt += `     ✅ Cobrado:    ${p.cobrado_cant} cupones   $${p.cobrado_monto.toLocaleString('es-AR',{maximumFractionDigits:0})}\n`;
    txt += `     ⏳ Pendiente:  ${p.pendiente_cant} clientes  $${p.pendiente_monto.toLocaleString('es-AR',{maximumFractionDigits:0})}\n`;
    totCob += p.cobrado_monto; totPend += p.pendiente_monto;
    totCliCob += p.cobrado_cant; totCliPend += p.pendiente_cant;
  });

  txt += `\n${'-'.repeat(60)}\n   TOTALES:\n`;
  txt += `   ✅ Cobrado:   ${totCliCob} cupones   $${totCob.toLocaleString('es-AR',{maximumFractionDigits:0})}\n`;
  txt += `   ⏳ Pendiente: ${totCliPend} clientes  $${totPend.toLocaleString('es-AR',{maximumFractionDigits:0})}\n`;

  if (Object.keys(d.metodos).length) {
    txt += `\n${'-'.repeat(60)}\n   DESGLOSE POR MÉTODO:\n`;
    Object.entries(d.metodos).forEach(([m, v]) => {
      txt += `   ${m.padEnd(20)} ${v.cant} pagos   $${v.monto.toLocaleString('es-AR',{maximumFractionDigits:0})}\n`;
    });
  }
  txt += `\n${sep}\n\n⚠️  Si confirmás el cierre se borran TODOS los clientes\n   de tus provincias para empezar el mes nuevo.`;

  abrirModal('📝 CIERRE DE MES', txt, [
    {txt:'❌ Cancelar',         color:'#7f8c8d', fn:'cerrarModal()'},
    {txt:'✅ Confirmar Cierre', color:'#c0392b', fn:'confirmarCierre()'}
  ]);
}

async function confirmarCierre() {
  cerrarModal();
  const fd = new FormData();
  fd.append('provincias', provincias.join(','));
  await fetch('/api/cierre/confirmar', {method:'POST', body:fd});
  currId = null;
  cargarTabla(); cargarBalance();
  alert('✅ Cierre confirmado. Mes reiniciado correctamente.');
}

// ── MODAL HELPER ─────────────────────────────────
function abrirModal(titulo, texto, botones) {
  document.getElementById('modal-titulo').textContent = titulo;
  document.getElementById('modal-texto').textContent  = texto;
  const bd = document.getElementById('modal-btns');
  bd.innerHTML = '';
  botones.forEach(b => {
    const btn = document.createElement('button');
    btn.textContent = b.txt;
    btn.style.background = b.color;
    btn.style.color = 'white';
    btn.onclick = () => eval(b.fn);
    bd.appendChild(btn);
  });
  document.getElementById('modal-overlay').classList.add('show');
}
function cerrarModal() {
  document.getElementById('modal-overlay').classList.remove('show');
}
document.getElementById('modal-overlay').onclick = e => {
  if (e.target === document.getElementById('modal-overlay')) cerrarModal();
};
</script>
</body>
</html>
