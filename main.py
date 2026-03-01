import os, re, uuid, io
from datetime import datetime
from collections import defaultdict
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from supabase import create_client, Client
import cv2, numpy as np
from pdf2image import convert_from_bytes
import pdfplumber

# ── CONFIGURACIÓN ─────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://xejfkrzaofqjzvzjyovh.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
POPPLER_PATH = os.environ.get("POPPLER_PATH", None)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

PROVINCIAS = {
    "NENNELLA":       ["BUENOS AIRES", "CORRIENTES", "SANTIAGO DEL ESTERO"],
    "MICAELA":        ["POSADAS", "SANTA FE"],
    "ADMINISTRADORA": ["BUENOS AIRES", "CORRIENTES", "SANTIAGO DEL ESTERO", "POSADAS", "SANTA FE"]
}

# ── RUTAS PRINCIPALES ─────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def do_login(usuario: str = Form(...), clave: str = Form(...)):
    if clave.lower() != "union":
        raise HTTPException(status_code=401, detail="Clave incorrecta")
    if usuario not in PROVINCIAS:
        raise HTTPException(status_code=401, detail="Usuario inválido")
    return {"ok": True, "usuario": usuario, "provincias": PROVINCIAS[usuario]}

@app.get("/panel", response_class=HTMLResponse)
async def panel(request: Request):
    return templates.TemplateResponse("panel.html", {"request": request})

# ── CUPONES ───────────────────────────────────────
@app.get("/api/cupones")
async def get_cupones(provincia: str, buscar: str = ""):
    hoy = datetime.now().strftime("%Y-%m-%d")
    q = supabase.table("cupones").select("*")\
        .or_(f"estado.eq.PENDIENTE,fecha_pago.eq.{hoy}")\
        .eq("provincia", provincia)
    if buscar:
        q = q.ilike("nombre", f"%{buscar}%")
    res = q.order("fecha_cobro").execute()
    rows = res.data

    conteo = defaultdict(int)
    for r in rows:
        if r["estado"] == "PENDIENTE":
            clave = r["cuenta"] if (r.get("cuenta") and r["cuenta"] != "S/D") else r["nombre"]
            conteo[clave] += 1
    cuentas_multi = {k for k, v in conteo.items() if v > 1}

    for r in rows:
        clave = r["cuenta"] if (r.get("cuenta") and r["cuenta"] != "S/D") else r["nombre"]
        if r["estado"] == "PAGADO" or r.get("listo"):
            r["color"] = "verde"
        elif clave in cuentas_multi:
            r["color"] = "naranja"
        else:
            r["color"] = ""
    return rows

@app.get("/api/cupones/hoy")
async def get_pagos_hoy():
    hoy = datetime.now().strftime("%Y-%m-%d")
    res = supabase.table("cupones").select("*").eq("fecha_pago", hoy).order("nombre").execute()
    return res.data

@app.get("/api/cupon/{cupon_id}")
async def get_cupon(cupon_id: int):
    res = supabase.table("cupones").select("*").eq("id", cupon_id).execute()
    if not res.data:
        raise HTTPException(404, "No encontrado")
    return res.data[0]

@app.post("/api/cupon/{cupon_id}/pago")
async def registrar_pago(cupon_id: int, medio_pago: str = Form(...), comentario: str = Form("")):
    hoy = datetime.now().strftime("%Y-%m-%d")
    supabase.table("cupones").update({
        "estado": "PAGADO", "fecha_pago": hoy,
        "medio_pago": medio_pago, "comentario": comentario, "listo": True
    }).eq("id", cupon_id).execute()
    return {"ok": True}

@app.post("/api/cupon/{cupon_id}/impago")
async def marcar_impago(cupon_id: int):
    supabase.table("cupones").update({
        "estado": "PENDIENTE", "fecha_pago": None, "medio_pago": None, "listo": False
    }).eq("id", cupon_id).execute()
    return {"ok": True}

@app.post("/api/cupon/{cupon_id}/visto")
async def marcar_visto(cupon_id: int):
    supabase.table("cupones").update({"visto": 1}).eq("id", cupon_id).execute()
    return {"ok": True}

