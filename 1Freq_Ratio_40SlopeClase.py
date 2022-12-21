# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:     1Freq_Ratio_40slope         Calculo FR para el factores slope
#
# Calcula para Clustered Frequency Ratio CFR de deslizamientos, para los pesos de SLOPE,
#   partiendo de 40 clases originales de 2 en 2º
#   creando el archivo ASCII para Reclasify de AGis .
#
#   Paso previo para calcular el LSM y la rutina general de cálculo FR
#   Utiliza modulo de acceso a datos arcpy.da y se trabaja con arrays
#
# Created:     1/06/19
#
#-------------------------------------------------------------------------------

import sys, os, time
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

# Definir workspace
wsp = env.workspace = ruta + r"\Trabajos\CVal_Susc"


# DATOS ENTRADA  ---------------


fName = "Slope40_"   #Raster provincial con 40 clases originales
prov = ["CS", "VL", "AL"]
prov =["VL"]

# patrón raster de COPUT34 extendido en binario para toda la Marina
pat = "\\DatosProcesados.gdb\\COPbin_"   # patron de referencia


# RESULTADOS
# se crean directamente los archivos .txt para Reclassify
# con fName "Slope_40Clase"

try:
    # Comienza el bucle de provincias
    for p in prov:
        print "... creando archivo de clasificacion para:", fName + p
        claseL = []
        factorL = []
        resL = []
        sumTP = 0    # suma total de pixels de la zona de estudio
        sumLP = 0    # suma total de pixels con landslides
        fNomRC = "\\DatosProcesados.gdb\\" + fName + p  # ruta completa RC

        # Creando raster combinado y su tabla
        rComb = Combine([Raster(fNomRC), Raster(pat + p)])
        tab = arcpy.BuildRasterAttributeTable_management(rComb, "NONE")

        # DOS POSIBILIDADES DE CREAR EL ARRAY
    ##        for row in arcpy.da.SearchCursor(tab,['Value','Count', n,'COP34_bin_TotLM']):
    ##            claseL.append(row)
    ##            a = np.array(claseL)
    ##            tras = np.transpose(a)    # matriz transpuesta para comprobación
    ##        del row
        # OJO con la longitud de los campos
        with arcpy.da.SearchCursor(tab,("Value",'Count', fName+p[0:2],'COPbin_'+ p)) as cursor:
            for row in cursor:
                claseL.append(row)
                a = np.array(claseL)
                tras = np.transpose(a)    # matriz transpuesta para comprobación
        # with crea y cierra el cursor sin preocuparse de bloqueos


        # se ordena la lista por la clase y COP, empezando por "1"
        claseL.sort(key= lambda n: (n[2], -n[3]) )

        # comprobando que son pares (todas las clases tienen valores)
        if len(claseL)%2 <> 0:
            print "OJO!! tabla con datos no pareados. Saliendo del programa..."
            sys.exit()

        # --- Calculando el valor de Frequency Ratio
        for i in range(len(claseL)):
            sumTP = sumTP + claseL[i][1]
            if claseL[i][3]== 1:    # con deslizamientos
                valCP = 0    # se comienza la clase con 1 y valiendo la suma 0
                sumLP = sumLP + claseL[i][1]
                valCP = claseL[i][1]   # pixels con deslizamiento en clase i
            if claseL[i][3]== 0:    # sin deslizamientos
                sumCP = valCP + claseL[i][1]
                factorL.append ((claseL[i][2], valCP, sumCP))  # clase, valor LP, valor tot

        for j in range(len(factorL)):
            FR = (factorL[j][1]/float(sumLP)) / (factorL[j][2]/float(sumTP))
            resL.append ((factorL[j][0], FR))
            #j = j+1

        sumTP_A = sum(tras[1])   # suma vectorial de los datos totales - Array
        sumLP_A = sum(tras[1]*tras[3])  # suma de datos con deslizamientos
        print " Comprobacion: ",
        print sumTP, "=", sumTP_A, " - - ", sumLP, "=", sumLP_A

        # se suma el total de las FR para normalizar a suma 100 todos los FR
        sumFR = 0
        for j in range(len(resL)):
            sumFR = resL[j][1] + sumFR

        # --- Creando los archivos de texto (parcial y total)
        nomFile = open(wsp + "\\FR\\FR_"+ fName + p + ".txt", "w")
        nomFileT = open(wsp + "\\FR\\FR_"+ fName + p + "_Tot.txt", "w")
        nomFile.write ("# Clase  -  FR \n")
        nomFileT.write ("#Clase - Nº px desliz - Nº px tot - FR - FR % \n")

        # El porcentaje se multiplica por 1000 y se redondea
        for i in range(len(resL)):
            nomFile.write(" " + str(resL[i][0]) + " : " + \
                str(int(round(resL[i][1]*1000/sumFR))) + "\n")
                # "   " + str(resL[i][1]/sumFR) + "\n")  # valor en porcentaje

            nomFileT.write("      " + str(resL[i][0]) + " : " +  str(factorL[i][1]) + "    " + \
                str(factorL[i][2]) + "    {0:.4f}".format(resL[i][1]) + \
                "    {0:.4f}".format(resL[i][1]/sumFR) + "\n")


        nomFile.close()
        nomFileT.close()
        # FIN bucle de provincias

    # Borra rasters temporales creados en workspace
    for r in arcpy.ListRasters():
        print u"... ...  borrando raster temporal", r
        arcpy.Delete_management (r)
    ##

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


