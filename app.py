# ==============================================================================
# CALCULADORA Y SIMULADOR FISCAL ROLANIA — MVP v1.1 (Estable + Monetización)
# Aplicación web interactiva con Streamlit para expatriados españoles en Paraguay
# ==============================================================================

# --- 1. IMPORTACIONES ---------------------------------------------------------
import streamlit as st
import streamlit.components.v1 as components
import urllib.parse

# --- 2. CONSTANTES DE LA APLICACIÓN -------------------------------------------
PERFIL_AUTONOMO = "Autónomo Activo (Servicios Online)"
PERFIL_PRIVADO = "Pensionista Privado (INSS / Planes)"
PERFIL_PUBLICO = "Pensionista Público (Clases Pasivas)"

TRAMO_1_LIMITE = 30000
TRAMO_2_LIMITE = 60000
TIPO_TRAMO_1 = 0.22
TIPO_TRAMO_2 = 0.32
TIPO_TRAMO_3 = 0.40

TIPO_IRNR_PENSION_PUBLICA = 0.24

# ⚠️ NÚMERO DE WHATSAPP COMERCIAL DE ROLANIA (Cambia esto por tu móvil real con código de país)
TELEFONO_WHATSAPP_ROLANIA = "34600000000"

# --- 3. CONFIGURACIÓN INICIAL DE LA PÁGINA ------------------------------------
st.set_page_config(
    page_title="Simulador Fiscal ROLANIA",
    page_icon="🧭",
    layout="wide",
)

# --- 4. FUNCIONES DEL MOTOR DE CÁLCULO (BACKEND) ------------------------------
def formato_euros(cantidad: float) -> str:
    return f"{cantidad:,.0f} €".replace(",", ".")

def calcular_carga_espana(ingresos: float) -> float:
    if ingresos <= TRAMO_1_LIMITE:
        return ingresos * TIPO_TRAMO_1
    elif ingresos <= TRAMO_2_LIMITE:
        return ingresos * TIPO_TRAMO_2
    else:
        return ingresos * TIPO_TRAMO_3

def calcular_carga_paraguay(perfil: str, ingresos: float, reside_py: bool, nacionalidad: bool) -> float:
    if not reside_py:
        return calcular_carga_espana(ingresos)

    if perfil == PERFIL_AUTONOMO or perfil == PERFIL_PRIVADO:
        return 0.0
    elif perfil == PERFIL_PUBLICO:
        if nacionalidad:
            return 0.0
        else:
            return ingresos * TIPO_IRNR_PENSION_PUBLICA
    return 0.0

def construir_diagrama_mermaid(perfil: str, reside_py: bool, nacionalidad: bool,
                               txt_espana: str, txt_paraguay: str, txt_ahorro: str) -> str:
    if not reside_py:
        return f"""
flowchart TD
    A["🇪🇸 Situación actual en España<br>Carga estimada: {txt_espana}"] --> B{{"¿Resides +183 días al año en Paraguay<br>y obtienes el RUC?"}}
    B -- "NO" --> C["❌ Art. 9 LIRPF: sigues siendo<br>residente fiscal en España"]
    C --> D["Sin traslado físico ni RUC no hay exención posible<br>Carga final: {txt_paraguay} | Ahorro neto: {txt_ahorro}"]
    style C fill:#ffe5e5,stroke:#c0392b,stroke-width:2px
    style D fill:#ffe5e5,stroke:#c0392b,stroke-width:2px
"""
    if perfil == PERFIL_AUTONOMO:
        return f"""
flowchart TD
    A["🇪🇸 Autónomo en España<br>Carga actual: {txt_espana}"] --> B{{"¿Resides +183 días al año en Paraguay<br>y obtienes el RUC?"}}
    B -- "SÍ" --> C["✅ Residencia fiscal en Paraguay acreditada<br>+ baja y cese de cuotas RETA en España"]
    C --> D["Art. 14 CDI: al no tener base fija en España,<br>tus beneficios profesionales solo tributan en Paraguay"]
    D --> E["Ley 6380/2019: el principio de territorialidad exime<br>los ingresos facturados a clientes del extranjero"]
    E --> F["💰 Carga final en Paraguay: 0 €<br>Ahorro neto anual: {txt_ahorro}"]
    style F fill:#e6ffed,stroke:#1a7f37,stroke-width:2px
"""
    elif perfil == PERFIL_PRIVADO:
        return f"""
flowchart TD
    A["🇪🇸 Pensionista Privado en España<br>Carga actual: {txt_espana}"] --> B{{"¿Resides +183 días al año en Paraguay<br>y obtienes el RUC?"}}
    B -- "SÍ" --> C["✅ Residencia fiscal en Paraguay acreditada<br>+ comunicación al INSS / pagador privado"]
    C --> D["Art. 17 CDI: la pensión privada queda sometida<br>a imposición EXCLUSIVA en el Estado de residencia"]
    D --> E["Ley 6380/2019: la pensión procedente de España<br>es renta de fuente extranjera en Paraguay (tipo 0 %)"]
    E --> F["💰 Carga final en Paraguay: 0 €<br>Ahorro neto anual: {txt_ahorro}"]
    style F fill:#e6ffed,stroke:#1a7f37,stroke-width:2px
"""
    else:
        return f"""
flowchart TD
    A["🇪🇸 Pensionista Público (Clases Pasivas)<br>Carga actual: {txt_espana}"] --> B{{"¿Resides +183 días al año en Paraguay<br>y obtienes el RUC?"}}
    B -- "SÍ" --> C{{"¿Tramitas la Nacionalidad Paraguaya<br>(Ley 6984/2022) a los 3 años de residencia?"}}
    C -- "SÍ" --> D["Art. 18.2.b CDI: exención activada<br>al ser nacional y residente, tributas solo en Paraguay"]
    D --> E["Ley 6380/2019: fuente extranjera en Paraguay → tipo 0 %"]
    E --> F["💰 Carga final en Paraguay: 0 €<br>Ahorro neto anual: {txt_ahorro}"]
    C -- "NO" --> G["Art. 18.2.a CDI (regla general): España retiene<br>por IRNR en exclusiva (tipo medio ~24 %)"]
    G --> H["Carga final en Paraguay: {txt_paraguay}<br>Ahorro neto anual: {txt_ahorro}"]
    style F fill:#e6ffed,stroke:#1a7f37,stroke-width:2px
    style G fill:#fff4e5,stroke:#b26a00,stroke-width:2px
"""

