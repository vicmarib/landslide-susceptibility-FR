# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:     6calcKappaW-5Niveles         Calculo Kappa para 5 niveles
#
# Purpose:  Calcular Kappa Weighted para LSM's y ELSUS.
#  OJO!  para arcGis 10.5
#
# Created:     18/03/2019, revisado 15/06/2019
# Copyright:   (c) icantari 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import sys, os, time
import arcpy
from arcpy import env
#import scipy
import numpy as np


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


# DATOS ENTRADA  ---------------

#mod = "COP"     # OJO!   ELEGIR UNO DE LOS DOS <<<<<----------------
#mod = "ELS"    # aunque realmente no empleamos el ELSUS como base

prov = ["CS", "VL", "AL"]
#prov = ["CS"]
nMap1 = "ClasLSM_"
nMap2 = "ClasLSM_RFR"      # ELEGIR patrón en nMap2, p.e., RFR
#nMap2 = mod + "_clasLSM2_HT"

# Indicar tipo de clasificación
gdb = "\\ELSUS.gdb\\"
#gdb = "\\Validar.gdb\\"     # para clasificación GY


#tipos de FRatio para Slope
fRat = ["FR1_", "FR2_", "MFR6_", "CFR_", "RFR_"]   # ELSUS v1, v2 y CFR"
fRat.remove(nMap2[8:]+ "_")  # se elimina el patrón

map1 = gdb + nMap1
map2 = gdb + nMap2   # también aquí si nMap2 es ELSUS
#map2 = "\\Validar.gdb\\"+ nMap2


# RESULTADOS
tabLS = gdb + "\\LSM_calcKappa"   # tabla con resultados GY/ELSUS


# la salida de datos es directa por pantalla


try:
    print "RESULTADOS para ", gdb
    # Comienza bucle de provincias
    for p in prov:
        print "... calculando Kappa para prov.", p
        #  Comienza bucle de ratios
        for f in fRat:
            # Creando raster combinado
            rComb = Combine([Raster(map1+f+p), Raster(map2+"_"+p)])
            # Creando la tabla de atributos ROC del raster
            arcpy.BuildRasterAttributeTable_management(rComb, "NONE")
            arcpy.CopyRows_management(rComb, tabLS, "")

            n1 = np.array ([0,0,0,0,0])
            n2 = np.array ([0,0,0,0,0])
            n3 = np.array ([0,0,0,0,0])
            n4 = np.array ([0,0,0,0,0])
            n5 = np.array ([0,0,0,0,0])

            outL = []      # valores sin datos en ambos modelos

            cur = arcpy.SearchCursor(tabLS)
            for c in cur:
                if nMap2 == "ClasLSM_FR2" and f == "FR1":
                    val1 = c.getValue((nMap1+f+p)[:9]+ "1")   # nombre del campo solo tiene 10 caracteres(10.5)
                    val2 = c.getValue((nMap2+p)[:9] +"2")
                else:
                    val1 = c.getValue((nMap1+f+p)[:10])   # nombre del campo solo tiene 10 caracteres(10.5)
                    val2 = c.getValue((nMap2+p)[:10])
                valSt = str(val1)+str(val2)
                val = int(valSt)
                num = c.Count
                if val in (1, 2, 3, 4, 5):       # Valores COPUT sin ELSUS
                    outL.append(num)
                elif val in (10, 20, 30, 40, 50):    # valores ELSUS sin COPUT
                    outL.append(num)
                elif val == 11:      # coincide 11
                    n1[0] = num
                elif val == 12 :
                    n1[1] = num
                elif val == 13:
                    n1[2] = num
                elif val == 14 :
                    n1[3] = num
                elif val == 15 :
                    n1[4] = num

                elif val == 21:
                    n2[0] = num
                elif val == 22 :    # coincide 22
                    n2[1] = num
                elif val == 23:
                    n2[2] = num
                elif val == 24 :
                    n2[3] = num
                elif val == 25 :
                    n2[4] = num

                elif val == 31:
                    n3[0] = num
                elif val == 32 :
                    n3[1] = num
                elif val == 33:     # coincide 33
                    n3[2] = num
                elif val == 34 :
                    n3[3] = num
                elif val == 35 :
                    n3[4] = num

                elif val == 41:
                    n4[0] = num
                elif val == 42 :
                    n4[1] = num
                elif val == 43:
                    n4[2] = num
                elif val == 44 :        # coincide 44
                    n4[3] = num
                elif val == 45 :
                    n4[4] = num

                elif val == 51:
                    n5[0] = num
                elif val == 52 :
                    n5[1] = num
                elif val == 53:
                    n5[2] = num
                elif val == 54 :
                    n5[3] = num
                elif val == 55 :
                    n5[4] = num        # coincide 55

            del cur
        ##    n1 = np.array ([1, 1, 2, 1, 0])
        ##    n2 = np.array ([1, 2, 1, 1, 0])
        ##    n3 = np.array ([2, 0, 4, 1, 0])
        ##    n4 = np.array ([1, 1, 1, 1, 0])
        ##    n5 = np.array ([0, 0, 0, 0, 2])

            # suma de datos totales coincidentes
            N = sum(n1+n2+n3+n4+n5)
            Nout = sum(outL)

            # ponderación linear L en aumento de 1 a 4
            w1 = np.array([0, 1, 2, 3, 4])
            w2 = np.array([1, 0, 1, 2, 3])
            w3 = np.array([2, 1, 0, 1, 2])
            w4 = np.array([3, 2, 1, 0, 1])
            w5 = np.array([4, 3, 2, 1, 0])

            # con ponderación cuadrática Q
            ww1 = np.array([0, 1, 4, 9, 16])
            ww2 = np.array([1, 0, 1, 4, 9])
            ww3 = np.array([4, 1, 0, 1, 4])
            ww4 = np.array([9, 4, 1, 0, 1])
            ww5 = np.array([16, 9, 4, 1, 0])


            sumObsL = sum(n1*w1 + n2*w2 + n3*w3 + n4*w4 + n5*w5)   # pond. lineal
            sumObsQ = sum(n1*ww1 + n2*ww2 + n3*ww3 + n4*ww4 + n5*ww5)

            sumC = n1 + n2 + n3 + n4 + n5                              # suma de columnas
            sumF = np.array([sum(n1), sum(n2), sum(n3), sum(n4), sum(n5)])    # suma de filas

            # Datos esperados
            es1 = (1.0/N)* sumC[0] * sumF
            es2 = (1.0/N)* sumC[1] * sumF
            es3 = (1.0/N)* sumC[2] * sumF
            es4 = (1.0/N)* sumC[3] * sumF
            es5 = (1.0/N)* sumC[4] * sumF

            sumPreL = sum(es1*w1 + es2*w2 + es3*w3 + es4*w4 + es5*w5)
            sumPreQ = sum(es1*ww1 + es2*ww2 + es3*ww3 + es4*ww4 + es5*ww5)

            wKapL = 1 - (sumObsL/sumPreL)
            wKapQ = 1 - (sumObsQ/sumPreQ)

            print " ---> ", nMap1+f+p, nMap2,
            print " wKappa L: {0:.4f}".format(wKapL), " wKappa Q: {0:.4f}".format(wKapQ)
            print "Datos totales:", N+Nout, " Datos no coincidentes", Nout
    # ... fin de bucle de provincias

        # ----------
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


