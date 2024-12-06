from pulp import *
import pandas as pd

# Inicializar problema PL
modelo= LpProblem("Modelo Multi-Servicios - Cobertura de Quirófanos", LpMinimize)

# Cargar los datos de operaciones y costes
excel_operaciones = pd.read_excel("241204_datos_operaciones_programadas.xlsx")
excel_costes = pd.read_excel("241204_costes.xlsx")

# Poner nombre a la primera columna de los costes
excel_costes.rename(columns={excel_costes.columns[0]: "Quirófanos"}, inplace=True)

servicios = [
    "Cardiología Pediátrica",
    "Cirugía Cardíaca Pediátrica",
    "Cirugía Cardiovascular",
    "Cirugía General y del Aparato Digestivo"
]

# Filtrar las operaciones solo a los servicios requeridos 
operaciones_servicios = excel_operaciones[excel_operaciones["Especialidad quirúrgica"].isin(servicios)]


# Crear conjuntos
I = operaciones_servicios["Código operación"].tolist()  # Operaciones
J = excel_costes["Quirófanos"].tolist()  # Quirófanos
Ci = excel_costes.select_dtypes(include='number').mean(axis=0).to_dict()  #costes medios por operacion
horarios = operaciones_servicios.set_index("Código operación")[["Hora inicio ", "Hora fin"]].to_dict(orient="index")
#print(horarios)

def planificar(I, J, horarios):
    planificaciones = {quir: [] for quir in J}
    copiaI = I.copy()
    for quir in J:  # Iterar sobre cada quirófano
        for op1 in copiaI:  # Iterar sobre cada operación
            conflicto = False 
            
            for op2 in planificaciones[quir]:  # Verificar con operaciones ya planificadas
                # Comparar horarios para evitar conflictos
                if not (
                    horarios[op1]['Hora fin'] <= horarios[op2]['Hora inicio '] or
                    horarios[op2]['Hora fin'] <= horarios[op1]['Hora inicio ']
                ):
                    conflicto = True
                    break
            
            # Si no hay conflicto, agregar la operación al quirófano
            if not conflicto:
                planificaciones[quir].append(op1)
                copiaI.remove(op1) 
    
    return planificaciones
llamada = planificar(I, J, horarios)

# Filtrar quirófanos sin operaciones asignadas
llamada_filtrada = {quir: ops for quir, ops in llamada.items() if ops}

# Imprimir todos los elementos del diccionario línea a línea
print("\nPlanificaciones por quirófano:")
for quir, ops in llamada_filtrada.items():
    print(f"{quir}:")
    for op in ops:
        print(f"   {op}")

lista_planificaciones = [i for i in llamada.keys()]

# Declaración de Bik
Bik = {}
for i in I:
    for k in llamada.keys():
        Bik[(i, k)] = 1 if i in llamada[k] else 0


#Declaracion Ck
Ck = {}
for k in llamada.keys():
    Ck[k] = sum(Bik[(i,k)] * Ci[i] for i in I)

#y
y = LpVariable.dicts('y', [k for k in llamada.keys()], cat = 'Binary')

#FO
modelo += lpSum(Ck[k] * y[k] for k in llamada.keys())


#Restriccion
for i in I:
    modelo += lpSum(Bik[(i,k)] * y[k] for k in llamada.keys()) >= 1

modelo.solve()

# Resultados
print("\n\nEstado del modelo:", LpStatus[modelo.status])
print("\nCoste total de asignación:", value(modelo.objective))