@app.post("/api/cupon/{cupon_id}/guardar")
async def guardar_cupon(cupon_id: int, cuenta: str = Form(""), nombre: str = Form(""),
                         monto: str = Form(""), cta: str = Form(""),
                         fecha_cobro: str = Form(""), telefono: str = Form(""),
                         comentario: str = Form("")):
    supabase.table("cupones").update({
        "cuenta": cuenta, "nombre": nombre,
        "monto": float(monto) if monto else 0,
        "cta": cta, "fecha_cobro": fecha_cobro,
        "telefono": telefono, "comentario": comentario, "listo": True
    }).eq("id", cupon_id).execute()
    return {"ok": True}

@app.delete("/api/cupon/{cupon_id}")
async def eliminar_cupon(cupon_id: int):
    supabase.table("cupones").delete().eq("id", cupon_id).execute()
    return {"ok": True}

@app.post("/api/cupon/agregar")
async def agregar_manual(provincia: str = Form(...)):
    supabase.table("cupones").insert({
        "nombre": "NUEVO", "provincia": provincia,
        "estado": "PENDIENTE", "monto": 0, "balance_inicial": 0
    }).execute()
    return {"ok": True}

@app.get("/api/cupon/{cupon_id}/imagen")
async def get_imagen(cupon_id: int):
    res = supabase.table("cupones").select("img_path").eq("id", cupon_id).execute()
    if not res.data or not res.data[0].get("img_path"):
        raise HTTPException(404, "Sin imagen")
    return {"url": res.data[0]["img_path"]}

# ── PROGRESO OCR ──────────────────────────────────
progreso_tareas = {}

@app.get("/api/progreso/{tarea_id}")
async def get_progreso(tarea_id: str):
    return progreso_tareas.get(tarea_id, {"pagina": 0, "total": 0, "detectados": 0, "estado": "procesando"})

