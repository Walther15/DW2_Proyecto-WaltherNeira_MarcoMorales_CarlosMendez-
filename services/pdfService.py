from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
import os

def generar_liquidacion_pdf(empleado: dict, empresa: dict, contrato: dict, calculo: dict, output_path: str):
    c = canvas.Canvas(output_path, pagesize=letter)
    W, H = letter
    y = H - 50

    logo_path = os.path.join(os.path.dirname(__file__), "logos", "finantel_logo.png")
    if os.path.exists(logo_path):
        c.drawImage(logo_path, 50, H - 90, width=80, height=60, mask='auto')

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(W / 2, H - 60, "LIQUIDACIÓN DE SUELDO")

    c.setFont("Helvetica", 10)
    c.drawRightString(W - 50, H - 60, datetime.now().strftime("%d-%m-%Y"))

    y -= 70
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"Empresa: {empresa['nombre']}")
    y -= 18
    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Empleado: {empleado['nombre']}  (ID {empleado['id']})")
    y -= 18
    c.drawString(50, y, f"RUT: {empleado['rut']}")
    y -= 18
    c.drawString(50, y, f"Tipo de Contrato: {contrato['tipo']}")
    y -= 18
    c.drawString(50, y, f"Fecha de Inicio: {contrato['fecha_inicio']}")
    y -= 10
    c.line(50, y, W - 50, y)
    y -= 20

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Detalle de Haberes")
    y -= 18
    c.setFont("Helvetica", 11)
    c.drawString(60, y, f"Días trabajados: {calculo['dias_trabajados']}/30")
    y -= 16
    c.drawString(60, y, f"Sueldo Base: ${calculo['sueldo_base']:,.0f}")
    y -= 16
    c.drawString(60, y, f"Sueldo Base Proporcional: ${calculo['sueldo_base_proporcional']:,.0f}")
    y -= 16
    c.drawString(60, y, f"Horas Extras: ${calculo['horas_extras']:,.0f}")
    y -= 16
    c.drawString(60, y, f"Gratificación: ${calculo['gratificacion']:,.0f}")
    y -= 16
    c.drawString(60, y, f"Total Haberes: ${calculo['total_haberes']:,.0f}")
    y -= 20

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Descuentos Legales")
    y -= 18
    c.setFont("Helvetica", 11)
    c.drawString(60, y, f"AFP: ${calculo['afp']:,.0f}")
    y -= 16
    c.drawString(60, y, f"Salud: ${calculo['salud']:,.0f}")
    y -= 16
    c.drawString(60, y, f"AFC: ${calculo['afc']:,.0f}")
    y -= 16
    c.drawString(60, y, f"Total Descuentos: ${calculo['total_descuentos']:,.0f}")
    y -= 20

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"Sueldo Líquido: ${calculo['liquido']:,.0f}")
    y -= 30

    c.line(50, y, 250, y)
    y -= 15
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Representante de {empresa['nombre']}")

    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawCentredString(W / 2, 40, f"Documento generado automáticamente © {datetime.now().year}")

    c.showPage()
    c.save()
