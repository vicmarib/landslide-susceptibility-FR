# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:     5Calc_indexR         Calculo R index 5 niveles
#
# Purpose:  Calcular landslide density, R index, propuesta weighted (no utilizada)
#           COMPROBAR si están activos los pesos. Para todas las clasificaciones
#           GY, ELSUS, cuantil, NBreaks
#
# Created:     18/07/2019
# Copyright:   (c) icantari 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import sys, os, time
InicioProc = time.time() # inicio en segundos para cálculo del proceso

import arcpy
from arcpy import env
import scipy
import numpy as np
from collections import Counter

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
env.workspace = ruta + r"\Trabajos\CVal_Susc"


print seghora(time.time())

# ELEGIR SI SALIDA CON DATOS COMPLETOS O BASICOS
outBas = 1    # Salida Basica, si outBas <> 1, salida Completa

# DATOS ENTRADA  ---------------
prov = ["CS", "VL", "AL"]
#prov = ["AL"]

#tipos de FRatio
fRat = ["FR2_", "MFR_",  "CFR_", "RFR_"]   # ELSUS v2, MFR, CFR, RFR"
#fRat = ["FR2_"]    # para pruebas

gdb = "\\Cuantil.gdb\\"   # INDICAR GRUPO A ANALIZAR: Cuantil, ESLSUS o YOUDEN
#gdb = "\\ELSUS.gdb\\"
#gdb = "\\NBreaks.gdb\\"
#gdb = "\\Validar.gdb\\"   # Youden geneeralizado GY

pat = "\\DatosProcesados.gdb\\COPbin_"  # patron de referencia por provincia 0 y 1

# COLOCAR AQUI EL MAPA A ANALIZAR clasificado
nMap = "ClasLSM_"

# RESULTADOS
resComb = ruta + r"\Trabajos\CVal_Susc" + gdb + "Comb_LSM_"
#resComb = "\\ELSUS.gdb\\Comb_LSM_" + nMap[8:]



