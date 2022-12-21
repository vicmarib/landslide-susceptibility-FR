# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# 3MapaLS_create.py    --> para modelos creados con AHP
# Created on: 7/2019, revisado 15/7/2019 (con valores ajustados solo para Lito)
# OJO! ha dado bastantes problemas extraños esta rutina
#  por ejemplo, no funciona si Slpc_FR1 está calculado y LSM_FR1 no
# PROBLEMA: multiplicar raster por decimales.
# SOLUCIÓN: Se multiplica por enteros y luego se divide

# Descripción: Genera los LSM a partir de los valores de clase y factores
# Para CFR, RFR y FR1 y 2 y las tres provincias por separado
#
# Incluye tambien el nuevo RFR por regresión y MFR
#   Crea la tabla de confusión organizada
#  DATOS DE ENTRADA: incluir los coeficientes de factores según AHP (solo 1 modelo)
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

print seghora(time.time())
# Definir workspace
wsp = env.workspace = ruta + r"\Trabajos\CVal_Susc"
print seghora(time.time())

# Definir Scratch workspace temporal
#swp = env.scratchWorkspace = ruta + r"\Trabajos\CVal_Susc"


# --- DATOS DE ENTRADA

prov = ["_CS", "_VL", "_AL"]
cProv = ["12", "46", "03"]   # solo utilizado para extraer máscara de provincia
muni = ruta + r"\Datos_ESP\ComVal\Datos_ComVal.gdb\MunicipiosCV2012"

#tipos de FRatio para Slope
fRat = ["FR1", "FR2", "CFR", "MFR"]   # ELSUS v1, v2 y CFR"

#prov = ["_CS", "_VL"]     # OJO!!  PARA PRUEBAS
#cProv = ["03"]
fRat = ["MFR7"]


# valores coeficientes de factores, en orden de pendiente, lito y usos
# lsm0 = [0.58, 0.28, 0.14]    coef. del mapa ELSUS: NO UTILIZADO
#lsm1 = [0.65, 0.23, 0.12]
#lsm2 = [0.74, 0.16, 0.10]
#lsm = [lsm0, lsm1, lsm2]
lsm = [0.70, 0.19, 0.11]    # media de lsm1 y lsm2
lsm100 = [70, 19, 11]  # para no trabajar con decimales

# valores de clases de los factores por FR (solo litologia con valores ajustados)
##clasSlpFR1 = "\\FR\\FR_Slp8FR1_"   # basado en ELSUS v1
##clasSlpFR2 = "\\FR\\FR_Slp8FR2_"   # basado en ELSUS v2
##clasSlpCFR = "\\FR\\FR_Slp8CFR_"   # Cluster FR
##clasSlpMFR = "\\FR\\FR_Slp8MFR_"   # sistema MFR

clasSlp = "\\FR\\FR_Slp8"   # Cluster FR
clasLito = "\\FR\\FRaj_Lito_"   # valores ajustados solo para Lito
clasUsos = "\\FR\\FR_Usos_"

# raster de factores con clases numéricas
##slpFR1 = r"\DatosProcesados.gdb\Slp8FR1_"    # FR General: v1
##slpFR2 = r"\DatosProcesados.gdb\Slp8FR2_"    # FR General: v2
##slpCFR = r"\DatosProcesados.gdb\Slp8CFR_"    # FR Cluster: CFR
##slpMFR = r"\DatosProcesados.gdb\Slp8MFR_"    # FR Modified: MFR

slp = r"\DatosProcesados.gdb\Slp8"
litoClas = "\\DatosProcesados.gdb\\Lito_CVA"
usosClas = "\\DatosProcesados.gdb\\Usos_CVA"

pat = "\\DatosProcesados.gdb\\COPbin"  # patron de referencia por provincia 0 y 1

Res_gdb = "\\Resultados.gdb"

# ----- RESULTADOS
fProv = "\\DatosProcesados.gdb\\Prov\\Prov_"    # máscara de provincias con municipios

