import os
import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict, field

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

load_dotenv()

REPORTS_DIR = Path(os.getenv("REPORTS_DIR", "reports")).expanduser().resolve()
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="QC Dispositivos", page_icon="✅", layout="wide")

@dataclass
class ChecklistItem:
    descripcion: str
    estado: str = ""
    observacion: str = ""

@dataclass
class Seccion:
    titulo: str
    items: list[ChecklistItem] = field(default_factory=list)
    observacion_general: str = ""

@dataclass
class InformeQC:
    identificador: str
    modelo: str
    cliente: str
    fecha_inspeccion: str
    fecha_fabricacion: str
    documento: str
    secciones: list[Seccion]
    creado_en: str

def secciones_por_defecto() -> list[Seccion]:
    return [
        Seccion(
            titulo="REVISIONES ELÉCTRICAS",
            items=[
                ChecklistItem("Consumo total (0.7A – 0.9A)"),
                ChecklistItem("Revisión de cortocircuitos"),
                ChecklistItem("Revisión visual de conexiones"),
                ChecklistItem("Tensión de alimentación del procesador"),
            ],
        ),
        Seccion(
            titulo="REVISIONES DE SOFTWARE",
            items=[
                ChecklistItem("Conexión WiFi"),
                ChecklistItem("Señal de Apagar con fuente de alimentación"),
                ChecklistItem("Conexión Ethernet"),
                ChecklistItem("Señal de Reinicio con fuente de alimentación"),
                ChecklistItem("Configuración de fecha y hora"),
                ChecklistItem("Lectura CAN"),
                ChecklistItem("Configuración"),
                ChecklistItem("Descarga de datos automática"),
            ],
        ),
        Seccion(
            titulo="REVISIONES DE HARDWARE",
            items=[
                ChecklistItem("Tornillos conector militar 19 pines"),
                ChecklistItem("Temperatura (70 – 80 ºC)"),
                ChecklistItem("Tornillos conector militar 6 pines"),
                ChecklistItem("Revisión visual de la carcasa"),
                ChecklistItem("Tornillos ventilador"),
                ChecklistItem("Funcionamiento del ventilador"),
                ChecklistItem("Tornillos disipador"),
                ChecklistItem("Colocación de las baterías"),
                ChecklistItem("Tornillos carcasa"),
                ChecklistItem("Revisión de soldaduras"),
                ChecklistItem("Tornillo placa relé"),
                ChecklistItem("Revisión de cableado"),
            ],
        ),
    ]

def radio_estado(key: str) -> str:
    return st.radio(key, ["", "OK", "NOK", "N/A"], index=0, horizontal=True, label_visibility="collapsed")

def construir_pdf(informe: InformeQC, destino_pdf: Path) -> None:
    estilos = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(destino_pdf), pagesize=A4, topMargin=24, leftMargin=24, rightMargin=24, bottomMargin=24)
    contenido = []
    contenido += [Paragraph(f"Informe de Control de Calidad — {informe.identificador}", estilos["Title"]), Spacer(1, 8)]
    meta = [
        ["N.º Identificador", informe.identificador, "Fecha de inspección", informe.fecha_inspeccion],
        ["Modelo", informe.modelo, "Fecha de fabricación", informe.fecha_fabricacion],
        ["Cliente", informe.cliente, "N.º de documento", informe.documento],
        ["Creado en", informe.creado_en, "", ""],
    ]
    tmeta = Table(meta, colWidths=[110, 180, 140, 120])
    tmeta.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.5,colors.black),("BACKGROUND",(0,0),(-1,0),colors.whitesmoke),("VALIGN",(0,0),(-1,-1),"MIDDLE")]))
    contenido += [tmeta, Spacer(1, 12)]
    for seccion in informe.secciones:
        contenido.append(Paragraph(seccion.titulo, estilos["Heading2"]))
        data = [["Descripción", "Estado", "Observación"]]
        for it in seccion.items:
            data.append([it.descripcion, it.estado or "-", it.observacion or "-"])
        tabla = Table(data, colWidths=[260, 70, 220])
        tabla.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.5,colors.black),("BACKGROUND",(0,0),(-1,0),colors.lightgrey),("VALIGN",(0,0),(-1,-1),"TOP")]))
        contenido += [tabla]
        if seccion.observacion_general.strip():
            contenido += [Spacer(1, 6), Paragraph(f"Observaciones: {seccion.observacion_general}", estilos["Normal"])]
        contenido.append(Spacer(1, 12))
    doc.build(contenido)

def guardar_informe(informe: InformeQC, base_dir: Path | None = None) -> tuple[Path, Path]:
    base_root = Path(base_dir) if base_dir else REPORTS_DIR
    base = base_root / informe.identificador
    base.mkdir(parents=True, exist_ok=True)
    json_path = base / f"{informe.identificador}.json"
    pdf_path = base / f"{informe.identificador}.pdf"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(asdict(informe), f, ensure_ascii=False, indent=2)
    construir_pdf(informe, pdf_path)
    return json_path, pdf_path

def cargar_informes() -> pd.DataFrame:
    rows = []
    for jf in REPORTS_DIR.rglob("*.json"):
        try:
            with jf.open(encoding="utf-8") as f:
                data = json.load(f)
            rows.append({
                "identificador": data.get("identificador",""),
                "modelo": data.get("modelo",""),
                "cliente": data.get("cliente",""),
                "fecha_inspeccion": data.get("fecha_inspeccion",""),
                "fecha_fabricacion": data.get("fecha_fabricacion",""),
                "documento": data.get("documento",""),
                "creado_en": data.get("creado_en",""),
                "carpeta": str(Path(jf).parent),
                "json": str(jf),
                "pdf": str(Path(jf).with_suffix(".pdf")),
            })
        except Exception:
            continue
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(by="creado_en", ascending=False)
    return df