# ── SUBIR PDF ─────────────────────────────────────
@app.post("/api/subir_pdf")
async def subir_pdf(provincia: str = Form(...), archivo: UploadFile = File(...)):
    contenido = await archivo.read()
    detectados = 0
    saltados = 0
    prov_actual = provincia.strip().upper()
    tarea_id = uuid.uuid4().hex
    progreso_tareas[tarea_id] = {"pagina": 0, "total": 0, "detectados": 0, "saltados": 0, "estado": "procesando"}

    try:
        with pdfplumber.open(io.BytesIO(contenido)) as pdf:
            total = len(pdf.pages)
            progreso_tareas[tarea_id]["total"] = total

            for idx, pagina in enumerate(pdf.pages):
                progreso_tareas[tarea_id]["pagina"] = idx + 1
                pw, ph = float(pagina.width), float(pagina.height)
                anclas = pagina.search("ODONTOLOGIA POR ABONO MENSUAL")
                anclas_izq = sorted([f for f in anclas if f['x0'] < pw / 2], key=lambda f: f['top'])
                if not anclas_izq:
                    continue

                pdf_kwargs = {"first_page": idx+1, "last_page": idx+1, "dpi": 200}
                if POPPLER_PATH:
                    pdf_kwargs["poppler_path"] = POPPLER_PATH
                imgs = convert_from_bytes(contenido, **pdf_kwargs)
                img_pil = imgs[0]
                img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
                hi, wi = img_cv.shape[:2]
                escala_y = hi / ph
                escala_x = wi / pw

                for i, f in enumerate(anclas_izq):
                    y0_pdf = max(0, f['top'] - 5)
                    y1_pdf = anclas_izq[i+1]['top'] - 5 if i+1 < len(anclas_izq) else ph

                    txt_izq = pagina.within_bbox((0, y0_pdf, pw/2, y1_pdf)).extract_text() or ""
                    tel = "S/D"
                    m_tel = re.search(r'TELEF[OÓ]NOS?\s*[\|\s]*(.{0,80})', txt_izq, re.IGNORECASE)
                    if m_tel:
                        nums = re.findall(r'\d{8,12}', m_tel.group(1))
                        if nums: tel = nums[0]
                    if tel == "S/D":
                        nums = re.findall(r'\d{10}', txt_izq)
                        if nums: tel = nums[0]

                    txt_der = pagina.within_bbox((pw/2, y0_pdf, pw, y1_pdf)).extract_text() or ""
                    cta_n = "S/D"
                    m_cta = re.search(r'N[°º.\s]\s*(\d+)', txt_der)
                    if m_cta: cta_n = m_cta.group(1)

                    nom = "S/D"
                    KW = ['DIRECCION','PROVINCIA','COBRO','PLAN','MONTO','CTA','TALON','RECUERDE']
                    if "AFILIADO" in txt_der.upper():
                        try:
                            parte = txt_der.upper().split("AFILIADO")[1]
                            lineas = [l.strip() for l in parte.split('\n') if l.strip()]
                            parts = []
                            for linea in lineas[:2]:
                                limpia = re.sub(r'[^A-Z\s]', '', linea).strip()
                                if limpia and not any(k in limpia for k in KW):
                                    parts.append(limpia)
                                else:
                                    break
                            nom = ' '.join(parts).strip() or "S/D"
                        except: pass

                    monto = 0.0
                    if "$" in txt_der:
                        try:
                            mp = txt_der.split("$")[-1].split()[0]
                            ml = re.sub(r'[^\d]', '', mp.split('.')[0])
                            if ml: monto = float(ml)
                        except: pass

                    cta_cuota = "S/D"
                    mc = re.search(r'\$\s*[\d.,]+\s+(\d{1,2})\s+\d{9,}', txt_der)
                    if mc: cta_cuota = mc.group(1)

                    f_cobro = ""
                    mf = re.search(r'(\d{2}/\d{2}/\d{4})', txt_der)
                    if mf: f_cobro = mf.group(1)

                    # ── ANTI-DUPLICADOS: verificar si ya existe cuenta+mes ──
                    if cta_n != "S/D":
                        existente = supabase.table("cupones").select("id")\
                            .eq("cuenta", cta_n)\
                            .eq("provincia", prov_actual)\
                            .execute()
                        if existente.data and len(existente.data) > 0:
                            saltados += 1
                            progreso_tareas[tarea_id]["saltados"] = saltados
                            continue

                    y0_img = int(y0_pdf * escala_y)
                    y1_img = int(y1_pdf * escala_y)
                    x0_img = int((pw/2) * escala_x)
                    recorte = img_cv[y0_img:y1_img, x0_img:wi]

                    img_url = ""
                    if recorte.size > 0:
                        try:
                            nombre_img = f"{uuid.uuid4().hex}.jpg"
                            _, buf = cv2.imencode('.jpg', recorte, [cv2.IMWRITE_JPEG_QUALITY, 85])
                            supabase.storage.from_("cupones").upload(
                                path=nombre_img,
                                file=buf.tobytes(),
                                file_options={"content-type": "image/jpeg"}
                            )
                            img_url = supabase.storage.from_("cupones").get_public_url(nombre_img)
                        except Exception:
                            img_url = ""

                    supabase.table("cupones").insert({
                        "cuenta": cta_n, "nombre": nom, "monto": monto,
                        "cta": cta_cuota, "telefono": tel, "provincia": prov_actual,
                        "img_path": img_url, "balance_inicial": monto,
                        "fecha_cobro": f_cobro, "estado": "PENDIENTE", "visto": 0, "listo": False
                    }).execute()
                    detectados += 1
                    progreso_tareas[tarea_id]["detectados"] = detectados

        progreso_tareas[tarea_id]["estado"] = "listo"
        return {"ok": True, "detectados": detectados, "saltados": saltados, "paginas": total, "tarea_id": tarea_id}
    except Exception as e:
        progreso_tareas[tarea_id]["estado"] = "error"
        import traceback
        raise HTTPException(500, str(e) + "\n" + traceback.format_exc()[-800:])

