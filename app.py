import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io

# Configuración de página optimizada para celulares
st.set_page_config(
    page_title="726 - Control de Ventas",
    page_icon="🏷️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilos CSS limpios y adaptables
st.markdown("""
    <style>
    .main { padding: 0px 15px; }
    h1 { color: #2563EB; font-weight: 700; padding-bottom: 10px; }
    h3 { font-size: 1.2rem !important; margin-top: 15px !important; }
    div.stButton > button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

DB_NAME = "negocio_726.db"

# Inicializar Base de Datos y precargar catálogo si está vacío
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS catalogo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            talle TEXT NOT NULL,
            costo REAL NOT NULL,
            precio_venta REAL NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            producto TEXT NOT NULL,
            talle TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            precio_unitario REAL NOT NULL,
            costo_unitario REAL NOT NULL,
            total REAL NOT NULL,
            ganancia REAL NOT NULL,
            cliente TEXT,
            metodo_pago TEXT,
            notas TEXT
        )
    """)
    
    # Precargar productos iniciales
    cursor.execute("SELECT COUNT(*) FROM catalogo")
    if cursor.fetchone()[0] == 0:
        productos_iniciales = [
            ("Mallas", "S", 10000.0, 30000.0),
            ("Mallas", "M", 10000.0, 30000.0),
            ("Mallas", "L", 10000.0, 30000.0),
            ("Mallas", "XL", 10000.0, 30000.0),
            ("Mallas", "XXL", 10000.0, 30000.0),
            ("Conjunto Musculosa y Short", "S", 28000.0, 50000.0),
            ("Conjunto Musculosa y Short", "M", 28000.0, 50000.0),
            ("Conjunto Musculosa y Short", "L", 28000.0, 50000.0),
            ("Conjunto Musculosa y Short", "XL", 28000.0, 50000.0),
            ("Conjunto Musculosa y Short", "XXL", 28000.0, 50000.0),
            ("Remeras Retro", "S", 27000.0, 45000.0),
            ("Remeras Retro", "M", 27000.0, 45000.0),
            ("Remeras Retro", "L", 27000.0, 45000.0),
            ("Remeras Retro", "XL", 27000.0, 45000.0),
            ("Remeras Retro", "XXL", 27000.0, 45000.0),
            ("Parlante JBL Go 4 Pro", "Único (N/A)", 15000.0, 40000.0),
        ]
        cursor.executemany("INSERT INTO catalogo (nombre, talle, costo, precio_venta) VALUES (?, ?, ?, ?)", productos_iniciales)
        conn.commit()
    conn.close()

init_db()

def get_catalogo():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM catalogo", conn)
    conn.close()
    return df

def get_ventas():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM ventas ORDER BY id DESC", conn)
    conn.close()
    return df

st.markdown("<h1 style='text-align: center;'>🏷️ 726 - Control de Ventas</h1>", unsafe_allow_html=True)

# Pestañas principales
pestanas = st.tabs(["🛒 Nueva Venta", "📊 Panel", "📦 Catálogo", "📥 Exportar"])

# ==================== PESTAÑA 1: NUEVA VENTA ====================
with pestanas[0]:
    st.subheader("Registrar Nueva Venta")
    catalogo_df = get_catalogo()
    nombres_productos = catalogo_df["nombre"].unique().tolist()
    
    producto_sel = st.selectbox("Producto", nombres_productos)
    talles_disponibles = catalogo_df[catalogo_df["nombre"] == producto_sel]["talle"].tolist()
    talle_sel = st.selectbox("Talle / Variante", talles_disponibles)
    
    # Obtener costo y precio predeterminado
    item_row = catalogo_df[(catalogo_df["nombre"] == producto_sel) & (catalogo_df["talle"] == talle_sel)].iloc[0]
    costo_unitario = float(item_row["costo"])
    precio_sugerido = float(item_row["precio_venta"])
    
    col1, col2 = st.columns(2)
    with col1:
        cantidad = st.number_input("Cantidad", min_value=1, value=1, step=1)
    with col2:
        precio_unitario = st.number_input("Precio Venta Unitario ($)", min_value=0.0, value=precio_sugerido, step=500.0)
    
    # Cálculos automáticos en vivo
    total_cobrado = precio_unitario * cantidad
    ganancia_neta = (precio_unitario - costo_unitario) * cantidad
    
    st.info(f"💵 **Total a Cobrar:** ${total_cobrado:,.2f} ARS\n\n📈 **Ganancia Neta:** ${ganancia_neta:,.2f} ARS")
    
    with st.form("form_venta", clear_on_submit=True):
        cliente = st.text_input("Nombre del Cliente (Opcional)")
        metodo_pago = st.selectbox("Método de Pago", ["Efectivo ARS", "Transferencia", "Mercado Pago", "Otro"])
        notas = st.text_area("Notas / Observaciones")
        
        submit_btn = st.form_submit_button("✅ Registrar Venta", use_container_width=True)
        if submit_btn:
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ventas (fecha, producto, talle, cantidad, precio_unitario, costo_unitario, total, ganancia, cliente, metodo_pago, notas)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (fecha_actual, producto_sel, talle_sel, cantidad, precio_unitario, costo_unitario, total_cobrado, ganancia_neta, cliente, metodo_pago, notas))
            conn.commit()
            conn.close()
            st.success("¡Venta registrada exitosamente! 🎉")

