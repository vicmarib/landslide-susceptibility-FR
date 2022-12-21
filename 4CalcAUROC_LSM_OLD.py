# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:     4calc_AUROC_LSM         prueba compleja con repeticiones y p. corte
#
# RUTINA ANTIGUA. MEJOR NO UTILIZAR!!
# ==============
# Purpose:  Calcular datos para curva ROC y el área bajo la curva AUROC
#           para el mapa de suscepbilidad LSM, proveniente de raster
#           Se establece el nivel de corte por debajo del cual no se consideran datos
#           Salidas y entrada a tabla
#  OJO!  No utilizar decimales en los datos
# Incluye pruebas con EsayROC
#  BORRAR resTabOrd para comenzar los cálculos de nuevo con nuevos datos LSI
#
# IMPORTANTE, las tablas de confusión no deben tener valores LSI = Null ni LSI = 0
#       Se pueden eliminar a mano con el Editor AGIS
#       Ambos valores LSI se eliminan con la selección de un límite inferior "limInf"
#
# Se plantea un límInf para LSI por debajo del cual no se toman en cuenta los valores
#   se utilizan los puntos de corte óptimos obtenidos con el cálculo completo
#
# USO: Colocar los datos cuantitativos ordenados en orden decreciente,
#   y los "1" en los valores mayores
#   Vale para mapas de suscept. con patrón de referencia fijo, y variando el umbral
#   del LSmap calculado (punto de corte)
#
#   Calcula los datos de cutoff con coste (incluir en wOC) para los niveles de clase
#
# Created:     18/07/2019, revisado 19/7/19
# Copyright:   (c) icantari 2019
#
#-------------------------------------------------------------------------------

import sys, os, time
import arcpy
from arcpy import env
from collections import Counter
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

# ------ Funcion proximo() devuelve el numero mas próximo a otro de una lista -----
# numeros es una lista de números, final el número que se quiere buscar más próximo
def proximo(final,numeros):
 def el_menor(numeros):
  menor = numeros[0]
  retorno = 0
  for x in range(len(numeros)):
   if numeros[x]<menor:
    menor = numeros[x]
    retorno = x
  return retorno

 diferencia = []
 for x in range(len(numeros)):
  diferencia.append(abs(final - numeros[x]))
 return numeros[el_menor(diferencia)]
# ---- fin de definición función próximo

# Definir workspace
wsp = env.workspace = ruta + r"\Trabajos\CVal_Susc"


# DATOS ENTRADA  --> COMPLETAR!!! ---------------

fR = "FR2"   # OJO! indicar si es ClusterFR CFR o General FR1 o FR2
fR = "EasyROC"   # para pruebas
limInf = [0, 0, 0]      # con limInf = 0 el cálculo es completo
limInf = [356, 356, 356]    # con limInf > 0 el cálculo es parcial
lInt = 5  # longitud de cada intervalo. Para mayor exactitud --> EL MENOR POSIBLE!

grabROCparc = "S"   # indicar si se quieren grabar los datos parciales: "S". No funciona

print u"... trabajando con patrón/FR", fR
# Diferenciando FR de CFR
if fR == "FR1":
    lSup = 560 # limite intervalo superior, redondeado por encima el valor + alto de LSI
    prov = ["FR1_CS", "FR1_VL", "FR1_AL"]    # lista de mapas provinciales LSM creados por AHP
    if not 0 in limInf:  # valores calculados como P.Corte óptimos para datos completos
        limInf = [100, 75, 55]   # para level > M (clase 3)
        limInf = [149, 115, 102] # para level Q4
        limInf = [104, 80, 69]  # para level > H (clase 4)
        #limInf = [69]  # Level H para Quantile
    prov = ["FR1_AL"]

elif fR == "FR2":
    lSup = 550 # limite intervalo superior, redondeado por encima el valor + alto de LSI
    prov = ["FR2_CS", "FR2_VL", "FR2_AL"]    # lista de mapas provinciales LSM creados por AHP
    if not 0 in limInf:
        limInf = [75, 65, 45]  # Level > M
        limInf = [81, 68, 60]  # Level > H
        limInf = [60]  # Level H para Quantile
    prov = ["FR2_AL"]

