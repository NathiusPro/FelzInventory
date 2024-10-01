import streamlit as st
import pandas as pd
import os

# Directorio para almacenar los archivos CSV de las sucursales
branch_dir = './branches'
if not os.path.exists(branch_dir):
    os.makedirs(branch_dir)

# Variables globales
branches = ["Coyoacán", "Cuautitlán Izcalli"]  # Sucursales predefinidas

# Función para obtener el archivo CSV de la sucursal seleccionada
def get_branch_file(branch_name):
    return os.path.join(branch_dir, f"{branch_name}.csv")

# Inicializar las sucursales por defecto
def initialize_default_branches():
    for branch_name in branches:
        branch_file = get_branch_file(branch_name)
        if not os.path.exists(branch_file):
            df = pd.DataFrame(columns=['Barcode', 'Quantity'])
            df.to_csv(branch_file, index=False)

# Función para cargar el inventario desde el archivo CSV
def load_inventory(branch_file):
    if os.path.exists(branch_file):
        return pd.read_csv(branch_file)
    else:
        return pd.DataFrame(columns=['Barcode', 'Quantity'])

# Función para agregar o actualizar un producto en el inventario
def add_to_inventory(branch_file, barcode, quantity):
    df = load_inventory(branch_file)
    barcode = str(barcode).strip()  # Eliminar espacios y asegurar que se trate de texto
    df['Barcode'] = df['Barcode'].astype(str)

    if barcode in df['Barcode'].values:
        # Actualizar la cantidad del producto existente
        df.loc[df['Barcode'] == barcode, 'Quantity'] = quantity
        st.success(f"Cantidad actualizada. Nueva cantidad para {barcode}: {quantity}")
    else:
        # Agregar nuevo producto
        new_entry = pd.DataFrame({'Barcode': [barcode], 'Quantity': [quantity]})
        df = pd.concat([df, new_entry], ignore_index=True)
        st.success(f"Producto con código {barcode} agregado con cantidad {quantity}.")

    # Guardar el archivo CSV actualizado
    df.to_csv(branch_file, index=False)

# Función para eliminar un producto del inventario por código de barras
def delete_from_inventory(branch_file, barcode):
    df = load_inventory(branch_file)
    barcode = str(barcode).strip()  # Eliminar espacios
    df['Barcode'] = df['Barcode'].astype(str)

    if barcode in df['Barcode'].values:
        # Eliminar el producto con el código de barras
        df = df[df['Barcode'] != barcode]
        df.to_csv(branch_file, index=False)
        st.success(f"Producto con código {barcode} eliminado.")
    else:
        st.error(f"Producto con código {barcode} no encontrado.")

# Función para mostrar el inventario actual
def show_inventory(branch_file):
    df = load_inventory(branch_file)
    if not df.empty:
        st.table(df)
    else:
        st.write("No hay productos en el inventario.")

# Función principal para gestionar la pantalla
def inventory_app():
    if 'branch_name' not in st.session_state:
        st.session_state['branch_name'] = None

    if st.session_state['branch_name'] is None:
        st.title("Gestión de Inventario por Sucursal")
        branch_name = st.selectbox("Selecciona una sucursal", branches)
        
        if st.button("Seleccionar Sucursal"):
            st.session_state['branch_name'] = branch_name
            st.experimental_rerun()
    else:
        branch_name = st.session_state['branch_name']
        branch_file = get_branch_file(branch_name)

        st.write(f"**Sucursal seleccionada:** {branch_name}")
        st.markdown("---")

        # Variables de control para saber si ya existe el código de barras
        if 'existing_barcode' not in st.session_state:
            st.session_state['existing_barcode'] = None

        # Formulario para agregar o actualizar productos
        with st.form("add_inventory_form", clear_on_submit=False):
            st.markdown("### Agregar/Actualizar Inventario")
            barcode = st.text_input("Escanea el código de barras:", key="barcode_field").strip()  # Elimina espacios
            quantity = st.number_input("Ingresa la cantidad:", min_value=1, step=1, key="quantity_field")

            # Botón para agregar/actualizar el inventario
            submitted = st.form_submit_button("Agregar/Actualizar Inventario")

            if submitted:
                if barcode:
                    # Comprobar si el producto ya existe en el inventario
                    df = load_inventory(branch_file)
                    df['Barcode'] = df['Barcode'].astype(str)

                    if barcode in df['Barcode'].values:
                        st.session_state['existing_barcode'] = barcode
                        st.session_state['existing_quantity'] = df.loc[df['Barcode'] == barcode, 'Quantity'].values[0]
                    else:
                        # Agregar el nuevo producto directamente
                        add_to_inventory(branch_file, barcode, quantity)
                        st.session_state['existing_barcode'] = None  # Limpiar si se agregó un nuevo producto
                        st.session_state['existing_quantity'] = None  # Limpiar cualquier cantidad existente
                else:
                    st.error("Por favor ingresa un código de barras válido.")

        # Si el código ya existe, mostrar cantidad actual y preguntar por nueva cantidad
        if st.session_state['existing_barcode']:
            st.warning(f"El código {st.session_state['existing_barcode']} ya existe con {st.session_state['existing_quantity']} unidades.")
            new_quantity = st.number_input("Ingresa la nueva cantidad para sobrescribir:", min_value=1, step=1, key="new_quantity_field")

            if st.button("Confirmar Acción"):
                add_to_inventory(branch_file, st.session_state['existing_barcode'], new_quantity)
                st.session_state['existing_barcode'] = None  # Limpiar después de procesar
                st.session_state['existing_quantity'] = None  # Limpiar cualquier cantidad existente
                st.experimental_rerun()  # Recargar para limpiar la vista

        st.markdown("---")

        # Formulario para eliminar productos
        with st.form("delete_inventory_form", clear_on_submit=True):
            st.markdown("### Eliminar Producto")
            delete_barcode = st.text_input("Eliminar producto con código de barras:", key="delete_barcode_field").strip()  # Elimina espacios
            delete_submitted = st.form_submit_button("Eliminar Producto")

            if delete_submitted:
                if delete_barcode:  # Validar que se haya ingresado un código de barras
                    delete_from_inventory(branch_file, delete_barcode)
                else:
                    st.error("Por favor ingresa un código de barras válido.")

        st.markdown("---")

        # Mostrar el inventario actual
        st.markdown(f"### Inventario de la Sucursal: **{branch_name}**")
        show_inventory(branch_file)

        # Botón para regresar a la selección de sucursal
        st.markdown("---")
        if st.button("Cambiar Sucursal"):
            st.session_state['branch_name'] = None
            st.experimental_rerun()

# Ejecución de la aplicación
if __name__ == "__main__":
    initialize_default_branches()
    inventory_app()
