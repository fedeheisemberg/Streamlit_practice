import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import altair as alt

class InventoryValuation:
    def __init__(self):
        self.inventory = []
        self.history = []
        self.replacement_cost = 0
        
    def add_initial_inventory(self, date, quantity, cost):
        self.inventory = [{"quantity": quantity, "cost": cost}]
        self.history.append({
            "date": date,
            "concept": "Existencia Inicial",
            "entry_qty": 0,
            "entry_cost": 0,
            "entry_total": 0,
            "exit_qty": 0,
            "exit_cost": 0,
            "exit_total": 0,
            "balance_qty": quantity,
            "balance_cost": cost,
            "balance_total": quantity * cost
        })
        
    def calculate_fifo(self, quantity, is_exit=True):
        remaining = quantity
        total_cost = 0
        new_inventory = self.inventory.copy()
        
        if not is_exit:  # Si es una entrada
            new_inventory.append({"quantity": quantity, "cost": self.current_cost})
            return quantity * self.current_cost, new_inventory
            
        while remaining > 0 and new_inventory:
            if new_inventory[0]["quantity"] <= remaining:
                total_cost += new_inventory[0]["quantity"] * new_inventory[0]["cost"]
                remaining -= new_inventory[0]["quantity"]
                new_inventory.pop(0)
            else:
                total_cost += remaining * new_inventory[0]["cost"]
                new_inventory[0]["quantity"] -= remaining
                remaining = 0
                
        return total_cost, new_inventory
    
    def calculate_lifo(self, quantity, is_exit=True):
        remaining = quantity
        total_cost = 0
        new_inventory = self.inventory.copy()
        
        if not is_exit:  # Si es una entrada
            new_inventory.append({"quantity": quantity, "cost": self.current_cost})
            return quantity * self.current_cost, new_inventory
            
        while remaining > 0 and new_inventory:
            if new_inventory[-1]["quantity"] <= remaining:
                total_cost += new_inventory[-1]["quantity"] * new_inventory[-1]["cost"]
                remaining -= new_inventory[-1]["quantity"]
                new_inventory.pop()
            else:
                total_cost += remaining * new_inventory[-1]["cost"]
                new_inventory[-1]["quantity"] -= remaining
                remaining = 0
                
        return total_cost, new_inventory
    
    def calculate_average(self, quantity, is_exit=True):
        total_qty = sum(item["quantity"] for item in self.inventory)
        total_cost = sum(item["quantity"] * item["cost"] for item in self.inventory)
        
        if total_qty == 0:
            avg_cost = self.current_cost
        else:
            avg_cost = total_cost / total_qty
            
        if not is_exit:  # Si es una entrada
            new_total_qty = total_qty + quantity
            new_total_cost = total_cost + (quantity * self.current_cost)
            new_avg_cost = new_total_cost / new_total_qty
            return quantity * self.current_cost, [{"quantity": new_total_qty, "cost": new_avg_cost}]
        
        return quantity * avg_cost, [{"quantity": total_qty - quantity, "cost": avg_cost}]
    
    def process_transaction(self, date, concept, quantity, cost, method):
        self.current_cost = cost
        is_exit = concept in ["Consumo", "Devolución a Proveedor"]
        
        if method == "PEPS":
            total_cost, new_inventory = self.calculate_fifo(quantity, is_exit)
        elif method == "UEPS":
            total_cost, new_inventory = self.calculate_lifo(quantity, is_exit)
        else:  # Promedio Ponderado
            total_cost, new_inventory = self.calculate_average(quantity, is_exit)
            
        self.inventory = new_inventory
        
        balance_qty = sum(item["quantity"] for item in self.inventory)
        if balance_qty > 0:
            balance_total = sum(item["quantity"] * item["cost"] for item in self.inventory)
            balance_cost = balance_total / balance_qty
        else:
            balance_total = 0
            balance_cost = 0
            
        transaction = {
            "date": date,
            "concept": concept,
            "entry_qty": quantity if not is_exit else 0,
            "entry_cost": cost if not is_exit else 0,
            "entry_total": total_cost if not is_exit else 0,
            "exit_qty": quantity if is_exit else 0,
            "exit_cost": total_cost/quantity if is_exit and quantity > 0 else 0,
            "exit_total": total_cost if is_exit else 0,
            "balance_qty": balance_qty,
            "balance_cost": balance_cost,
            "balance_total": balance_total
        }
        
        self.history.append(transaction)
        return transaction

    def calculate_rpt(self):
        """Calcula el Resultado por Tenencia"""
        if not self.inventory or self.replacement_cost == 0:
            return 0, 0, 0
            
        total_qty = sum(item["quantity"] for item in self.inventory)
        current_value = sum(item["quantity"] * item["cost"] for item in self.inventory)
        replacement_value = total_qty * self.replacement_cost
        
        return total_qty, current_value, replacement_value

