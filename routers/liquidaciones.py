from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import FileResponse
import mysql.connector
from services.pdfService import generar_liquidacion_pdf
from datetime import datetime
import os
import tempfile

router = APIRouter(prefix="/liquidacion", tags=["liquidacion"])

def get_connection():
    return mysql.connector.connect(host="localhost", user="root", password="", database="holding_rrhh")

@router.post("/{empleado_id}/pdf", response_class=FileResponse)
def generar_pdf_liquidacion(
    empleado_id: int,
    payload: dict = Body(...)
):
    try:
        horas_extras = float(payload.get("horas_extras", 0))
        dias_trabajados = int(payload.get("dias_trabajados", 30))
        if dias_trabajados < 1 or dias_trabajados > 30 or horas_extras < 0:
            raise HTTPException(status_code=422, detail="Valores inválidos: días [1..30], horas >= 0")

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT e.id AS id,
               e.nombres, e.apellidos, e.rut,
               emp.nombre AS empresa,
               c.id AS contrato_id,
               c.tipo, c.fecha_inicio, c.sueldo_base,
               at.tasa AS tasa_afp,
               st.tasa AS tasa_salud,
               act.tasa_trabajador AS tasa_afc
        FROM contratos c
        JOIN empleados e ON c.empleado_id = e.id
        JOIN empresas emp ON c.empresa_id = emp.id
        JOIN afp_tasas at ON c.afp_id = at.afp_id
        JOIN salud_tasas st ON c.salud_id = st.salud_id
        JOIN afc_tasas act ON c.afc_id = act.afc_id
        WHERE c.empleado_id = %s
        ORDER BY c.fecha_inicio DESC
        LIMIT 1
        """
        cursor.execute(query, (empleado_id,))
        empleado = cursor.fetchone()
        if not empleado:
            raise HTTPException(status_code=404, detail="Empleado no encontrado o sin contrato activo")

        sueldo_base = float(empleado["sueldo_base"])
        sueldo_base_proporcional = sueldo_base * (dias_trabajados / 30)

        valor_hora = sueldo_base / 160
        monto_horas_extras = valor_hora * 1.5 * horas_extras

        ingreso_minimo_mensual = 470000
        tope_gratificacion = (4.75 * ingreso_minimo_mensual) / 12
        gratificacion = min(sueldo_base_proporcional * 0.25, tope_gratificacion)

        total_haberes = sueldo_base_proporcional + monto_horas_extras + gratificacion

        afp = total_haberes * (float(empleado["tasa_afp"]) / 100)
        salud = total_haberes * (float(empleado["tasa_salud"]) / 100)
        afc = total_haberes * (float(empleado["tasa_afc"]) / 100) if empleado["tipo"].upper() == "INDEFINIDO" else 0.0

        total_descuentos = afp + salud + afc
        liquido = total_haberes - total_descuentos

        fecha_actual = datetime.now()
        mes = fecha_actual.month
        anio = fecha_actual.year

        insert = """
        INSERT INTO liquidaciones (contrato_id, periodo, mes, sueldo_base, horas_extra, gratificacion, total_imponible, total_descuentos, liquido_a_pagar)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert, (
            empleado["contrato_id"], anio, mes, sueldo_base_proporcional, monto_horas_extras,
            gratificacion, total_haberes, total_descuentos, liquido
        ))
        conn.commit()

        pdf_path = os.path.join(
            tempfile.gettempdir(),
            f"liquidacion_{empleado['nombres']}_{anio}-{mes}.pdf"
        )

        generar_liquidacion_pdf(
            empleado={
                "id": empleado["id"],
                "nombre": f"{empleado['nombres']} {empleado['apellidos']}",
                "rut": empleado["rut"]
            },
            empresa={"nombre": empleado["empresa"]},
            contrato={
                "tipo": empleado["tipo"],
                "fecha_inicio": empleado["fecha_inicio"]
            },
            calculo={
                "dias_trabajados": dias_trabajados,
                "sueldo_base": sueldo_base,
                "sueldo_base_proporcional": sueldo_base_proporcional,
                "horas_extras": monto_horas_extras,
                "gratificacion": gratificacion,
                "total_haberes": total_haberes,
                "afp": round(afp, 2),
                "salud": round(salud, 2),
                "afc": round(afc, 2),
                "total_descuentos": round(total_descuentos, 2),
                "liquido": round(liquido, 2)
            },
            output_path=pdf_path
        )

        return FileResponse(pdf_path, media_type="application/pdf", filename=os.path.basename(pdf_path))

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"DB error: {err}")

    finally:
        try:
            cursor.close()
            conn.close()
        except:  # noqa
            pass