elif fR == "CFR":    # análisis cluster solo
    lSup = 410 # limite intervalo superior, redondeado por encima el valor + alto de LSI
    prov = ["CFR_CS", "CFR_VL", "CFR_AL"]    # lista de mapas provinciales LSM creados por AHP
    if not 0 in limInf:
        limInf = [55, 55, 45]
        limInf = [71, 63, 63]  # Level > H
        limInf = [89]  # Level H para Quantile
    prov = ["CFR_AL"]

elif fR == "RFR":     # análisis cluster + regresión
    lSup = 460 # limite intervalo superior, redondeado por encima el valor + alto de LSI
    prov = ["RFR_CS", "RFR_VL", "RFR_AL"]    # lista de mapas provinciales LSM creados por AHP
    if not 0 in limInf:
        limInf = [71, 63, 57]
        #limInf = [80]
    prov = ["RFR_AL"]

elif fR == "EasyROC":   # solo para pruebas externas
    lSup = 640
    prov =["xEasyROC2"]

interv = range (lSup, 0, -lInt)
interv.append(0)

#costes (pesos) para el Optimo Cutoff - OC [Se, Sp]
wOC = np.array([[0.2, 0.8], [0.5, 0.5], [0.73, 0.27], [0.89, 0.11]])
# -- una prueba para repartir mejor los pixels en La Marina
wOC = np.array([[0.2, 0.8], [0.5, 0.5], [0.72, 0.28], [0.89, 0.11]])

# OJO, las tablas de confusión no deben tener valores de LSI = Null. Eliminar a mano
# Ahora ya hay una selección LSI > 0
resTabOrd = "\\Resultados.gdb\\ConfTabOrd_"

#cLSM = ruta + "\\Trabajos\\LaMarina\\Validar.gdb\\" + mod + "cLSM"

# --- RESULTADOS

resROCp = "\\Tablas_ROC.gdb\\ROCdatParc_"
resROCt = "\\Tablas_ROC.gdb\\ROCdatTot_"

clasLSM = ruta + "\\Trabajos\\CVal_Susc\\Validar.gdb\\ClasLSM_"


# Borrando el archivo al principio no da error 32 de lectura con creaXLS
if arcpy.Exists("Z_borrame.xls"):
    os.remove (wsp + "\\Z_borrame.xls")
if arcpy.Exists("Z_borrame2.xls"):
    os.remove (wsp + "\\Z_borrame2.xls")

# OJO! las listas deben estar ordenadas