# ── BALANCE ──────────────────────────────────────
@app.get("/api/balance")
async def get_balance(provincias: str):
    provs = provincias.split(",")
    resultado = []
    for p in provs:
        res = supabase.table("cupones").select("cuenta,nombre").eq("provincia", p.strip()).execute()
        claves = set()
        for r in res.data:
            claves.add(r["cuenta"] if (r.get("cuenta") and r["cuenta"] != "S/D") else r["nombre"])

        res2 = supabase.table("cupones").select("monto").eq("provincia", p.strip()).eq("estado", "PAGADO").execute()
        cobrado = sum(r["monto"] or 0 for r in res2.data)

        res3 = supabase.table("cupones").select("cuenta,nombre,monto").eq("provincia", p.strip()).eq("estado", "PENDIENTE").execute()
        por_cliente = defaultdict(list)
        for r in res3.data:
            clave = r["cuenta"] if (r.get("cuenta") and r["cuenta"] != "S/D") else r["nombre"]
            por_cliente[clave].append(r["monto"] or 0)
        inicial = sum(min(v) for v in por_cliente.values())

        resultado.append({"provincia": p.strip(), "cant": len(claves), "inicial": inicial, "cobrado": cobrado})
    return resultado

# ── BALANCE DIARIO ────────────────────────────────
@app.get("/api/balance_diario")
async def balance_diario():
    hoy = datetime.now().strftime("%Y-%m-%d")
    res = supabase.table("cupones").select("*").eq("fecha_pago", hoy).execute()
    clientes = defaultdict(lambda: {"nombre": "", "cuotas": [], "total": 0.0, "medio": "", "comentario": "", "provincia": ""})
    for r in res.data:
        key = r["cuenta"] if (r.get("cuenta") and r["cuenta"] != "S/D") else r["nombre"]
        clientes[key]["nombre"] = r["nombre"] or ""
        clientes[key]["provincia"] = r["provincia"] or ""
        clientes[key]["medio"] = r["medio_pago"] or ""
        clientes[key]["comentario"] = r["comentario"] or ""
        clientes[key]["total"] += r["monto"] or 0
        if r["cta"]: clientes[key]["cuotas"].append(str(r["cta"]))

    total_general  = sum(c["total"] for c in clientes.values())
    total_efectivo = sum(c["total"] for c in clientes.values() if "EFECTIVO" in (c["medio"] or "").upper())
    total_transfer = sum(c["total"] for c in clientes.values() if "TRANSFER" in (c["medio"] or "").upper())
    total_mp       = sum(c["total"] for c in clientes.values() if "MERCADO"  in (c["medio"] or "").upper())
    total_tarjeta  = sum(c["total"] for c in clientes.values() if "TARJETA"  in (c["medio"] or "").upper())

    return {
        "fecha": datetime.now().strftime("%d/%m/%Y"),
        "total_clientes": len(clientes), "total_general": total_general,
        "total_efectivo": total_efectivo, "total_transfer": total_transfer,
        "total_mp": total_mp, "total_tarjeta": total_tarjeta,
        "clientes": [{**v, "key": k, "cuotas_str": ", ".join(v["cuotas"]), "multi": len(v["cuotas"]) > 1}
                     for k, v in sorted(clientes.items(), key=lambda x: (x[1]["provincia"], x[1]["nombre"]))]
    }

