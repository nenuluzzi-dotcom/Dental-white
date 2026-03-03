import os, re, uuid, io, threading
from datetime import datetime
from zoneinfo import ZoneInfo
TZ_ARG = ZoneInfo('America/Argentina/Buenos_Aires')
from collections import defaultdict
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from supabase import create_client, Client
import pdfplumber
import pypdfium2 as pdfium
from PIL import Image

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://xejfkrzaofqjzvzjyovh.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
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

progreso_tareas = {}

# ── LOGIN ───────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def do_login(usuario: str = Form(...), clave: str = Form(...)):
    if clave.lower() != "union":
        raise HTTPException(401, "Clave incorrecta")
    if usuario not in PROVINCIAS:
        raise HTTPException(401, "Usuario invalido")
    return {"ok": True, "usuario": usuario, "provincias": PROVINCIAS[usuario]}

@app.get("/panel", response_class=HTMLResponse)
async def panel(request: Request):
    return templates.TemplateResponse("panel.html", {"request": request})

def _borrar_img(img_path: str):
    if not img_path or not img_path.startswith("http"):
        return
    try:
        if "/imagenes/" in img_path:
            nombre = "imagenes/" + img_path.split("/imagenes/")[-1].split("?")[0]
            supabase.storage.from_("cupones").remove([nombre])
    except:
        pass

# ── CUPONES ─────────────────────────────────────────────
@app.get("/api/cupones")
async def get_cupones(provincia: str, buscar: str = ""):
    hoy = datetime.now(TZ_ARG).strftime("%Y-%m-%d")
    q = supabase.table("cupones").select("*")\
        .or_(f"estado.eq.PENDIENTE,fecha_pago.eq.{hoy}")\
        .eq("provincia", provincia)
    if buscar:
        q = q.ilike("nombre", f"%{buscar}%")
    rows = q.order("fecha_cobro").execute().data

    conteo = defaultdict(int)
    for r in rows:
        if r["estado"] == "PENDIENTE":
            clave = r["cuenta"] if (r.get("cuenta") and r["cuenta"] != "S/D") else r["nombre"]
            conteo[clave] += 1

    for r in rows:
        clave = r["cuenta"] if (r.get("cuenta") and r["cuenta"] != "S/D") else r["nombre"]
        cant  = conteo.get(clave, 0)
        r["cuotas_pendientes"] = cant
        if r["estado"] == "PAGADO" or r.get("listo"):
            r["color"] = "verde"
        elif cant > 1:
            r["color"] = "naranja"
        else:
            r["color"] = ""
    return rows

@app.get("/api/cupones/hoy")
async def get_pagos_hoy(provincias: str = ""):
    hoy = datetime.now(TZ_ARG).strftime("%Y-%m-%d")
    todos = fetch_all(supabase.table("cupones").select("*").eq("fecha_pago", hoy).order("nombre"))
    # Filtrar por provincias del usuario si se pasan
    if provincias:
        provs = [p.strip().upper() for p in provincias.split(",") if p.strip()]
        if provs:
            todos = [r for r in todos if (r.get("provincia") or "").upper() in provs]
    return todos

@app.get("/api/cupon/{cupon_id}")
async def get_cupon(cupon_id: int):
    res = supabase.table("cupones").select("*").eq("id", cupon_id).execute()
    if not res.data:
        raise HTTPException(404, "No encontrado")
    return res.data[0]

