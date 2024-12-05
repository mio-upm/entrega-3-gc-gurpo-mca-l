from pulp import *
import pandas as pd

# Iniciar el problema
modelo = LpProblem("Entrega 3 - Grupo L - Apartado 1", sense=LpMinimize)

# Leer los datos de Excel
exceloperaciones = pd.read_excel("241204_datos_operaciones_programadas.xlsx")
excelcostes = pd.read_excel("241204_costes.xlsx")

# Añadir nombre Quirófanos a la primera columna del excel de costes
excelcostes.rename(columns={excelcostes.columns[0]: "Quirófanos"}, inplace=True)

# Filtrar las operaciones de Cardiología Pediátrica
cardiologia = exceloperaciones[exceloperaciones["Especialidad quirúrgica"] == "Cardiología Pediátrica"]

# Definir conjuntos
I = cardiologia["Código operación"].tolist()  # Operaciones
J = excelcostes["Quirófanos"].tolist()  # Quirófanos

# Crear diccionario de diccionarios de los costes por cada quirófano y operación
costes_dict = excelcostes.set_index("Quirófanos").to_dict(orient="index")

# Subconjunto incompatible
Li = {}
horarios = cardiologia.set_index("Código operación")[["Hora inicio ", "Hora fin"]].to_dict(orient="index")
for i in I:
    Li[i] = []
    for h in I:
        if i != h:
            if horarios[i]["Hora inicio "] < horarios[h]["Hora fin"] and horarios[h]["Hora inicio "] < horarios[i]["Hora fin"]:
                Li[i].append(h)

# Variables de decisión
x = LpVariable.dicts("x", [(i, j) for i in I for j in J], cat="Binary")

# Función objetivo: minimizar el coste total
modelo += lpSum(costes_dict[j][i] * x[(i, j)] for i in I for j in J)

# Restricción 1: Cada operación debe asignarse a un quirófano
for i in I:
    modelo += lpSum(x[(i, j)] for j in J) >= 1

# Restricción 2: Operaciones incompatibles no pueden compartir quirófano
for i in I:
    for h in Li[i]:
        for j in J:
            modelo += x[(i, j)] + x[(h, j)] <= 1

# Resolver el modelo
modelo.solve()

# Resultados del modelo
print("\n\nEstado del modelo:", LpStatus[modelo.status])
print("\nCoste total de asignación:", value(modelo.objective))

# Mostrar asignaciones óptimas
asignaciones = [(i, j) for i in I for j in J if x[(i, j)].value() == 1]
asignaciones_df = pd.DataFrame(asignaciones, columns=["Operación", "Quirófano"])
print("\n")
print(asignaciones_df.to_string(index=False))