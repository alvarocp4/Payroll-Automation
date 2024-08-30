import os
import pandas as pd
import pdfplumber
import re
import streamlit as st

# Define paths and file names
data_path = "data/pdfs"
output_csv = "data/mercadata.csv"

def categorize_item(item):
    """Función para categorizar los ítems"""
    # We normalize the item name
    item = re.sub(r'[^a-zA-Z\s]', '', item).lower()
    
    # Keyword category dictionary
    categories = {
        "Compra-Ropa/Casa": ["ketchup", "azúcar", "harina", "sabor", "para freir"],
        "Compra-Super": ["leche", "yogur", "mantequilla", "queso", "cremoso", "stracciatella", "griego", "nata"],
        "Gasolina": ["jamoncitos", "burger", "chuleta", "lomo", "cuarto trasero", "pavo", "albóndigas", "longaniza", "gallina", "tacos", "paleta", "loncha"],
        "Gym": ["garbanzo", "maíz", "ensalada", "cebolla", "pimiento", "champiñón", "calabacín", "zanahoria", "ajo", "brotes tiernos"],
        "Nomina": ["patatas", "chocolate", "chicles", "cereales rellenos", "patatas lisas", "patatas chili lima", "nachos", "varitas frambuesa"],
        "Ocio/Fiesta": ["panecillo", "barra de pan", "barra rústica", "croqueta", "tortillas mexicanas", "chapata cristal", "pan m. 55% centeno", "pan viena redondo"],
        "Otros": ["huevos frescos", "estropajo", "toall.bebe", "dermo", "gamuza atrapapolvo", "rollo hogar doble", "lavavajillas", "colg. triple", "gel crema"],
        "Peluqueria": ["caldo de pollo", "salsa de soja", "agua mineral", "soja calcio brick"],
        "Ticket-Restaurant": ["aguacate", "fresón", "nectarina", "paraguayo", "tomate", "pera rocha", "ciruela roja", "banana", "pera conferencia", "mezcla de frutos rojos"],
        "Viajes": ["almendra", "anacardo", "nuez", "pasas sultanas", "cacahuete"]
    }

    for category, keywords in categories.items():
        if any(keyword in item for keyword in keywords):
            return category
    return "otros"

def extract_location(text):
    """Función para extraer la ubicación de la tienda del ticket."""
    location_match = re.search(r"MERCADONA,\s+S\.A\.\s+[^\n]*\n(.*?)(?=TELÉFONO:)", text, re.DOTALL)
    return location_match.group(1).strip() if location_match else "Ubicación no encontrada"

def process_pdfs(uploaded_files):
    data = []

    # Ensure that the data directory exists
    data_path = "data"
    if not os.path.exists(data_path):
        os.makedirs(data_path)

    for uploaded_file in uploaded_files:
        pdf_path = os.path.join(data_path, uploaded_file.name)
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Process each PDF file
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[0]
            text = page.extract_text()

            if text:
                print("Text extracted from Excel:")
                print(text)

                # Extract location
                location = extract_location(text)

                # Extract date and ticket identifier
                date_match = re.search(r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}", text)
                fecha = date_match.group(0) if date_match else "Date not found"

                ticket_match = re.search(r"FACTURA SIMPLIFICADA:\s+([0-9\-]+)", text)
                identificativo = ticket_match.group(1) if ticket_match else "Identifier not found"

                # Extract items and prices using a more flexible pattern
                # Enhanced pattern for capturing items with multiple words and prices
                item_pattern = r"([A-Z0-9\s/]+)\s+(\d+,\d{2})"

                # Filter lines not related to products
                patron_no_producto = re.compile(r"(TARJETA BANCARIA|TOTAL|SUBTOTAL|CREDITO)", re.IGNORECASE)
                
                # Filter lines not related to products
                filtered_lines = [line for line in text.splitlines() if not patron_no_producto.search(line)]

                # Extract items from filtered rows
                items = re.findall(item_pattern, '\n'.join(filtered_lines))

                for item, precio in items:
                    item = item.strip()
                    precio = round(float(precio.replace(",", ".")), 2)
                    categoria = categorize_item(item)
                    data.append([fecha, identificativo, location, item, categoria, precio])
            else:
                print(f"Text could not be extracted from the file: {uploaded_file.name}")

    if data:
        # Create a DataFrame and save locally as CSV
        df = pd.DataFrame(data, columns=["fecha", "identificativo de ticket", "ubicación", "item", "categoría", "precio"])
        df.to_csv(output_csv, index=False)
        st.success(f"CSV file generated successfully: {output_csv}")

    else:
        st.info("No data was found to write to the CSV file.")

def main():
    st.title("PDF Ticket Processor")

    # Allow users to upload PDF files
    uploaded_files = st.file_uploader("Upload your Excel files", accept_multiple_files=True, type="pdf")

    if uploaded_files:
        process_pdfs(uploaded_files)

if __name__ == "__main__":
    main()