@app.post("/api/cupon/{cupon_id}/pago")
async def registrar_pago(cupon_id: int, medio_pago: str = Form(...), comentario: str = Form("")):
    hoy = datetime.now(TZ_ARG).strftime("%Y-%m-%d")
    supabase.table("cupones").update({
        "estado": "PAGADO", "fecha_pago": hoy,
        "medio_pago": medio_pago, "comentario": comentario, "listo": True
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
    res = supabase.table("cupones").select("img_path").eq("id", cupon_id).execute()
    if res.data and res.data[0].get("img_path"):
        _borrar_img(res.data[0]["img_path"])
    supabase.table("cupones").delete().eq("id", cupon_id).execute()
    return {"ok": True}

@app.post("/api/cupon/agregar")
async def agregar_manual(provincia: str = Form(...)):
    supabase.table("cupones").insert({
        "nombre": "NUEVO", "provincia": provincia,
        "estado": "PENDIENTE", "monto": 0, "balance_inicial": 0
    }).execute()
    return {"ok": True}

# ── PROGRESO ────────────────────────────────────────────
@app.get("/api/progreso/{tarea_id}")
async def get_progreso(tarea_id: str):
    return progreso_tareas.get(tarea_id, {
        "pagina": 0, "total": 0, "detectados": 0,
        "saltados": 0, "estado": "procesando",
        "img_ok": 0, "img_total": 0
    })

# ── IMAGEN ON-DEMAND (renderiza 1 pagina al hacer click) ──
@app.get("/api/imagen/{cupon_id}")
async def get_imagen_cupon(cupon_id: int):
    """
    Descarga el PDF de Supabase, renderiza SOLO la pagina del cupon
    y devuelve el recorte como JPEG. Sin guardar nada en disco.
    """
    import logging, httpx, gc
    log = logging.getLogger("uvicorn.error")

    res = supabase.table("cupones").select("img_path").eq("id", cupon_id).execute()
    if not res.data or not res.data[0].get("img_path"):
        raise HTTPException(404, "Sin imagen")

    img_path = res.data[0]["img_path"]

    # Formato: REF|url_pdf|page_idx|y0_ratio|y1_ratio
    if not img_path.startswith("REF|"):
        # Es una URL directa de imagen vieja — redirigir
        from fastapi.responses import RedirectResponse
        return RedirectResponse(img_path)

    parts     = img_path.split("|")
    pdf_url   = parts[1]
    page_idx  = int(parts[2])
    y0r       = float(parts[3])
    y1r       = float(parts[4])

    try:
        # Descargar PDF
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(pdf_url)
            pdf_bytes = r.content

        # Renderizar UNA sola pagina con pypdfium2
        doc   = pdfium.PdfDocument(pdf_bytes)
        page  = doc[page_idx]
        SCALE = 96 / 72  # DPI 96
        bm    = page.render(scale=SCALE)
        img   = bm.to_pil()
        iw, ih = img.size
        doc.close()
        del pdf_bytes, bm
        gc.collect()

        # Recortar mitad derecha + franja vertical
        x0 = iw // 2
        y0 = max(0, int(ih * y0r))
        y1 = min(ih, int(ih * y1r))
        recorte = img.crop((x0, y0, iw, y1))
        del img
        gc.collect()

        buf = io.BytesIO()
        recorte.save(buf, format="JPEG", quality=82)
        jpeg_bytes = buf.getvalue()
        del recorte
        gc.collect()

        from fastapi.responses import Response as Resp
        return Resp(content=jpeg_bytes, media_type="image/jpeg",
                    headers={"Cache-Control": "public, max-age=3600"})

    except Exception as e:
        log.error(f"[IMG] on-demand fallo cupon={cupon_id}: {e}")
        raise HTTPException(500, f"Error renderizando imagen: {e}")

# ── PROCESAMIENTO PDF ───────────────────────────────────
def procesar_pdf_background(contenido: bytes, prov: str, tarea_id: str):
    import logging, traceback
    log = logging.getLogger("uvicorn.error")
    p   = progreso_tareas[tarea_id]
    KW  = ["DIRECCION","PROVINCIA","COBRO","PLAN","MONTO","CTA","TALON","RECUERDE"]

    try:
        # Subir PDF a Storage UNA sola vez (para el visor)
        pdf_nombre = f"pdfs/{tarea_id}.pdf"
        pdf_url    = ""
        try:
            supabase.storage.from_("cupones").upload(
                path=pdf_nombre, file=contenido,
                file_options={"content-type": "application/pdf"}
            )
            pdf_url = supabase.storage.from_("cupones").get_public_url(pdf_nombre)
            log.info(f"[PDF] Subido a storage: {pdf_url[:60]}...")
        except Exception as e:
            log.warning(f"[PDF] Storage fallo (continua sin imagen): {e}")

        # Anti-duplicado en memoria
        existentes = set()
        res_ex = supabase.table("cupones").select("cuenta,cta").eq("provincia", prov).execute()
        for r in res_ex.data:
            existentes.add((r.get("cuenta",""), r.get("cta","")))

        with pdfplumber.open(io.BytesIO(contenido)) as pdf:
            total = len(pdf.pages)
            p["total"] = total
            log.info(f"[PDF] {total} pags, prov={prov}")

            for idx, pagina in enumerate(pdf.pages):
                p["pagina"] = idx + 1

                pw, ph = float(pagina.width), float(pagina.height)
                anclas = pagina.search("ODONTOLOGIA POR ABONO MENSUAL")
                anclas_izq = sorted(
                    [f for f in anclas if f["x0"] < pw / 2],
                    key=lambda f: f["top"])
                if not anclas_izq:
                    continue

                for i, f in enumerate(anclas_izq):
                    y0 = max(0, f["top"] - 5)
                    y1 = anclas_izq[i+1]["top"] - 5 if i+1 < len(anclas_izq) else ph

                    txt_izq = pagina.within_bbox((0, y0, pw/2, y1)).extract_text() or ""
                    tel = "S/D"
                    m_tel = re.search(r"TELEF[OÓ]NOS?\s*[\|\s]*(.{0,80})", txt_izq, re.IGNORECASE)
                    if m_tel:
                        nums = re.findall(r"\d{8,12}", m_tel.group(1))
                        if nums: tel = nums[0]
                    if tel == "S/D":
                        nums = re.findall(r"\d{10}", txt_izq)
                        if nums: tel = nums[0]

                    txt_der = pagina.within_bbox((pw/2, y0, pw, y1)).extract_text() or ""

                    cta_n = "S/D"
                    mc = re.search(r"N[°º.\s]\s*(\d+)", txt_der)
                    if mc: cta_n = mc.group(1)

                    nom = "S/D"
                    if "AFILIADO" in txt_der.upper():
                        try:
                            parte  = txt_der.upper().split("AFILIADO")[1]
                            lineas = [l.strip() for l in parte.split("\n") if l.strip()]
                            parts  = []
                            for linea in lineas[:2]:
                                limpia = re.sub(r"[^A-Z\s]", "", linea).strip()
                                if limpia and not any(k in limpia for k in KW):
                                    parts.append(limpia)
                                else:
                                    break
                            nom = " ".join(parts).strip() or "S/D"
                        except: pass

                    monto = 0.0
                    if "$" in txt_der:
                        try:
                            mp = txt_der.split("$")[-1].split()[0]
                            ml = re.sub(r"[^\d]", "", mp.split(".")[0])
                            if ml: monto = float(ml)
                        except: pass

                    cta_cuota = "S/D"
                    mcu = re.search(r"\$\s*[\d.,]+\s+(\d{1,2})\s+\d{9,}", txt_der)
                    if mcu: cta_cuota = mcu.group(1)

                    f_cobro = ""
                    mf = re.search(r"(\d{2}/\d{2}/\d{4})", txt_der)
                    if mf: f_cobro = mf.group(1)

                    clave_dup = (cta_n, cta_cuota)
                    if cta_n != "S/D" and clave_dup in existentes:
                        p["saltados"] += 1
                        continue
                    existentes.add(clave_dup)

                    # img_path guarda referencia: URL_PDF|page_idx|y0_ratio|y1_ratio
                    # El endpoint /api/imagen/{id} renderiza solo esa pagina al hacer click
                    if pdf_url:
                        y0r = round(y0 / ph, 4)
                        y1r = round(y1 / ph, 4)
                        img_ref = f"REF|{pdf_url}|{idx}|{y0r}|{y1r}"
                    else:
                        img_ref = ""

                    supabase.table("cupones").insert({
                        "cuenta": cta_n, "nombre": nom, "monto": monto,
                        "cta": cta_cuota, "telefono": tel, "provincia": prov,
                        "img_path": img_ref, "balance_inicial": monto,
                        "fecha_cobro": f_cobro, "estado": "PENDIENTE",
                        "visto": 0, "listo": False
                    }).execute()
                    p["detectados"] += 1

        p["estado"] = "listo"
        log.info(f"[PDF] Listo: {p['detectados']} cupones, {p['saltados']} saltados")

    except Exception as e:
        p["estado"] = "error"
        p["error"]  = str(e)
        log.error(f"[PDF] ERROR: {traceback.format_exc()}")

@app.post("/api/subir_pdf")
async def subir_pdf(provincia: str = Form(...), archivo: UploadFile = File(...)):
    contenido = await archivo.read()
    tarea_id  = uuid.uuid4().hex
    prov      = provincia.strip().upper()
    progreso_tareas[tarea_id] = {
        "pagina": 0, "total": 0, "detectados": 0,
        "saltados": 0, "estado": "procesando",
        "img_ok": 0, "img_total": 0
    }
    threading.Thread(
        target=procesar_pdf_background,
        args=(contenido, prov, tarea_id),
        daemon=True
    ).start()
    return {"ok": True, "tarea_id": tarea_id}

# ── BALANCE ─────────────────────────────────────────────
def fetch_all(query):
    """Trae TODAS las filas superando el limite de 1000 de Supabase."""
    todas = []
    offset = 0
    while True:
        res = query.range(offset, offset + 999).execute()
        todas.extend(res.data)
        if len(res.data) < 1000:
            break
        offset += 1000
    return todas

@app.get("/api/balance")
async def get_balance(provincias: str):
    resultado = []
    for p in provincias.split(","):
        p = p.strip()
        res_all = fetch_all(supabase.table("cupones").select("cuenta,nombre").eq("provincia", p))
        claves  = set()
        for r in res_all:
            claves.add(r["cuenta"] if (r.get("cuenta") and r["cuenta"] != "S/D") else r["nombre"])
        res_pag = fetch_all(supabase.table("cupones").select("monto").eq("provincia", p).eq("estado", "PAGADO"))
        cobrado = sum(r["monto"] or 0 for r in res_pag)
        res_pen = fetch_all(supabase.table("cupones").select("cuenta,nombre,monto").eq("provincia", p).eq("estado", "PENDIENTE"))
        por_cli = defaultdict(list)
        for r in res_pen:
            clave = r["cuenta"] if (r.get("cuenta") and r["cuenta"] != "S/D") else r["nombre"]
            por_cli[clave].append(r["monto"] or 0)
        resultado.append({
            "provincia": p, "cant": len(claves),
            "inicial": sum(min(v) for v in por_cli.values()), "cobrado": cobrado
        })
    return resultado

@app.get("/api/balance_diario")
async def balance_diario(provincias: str = ""):
    hoy = datetime.now(TZ_ARG).strftime("%Y-%m-%d")
    pagos = fetch_all(supabase.table("cupones").select("*").eq("fecha_pago", hoy))
    if provincias:
        provs = [p.strip().upper() for p in provincias.split(",") if p.strip()]
        if provs:
            pagos = [r for r in pagos if (r.get("provincia") or "").upper() in provs]
    clientes = defaultdict(lambda: {"nombre":"","cuotas":[],"total":0.0,"medio":"","comentario":"","provincia":""})
    for r in pagos:
        key = r["cuenta"] if (r.get("cuenta") and r["cuenta"] != "S/D") else r["nombre"]
        clientes[key]["nombre"]     = r["nombre"] or ""
        clientes[key]["provincia"]  = r["provincia"] or ""
        clientes[key]["medio"]      = r["medio_pago"] or ""
        clientes[key]["comentario"] = r["comentario"] or ""
        clientes[key]["total"]     += r["monto"] or 0
        if r["cta"]: clientes[key]["cuotas"].append(str(r["cta"]))
    tg  = sum(c["total"] for c in clientes.values())
    tef = sum(c["total"] for c in clientes.values() if "EFECTIVO"  in (c["medio"] or "").upper())
    ttr = sum(c["total"] for c in clientes.values() if "TRANSFER"  in (c["medio"] or "").upper())
    tmp = sum(c["total"] for c in clientes.values() if "MERCADO"   in (c["medio"] or "").upper())
    tta = sum(c["total"] for c in clientes.values() if "TARJETA"   in (c["medio"] or "").upper())
    return {
        "fecha": datetime.now(TZ_ARG).strftime("%d/%m/%Y"),
        "total_clientes": len(clientes), "total_general": tg,
        "total_efectivo": tef, "total_transfer": ttr, "total_mp": tmp, "total_tarjeta": tta,
        "clientes": [{**v,"key":k,"cuotas_str":", ".join(v["cuotas"]),"multi":len(v["cuotas"])>1}
                     for k,v in sorted(clientes.items(), key=lambda x:(x[1]["provincia"],x[1]["nombre"]))]
    }

@app.get("/api/balance_diario/txt")
async def balance_diario_txt(provincias: str = ""):
    hoy = datetime.now(TZ_ARG).strftime("%Y-%m-%d")
    pagos = fetch_all(supabase.table("cupones").select("*").eq("fecha_pago", hoy))
    if provincias:
        provs = [p.strip().upper() for p in provincias.split(",") if p.strip()]
        if provs:
            pagos = [r for r in pagos if (r.get("provincia") or "").upper() in provs]
    clientes = defaultdict(lambda: {"nombre":"","cuotas":[],"total":0.0,"medio":"","comentario":"","provincia":""})
    for r in pagos:
        key = r["cuenta"] if (r.get("cuenta") and r["cuenta"] != "S/D") else r["nombre"]
        clientes[key]["nombre"]     = r["nombre"] or ""
        clientes[key]["provincia"]  = r["provincia"] or ""
        clientes[key]["medio"]      = r["medio_pago"] or ""
        clientes[key]["comentario"] = r["comentario"] or ""
        clientes[key]["total"]     += r["monto"] or 0
        if r["cta"]: clientes[key]["cuotas"].append(str(r["cta"]))
    tg  = sum(c["total"] for c in clientes.values())
    tef = sum(c["total"] for c in clientes.values() if "EFECTIVO"  in (c["medio"] or "").upper())
    ttr = sum(c["total"] for c in clientes.values() if "TRANSFER"  in (c["medio"] or "").upper())
    tmp = sum(c["total"] for c in clientes.values() if "MERCADO"   in (c["medio"] or "").upper())
    tta = sum(c["total"] for c in clientes.values() if "TARJETA"   in (c["medio"] or "").upper())
    fecha_fmt = datetime.now(TZ_ARG).strftime("%d/%m/%Y %H:%M")
    lineas = ["="*50,"     DENTAL WHITE - BALANCE DIARIO",f"     {fecha_fmt}","="*50,""]
    prov_act = ""
    for k,c in sorted(clientes.items(), key=lambda x:(x[1]["provincia"],x[1]["nombre"])):
        if c["provincia"] != prov_act:
            prov_act = c["provincia"]
            lineas += ["",f"  [ {prov_act} ]","-"*50]
        cuotas = f"  (cta/s: {', '.join(c['cuotas'])})" if c["cuotas"] else ""
        medio  = f"  [{c['medio']}]" if c["medio"] else ""
        nota   = f"  - {c['comentario']}" if c["comentario"] else ""
        lineas.append(f"  {c['nombre']:<30} $ {c['total']:>10,.0f}{medio}{cuotas}{nota}")
    lineas += ["","="*50,f"  CLIENTES: {len(clientes)}",f"  TOTAL:    $ {tg:>10,.0f}","-"*50]
    if tef: lineas.append(f"  Efectivo:       $ {tef:>10,.0f}")
    if ttr: lineas.append(f"  Transferencia:  $ {ttr:>10,.0f}")
    if tmp: lineas.append(f"  Mercado Pago:   $ {tmp:>10,.0f}")
    if tta: lineas.append(f"  Tarjeta:        $ {tta:>10,.0f}")
    lineas.append("="*50)
    nombre = f"balance_{datetime.now(TZ_ARG).strftime('%Y%m%d_%H%M')}.txt"
    return PlainTextResponse("\n".join(lineas), headers={"Content-Disposition": f"attachment; filename={nombre}"})

@app.get("/api/cierre")
async def cierre(provincias: str):
    hoy = datetime.now(TZ_ARG).strftime("%Y-%m-%d")
    resultado = []
    for p in provincias.split(","):
        p = p.strip()
        res_cob = supabase.table("cupones").select("monto").eq("provincia", p).eq("fecha_pago", hoy).execute()
        cobrado = sum(r["monto"] or 0 for r in res_cob.data)
        res_pen = supabase.table("cupones").select("cuenta,nombre,monto").eq("provincia", p).eq("estado", "PENDIENTE").execute()
        por_cli = defaultdict(list)
        for r in res_pen.data:
            clave = r["cuenta"] if (r.get("cuenta") and r["cuenta"] != "S/D") else r["nombre"]
            por_cli[clave].append(r["monto"] or 0)
        resultado.append({
            "provincia": p, "cobrado_cant": len(res_cob.data), "cobrado_monto": cobrado,
            "pendiente_cant": len(por_cli),
            "pendiente_monto": sum(min(v) for v in por_cli.values())
        })
    res_met = supabase.table("cupones").select("medio_pago,monto").eq("fecha_pago", hoy).execute()
    metodos = defaultdict(lambda: {"cant": 0, "monto": 0})
    for r in res_met.data:
        m = r["medio_pago"] or "SIN METODO"
        metodos[m]["cant"] += 1; metodos[m]["monto"] += r["monto"] or 0
    return {"provincias": resultado, "metodos": dict(metodos)}

@app.get("/api/cierre/txt")
async def cierre_txt(provincias: str):
    hoy = datetime.now(TZ_ARG).strftime("%Y-%m-%d")
    resultado = []
    for p in provincias.split(","):
        p = p.strip()
        res_cob = supabase.table("cupones").select("monto").eq("provincia", p).eq("fecha_pago", hoy).execute()
        cobrado = sum(r["monto"] or 0 for r in res_cob.data)
        res_pen = supabase.table("cupones").select("cuenta,nombre,monto").eq("provincia", p).eq("estado", "PENDIENTE").execute()
        por_cli = defaultdict(list)
        for r in res_pen.data:
            clave = r["cuenta"] if (r.get("cuenta") and r["cuenta"] != "S/D") else r["nombre"]
            por_cli[clave].append(r["monto"] or 0)
        resultado.append({
            "provincia": p, "cobrado_cant": len(res_cob.data), "cobrado_monto": cobrado,
            "pendiente_cant": len(por_cli),
            "pendiente_monto": sum(min(v) for v in por_cli.values())
        })
    res_met = supabase.table("cupones").select("medio_pago,monto").eq("fecha_pago", hoy).execute()
    metodos = defaultdict(lambda: {"cant": 0, "monto": 0})
    for r in res_met.data:
        m = r["medio_pago"] or "SIN METODO"
        metodos[m]["cant"] += 1; metodos[m]["monto"] += r["monto"] or 0
    fecha_fmt = datetime.now(TZ_ARG).strftime("%d/%m/%Y %H:%M")
    lineas = ["="*50,"     DENTAL WHITE - CIERRE DEL DIA",f"     {fecha_fmt}","="*50]
    tc, tp = 0, 0
    for r in resultado:
        lineas += ["",f"  PROVINCIA: {r['provincia']}","-"*50,
                   f"  Cobrado:    {r['cobrado_cant']} cliente/s  $ {r['cobrado_monto']:>10,.0f}",
                   f"  Pendiente:  {r['pendiente_cant']} cliente/s  $ {r['pendiente_monto']:>10,.0f}"]
        tc += r["cobrado_monto"]; tp += r["pendiente_monto"]
    lineas += ["","="*50,"  RESUMEN GENERAL","-"*50,
               f"  Total cobrado:   $ {tc:>10,.0f}",
               f"  Total pendiente: $ {tp:>10,.0f}","","  POR METODO:"]
    for m,v in metodos.items():
        lineas.append(f"    {m:<20} {v['cant']} pago/s  $ {v['monto']:>10,.0f}")
    lineas.append("="*50)
    nombre = f"cierre_{datetime.now(TZ_ARG).strftime('%Y%m%d_%H%M')}.txt"
    return PlainTextResponse("\n".join(lineas), headers={"Content-Disposition": f"attachment; filename={nombre}"})

@app.post("/api/cierre/confirmar")
async def cierre_confirmar(provincias: str = Form(...)):
    import logging
    log = logging.getLogger("uvicorn.error")
    for p in provincias.split(","):
        p = p.strip()
        res = supabase.table("cupones").select("img_path").eq("provincia", p).execute()
        for r in res.data:
            if r.get("img_path"):
                try: _borrar_img(r["img_path"])
                except: pass
        supabase.table("cupones").delete().eq("provincia", p).execute()
        log.info(f"[CIERRE] {p} borrado con imagenes")
    return {"ok": True}

@app.get("/api/iniciar_mes/preview")
async def iniciar_mes_preview(provincias: str):
    resultado = []
    for p in provincias.split(","):
        p = p.strip()
        res = supabase.table("cupones").select("cuenta,nombre,monto").eq("provincia", p).eq("estado", "PENDIENTE").execute()
        por_cli = defaultdict(list)
        for r in res.data:
            clave = r["cuenta"] if (r.get("cuenta") and r["cuenta"] != "S/D") else r["nombre"]
            por_cli[clave].append(r["monto"] or 0)
        resultado.append({
            "provincia": p, "clientes": len(por_cli),
            "cupones": len(res.data),
            "monto": sum(min(v) for v in por_cli.values())
        })
    return resultado