try:
    print u"Cálculos para ....", gdb
    # bucle de provincias
    for p in prov:
        # Creando raster provincial
        print ""
        print u"Comenzando el cálculo de indicadores para", p, " -------------"
        for f in fRat:
            #print "... calculando index R para", f+p
            map = ruta + r"\Trabajos\CVal_Susc" + gdb + nMap + f + p
            rComb = Combine([Raster(map), Raster(pat+p)])
            # Creando la tabla de atributos ROC del raster
            arcpy.BuildRasterAttributeTable_management(rComb, "NONE")
            arcpy.CopyRows_management(rComb, resComb + f + p, "")


            n1 = np.array ([0,0,0,0,0])
            n2 = np.array ([0,0,0,0,0])

            outL = []      # valores sin datos en ambos modelos

            cur = arcpy.SearchCursor(resComb + f + p)
            for c in cur:
                valG = c.getValue("COPbin_"+ p)   # Valor del raster 1 = deslizamiento
                valLSM = c.getValue((nMap+f)[:10])   #los 10 1ºs caracteres del nombre raster
                valSt = str(valLSM)+str(valG)  # juntar valores LSM + COPUT
                val = int(valSt)  # numerizar el valor
                num = c.Count
                if val in (1, 2, 3, 4, 5):       # Valores COPUT sin LSM. No se utiliza
                    outL.append(num)
                #elif val in (10, 20, 30, 40, 50):    # valores LSM sin COPUT
                #    outL.append(num)
                # Fallos n1. Son los FP
                elif val == 10:
                    n1[0] = num
                elif val == 20 :
                    n1[1] = num
                elif val == 30:
                    n1[2] = num
                elif val == 40 :
                    n1[3] = num
                elif val == 50 :
                    n1[4] = num

                # aciertos n2. Son los TP
                elif val == 11:
                    n2[0] = num
                elif val == 21 :
                    n2[1] = num
                elif val == 31:
                    n2[2] = num
                elif val == 41 :
                    n2[3] = num
                elif val == 51 :
                    n2[4] = num


            del cur

            # ---------- CALCULO R INDEX
            # Calculo Rindex para nivel 3/4 COPUT, sin llegar al nivel 1
            # propuesta de incluir un peso lineal como en kappa, ahora NO activa
            w = [1,2,3,4,5]
            w = [1,1,1,1,1]

            #Calculando la densidad de deslizamiento para cada franja, n1 fallos, n2 aciertos
            numR5 = float(n2[4])/(n1[4]+n2[4]) *  w[4]
            numR4 = float(n2[3])/(n1[3]+n2[3]) *  w[3]
            numR3 = float(n2[2])/(n1[2]+n2[2]) *  w[2]
            numR2 = float(n2[1])/(n1[1]+n2[1]) *  w[1]
            numR1 = float(n2[0])/(n1[0]+n2[0]) *  w[0]

            # densidad de los niveles 4 y 5
            numR45 = float(n2[4] +n2[3])/(n1[4]+n2[4] + n1[3]+n2[3])
            # densidad de los niveles 3, 4 y 5
            numR35 = float(n2[4] +n2[3] +n2[2])/(n1[4]+n2[4] + n1[3]+n2[3] + n1[2]+n2[2])
            # densidad de los niveles 2 y 3
            numR23 = float(n2[2] +n2[1])/(n1[1]+n2[1] + n1[2]+n2[2])

            # ---> sumando las densidades de cada franja
            # 5 niveles
            denR = numR5 + numR4 + numR3 + numR2 + numR1

            # N4+N5, N3, N2, N1
            denR45 = numR45 + numR3 + numR2 + numR1
            # N3+N4+N5, N2, N1
            denR35 = numR35 + numR2 + numR1
            # N4+N5, N3+N2 (dos niveles agrupados). No se incluye N1
            denR2n = numR23 + numR45

            # Calculando el índice para cada franja
            indR5 = (numR5/denR)
            indR4 = (numR4/denR)
            indR3 = (numR3/denR)
            indR2 = (numR2/denR)
            indR1 = (numR1/denR)

            indR45 = (numR45/denR45)
            indR35 = (numR35/denR35)
            indR2n = (numR45/denR2n)

            # Calculando el % de pixel por franja 4-5
            pc45 = float((n1[4]+n2[4] + n1[3] + n2[3]))/(np.sum(n1)+np.sum(n2))
            # Calculando el % de pixel por franja 3 -5
            pc35 = float((n1[4]+n2[4] +n1[3]+n2[3] +n1[2]+n2[2]))/(np.sum(n1)+np.sum(n2))

            # Calculando porcentajes de clases
            pc5 = float((n1[4] + n2[4]))/(np.sum(n1)+np.sum(n2))
            pc4 = float((n1[3] + n2[3]))/(np.sum(n1)+np.sum(n2))
            pc3 = float((n1[2] + n2[2]))/(np.sum(n1)+np.sum(n2))
            pc2 = float((n1[1] + n2[1]))/(np.sum(n1)+np.sum(n2))
            pc1 = float((n1[0] + n2[0]))/(np.sum(n1)+np.sum(n2))

            # Calculando el Density Ratio Dr
            dRat1 = (1.0* n2[4]/(n1[4]+n2[4])) / (1.0*np.sum(n2)/(np.sum(n1)+np.sum(n2)))
            dRat2 = (1.0* n2[3]/(n1[3]+n2[3])) / (1.0*np.sum(n2)/(np.sum(n1)+np.sum(n2)))
            dRat3 = (1.0* n2[2]/(n1[2]+n2[2])) / (1.0*np.sum(n2)/(np.sum(n1)+np.sum(n2)))
            dRat4 = (1.0* n2[1]/(n1[1]+n2[1])) / (1.0*np.sum(n2)/(np.sum(n1)+np.sum(n2)))
            dRat5 = (1.0* n2[0]/(n1[0]+n2[0])) / (1.0*np.sum(n2)/(np.sum(n1)+np.sum(n2)))

            # Calculando area Ratio
            s1 = (1.0* n1[4] + n2[4])/ (np.sum(n1)+np.sum(n2))
            s2 = (1.0* n1[3] + n2[3])/ (np.sum(n1)+np.sum(n2))
            s3 = (1.0* n1[2] + n2[2])/ (np.sum(n1)+np.sum(n2))
            s4 = (1.0* n1[1] + n2[1])/ (np.sum(n1)+np.sum(n2))
            s5 = (1.0* n1[0] + n2[0])/ (np.sum(n1)+np.sum(n2))

            # Calculando el Quality index
            q1 = 1.0 * (dRat1-1)**2 * s1
            q2 = 1.0 * (dRat2-1)**2 * s2
            q3 = 1.0 * (dRat3-1)**2 * s3
            q4 = 1.0 * (dRat4-1)**2 * s4
            q5 = 1.0 * (dRat5-1)**2 * s5
            qSum = q1 + q2  # + q3 + q4 + q5

            # Calculando error relativo
            err25 = (float(np.sum(n2)) - (n2[4] +n2[3] +n2[2] + n2[1]))/(np.sum(n2))
            err35 = (float(np.sum(n2)) - (n2[4] +n2[3] +n2[2]))/(np.sum(n2))
            err45 = (float(np.sum(n2)) - (n2[4] +n2[3]))/(np.sum(n2))
            err5 = (float(np.sum(n2)) - (n2[4]))/(np.sum(n2))

            # Calculando Sensibilidad o TPR (razón de verdaderos positivos)
            tpr5 = float(n2[4])/np.sum(n2)
            tpr4 = float(n2[3]+n2[4])/np.sum(n2)
            tpr3 = float(n2[2] +n2[3]+n2[4])/np.sum(n2)

            # Calculando Especificidad o TNR (razón de verdaderos negativos)
            tnr5 = 1 - float(n1[4])/np.sum(n1)
            tnr4 = 1 - float(n1[3] + n1[4])/np.sum(n1)
            tnr3 = 1 - float(n1[2] + n1[3] + n1[4])/np.sum(n1)

            # Calculando la exactitud (ACC)
            acc4= float((n2[4] + n2[3] + n1[2] + n1[1] + n1[0]))/(np.sum(n1)+np.sum(n2))

            # Calculando la dispersión niveles H y L
            dispHL = 1.0 * (n1[4] + n1[3] + n2[4] +n2[3]) / (n1[1] + n1[0] + n2[1] +n2[0])

            # Calculando eficiencia
            eff4 = 1.0 * np.sum(n2)/(n1[4] + n1[3] + n2[4] +n2[3])

            # Calculando la frecuencia de positivos en N45
            freqN45 = float(n2[4] +n2[3])/(np.sum(n2))

            # Calculando valor de Youden
            y5 = 0.2 * tpr5 + 0.8 * tnr5
            y4 = 0.5 * tpr4 + 0.5 * tnr4
            y3 = 0.73 * tpr3 + 0.27 * tnr3

            if outBas == 1:
                print " --> " + f[:3] + " Rind N45: {0:.3f}".format(indR45), \
                    "; Efic. N45: {0:.3f}".format(eff4), \
                    "; Eff H/L: {0:.3f}".format(1-pc45), \
                    "; Freq. N45: {0:.3f}".format(freqN45), \
                    "; Prueba: {0:.3f}".format(indR45*(1-pc45)), \
                     " acc: {0:.3f}".format(acc4)
                    #dRat1, dRat2, dRat3, dRat4, dRat5

            else:
                print " --> "+f[:3]+ " Rind N45: {0:.4f}".format(indR45), \
                    " Rind N35: {0:.4f}".format(indR35), \
                    " Rind N5: {0:.4f}".format(indR5), \
                    " Rind N4: {0:.4f}".format(indR4), \
                    " Rind N3: {0:.4f}".format(indR3), \
                    " mx N5: {0:.4f}".format(y5), \
                    " mx N4: {0:.4f}".format(y4), \
                    " mx N3: {0:.4f}".format(y3)
                print    " pN5: {0:.4f}".format(numR5), \
                    " pN4: {0:.4f}".format(numR4), \
                    " pN45: {0:.4f}".format(numR45), \
                    " pc%45: {0:.4f}".format(pc45), \
                    " pc%35: {0:.4f}".format(pc35), \
                    " Error5: {0:.4f}".format(err5), \
                    " Error45: {0:.4f}".format(err45), \
                    " TNR4: {0:.4f}".format(tnr4), \
                    " ACC: {0:.4f}".format(acc4)


            #print str(indR1+indR2+indR3+indR4+indR5)    # paa comprobar que la suma da 1.0

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