# ── EXPORTAR BALANCE COMO TXT ─────────────────────
@app.get("/api/balance_diario/txt")
async def balance_diario_txt():
    hoy = datetime.now().strftime("%Y-%m-%d")
    res = supabase.table("cupones").select("*").eq("fecha_pago", hoy).execute()
    clientes = defaultdict(lambda: {"nombre": "", "cuotas": [], "total": 0.0, "medio": "", "comentario": "", "provincia": ""})
    for r in res.data:
        key = r["cuenta"] if (r.get("cuenta") and r["cuenta"] != "S/D") else r["nombre"]
        clientes[key]["nombre"] = r["nombre"] or ""
        clientes[key]["provincia"] = r["provincia"] or ""
        clientes[key]["medio"] = r["medio_pago"] or ""
        clientes[key]["comentario"] = r["comentario"] or ""
        clientes[key]["total"] += r["monto"] or 0
        if r["cta"]: clientes[key]["cuotas"].append(str(r["cta"]))

    total_general  = sum(c["total"] for c in clientes.values())
    total_efectivo = sum(c["total"] for c in clientes.values() if "EFECTIVO" in (c["medio"] or "").upper())
    total_transfer = sum(c["total"] for c in clientes.values() if "TRANSFER" in (c["medio"] or "").upper())
    total_mp       = sum(c["total"] for c in clientes.values() if "MERCADO"  in (c["medio"] or "").upper())
    total_tarjeta  = sum(c["total"] for c in clientes.values() if "TARJETA"  in (c["medio"] or "").upper())

    fecha_fmt = datetime.now().strftime("%d/%m/%Y %H:%M")
    lineas = []
    lineas.append("=" * 50)
    lineas.append("         DENTAL WHITE - BALANCE DIARIO")
    lineas.append(f"         {fecha_fmt}")
    lineas.append("=" * 50)
    lineas.append("")

    prov_actual = ""
    for k, c in sorted(clientes.items(), key=lambda x: (x[1]["provincia"], x[1]["nombre"])):
        if c["provincia"] != prov_actual:
            prov_actual = c["provincia"]
            lineas.append("")
            lineas.append(f"  [ {prov_actual} ]")
            lineas.append("-" * 50)
        cuotas_str = f"  (cuota/s: {', '.join(c['cuotas'])})" if c["cuotas"] else ""
        medio_str = f"  [{c['medio']}]" if c["medio"] else ""
        comentario_str = f"  - {c['comentario']}" if c["comentario"] else ""
        lineas.append(f"  {c['nombre']:<30} $ {c['total']:>10,.0f}{medio_str}{cuotas_str}{comentario_str}")

    lineas.append("")
    lineas.append("=" * 50)
    lineas.append(f"  TOTAL CLIENTES: {len(clientes)}")
    lineas.append(f"  TOTAL GENERAL:  $ {total_general:>10,.0f}")
    lineas.append("-" * 50)
    if total_efectivo:  lineas.append(f"  Efectivo:       $ {total_efectivo:>10,.0f}")
    if total_transfer:  lineas.append(f"  Transferencia:  $ {total_transfer:>10,.0f}")
    if total_mp:        lineas.append(f"  Mercado Pago:   $ {total_mp:>10,.0f}")
    if total_tarjeta:   lineas.append(f"  Tarjeta:        $ {total_tarjeta:>10,.0f}")
    lineas.append("=" * 50)

    contenido_txt = "\n".join(lineas)
    nombre_archivo = f"balance_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"

    return PlainTextResponse(
        content=contenido_txt,
        headers={"Content-Disposition": f"attachment; filename={nombre_archivo}"}
    )

# ── EXPORTAR CIERRE COMO TXT ──────────────────────
@app.get("/api/cierre/txt")
async def cierre_txt(provincias: str):
    hoy = datetime.now().strftime("%Y-%m-%d")
    provs = provincias.split(",")
    resultado = []
    for p in provs:
        res_cob = supabase.table("cupones").select("cuenta,nombre,monto,medio_pago").eq("provincia", p.strip()).eq("fecha_pago", hoy).execute()
        cobrado = sum(r["monto"] or 0 for r in res_cob.data)
        res_pend = supabase.table("cupones").select("cuenta,nombre,monto").eq("provincia", p.strip()).eq("estado", "PENDIENTE").execute()
        por_cliente = defaultdict(list)
        for r in res_pend.data:
            clave = r["cuenta"] if (r.get("cuenta") and r["cuenta"] != "S/D") else r["nombre"]
            por_cliente[clave].append(r["monto"] or 0)
        resultado.append({
            "provincia": p.strip(),
            "cobrado_cant": len(res_cob.data), "cobrado_monto": cobrado,
            "pendiente_cant": len(por_cliente),
            "pendiente_monto": sum(min(v) for v in por_cliente.values()),
            "detalle_cobrado": res_cob.data
        })

    res_met = supabase.table("cupones").select("medio_pago,monto").eq("fecha_pago", hoy).execute()
    metodos = defaultdict(lambda: {"cant": 0, "monto": 0})
    for r in res_met.data:
        m = r["medio_pago"] or "SIN MÉTODO"
        metodos[m]["cant"] += 1
        metodos[m]["monto"] += r["monto"] or 0

    fecha_fmt = datetime.now().strftime("%d/%m/%Y %H:%M")
    lineas = []
    lineas.append("=" * 50)
    lineas.append("         DENTAL WHITE - CIERRE DEL DIA")
    lineas.append(f"         {fecha_fmt}")
    lineas.append("=" * 50)

    total_cobrado_gral = 0
    total_pendiente_gral = 0
    for r in resultado:
        lineas.append("")
        lineas.append(f"  PROVINCIA: {r['provincia']}")
        lineas.append("-" * 50)
        lineas.append(f"  Cobrado hoy:  {r['cobrado_cant']} cliente/s  $ {r['cobrado_monto']:>10,.0f}")
        lineas.append(f"  Pendiente:    {r['pendiente_cant']} cliente/s  $ {r['pendiente_monto']:>10,.0f}")
        total_cobrado_gral += r["cobrado_monto"]
        total_pendiente_gral += r["pendiente_monto"]

    lineas.append("")
    lineas.append("=" * 50)
    lineas.append("  RESUMEN GENERAL")
    lineas.append("-" * 50)
    lineas.append(f"  Total cobrado:   $ {total_cobrado_gral:>10,.0f}")
    lineas.append(f"  Total pendiente: $ {total_pendiente_gral:>10,.0f}")
    lineas.append("")
    lineas.append("  POR METODO DE PAGO:")
    for m, v in metodos.items():
        lineas.append(f"    {m:<20} {v['cant']} pago/s  $ {v['monto']:>10,.0f}")
    lineas.append("=" * 50)

    contenido_txt = "\n".join(lineas)
    nombre_archivo = f"cierre_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"

    return PlainTextResponse(
        content=contenido_txt,
        headers={"Content-Disposition": f"attachment; filename={nombre_archivo}"}
    )