def ui_seccion(seccion: Seccion, key_prefix: str) -> Seccion:
    st.subheader(seccion.titulo)
    for i, item in enumerate(seccion.items):
        c1, c2, c3 = st.columns([3,1,3])
        with c1: st.markdown(item.descripcion)
        with c2: estado = radio_estado(f"{key_prefix}_estado_{i}")
        with c3: obs = st.text_input(" ", key=f"{key_prefix}_obs_{i}", label_visibility="collapsed", placeholder="Observaciones")
        seccion.items[i] = ChecklistItem(item.descripcion, estado, obs)
    seccion.observacion_general = st.text_area("Observaciones generales", key=f"{key_prefix}_obs_general", placeholder="Incidencias y medidas a tomar")
    st.divider()
    return seccion

def pagina_nuevo_informe():
    st.header("Nuevo informe")
    c1, c2 = st.columns(2)
    with c1:
        identificador = st.text_input("N.º Identificador")
        modelo = st.text_input("Modelo")
        cliente = st.text_input("Cliente")
    with c2:
        fecha_inspeccion = st.date_input("Fecha de inspección", value=datetime.today()).strftime("%d/%m/%Y")
        fecha_fabricacion = st.text_input("Fecha de fabricación", value=datetime.today().strftime("%m/%Y"))
        documento = st.text_input("N.º de documento")

    st.info(f"Ubicación por defecto: {REPORTS_DIR}")

    if "secciones" not in st.session_state:
        st.session_state.secciones = secciones_por_defecto()

    secciones_actualizadas = [ui_seccion(sec, f"sec{i}") for i, sec in enumerate(st.session_state.secciones)]

    preparar = st.button("Preparar guardado…", use_container_width=True, type="primary")

    if preparar:
        if not identificador.strip():
            st.error("El N.º Identificador es obligatorio")
            return
        st.session_state.informe_pendiente = InformeQC(
            identificador=identificador.strip(),
            modelo=modelo.strip(),
            cliente=cliente.strip(),
            fecha_inspeccion=fecha_inspeccion,
            fecha_fabricacion=fecha_fabricacion.strip(),
            documento=documento.strip(),
            secciones=secciones_actualizadas,
            creado_en=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        st.session_state.dir_guardado = str(REPORTS_DIR)
        st.session_state.confirmar_guardado = True

    if st.session_state.get("confirmar_guardado"):
        st.subheader("Confirmar ubicación de guardado")
        st.info("Se guardará en la carpeta indicada; puedes modificarla.")
        nueva_ruta = st.text_input(
            "Ubicación de guardado",
            value=st.session_state.get("dir_guardado", str(REPORTS_DIR)),
            help="Rutas absolutas o relativas. Se crea si no existe."
        )
        cok, ccancel = st.columns(2)
        with cok: confirmar = st.button("Confirmar y guardar", use_container_width=True)
        with ccancel: cancelar = st.button("Cancelar", use_container_width=True)

        if cancelar:
            st.session_state.confirmar_guardado = False
            st.session_state.informe_pendiente = None
            st.stop()

        if confirmar:
            try:
                destino = Path(nueva_ruta).expanduser().resolve()
                destino.mkdir(parents=True, exist_ok=True)
                informe = st.session_state.informe_pendiente
                _, pdf_path = guardar_informe(informe, base_dir=destino)
                with open(pdf_path, "rb") as f:
                    st.success(f"Informe guardado en {pdf_path}")
                    st.download_button("Descargar PDF", f.read(), file_name=pdf_path.name, use_container_width=True)
                st.session_state.confirmar_guardado = False
                st.session_state.informe_pendiente = None
            except Exception as e:
                st.error(f"No se pudo guardar el informe: {e}")
                st.stop()

def pagina_consultar():
    st.header("Consultar informes")
    df = cargar_informes()
    if df.empty:
        st.info("No hay informes aún.")
        return
    buscador = st.text_input("Buscar por identificador/cliente/modelo")
    if buscador:
        mask = (
            df.identificador.str.contains(buscador, case=False, na=False) |
            df.cliente.str.contains(buscador, case=False, na=False) |
            df.modelo.str.contains(buscador, case=False, na=False)
        )
        df = df[mask]
    st.dataframe(df[["identificador","cliente","modelo","fecha_inspeccion","creado_en","carpeta"]].reset_index(drop=True), use_container_width=True, hide_index=True)
    if not df.empty:
        seleccion = st.selectbox("Selecciona un informe", df["identificador"].tolist())
        fila = df[df["identificador"] == seleccion].iloc[0]
        ca, cb = st.columns(2)
        with ca:
            st.write(f"Carpeta: {fila.carpeta}")
            st.write(f"Creado: {fila.creado_en}")
        with cb:
            pdf = Path(fila.pdf)
            if pdf.exists():
                with open(pdf, "rb") as f:
                    st.download_button("Descargar PDF", f.read(), file_name=pdf.name, use_container_width=True)
            else:
                st.warning("PDF no encontrado")
        jf = Path(fila.json)
        if jf.exists():
            with jf.open("r", encoding="utf-8") as f:
                st.expander("Vista rápida del contenido").json(json.load(f))

def main():
    st.sidebar.title("Menú")
    opcion = st.sidebar.radio("Navegación", ["Nuevo informe", "Consultar informes"])
    if opcion == "Nuevo informe":
        pagina_nuevo_informe()
    else:
        pagina_consultar()

if __name__ == "__main__":
    main()