def main():
    st.set_page_config(page_title="📊 Valuación de Inventarios", layout="wide")
    
    st.title("📊 Sistema de Valuación de Inventarios")
    st.markdown("---")
    
    with st.expander("ℹ️ Información sobre Métodos de Valuación y RPT", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            ### PEPS (FIFO)
            - Primero en Entrar, Primero en Salir
            - Las primeras unidades que entran son las primeras en salir
            - Refleja mejor el valor actual del inventario
            - En períodos de inflación, muestra mayores utilidades
            """)
            
        with col2:
            st.markdown("""
            ### UEPS (LIFO)
            - Último en Entrar, Primero en Salir
            - Las últimas unidades que entran son las primeras en salir
            - En períodos de inflación, refleja costos más actuales
            - Tiende a mostrar menores utilidades
            """)
            
        with col3:
            st.markdown("""
            ### Promedio Ponderado
            - Calcula un costo promedio para todas las unidades
            - Más simple de implementar
            - Suaviza las fluctuaciones de precios
            - Balance entre PEPS y UEPS
            """)

        with col4:
            st.markdown("""
            ### Resultado por Tenencia (RPT)
            - Mide la diferencia entre el valor actual del inventario y su costo de reposición
            - RPT = (Cantidad × Costo de Reposición) - Valor según método
            - Positivo: Ganancia por tenencia
            - Negativo: Pérdida por tenencia
            - Importante para análisis en contextos inflacionarios
            """)
    
    # Selección del método de valuación
    method = st.selectbox(
        "Seleccione el Método de Valuación",
        ["PEPS", "UEPS", "Promedio Ponderado"]
    )
    
    # Inicialización del sistema
    if 'inventory_system' not in st.session_state:
        st.session_state.inventory_system = InventoryValuation()
        st.session_state.transactions = []
    
    # Formulario para existencia inicial
    with st.expander("📥 Ingresar Existencia Inicial", expanded=True):
        with st.form("initial_inventory"):
            col1, col2, col3 = st.columns(3)
            with col1:
                initial_date = st.date_input("Fecha")
            with col2:
                initial_quantity = st.number_input("Cantidad Inicial", min_value=0)
            with col3:
                initial_cost = st.number_input("Costo Unitario Inicial", min_value=0.0)
            
            if st.form_submit_button("Establecer Existencia Inicial"):
                st.session_state.inventory_system = InventoryValuation()
                st.session_state.inventory_system.add_initial_inventory(
                    initial_date, initial_quantity, initial_cost
                )
                st.session_state.transactions = []
                st.success("✅ Existencia inicial establecida!")
    
    # Formulario para transacciones
    with st.expander("📝 Registrar Transacción", expanded=True):
        with st.form("transaction"):
            col1, col2, col3 = st.columns(3)
            with col1:
                date = st.date_input("Fecha de Transacción")
            with col2:
                concept = st.selectbox(
                    "Tipo de Transacción",
                    ["Compra", "Consumo", "Devolución a Proveedor", "Devolución a Almacén"]
                )
            with col3:
                quantity = st.number_input("Cantidad", min_value=0)
            
            cost = st.number_input("Costo Unitario", min_value=0.0)
            
            if st.form_submit_button("Registrar Transacción"):
                if hasattr(st.session_state.inventory_system, 'inventory'):
                    transaction = st.session_state.inventory_system.process_transaction(
                        date, concept, quantity, cost, method
                    )
                    st.session_state.transactions.append(transaction)
                    st.success("✅ Transacción registrada exitosamente!")
                else:
                    st.error("❌ Por favor, establezca primero la existencia inicial.")

    # Agregar input para costo de reposición
    with st.expander("💰 Establecer Costo de Reposición", expanded=True):
        replacement_cost = st.number_input(
            "Costo de Reposición",
            min_value=0.0,
            help="Ingrese el costo de reposición actual del inventario"
        )
        if st.button("Actualizar Costo de Reposición"):
            st.session_state.inventory_system.replacement_cost = replacement_cost
            st.success("✅ Costo de reposición actualizado!")
    
    # Mostrar resultados
    if st.session_state.transactions:
        st.markdown("### 📋 Registro de Transacciones")
        
        df = pd.DataFrame(st.session_state.inventory_system.history)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Formatear las columnas numéricas
        float_columns = ['entry_cost', 'entry_total', 'exit_cost', 'exit_total', 
                        'balance_cost', 'balance_total']
        for col in float_columns:
            df[col] = df[col].round(2)
        
        st.dataframe(df, use_container_width=True)
        
        # Gráfico de evolución del inventario usando Altair
        base = alt.Chart(df).encode(x='date:T')
        
        line_qty = base.mark_line(color='blue').encode(
            y='balance_qty:Q',
            tooltip=['date:T', 'balance_qty:Q']
        ).properties(title='Cantidad')
        
        line_total = base.mark_line(color='green').encode(
            y='balance_total:Q',
            tooltip=['date:T', 'balance_total:Q']
        ).properties(title='Valor Total')
        
        chart = alt.layer(line_qty, line_total).resolve_scale(
            y='independent'
        ).properties(
            title='Evolución del Inventario',
            width=800,
            height=400
        )
        
        st.altair_chart(chart, use_container_width=True)
        
        # Calcular y mostrar RPT
        qty, current_value, replacement_value = st.session_state.inventory_system.calculate_rpt()
        rpt = replacement_value - current_value
        
        st.markdown("### 💹 Análisis de Resultado por Tenencia")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Cantidad en Stock",
                f"{qty:,.0f} unidades"
            )
        
        with col2:
            st.metric(
                "Valor según " + method,
                f"${current_value:,.2f}"
            )
            
        with col3:
            st.metric(
                "Valor de Reposición",
                f"${replacement_value:,.2f}"
            )
            
        with col4:
            st.metric(
                "Resultado por Tenencia",
                f"${rpt:,.2f}",
                delta=f"{(rpt/current_value*100 if current_value else 0):,.1f}%"
            )
        
        # Gráfico comparativo de valores usando Altair
        if qty > 0:
            comparison_data = pd.DataFrame({
                'Tipo': ['Valor según ' + method, 'Valor de Reposición'],
                'Valor': [current_value, replacement_value]
            })
            
            bar_chart = alt.Chart(comparison_data).mark_bar().encode(
                x='Tipo:N',
                y='Valor:Q',
                color=alt.condition(
                    alt.datum.Tipo == 'Valor según ' + method,
                    alt.value('blue'),
                    alt.value('green')
                )
            ).properties(
                title='Comparación de Valores',
                width=800,
                height=400
            )
            
            st.altair_chart(bar_chart, use_container_width=True)
            
            # Agregar explicación del RPT
            st.markdown("#### 📝 Interpretación del Resultado por Tenencia")
            if rpt > 0:
                st.success(f"""
                Se registra una **ganancia por tenencia** de ${rpt:,.2f} ({(rpt/current_value*100):,.1f}%).
                Esto significa que el inventario ha aumentado su valor respecto al costo original.
                """)
            elif rpt < 0:
                st.error(f"""
                Se registra una **pérdida por tenencia** de ${abs(rpt):,.2f} ({abs(rpt/current_value*100):,.1f}%).
                Esto significa que el inventario ha perdido valor respecto al costo original.
                """)
            else:
                st.info("No hay resultado por tenencia, el valor del inventario se mantiene igual al costo original.")

if __name__ == "__main__":
    main()