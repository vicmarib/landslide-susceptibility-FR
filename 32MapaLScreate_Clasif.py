## -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# 32MapaLS_create_Clasif.py    --> para modelos LSI ya creados con AHP
# Created on: 7/2019, revisado 15/4/2021 (con valores ajustados solo para Lito)
# Solo para clasificar con puntos de corte predefinidos (ELSUS, NBreak y
#   cuantiles)

#  DATOS DE ENTRADA: incluir los valores de intervalos (para ELSUS y cuantiles)
# resultados en Resultados.gdb
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
env.workspace = ruta + r"\Trabajos\CVal_Susc"


# --- DATOS DE ENTRADA
prov = ["CS", "VL", "AL"]
cProv = ["12", "46", "03"]

#tipos de FRatio
fRat = ["FR2_", "CFR_", "RFR_", "MFR_"]   # ELSUS v2, MFR, CFR y RFR, sin FR1"

#prov = ["CS"]     # OJO!!  PARA PRUEBAS
fRat = ["MFR_"]

# DEFINIR TIPO DE CLASIFICACION: ELSUS / NBreaks / cuantil
rGdb = ruta + "\\Trabajos\\CVal_Susc\\ELSUS.gdb" # para ELSUS
#rGdb = ruta + "\\Trabajos\\CVal_Susc\\NBreaks.gdb" # para NBreaks
rGdb = ruta + "\\Trabajos\\CVal_Susc\\Cuantil.gdb" # para cuantil

rDir = "\\ELSUS"   # para LSM con clasificación ELSUS
#rDir = "\\NBreaks"   # para LSM con clasificación NB
rDir = "\\Cuantil"        # para LSM con clasificación CUANTIL

#rGdb = ruta + "\\Trabajos\\CVal_Susc\\Validar.gdb" # para GENERAL YOUDEN
#rDir = ""   # para LSM con clasificación YOUDEN

# Ficheros con puntos de corte
pCorte = rDir + "\\PtosCorte_LSM_"

# Raster con datos LSI
rLSI = "\\Resultados.gdb\\LSM_"


# ----- RESULTADOS
rcProv = rGdb + "\\ClasLSM_"


try:
    i = 0
    print u"Comenzando cálculo para clasificación", rDir[1:]
    for p in prov:
        print " --> creando archivos para la provincia:", p
        for f in fRat:
        # Reclasificando los raster mediante el archivo txt
            if not arcpy.Exists (rcProv + f + p):
                print u"... clasificando raster para", f, p
                # ojo! NODATA para que los valores fuera de tabla no aparezcan
                rClasProv = ReclassByASCIIFile(rLSI + f+ p, pCorte + f + p + ".txt", "NODATA")
                rClasProv.save (rcProv + f + p)

            else:
                print u" No se creará el raster de clasificación para", f + p
                # se crean los objetos raster, al no haberse creado directamente


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
