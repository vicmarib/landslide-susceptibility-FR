# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# 31SlopeClasific_continuo.py    --> para raster de pendiente continuo
# Created on: 7/2019, revisado 15/7/2019 (con valores ajustados solo para Lito)

# Descripción: Genera un raster con valores continuos
# proceden de una regresión lineal en dos tramos para las 8 clases FR
#
#  DATOS DE ENTRADA: ecuación de regresión
# ---------------------------------------------------------------------------

# Import arcpy module
import arcpy
import sys, os, time
from arcpy import env


# importar SAnalyst y validar la extension
from arcpy.sa import *
arcpy.CheckOutExtension("Spatial")

env.overwriteOutput = True  # sobreescribir archivos

# para el Join, nombres de campo cortos (así todos iguales)
env.qualifiedFieldNames = False

# para retroceder dos niveles de directorio (hasta \POBLACION)
ruta = os.path.dirname(os.path.dirname(os.getcwd()))

# Añadir funciones propias (cambiaNom y seghora)
sys.path.append (ruta + r"\PyScripts\2Funciones")   #añadir ruta para funciones
from FuncIsidro import *   # importa todas las funciones del archivo

InicioProc = time.time() # inicio en segundos para cálculo del proceso

# Definir workspace
wsp = env.workspace = ruta + r"\Trabajos\CVal_Susc"


# --- DATOS DE ENTRADA

prov = ["CS", "VL", "AL"]
#prov =["AL"]     # para pruebas
cProv = ["12", "46", "03"]
muni = ruta + r"\Datos_ESP\ComVal\Datos_ComVal.gdb\MunicipiosCV2012"
# se indican los coeficientes de las rectas inferior y superior
reg = [[[1.49, -3.72],[10.54, -213.2]],[[2.19, -7.97], [9.34, -169.5]],
    [[2.3, -5.89], [11.12, -162.95]]]    # coef. regresión [variable ind., constante]
reg2 =[11.12, -162.95]  # regresión del tramo alto
cambio = [22, 22, 20]     # valor en gradfos del cambio de reg1 a reg2
limSup = [450, 400, 440]

slp = "\\DatosProcesados.gdb\\Slope_"  # pendientes originales sin procesar

Res_gdb = "\\Resultados.gdb"

# ----- RESULTADOS
rCont = Res_gdb + r"\Slp_cRFR_"    # pendiente clasificada por Regresion RFR


try:
    i = 0
    for p in prov:
        print " --> creando raster de pendiente continuo para", p


        # Reclasificando los raster mediante el archivo txt
        if not arcpy.Exists (rCont + p):
            print u"... clasificando raster", rCont + p
            # ojo! NODATA para que los valores fuera de tabla no aparezcan

            rTemp1 = Con(Raster(slp + p) < cambio[i], reg[i][0][0]* Raster(slp+p) + reg[i][0][1],
                reg[i][1][0] * Raster(slp + p) + reg[i][1][1])
            rTemp2 = Con (rTemp1 < 0, 0, rTemp1)
            rTemp3 = Con (rTemp2 > limSup[i], limSup[i], rTemp2)
            rTemp4 = Int (rTemp3)

            #rutaRcon =

            rTemp4.save(ruta + "\\Trabajos\CVal_Susc\\"+ rCont + p)


        else:
            print u" No se creará el raster continuo", rCont+p


        i = i+1
        # FIN del bucle de provincias

    # Borra rasters temporales creados en workspace
    for r in arcpy.ListRasters():
        print u"... ...  borrando raster temporal", r
        arcpy.Delete_management (r)


except arcpy.ExecuteError: # error arcGIS
    print "------------> Error GIS en el script:"
    exc_tb = sys.exc_info()[2]
    print arcpy.GetMessages(2), "- Error en linea", exc_tb.tb_lineno

except Exception as error:  # error general
    print "-----------> Error general en el script:"
    # captura el valor en el tercer elemento de la tupla resultado
    exc_tb = sys.exc_info()[2]
    # propiedad tb_lineno da el nº de linea
    print error, "- Error en linea", exc_tb.tb_lineno

else: # si no hay excepciones
    print u"\n -- Finalizado con éxito --"
    FinProc = time.time()
    DuracionProc = (FinProc - InicioProc)
    print "Tiempo de proceso total:", seghora(DuracionProc)