# ==================== PESTAÑA 2: PANEL & GANANCIAS ====================
with pestanas[1]:
    st.subheader("Resumen y Estadísticas")
    ventas_df = get_ventas()
    
    if not ventas_df.empty:
        ventas_df["fecha_dt"] = pd.to_datetime(ventas_df["fecha"])
        hoy_str = datetime.now().strftime("%Y-%m-%d")
        ventas_hoy = ventas_df[ventas_df["fecha_dt"].dt.strftime("%Y-%m-%d") == hoy_str]
        
        st.markdown("### 📅 Métricas de Hoy")
        col_h1, col_h2, col_h3 = st.columns(3)
        with col_h1: st.metric("Ventas Hoy", len(ventas_hoy))
        with col_h2: st.metric("Facturado Hoy", f"${ventas_hoy['total'].sum():,.0f}")
        with col_h3: st.metric("Ganancia Hoy", f"${ventas_hoy['ganancia'].sum():,.0f}")
        
        st.markdown("---")
        st.markdown("### 📊 Métricas Históricas")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1: st.metric("Facturación Total", f"${ventas_df['total'].sum():,.0f}")
        with col_m2: st.metric("Ganancia Acumulada", f"${ventas_df['ganancia'].sum():,.0f}")
        with col_m3: st.metric("Unidades Vendidas", int(ventas_df['cantidad'].sum()))
        
        st.markdown("### 🏆 Top Productos Vendidos")
        top_prod = ventas_df.groupby(["producto", "talle"])["cantidad"].sum().reset_index()
        top_prod = top_prod.sort_values(by="cantidad", ascending=False).head(5)
        st.dataframe(top_prod, use_container_width=True, hide_index=True)
        
        st.markdown("### 🕒 Últimas Ventas Registradas")
        st.dataframe(ventas_df[["fecha", "producto", "talle", "cantidad", "total", "metodo_pago", "cliente"]].head(10), use_container_width=True, hide_index=True)
    else:
        st.info("Todavía no hay ventas registradas. ¡Registra la primera en la pestaña 'Nueva Venta'!")

# ==================== PESTAÑA 3: CATÁLOGO ====================
with pestanas[2]:
    st.subheader("Gestión de Catálogo")
    catalogo_df = get_catalogo()
    st.dataframe(catalogo_df[["id", "nombre", "talle", "costo", "precio_venta"]], use_container_width=True, hide_index=True)
    
    st.markdown("### ➕ Agregar Nuevo Producto o Variante")
    with st.form("form_nuevo_producto", clear_on_submit=True):
        nuevo_nombre = st.text_input("Nombre del Producto")
        nuevo_talle = st.text_input("Talle / Variante (ej: M, Único)")
        nuevo_costo = st.number_input("Costo Unitario ($)", min_value=0.0, step=500.0)
        nuevo_precio = st.number_input("Precio de Venta ($)", min_value=0.0, step=500.0)
        
        btn_agregar = st.form_submit_button("Agregar al Catálogo", use_container_width=True)
        if btn_agregar:
            if nuevo_nombre and nuevo_talle:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO catalogo (nombre, talle, costo, precio_venta) VALUES (?, ?, ?, ?)", (nuevo_nombre, nuevo_talle, nuevo_costo, nuevo_precio))
                conn.commit()
                conn.close()
                st.success("¡Producto agregado correctamente! Actualiza la página para ver los cambios.")
            else:
                st.error("Por favor completa el nombre y el talle.")

# ==================== PESTAÑA 4: EXPORTAR VENTAS ====================
with pestanas[3]:
    st.subheader("Exportar Historial de Ventas")
    ventas_df = get_ventas()
    
    if not ventas_df.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            ventas_df.drop(columns=["fecha_dt"], errors="ignore").to_excel(writer, index=False, sheet_name='Ventas_726')
        excel_data = output.getvalue()
        
        st.download_button(
            label="📥 Descargar Excel con Ventas (.xlsx)",
            data=excel_data,
            file_name=f"ventas_726_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        st.info("No hay datos de ventas para exportar.")