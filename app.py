# ==============================================================================
# CALCULADORA Y SIMULADOR FISCAL ROLANIA — MVP v1.0
# Aplicación web interactiva con Streamlit para expatriados españoles en Paraguay
# ==============================================================================

# --- 1. IMPORTACIONES ---------------------------------------------------------
# 'streamlit' es la librería de Python que transforma este script en una página
# web interactiva. Cada vez que el usuario mueve un control (deslizador, menú...),
# Streamlit ejecuta el código desde el principio para redibujar la pantalla.
import streamlit as st

# --- 2. CONSTANTES DE LA APLICACIÓN -------------------------------------------
# Guardamos los nombres de los perfiles en constantes (convención en mayúsculas)
# para evitar errores tipográficos si tuviéramos que escribir las cadenas repetidas veces.
PERFIL_AUTONOMO = "Autónomo Activo (Servicios Online)"
PERFIL_PRIVADO = "Pensionista Privado (INSS / Planes)"
PERFIL_PUBLICO = "Pensionista Público (Clases Pasivas)"

# Tramos de estimación fiscal en España (simplificación IRPF + RETA o IRNR).
TRAMO_1_LIMITE = 30000  # Hasta 30.000 € anuales → tipo efectivo estimado: 22 %
TRAMO_2_LIMITE = 60000  # De 30.001 € a 60.000 € → tipo efectivo estimado: 32 %
TIPO_TRAMO_1 = 0.22
TIPO_TRAMO_2 = 0.32
TIPO_TRAMO_3 = 0.40     # Más de 60.000 € → tipo efectivo estimado: 40 %

# Retención media estimada en España por IRNR (Impuesto sobre la Renta de No Residentes)
# aplicada a pensiones públicas cuando no se activa la excepción de nacionalidad.
TIPO_IRNR_PENSION_PUBLICA = 0.24

# --- 3. CONFIGURACIÓN INICIAL DE LA PÁGINA ------------------------------------
# Debe ser SIEMPRE la primera orden de Streamlit del archivo.
# Define el título en la pestaña del navegador, el icono y el modo de pantalla ancha.
st.set_page_config(
    page_title="Simulador Fiscal ROLANIA",
    page_icon="🧭",
    layout="wide",
)

# --- 4. FUNCIONES DEL MOTOR DE CÁLCULO (BACKEND) ------------------------------
def formato_euros(cantidad: float) -> str:
    """Convierte un número en texto con formato de moneda español: 19200 -> '19.200 €'."""
    # Formateamos con comas como separador de miles y luego las reemplazamos por puntos.
    return f"{cantidad:,.0f} €".replace(",", ".")


def calcular_carga_espana(ingresos: float) -> float:
    """Calcula la presión fiscal actual estimada en España según el tramo de ingresos."""
    if ingresos <= TRAMO_1_LIMITE:
        return ingresos * TIPO_TRAMO_1
    elif ingresos <= TRAMO_2_LIMITE:
        return ingresos * TIPO_TRAMO_2
    else:
        return ingresos * TIPO_TRAMO_3


def calcular_carga_paraguay(perfil: str, ingresos: float, reside_py: bool, nacionalidad: bool) -> float:
    """
    Calcula la carga fiscal final en Paraguay bajo la estrategia jurídica ROLANIA.
    Aplica el Convenio de Doble Imposición (CDI) España-Paraguay y la Ley 6380/2019 paraguaya.
    """
    # Si el cliente NO se muda físicamente o no saca el RUC, sigue siendo residente fiscal
    # en España por el Art. 9 de la LIRPF. No hay ahorro posible; tributa igual que en España.
    if not reside_py:
        return calcular_carga_espana(ingresos)

    # Si SÍ cumple con la permanencia (>183 días) y activa el RUC paraguayo:
    if perfil == PERFIL_AUTONOMO:
        # Art. 14 CDI (sin base fija en España, el IRPF baja al 0 %) +
        # Ley 6380/2019 (territorialidad paraguaya: renta de fuente extranjera al 0 %) +
        # Cese de actividad en España (baja del RETA, cuota autónomos = 0 €).
        return 0.0

    elif perfil == PERFIL_PRIVADO:
        # Art. 17 CDI (las pensiones privadas tributan EXCLUSIVAMENTE en Paraguay) +
        # Ley 6380/2019 (la pensión procedente del extranjero es fuente extranjera -> 0 %).
        return 0.0

    elif perfil == PERFIL_PUBLICO:
        # Si el pensionista público obtiene la nacionalidad paraguaya (Ley 6984/2022),
        # activa el Art. 18.2.b del CDI: la pensión tributa solo en Paraguay -> 0 %.
        if nacionalidad:
            return 0.0
        else:
            # Si NO tramita la nacionalidad, se aplica la regla general (Art. 18.2.a CDI):
            # España retiene en exclusiva por IRNR (media estimada del 24 %).
            return ingresos * TIPO_IRNR_PENSION_PUBLICA

    return 0.0