# raster de factores con clases valoradas con FR
##SlpFR1_Clasif = "\\Resultados.gdb\\Slp_cFR1_"
##SlpFR2_Clasif = "\\Resultados.gdb\\Slp_cFR2_"
##SlpCFR_Clasif = "\\Resultados.gdb\\Slp_cCFR_"
##SlpRFR_Clasif = "\\Resultados.gdb\\Slp_cRFR_"
##SlpMFR_Clasif = "\\Resultados.gdb\\Slp_cMFR_"

Slp_Clasif = "\\Resultados.gdb\\Slp_c"
Slp_Clasif = ruta + "\\Trabajos\\CVal_Susc\\Resultados.gdb\\Slp_c"   # para el bucle de tipos FR
Lito_Clasif = "\\Resultados.gdb\\Lito_cFR"
Usos_Clasif = "\\Resultados.gdb\\Usos_cFR"

goldS_LSM_tab = "\\Resultados.gdb\\tabLSM"
cLSM = "\\Resultados.gdb\\cLSM"
LSM_mask = "\\Resultados.gdb\\LSM_mask"
LSM_int = "\\Resultados.gdb\\LSM_int"  # raster de enteros general
#LSM_int2 = "\\Resultados.gdb\\LSM_int2"  # raster de enteros para GFR2
#LSM_intC = "\\Resultados.gdb\\LSM_intC_"  # raster de enteros para CFR

#tabla de confusión ordenada de mayor a menor
resTabOrd = "\\Resultados.gdb\\ConfTabOrd_"

try:
    i = 0
    for p in prov:
        for f in fRat:
            print " --> creando archivos para", f+p
            # seleccionando y grabando feature de la provincia p
            # ... parece necesario para ExtractByMask
            if not arcpy.Exists (fProv + p):
                selP = "\"INECodProv\" = '" + cProv[i] + "'"
                arcpy.MakeFeatureLayer_management(muni, "provLay", selP)
                arcpy.CopyFeatures_management ("provLay", fProv + p)

            # Reclasificando los raster mediante el archivo txt
            if not arcpy.Exists (Slp_Clasif + f + p):    # poner "if not"
                print u"... clasificando raster y creando máscara para", f+p
                # ojo! NODATA para que los valores fuera de tabla no aparezcan

                Slp_Clase = ReclassByASCIIFile(slp + f+ p, clasSlp + f + p + ".txt", "NODATA")
                # extrayendo raster con máscara de provincias para lito y usos. ACTIVAR
                ##extLito = ExtractByMask (litoClas, fProv + p)
                ##extUsos = ExtractByMask (usosClas, fProv + p)
                ##Lito_Clase = ReclassByASCIIFile(extLito, clasLito + p + ".txt", "NODATA")
                ##Usos_Clase = ReclassByASCIIFile(extUsos, clasUsos + p + ".txt", "NODATA")

                # grabando los raster
                print u"... grabando raster"