# ── CIERRE ────────────────────────────────────────
@app.get("/api/cierre")
async def cierre(provincias: str):
    hoy = datetime.now().strftime("%Y-%m-%d")
    provs = provincias.split(",")
    resultado = []
    for p in provs:
        res_cob = supabase.table("cupones").select("monto").eq("provincia", p.strip()).eq("fecha_pago", hoy).execute()
        cobrado = sum(r["monto"] or 0 for r in res_cob.data)
        res_pend = supabase.table("cupones").select("cuenta,nombre,monto").eq("provincia", p.strip()).eq("estado", "PENDIENTE").execute()
        por_cliente = defaultdict(list)
        for r in res_pend.data:
            clave = r["cuenta"] if (r.get("cuenta") and r["cuenta"] != "S/D") else r["nombre"]
            por_cliente[clave].append(r["monto"] or 0)
        resultado.append({
            "provincia": p.strip(),
            "cobrado_cant": len(res_cob.data), "cobrado_monto": cobrado,
            "pendiente_cant": len(por_cliente),
            "pendiente_monto": sum(min(v) for v in por_cliente.values())
        })
    res_met = supabase.table("cupones").select("medio_pago,monto").eq("fecha_pago", hoy).execute()
    metodos = defaultdict(lambda: {"cant": 0, "monto": 0})
    for r in res_met.data:
        m = r["medio_pago"] or "SIN MÉTODO"
        metodos[m]["cant"] += 1
        metodos[m]["monto"] += r["monto"] or 0
    return {"provincias": resultado, "metodos": dict(metodos)}

@app.post("/api/cierre/confirmar")
async def cierre_confirmar(provincias: str = Form(...)):
    for p in provincias.split(","):
        supabase.table("cupones").delete().eq("provincia", p.strip()).execute()
    return {"ok": True}

@app.get("/api/iniciar_mes/preview")
async def iniciar_mes_preview(provincias: str):
    provs = provincias.split(",")
    resultado = []
    for p in provs:
        res = supabase.table("cupones").select("cuenta,nombre,monto").eq("provincia", p.strip()).eq("estado", "PENDIENTE").execute()
        por_cliente = defaultdict(list)
        for r in res.data:
            clave = r["cuenta"] if (r.get("cuenta") and r["cuenta"] != "S/D") else r["nombre"]
            por_cliente[clave].append(r["monto"] or 0)
        resultado.append({
            "provincia": p.strip(), "clientes": len(por_cliente),
            "cupones": len(res.data), "monto": sum(min(v) for v in por_cliente.values())
        })
    return resultado