def construir_diagrama_mermaid(perfil: str, reside_py: bool, nacionalidad: bool,
                               txt_espana: str, txt_paraguay: str, txt_ahorro: str) -> str:
    """Genera el código de diagrama Mermaid según las decisiones de la simulación."""
    
    # Caso 1: El cliente no acepta vivir +183 días en Paraguay ni tramitar el RUC
    if not reside_py:
        return f"""
flowchart TD
    A["🇪🇸 Situación actual en España<br>Carga estimada: {txt_espana}"] --> B{{"¿Resides +183 días al año en Paraguay<br>y obtienes el RUC?"}}
    B -- "NO" --> C["❌ Art. 9 LIRPF: sigues siendo<br>residente fiscal en España"]
    C --> D["Sin traslado físico ni RUC no hay exención posible<br>Carga final: {txt_paraguay} | Ahorro neto: {txt_ahorro}"]
    style C fill:#ffe5e5,stroke:#c0392b,stroke-width:2px
    style D fill:#ffe5e5,stroke:#c0392b,stroke-width:2px
"""

    # Caso 2: Autónomo Activo que sí traslada su residencia
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

    # Caso 3: Pensionista Privado
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

    # Caso 4: Pensionista Público (bifurcación según la nacionalidad)
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

# --- 5. INTERFAZ DE USUARIO — BARRA LATERAL (SIDEBAR) -------------------------
st.sidebar.header("⚙️ Panel de Control")
st.sidebar.markdown("Configura los datos del cliente para calcular el impacto fiscal.")

# Control 1: Selección de perfil profesional
perfil_seleccionado = st.sidebar.selectbox(
    "👤 Perfil Profesional",
    options=(PERFIL_AUTONOMO, PERFIL_PRIVADO, PERFIL_PUBLICO),
    index=0,
)

# Control 2: Deslizador de ingresos brutos anuales
ingresos_seleccionados = st.sidebar.slider(
    "💶 Ingresos Brutos Anuales en España (€)",
    min_value=10000,
    max_value=150000,
    step=1000,
    value=60000,
    format="%d €",
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Requisitos Jurídicos del Modelo")

# Control 3: Compromiso de permanencia y RUC paraguayo
compromiso_residencia = st.sidebar.checkbox(
    "¿Te comprometes a residir más de 183 días al año en Paraguay y obtener el RUC?",
    value=True,
)

# Control 4: Casilla condicional (SOLO se muestra si el perfil es Pensionista Público)
compromiso_nacionalidad = False
if perfil_seleccionado == PERFIL_PUBLICO:
    compromiso_nacionalidad = st.sidebar.checkbox(
        "¿Estás dispuesto a tramitar la Nacionalidad Paraguaya (Ley 6984/2022) a los 3 años para activar la exención del CDI?",
        value=False,
    )

# --- 6. EJECUCIÓN DE CÁLCULOS -------------------------------------------------
carga_esp = calcular_carga_espana(ingresos_seleccionados)
carga_py = calcular_carga_paraguay(
    perfil=perfil_seleccionado,
    ingresos=ingresos_seleccionados,
    reside_py=compromiso_residencia,
    nacionalidad=compromiso_nacionalidad,
)
ahorro_neto = carga_esp - carga_py

# Formateamos los valores en texto para mostrarlos en la interfaz
txt_carga_esp = formato_euros(carga_esp)
txt_carga_py = formato_euros(carga_py)
txt_ahorro = formato_euros(ahorro_neto)

# --- 7. INTERFAZ DE USUARIO — CUERPO PRINCIPAL (MAIN BODY) --------------------
st.title("🧭 Calculadora y Simulador Fiscal ROLANIA")
st.markdown("### Simulador de Expatriación Legal España → Paraguay")
st.markdown(
    "Garantía de seguridad jurídica avalada por el **Convenio de Doble Imposición (CDI) España–Paraguay** "
    "(vigente y plenos efectos desde 2025) y la **Ley 6380/2019 de Modernización y Simplificación del Sistema Tributario Paraguayo**. "
    "Sin interpretaciones agresivas ni opacidad: optimización 100 % legal basada en convenios internacionales."
)

st.divider()

# EVALUACIÓN DE CONDICIONES Y AVISOS DE SEGURIDAD JURÍDICA
# Si el usuario desmarca la casilla de residencia, mostramos la alerta roja de error exigida.
if not compromiso_residencia:
    st.error(
        "❌ **Sin residir >183 días y sin RUC, sigues siendo residente fiscal en España por el Art. 9 de la LIRPF. No hay ahorro posible.**\n\n"
        "La fiscalidad internacional no opera «sobre el papel». Para aplicar el CDI y las exenciones paraguayas es requisito innegociable "
        "trasladar de forma efectiva el centro de vida y acreditar la residencia ante la Dirección Nacional de Ingresos Tributarios (DNIT)."
    )

# TARJETAS DE MÉTRICAS (COLUMNAS DESTACADAS)
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="🇪🇸 Carga Fiscal en España (Estimada)",
        value=txt_carga_esp,
        help="Carga combinada estimada (IRPF + RETA para autónomos o IRPF/IRNR en pensiones)."
    )