##                rSl1 = ruta + "\\Trabajos\\CVal_Susc\\" + SlpFR1_Clasif + p
##                rSl2 = ruta + "\\Trabajos\\CVal_Susc\\" + SlpFR2_Clasif + p
##                rSlC = ruta + "\\Trabajos\\CVal_Susc\\" + SlpCFR_Clasif + p

                rSl = ruta + "\\Trabajos\\CVal_Susc\\" + Slp_Clasif + f + p
                rLit = ruta + "\\Trabajos\\CVal_Susc\\" + Lito_Clasif + p
                rUso = ruta + "\\Trabajos\\CVal_Susc\\"+ Usos_Clasif + p
                #sys.exit()    # PARA LAS PRUEBAS CON ALICANTE (no grabar tdodos los raster)

                Slp_Clase.save(Slp_Clasif + f + p)   # a mano
                # Slp_Clase.save(rSl)
                Lito_Clase = Raster(Lito_Clasif + p)   # borrar tras pruebas
                Usos_Clase = Raster(Usos_Clasif + p)   # borrar tras  pruebas
                ##Lito_Clase.save(rLit)    #activar
                ##Usos_Clase.save(rUso)   #activar


            else:
                print u" No se crearán los rasters de clasificación para", f+p
                # se crean los objetos raster, al no haberse creado directamente
                #SlpGFR_Clase = Raster(SlpGFR_Clasif + p)
                #SlpCFR_Clase = Raster(SlpCFR_Clasif + p)
                Lito_Clase = Raster(Lito_Clasif + p)
                Usos_Clase = Raster(Usos_Clasif + p)


            # Creación del patrón de oro (standard) de referencia COPUT (gold)
            # El raster binario extendido se valora en 1000 si tiene dato>0, -1000 si no
            goldS_bin_ext = Con (Raster(pat+p) > 0, 1000, -1000)

            # Crear raster LSM para todos los valores lsm, igual para coput y elsus
            # Comienza el bucle de FRatio (GFR y CFR)
            j = 0

            if not arcpy.Exists (goldS_LSM_tab + f + p):    # tabla tabLSM
                print " ... creando mapa LSM", f + p
                # se crea el objeto raster de Freq. Ratio
                Slp_Clase = Raster(Slp_Clasif  + f +  p)
                #objR = Slp_Clasif  + f + "_" + p

                # multiplicando rasters por enteros para que funcione
                calcLSM = Slp_Clase * lsm100[0] + Lito_Clase * lsm100[1] + \
                    Usos_Clase * lsm100[2]
                # se regresa a los valores originales AHP
                calcLSM = calcLSM / 100
                 # Crear un mapa de enteros
                LSMap_integ = Int(calcLSM)

                # rutas de raster de decimales y enteros
                resLSM = ruta + r"\Trabajos\CVal_Susc\Resultados.gdb\LSM_"+ f + p
                resLSMint = ruta + r"\Trabajos\CVal_Susc\Resultados.gdb\LSM_int" + f +  p

                calcLSM.save(resLSM)
                LSMap_integ.save(resLSMint)

                print " ... creando mosaico LSM - COPUT"
                 # Se suma el LSM y el raster COPUT
                arcpy.MosaicToNewRaster_management([Raster(LSM_int + f + p), goldS_bin_ext],
                Res_gdb, "LSM", "", "16_BIT_SIGNED", "25", "1", "SUM", "FIRST")

                # Creando la tabla de atributos ROC del raster
                arcpy.BuildRasterAttributeTable_management("\\Resultados.gdb\\LSM",
                 "NONE")
                arcpy.CopyRows_management("\\Resultados.gdb\\LSM",
                    goldS_LSM_tab + f + p, "")


            else:
                print u" No se creará el mapa LSM", f+ p


            #  Organizando tabla de confusión
            if not arcpy.Exists (resTabOrd + f + p):
                print u"... creando tabla de confusión", resTabOrd + f + p
                # arcpy.CopyRows_management (tabLSI, resTab)
                arcpy.AddField_management (goldS_LSM_tab + f + p,"LSI", "LONG", 8)
                arcpy.AddField_management (goldS_LSM_tab + f + p, "patron", "LONG", 3)
                cur = arcpy.UpdateCursor(goldS_LSM_tab + f +  p)
                for c in cur:
                    val = c.Value
                    if val > 1000:       # verdaderos positivos
                        c.LSI = val - 1000
                        c.patron = 1
                    elif val == -1000:    # verdaderos negativos
                        c.LSI = 0
                        c.patron = 0
                    elif val == 1000:      # falsos negativos
                        c.LSI = 0
                        c.patron = 1
                    else :                  # falsos positivos, valores negativos de "val"
                        if val < 0 and val < -1000:
                            c.LSI = val
                        if val < 0 and val > - 1000:
                            c.LSI = 1000 + val
                        c.patron = 0
                    cur.updateRow(c)
                del cur

                # creando tabla de confusión final ordenada en descendente
                arcpy.Sort_management (goldS_LSM_tab + f + p, resTabOrd + f + p,
                    [["LSI", "DESCENDING"]])

            else:
                print u" No se creará", resTabOrd + f + p

            j = j+1
            # fin del bucle de FREQ. RATIO

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