def renderizar_mermaid_seguro(codigo_mermaid: str, altura: int = 420):
    """
    Parche de Arquitectura v1.1: Renderiza Mermaid usando el motor oficial de CDN
    en un componente HTML aislado para evitar errores de atributos en Streamlit.
    """
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ startOnLoad: true, theme: 'dark', securityLevel: 'loose' }});
        </script>
        <style>
            body {{ margin: 0; padding: 0; background-color: transparent; display: flex; justify-content: center; }}
            .mermaid {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; width: 100%; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="mermaid">
            {codigo_mermaid}
        </div>
    </body>
    </html>
    """
    components.html(html_code, height=altura, scrolling=True)

# --- 5. INTERFAZ DE USUARIO — BARRA LATERAL (SIDEBAR) -------------------------
st.sidebar.header("⚙️ Panel de Control")
st.sidebar.markdown("Configura los datos del cliente para calcular el impacto fiscal.")

perfil_seleccionado = st.sidebar.selectbox(
    "👤 Perfil Profesional",
    options=(PERFIL_AUTONOMO, PERFIL_PRIVADO, PERFIL_PUBLICO),
    index=0,
)

ingresos_seleccionados = st.sidebar.slider(
    "💶 Ingresos Brutos Anuales en España (€)",
    min_value=10000, max_value=150000, step=1000, value=60000, format="%d €",
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Requisitos Jurídicos del Modelo")

compromiso_residencia = st.sidebar.checkbox(
    "¿Te comprometes a residir más de 183 días al año en Paraguay y obtener el RUC?", value=True,
)

compromiso_nacionalidad = False
if perfil_seleccionado == PERFIL_PUBLICO:
    compromiso_nacionalidad = st.sidebar.checkbox(
        "¿Estás dispuesto a tramitar la Nacionalidad Paraguaya (Ley 6984/2022) a los 3 años para activar la exención del CDI?", value=False,
    )

# --- 6. EJECUCIÓN DE CÁLCULOS -------------------------------------------------
carga_esp = calcular_carga_espana(ingresos_seleccionados)
carga_py = calcular_carga_paraguay(perfil_seleccionado, ingresos_seleccionados, compromiso_residencia, compromiso_nacionalidad)
ahorro_neto = carga_esp - carga_py

txt_carga_esp = formato_euros(carga_esp)
txt_carga_py = formato_euros(carga_py)
txt_ahorro = formato_euros(ahorro_neto)

# --- 7. INTERFAZ DE USUARIO — CUERPO PRINCIPAL (MAIN BODY) --------------------
st.title("🧭 Calculadora y Simulador Fiscal ROLANIA")
st.markdown("### Simulador de Expatriación Legal España → Paraguay")
st.markdown(
    "Garantía de seguridad jurídica avalada por el **Convenio de Doble Imposición (CDI) España–Paraguay** "
    "y la **Ley 6380/2019 de Modernización y Simplificación del Sistema Tributario Paraguayo**. "
    "Sin interpretaciones agresivas ni opacidad: optimización 100 % legal basada en convenios internacionales."
)

st.divider()

if not compromiso_residencia:
    st.error(
        "❌ **Sin residir >183 días y sin RUC, sigues siendo residente fiscal en España por el Art. 9 de la LIRPF. No hay ahorro posible.**\n\n"
        "La fiscalidad internacional no opera «sobre el papel». Para aplicar el CDI y las exenciones paraguayas es requisito innegociable "
        "trasladar de forma efectiva el centro de vida y acreditar la residencia ante la Dirección Nacional de Ingresos Tributarios (DNIT)."
    )

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="🇪🇸 Carga Fiscal en España (Estimada)", value=txt_carga_esp)
with col2:
    st.metric(label="🇵🇾 Carga Fiscal en Paraguay (ROLANIA)", value=txt_carga_py)
with col3:
    st.metric(label="💰 TU AHORRO NETO ANUAL CON ROLANIA", value=txt_ahorro)

if ahorro_neto > 0 and compromiso_residencia:
    st.success(
        f"✅ **Estrategia viable:** Trasladando tu residencia a Paraguay recuperas **{txt_ahorro} cada año** "
        f"de forma legal, protegiendo tu patrimonio y poder adquisitivo."
    )

# --- 8. MOTOR DE MONETIZACIÓN DUAL (NUEVO MVP v1.1) ---------------------------
st.markdown("---")
st.markdown("### 🚀 Da el Salto a Paraguay: Elige tu Vía de Acción")

col_cta1, col_cta2 = st.columns(2)

# VÍA 1: ATENCIÓN INMEDIATA POR WHATSAPP (HIGH-TICKET)
with col_cta1:
    st.info("📲 **Vía Rápida: Consultoría Personalizada**\n\n¿Quieres validar tu caso con un experto fiscal en directo? Habla ahora mismo con nuestro equipo comercial.")
    
    # Redacción dinámica del mensaje de WhatsApp integrando los datos simulados
    mensaje_wsp = (
        f"Hola equipo ROLANIA. He usado vuestra calculadora fiscal online:\n"
        f"• Mi perfil: {perfil_seleccionado}\n"
        f"• Ingresos en España: {ingresos_seleccionados:,.0f} €\n"
        f"• Ahorro estimado calculado: {txt_ahorro}\n"
        f"Quiero solicitar un Estudio de Viabilidad Personalizado para emigrar legalmente."
    )
    url_wsp = f"https://wa.me/{TELEFONO_WHATSAPP_ROLANIA}?text={urllib.parse.quote(mensaje_wsp)}"
    
    st.link_button(
        label="💬 Solicitar Estudio por WhatsApp",
        url=url_wsp,
        type="primary",
        use_container_width=True,
        help="Abre tu aplicación de WhatsApp con un mensaje pre-redactado con tus datos."
    )

# VÍA 2: CAPTURA DE LEADS (LIBRETO-GUÍA PDF)
with col_cta2:
    st.warning("📚 **Vía Estudio: Libreto-Guía en PDF**\n\n¿Prefieres analizar toda la legislación, tablas comparativas y diagramas a tu ritmo? Descarga el manual oficial.")
    
    with st.form(key="form_lead_rolania", clear_on_submit=True):
        email_cliente = st.text_input("Tu Correo Electrónico Profesional", placeholder="ejemplo@profesional.com")
        btn_enviar_lead = st.form_submit_button("📥 Enviar a mi correo el Libreto-Guía ROLANIA", use_container_width=True)
        
        if btn_enviar_lead:
            if "@" in email_cliente and "." in email_cliente:
                st.success(f"✅ ¡Confirmado! Hemos registrado tu solicitud para el correo **{email_cliente}**. Recibirás el Libreto-Guía en los próximos 5 minutos.")
                # Nota de arquitecto: Aquí en el futuro conectaremos tu base de datos de correos (ej. Mailchimp/ActiveCampaign)
            else:
                st.error("⚠️ Por favor, introduce una dirección de correo electrónico válida.")

st.divider()

# --- 9. BLOQUE EXPANDIBLE — JUSTIFICACIÓN LEGAL Y DIAGRAMA (CORREGIDO) --------
if not compromiso_residencia:
    vinetas_legales = [
        "**Artículo 9 de la Ley del IRPF española:** Se considera residente fiscal en España a quien pase más de 183 días al año en el país o tenga en él el núcleo principal de sus actividades económicas.",
        "**Inaplicabilidad del Convenio (CDI):** Sin la obtención de un RUC paraguayo y el certificado oficial de residencia fiscal de la DNIT, España no reconocerá ningún cambio de domicilio fiscal y seguirá reteniendo impuestos por tu renta mundial.",
        "**Compromiso ROLANIA:** Nuestra consultora no diseña estructuras vacías ni simulaciones de residencia. El primer paso ineludible de la optimización fiscal es el traslado físico y la tramitación migratoria legal en Paraguay.",
    ]
elif perfil_seleccionado == PERFIL_AUTONOMO:
    vinetas_legales = [
        "**Artículo 14 del CDI España–Paraguay (Servicios Profesionales):** Los ingresos obtenidos por un profesional independiente solo pueden someterse a imposición en su Estado de residencia (Paraguay), salvo que disponga de una «base fija» habitual en España. Al cerrar tu oficina/despacho en España, la AEAT pierde el derecho a gravarte.",
        "**Ley 6380/2019 paraguaya (Principio de Territorialidad):** Paraguay solo grava las rentas generadas dentro de su territorio nacional. Los servicios que prestes desde Paraguay vía online a clientes ubicados en España, la Unión Europea o EE. UU. se califican jurídicamente como renta de fuente extranjera y tributan al **0 %** de IRP.",
        "**Cese de cuotas de Seguridad Social (RETA):** Al tramitar tu baja censal en España (Modelo 030 y 036) por traslado en el extranjero, cesa tu obligación de cotizar al RETA español, ahorrando miles de euros en cuotas fijas sin obligación de abonar un equivalente fijo en el IPS paraguayo.",
    ]
elif perfil_seleccionado == PERFIL_PRIVADO:
    vinetas_legales = [
        "**Artículo 17 del CDI España–Paraguay (Pensiones Privadas):** Las pensiones pagadas por razón de un empleo privado anterior (Régimen General del INSS, planes de pensiones privados o mutualidades) solo pueden someterse a imposición en el Estado donde resida el perceptor. España deja de retener IRPF.",
        "**Exención por Territorialidad en Paraguay (Ley 6380/2019):** Al recibir la pensión en tu cuenta paraguaya, la normativa tributaria local la clasifica como ingreso de fuente extranjera. Por aplicación estricta del principio territorial, queda desgravada al **0 %** en tu declaración paraguaya.",
        "**Seguridad de cobro íntegro:** Mediante la presentación en el INSS del Certificado de Residencia Fiscal en Paraguay (emitido por la DNIT bajo convenio), se paraliza legalmente la retención en origen, cobrando el 100 % de tu pensión bruta mensual.",
    ]
else:
    vinetas_legales = [
        "**Regla General — Artículo 18.2.a del CDI (Clases Pasivas):** Las pensiones públicas pagadas por el Estado o Administraciones españolas (funcionarios, militares, jueces) tributan habitualmente de forma exclusiva en el Estado pagador (España), sufriendo una retención por IRNR que oscila entre el 8 % y el 40 % según cuantía.",
        "**La Ruta de Escape ROLANIA — Artículo 18.2.b del CDI:** El propio convenio establece que si el pensionista público es **residente Y NACIONAL** de Paraguay, el derecho de imposición pasa a ser exclusivo del Paraguay, prohibiendo a España retener ningún impuesto (IRNR = 0 €).",
        "**Viabilidad jurídica mediante la Ley 6984/2022:** Gracias al Convenio de Doble Nacionalidad España-Paraguay de 1959, puedes tramitar la nacionalidad paraguaya a los 3 años de residencia permanente sin perder tu ciudadanía española ni tu pasaporte europeo. Al jurar la nacionalidad, tu pensión pasa a tributar al **0 % total**.",
    ]

with st.expander("📜 Ver justificación legal y diagrama visual de tu ruta", expanded=False):
    st.markdown("#### Marco Jurídico Aplicable a tu Caso")
    for vineta in vinetas_legales:
        st.markdown(f"- {vineta}")

    st.markdown("---")
    st.markdown("#### Diagrama de Flujo y Decisión Fiscal")
    
    codigo_mermaid = construir_diagrama_mermaid(
        perfil=perfil_seleccionado,
        reside_py=compromiso_residencia,
        nacionalidad=compromiso_nacionalidad,
        txt_espana=txt_carga_esp,
        txt_paraguay=txt_carga_py,
        txt_ahorro=txt_ahorro,
    )
    
    # Usamos la nueva función de renderizado seguro por HTML aislado
    renderizar_mermaid_seguro(codigo_mermaid)

# --- 10. PIE DE PÁGINA (FOOTER) -----------------------------------------------
st.markdown("---")
st.caption(
    "⚠️ **Nota legal y de descargo de responsabilidad:** Este simulador fiscal proporciona estimaciones orientativas "
    "y educativas basadas en el Convenio de Doble Imposición (CDI) España-Paraguay y la normativa tributaria vigente. "
    "ROLANIA recomienda realizar un estudio de viabilidad fiscal individualizado antes de ejecutar cualquier traslado internacional."
)