with col2:
    st.metric(
        label="🇵🇾 Carga Fiscal en Paraguay (ROLANIA)",
        value=txt_carga_py,
        help="Carga tributaria aplicable al fijar tu residencia fiscal en Paraguay bajo el paraguas del CDI."
    )

with col3:
    st.metric(
        label="💰 TU AHORRO NETO ANUAL CON ROLANIA",
        value=txt_ahorro,
        help="Diferencia directa entre la carga fiscal española y la estrategia optimizada en Paraguay."
    )

# Si hay ahorro real positivo, mostramos un mensaje de confirmación
if ahorro_neto > 0 and compromiso_residencia:
    st.success(
        f"✅ **Estrategia viable:** Trasladando tu residencia a Paraguay recuperas **{txt_ahorro} cada año** "
        f"de forma legal, protegiendo tu patrimonio y poder adquisitivo."
    )

st.divider()

# --- 8. BLOQUE EXPANDIBLE — JUSTIFICACIÓN LEGAL Y DIAGRAMA --------------------
# Preparamos los textos explicativos (3 viñetas por caso) para el expandible
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
else:  # Pensionista Público
    vinetas_legales = [
        "**Regla General — Artículo 18.2.a del CDI (Clases Pasivas):** Las pensiones públicas pagadas por el Estado o Administraciones españolas (funcionarios, militares, jueces) tributan habitualmente de forma exclusiva en el Estado pagador (España), sufriendo una retención por IRNR que oscila entre el 8 % y el 40 % según cuantía.",
        "**La Ruta de Escape ROLANIA — Artículo 18.2.b del CDI:** El propio convenio establece que si el pensionista público es **residente Y NACIONAL** de Paraguay, el derecho de imposición pasa a ser exclusivo del Paraguay, prohibiendo a España retener ningún impuesto (IRNR = 0 €).",
        "**Viabilidad jurídica mediante la Ley 6984/2022:** Gracias al Convenio de Doble Nacionalidad España-Paraguay de 1959, puedes tramitar la nacionalidad paraguaya a los 3 años de residencia permanente sin perder tu ciudadanía española ni tu pasaporte europeo. Al jurar la nacionalidad, tu pensión pasa a tributar al **0 % total** (exenta en España por el Art. 18.2.b del CDI y exenta en Paraguay por territorialidad de fuente extranjera).",
    ]

# Renderizamos el contenido expansible con el desglose legal y el gráfico
with st.expander("📜 Ver justificación legal y diagrama visual de tu ruta", expanded=True):
    st.markdown("#### Marco Jurídico Aplicable a tu Caso")
    for vineta in vinetas_legales:
        st.markdown(f"- {vineta}")

    st.markdown("---")
    st.markdown("#### Diagrama de Flujo y Decisión Fiscal")
    
    # Generamos la cadena de texto con la sintaxis de Mermaid
    codigo_mermaid = construir_diagrama_mermaid(
        perfil=perfil_seleccionado,
        reside_py=compromiso_residencia,
        nacionalidad=compromiso_nacionalidad,
        txt_espana=txt_carga_esp,
        txt_paraguay=txt_carga_py,
        txt_ahorro=txt_ahorro,
    )
    
    # Llamamos a la orden de Streamlit para dibujar el gráfico en pantalla
    st.mermaid(codigo_mermaid)

# --- 9. PIE DE PÁGINA (FOOTER) ------------------------------------------------
st.markdown("---")
st.caption(
    "⚠️ **Nota legal y de descargo de responsabilidad:** Este simulador fiscal proporciona estimaciones orientativas "
    "y educativas basadas en el Convenio de Doble Imposición (CDI) España-Paraguay y la normativa tributaria vigente. "
    "Los cálculos de carga española representan una media efectiva simplificada por tramos y no sustituyen un asesoramiento "
    "profesional personalizado. ROLANIA recomienda realizar un estudio de viabilidad fiscal individualizado antes de ejecutar "
    "cualquier traslado internacional de residencia."
)