try:
    # ------- #     Gran bucle de los 3 LSM  # ------------#
    m = 0
    for lm in prov:
    #for lm in ["log", ""]:

        if lm == "":     # para el caso logit
            print " Saliendo del programa..."
            sys.exit()

        print " ... analizando y clasificando LSM para", lm, u"con lim. infº", limInf

        # se seleccionan valores LSI si se ha incluido el valor límite
        # En cualquier caso se eliminan valores Null y 0
        selVal = '"LSI" > ' + str(limInf[m])
        arcpy.MakeTableView_management (resTabOrd + lm, "resTabView", selVal)

        # creando lista de datos
        repet = []
        datLSI = []
        patron = []
        cur = arcpy.SearchCursor ("resTabView")
        for c in cur:
            rep = c.Count
            lsi = c.LSI
            pat = c.patron
            repet.append (rep)
            datLSI.append(lsi)
            patron.append(pat)


        #  --- BUCLE de Cálculo de datos generales ..........................
        pCorteL = [lSup]   # se le añade el elemento superior

        #tpL = []    # inicializando listas con datos
        tnL = []
        fnL=  []
        speL = []  # para cálculos de cut off
        senL = []

        # creando tabla vacía de resultados totales, la anterior se borrará
        if not arcpy.Exists (resROCt+lm + str(limInf)):
            arcpy.CreateTable_management(wsp, resROCt+lm+str(limInf[m]))
            for f in ("P_Corte", "DatInt", "DatAcum","TP", "TN", "FP", "FN"):
                arcpy.AddField_management (resROCt+lm+str(limInf[m]), f, "LONG")
            for g in ("AUCtot", "TPR_SEN", "TNR_SPE", "FPR"):
                arcpy.AddField_management (resROCt+lm+str(limInf[m]), g, "FLOAT", None, "8")
        else:
            print "borrando datos tabla resumen"
            arcpy.DeleteRows_management(resROCt+lm+str(limInf[m]))  # vacía el contenido si existe


        for pCorte in interv:
            print "... calculando datos generales para punto corte >=", pCorte

            # se comprueba si pCorte está en la lista de datos
            if not pCorte in datLSI:
                print "OJO!", pCorte, u"no está en la lista, se busca otro valor"
                print u"Se utilizará el más próximo en la lista:", proximo(pCorte, datLSI)
                pCorte = proximo(pCorte, datLSI)
                print
            # se comprueba que pCorte no está repetido
            if pCorte in pCorteL:
                continue   # se sale de la iteración
            pCorteL.append(pCorte)  # lista de puntos de corte


            # creando tabla vacía de resultados PARCIALES, la anterior se borrará
            if grabROCparc == "S":
                if not arcpy.Exists (resROCp+ lm + "_" + str(pCorte)):
                    arcpy.CreateTable_management(wsp, resROCp+lm + "_" + str(pCorte))
                    for f in ("LSI", "DatInt", "DatAcum","TP", "TN", "FP", "FN"):
                        arcpy.AddField_management (resROCp +lm+ "_" + str(pCorte), f, "LONG")
                    for g in ("AUC", "Y_TPR_SEN", "TNR_SPE", "X_FPR"):
                        arcpy.AddField_management (resROCp+lm +"_" + str(pCorte), g,
                            "FLOAT", None, "8")
                else:
                    print "borrando datos tabla resumen"
                    arcpy.DeleteRows_management(resROCp+lm + "_" + str(pCorte))  # vacía el contenido

            pCi = datLSI.index(pCorte)    #localiza la posición en la lista del pCorte
                                            # NO incluye el punto de corte
            if pCi +1 < len(datLSI):       # mientras pCi no sea el último de la lista
                if datLSI[pCi+1] == pCorte: # esto incluye el pCorte, si tiene "0" y/o "1"
                    pCi = pCi + 2           # caso si hay dos LSI (V/N en patron)
                else:
                    pCi = pCi + 1           # caso con un LSI (V o N en patron)
            fnC = 0
            tnC = 0    # falsos y verdaderos negativos a partir del punto de Corte
            if pCorte >= 0:    # solo se corta cuando el valor >= 0
                for t in range (0, len(datLSI[pCi:])):
                    if patron[pCi+t] > 0:
                        fnC = fnC + repet[pCi+t]   # sumando los valores de repetición final
                    if patron[pCi+t] == 0:
                        tnC = tnC + repet [pCi+t]

                # se recortan las series de datos hast pC
                repetC = repet[:pCi]
                datLSIC = datLSI[:pCi]
                patronC = patron[:pCi]


            j = 0     # contador de repeticiones en la lista
            tpT = tnT = fnT = fpT = 0   # valores totales T

            for x in datLSIC:
                if x > 0:   # valores positivos en datos
                    if patronC[j] == 0:   # j: posición en la lista
                        fpT = fpT + repetC[j]
                    if patronC[j] == 1:
                        tpT = tpT + repetC[j]
                if x == 0:  # valores negativos en datos
                    if patronC[j] == 0:
                        tnT = tnT + repetC[j]
                    if patronC[j] == 1:
                        fnT = fnT + repetC[j]

                j += 1

            # calculo de los índices ROC
            acc = float (tpT + tnT + tnC)/(tpT+fpT+tnT + fnT + fnC + tnC)   # l = p + n  --> todos los casos
            tnr = float(tnT+tnC) / (tnT + tnC + fpT) # specifity (exactitud clase positiva)
            tpr = float(tpT) / (tpT + fnT + fnC)  # sensitivity, eje Y para la curva
            fpr = 1 - tnr  # 1 - specifity, eje X para la curva

            print " TP: ", tpT, " TN:", tnT + tnC, " FP:", fpT, " FN:", fnT + fnC
            print "TNR:", tnr, " TPR (y):",  tpr , " FPR (x):", fpr , " ACC:", acc

            tnrC = tnr     # se guarda el dato para copiarlo en la tabla final
            tprC = tpr
            fprC = fpr
            tnL.append(tnT+tnC)   # para tabla resumen datos parciales
            fnL.append(fnT+fnC)
            senL.append(tpr)
            speL.append(tnr)

            #  ----- BUCLE DE INTERVALOS DE DATOS
            # se crea una lista que empieza en lSup y va disminuyendo lInt, por debajo del min
            if len(datLSIC)== 0:  # primer bucle
                minm = lSup
            else:
                minm = min(datLSIC)
            nInf = minm - lInt
            if nInf < 0:   nInf = 0

            int = range (lSup + lInt, nInf, -lInt)
            if int[-1] > 0 and int[-1] - lInt >= 0:
                int.append (0)   # se añade el intervalo final para los "0"s

            # Calculando valores de ROC
            j = 0     # contador de repeticiones en intervalo
            k = 1    # contador de valores en intervalo
            s = 0
            z = 0   # contador datos parciales tabla
            fSum0 = 0   # total negativos
            tSum1 = 0   # total positivos
            ac = 0      # nº datos acumulados
            h = 0   # contador de intervalo final (solo debe haber 1)
            xROC = [0]    # se marca el origen de coordendadas
            yROC = [0]
            AUC = []
            auc = []
            print "... calculando datos de intervalos ROC"

            # ---------  bucle de intervalo
            for i in pCorteL[1:]:  # empezando en el segundo
                nrep = 0  #para número de datos totales dentro de intervalo


                # ----------- bucle de datos dentro de intervalo
                for x in datLSIC:
                    #if x < i and x > i-lInt:
                    if x >= i and x < pCorteL[s]:    # valores dentro de intervalo de pCorte
                               # j: posición en la lista
                        if patronC[j] == 0:
                            fSum0 = fSum0 + repet[j]  # contando negativos totales
                            nrep = nrep + repet[j]    # contando nº datos
                        if patronC[j] == 1:
                            tSum1 = tSum1 + repet [j] # contando positivos totales
                            nrep = nrep + repet[j]
                        ac = fSum0 + tSum1    # nº de datos totales acumulados
                        #print x, ac, nrep
                        j = j + 1

                    fSum0tab = fSum0    # para datos parciales de la tabla
                    tSum1tab = tSum1

                s = s + 1
                if i <= pCorte and h < 1:    # tramo final deshechado
                    fSum0 = fSum0 + tnC    # parte final con la suma de negativos del patron
                    tSum1 = tSum1 + fnC    # parte final con la suma de positivos del patron
                    ac = fSum0 + tSum1
                    nrep = nrep + fnC + tnC
                    h += 1                      # solo se pasa una vez por el tramo final
                tpr = tSum1*1.0/(tpT + fnT + fnC)
                fpr = fSum0*1.0/(fpT + tnT + tnC)

                #sys.exit()
                # Cálculo de la curva ROC y del área AUROC
                xROC.append(fpr)
                yROC.append(tpr)

                auc = (xROC[k] - xROC[k-1]) * (yROC[k] + yROC[k-1]) * 0.5
                if auc >= 0:
                    AUC.append(auc)

                # print "Num:", nrep, " Num acum:", ac,  " FPR (x): {0:.3f};".format(fpr), \
                # " TPR (y): {0:.3f};".format(tpr), " auroc: {0:.3f}".format(auc)

                k += 1

                rows = arcpy.InsertCursor(resROCp+lm + "_" + str(pCorte))
                row = rows.newRow()
                row.LSI = i
                row.DatInt = nrep
                row.DatAcum = ac
                row.AUC = auc
                row.X_FPR = fpr
                row.Y_TPR_SEN = tpr
                row.TNR_SPE = 1-fpr
                row.TP = tSum1tab # no se tiene en cuenta el dato final
                row.TN =  tnL[z]  #(tnT + tnC) no vale, es constante
                row.FP = fSum0tab
                row.FN = fnL[z]

                z += 1
                rows.insertRow(row)
                del row, rows

                # fin de bucle-----------------------


            sumAUC = 0   # suma de la lista AUC para obtener AUROC
            for t in range (0, len(AUC)):
                sumAUC = sumAUC + AUC[t]

            print "pCorte:", pCorte, "  AUC:", sumAUC
            print

            # Se añaden datos uno a uno a la tabla resumen
            rows = arcpy.InsertCursor(resROCt+lm+str(limInf[m]))
            row = rows.newRow()
            row.P_Corte = pCorte
            row.DatInt = nrep
            row.DatAcum = ac
            row.TP = tpT
            row.TN = tnT + tnC
            row.FP = fpT
            row.FN = fnT + fnC
            row.AUCtot = sumAUC
            row.TPR_SEN = tprC
            row.TNR_SPE = tnrC
            row.FPR = fprC

            rows.insertRow(row)
            del row, rows

        # ------------ fin bucle

        # ABRIENDO FICHEROS PUNTOS DE CORTE TXT (solo para la lista de valores completa)
        # Calculando los cutoff óptimos, ficheros texto Totales y Parciales
        if limInf[m] == 0:
            nomFileT = open (wsp + "\\PtosCorte_TotDatLSM_"+ lm +".txt", "w")
            nomFileT.write ("# Punto corte  -  valor mx Se+Sp \n")
            nomFileP = open (wsp + "\\PtosCorte_LSM_"+ lm +".txt", "w")
            nomFileP.write ("#  Valores de puntos de corte para Reclasificar \n")
            i = 0   #número iteraciones
            #nomFileP.write (" " + str(lSup))

        # GRABANDO PUNTOS DE CORTE TXT (solo para la lista de valores completa)
            print u"\n ... grabando archivos con límites"
            ocValL = [lSup]
            for w in wOC:
                roc = np.array ([senL,speL])
                fMax = np.dot(w, roc)    # multiplicación vectorial, función a maximizar
                ocV = np.amax(fMax)     # devuelve el valor máximo
                ocI = np.argmax(fMax)  # devuelve el índice del valor máximo
                # como pCorteL incluye lSup, y senL no, hay que sumar 1 a pCorteL
                ocVal = pCorteL[ocI+1]  # localiza el valor en la lista
                ocValL.append(ocVal)   # Lista de valores de clase

                #grabando datos totales
                nomFileT.write ("   " +str(ocVal) + "   -   " + str(ocV) + "\n")

                i = i + 1
            # Grabando en archivo txt para 5 clases del raster en orden ascendente
            k = 0
            for j in ocValL:
                if k == 0:   # última linea fichero
                    nomFileP.write ("   0  " + str(ocValL[4]) + " : 1\n")
                else:
                    nomFileP.write (" " + str(ocValL[5-k]) + "  "+ str(ocValL[4-k]) + " : " \
                        + str(k+1) + "\n")

                k = k+1
            nomFileT.close()
            nomFileP.close()

        # Clasificando raster continuo en 5 clases o niveles. Solo para datos completos
            print " ... creando mapa clasificado", "clasLSM_" + lm
            cLSM = ReclassByASCIIFile("\\Resultados.gdb\\LSM_" + lm,
                "\\PtosCorte_LSM_" + lm + ".txt")
            cLSM.save(clasLSM + lm)

        else:
            print u" No se grabarán puntos de corte"

        # Copiando datos a Excel
        print "... copiando datos parciales y totales a Excel"
        xlsROCt = ruta + "\\Trabajos\\CVal_Susc\\ROCdatTot_" +lm + "_"+str(limInf[m]) +".xls"
        # Se graba en xls la ultima tabla parcial
        # resulta que no funciona la función de grabar varias hojas en libro.
        #   De momento, solo grabamos los resultados finales
        #creaXLS (resROCp + lm + "_" + str(pCorteL[-1]), xlsROCt)
        creaXLS (resROCt + lm + str(limInf[m]), xlsROCt)

    # --- fin del bucle de los 3 mapas

        m = m+1

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


