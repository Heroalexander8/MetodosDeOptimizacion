import pandas as pd
import numpy as np
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import matplotlib.pyplot as plt
import math

class ResolveMDVRP:
    def __init__(self, ruta_excel):
        self.ruta_excel = ruta_excel
        self.problemas = {}
        self.cargar_datos()
        
    def cargar_datos(self):
        """Cargar todas las hojas de problemas desde el archivo Excel"""
        try:
            xls = pd.ExcelFile(self.ruta_excel)
            print(f"Hojas disponibles: {xls.sheet_names}")
            
            for nombre_hoja in xls.sheet_names:
                if nombre_hoja.startswith('Problem'):
                    df = pd.read_excel(xls, sheet_name=nombre_hoja)
                    numero_problema = int(nombre_hoja.split()[1])
                    self.problemas[numero_problema] = self.procesar_hoja_problema(df)
                    print(f"Problema {numero_problema} cargado correctamente")
        except Exception as e:
            print(f"Error al cargar el archivo Excel: {e}")
            # Crear datos de ejemplo si falla la carga
            self.crear_datos_ejemplo()
    
    def crear_datos_ejemplo(self):
        """Crear datos de ejemplo para pruebas cuando el archivo Excel no esté disponible"""
        print("Creando datos de ejemplo...")
        self.problemas[1] = {
            'depositos': [
                {'x': 0, 'y': 0, 'id': 'D1'},
                {'x': 50, 'y': 50, 'id': 'D2'}
            ],
            'clientes': [
                {'numero': 1, 'x': 10, 'y': 10, 'id': 'C1'},
                {'numero': 2, 'x': 20, 'y': 20, 'id': 'C2'},
                {'numero': 3, 'x': 30, 'y': 15, 'id': 'C3'},
                {'numero': 4, 'x': 40, 'y': 35, 'id': 'C4'},
                {'numero': 5, 'x': 25, 'y': 45, 'id': 'C5'}
            ],
            'num_depositos': 2
        }
    
    def procesar_hoja_problema(self, df):
        """Procesar una hoja de problema individual en un formato estructurado"""
        try:
            # Mostrar estructura del DataFrame para depuración
            print(f"Columnas disponibles: {df.columns.tolist()}")
            print(f"Primeras filas:\n{df.head()}")
            
            # Buscar información de depósitos de manera más flexible
            depositos = []
            clientes = []
            
            # Método alternativo para extraer datos
            # Buscar patrones comunes en archivos MDVRP
            if 'x' in df.columns and 'y' in df.columns:
                # Asumir que las primeras filas son depósitos y el resto clientes
                # Esta lógica necesita ajustarse según el formato real del Excel
                for indice, fila in df.iterrows():
                    if pd.notna(fila['x']) and pd.notna(fila['y']):
                        if indice < 2:  # Asumir primeras 2 filas son depósitos
                            depositos.append({
                                'x': float(fila['x']),
                                'y': float(fila['y']),
                                'id': f'D{len(depositos)+1}'
                            })
                        else:  # Resto son clientes
                            clientes.append({
                                'numero': len(clientes)+1,
                                'x': float(fila['x']),
                                'y': float(fila['y']),
                                'id': f'C{len(clientes)+1}'
                            })
            
            # Si no se encontraron datos válidos, usar datos de ejemplo
            if not depositos or not clientes:
                print("No se pudieron extraer datos válidos del Excel, usando datos de ejemplo")
                return {
                    'depositos': [
                        {'x': 0, 'y': 0, 'id': 'D1'},
                        {'x': 50, 'y': 50, 'id': 'D2'}
                    ],
                    'clientes': [
                        {'numero': 1, 'x': 10, 'y': 10, 'id': 'C1'},
                        {'numero': 2, 'x': 20, 'y': 20, 'id': 'C2'},
                        {'numero': 3, 'x': 30, 'y': 15, 'id': 'C3'},
                        {'numero': 4, 'x': 40, 'y': 35, 'id': 'C4'}
                    ],
                    'num_depositos': 2
                }
            
            return {
                'depositos': depositos,
                'clientes': clientes,
                'num_depositos': len(depositos)
            }
            
        except Exception as e:
            print(f"Error procesando hoja: {e}")
            return None
    
    def matriz_distancias(self, numero_problema):
        """Crear matriz de distancias para un problema dado"""
        problema = self.problemas[numero_problema]
        ubicaciones = problema['depositos'] + problema['clientes']
        num_ubicaciones = len(ubicaciones)
        
        # Crear matriz de distancias
        matriz_distancias = np.zeros((num_ubicaciones, num_ubicaciones), dtype=int)
        
        for i in range(num_ubicaciones):
            for j in range(num_ubicaciones):
                if i == j:
                    matriz_distancias[i][j] = 0
                else:
                    ubicacion1 = ubicaciones[i]
                    ubicacion2 = ubicaciones[j]
                    # Convertir a entero para OR-Tools
                    matriz_distancias[i][j] = int(self.distancia_euclidiana(ubicacion1, ubicacion2))
        
        return matriz_distancias, ubicaciones
    
    def distancia_euclidiana(self, ubicacion1, ubicacion2):
        """Calcular distancia euclidiana entre dos puntos"""
        return math.sqrt((ubicacion1['x'] - ubicacion2['x'])**2 + (ubicacion1['y'] - ubicacion2['y'])**2)
    
    def resolver_problema(self, numero_problema, num_vehiculos=1):
        """Resolver una instancia específica del problema"""
        if numero_problema not in self.problemas:
            print(f"Problema {numero_problema} no encontrado")
            return None
            
        problema = self.problemas[numero_problema]
        matriz_distancias, ubicaciones = self.matriz_distancias(numero_problema)
        num_depositos = problema['num_depositos']
        num_clientes = len(problema['clientes'])
        
        print(f"Resolviendo problema con {num_depositos} depósitos y {num_clientes} clientes")
        print(f"Total de ubicaciones: {len(ubicaciones)}")
        
        # Crear administrador de índices de enrutamiento
        # CORRECCIÓN: Usar solo un vehículo por depósito inicialmente
        total_vehiculos = min(num_vehiculos, num_clientes)  # No más vehículos que clientes
        
        # Los depósitos son los índices de inicio/fin
        indices_depositos = list(range(num_depositos))
        
        administrador = pywrapcp.RoutingIndexManager(
            len(matriz_distancias), 
            total_vehiculos,
            indices_depositos,  # inicios
            indices_depositos   # finales
        )
        
        # Crear modelo de enrutamiento
        enrutamiento = pywrapcp.RoutingModel(administrador)
        
        def callback_distancia(desde_indice, hasta_indice):
            """Devuelve la distancia entre los dos nodos"""
            desde_nodo = administrador.IndexToNode(desde_indice)
            hasta_nodo = administrador.IndexToNode(hasta_indice)
            return int(matriz_distancias[desde_nodo][hasta_nodo])
        
        indice_callback_transito = enrutamiento.RegisterTransitCallback(callback_distancia)
        
        # Definir costo de cada arco
        enrutamiento.SetArcCostEvaluatorOfAllVehicles(indice_callback_transito)
        
        # Agregar restricción de distancia
        nombre_dimension = 'Distancia'
        enrutamiento.AddDimension(
            indice_callback_transito,
            0,  # sin holgura
            5000,  # distancia máxima de viaje del vehículo
            True,  # comenzar acumulado en cero
            nombre_dimension
        )
        dimension_distancia = enrutamiento.GetDimensionOrDie(nombre_dimension)
        dimension_distancia.SetGlobalSpanCostCoefficient(100)
        
        # CORRECCIÓN: Forzar que todos los clientes sean visitados
        for nodo in range(num_depositos, len(ubicaciones)):
            enrutamiento.AddDisjunction([administrador.NodeToIndex(nodo)], 1000000)
        
        # Configurar heurística de primera solución
        parametros_busqueda = pywrapcp.DefaultRoutingSearchParameters()
        parametros_busqueda.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        parametros_busqueda.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        parametros_busqueda.time_limit.FromSeconds(30)  # Más tiempo
        
        # Resolver el problema
        print("Iniciando resolución...")
        solucion = enrutamiento.SolveWithParameters(parametros_busqueda)
        
        # Procesar y devolver solución
        if solucion:
            print("¡Solución encontrada!")
            return self.procesar_solucion(numero_problema, administrador, enrutamiento, solucion, ubicaciones, num_depositos, total_vehiculos)
        else:
            print("No se encontró solución")
            return None
    
    def procesar_solucion(self, numero_problema, administrador, enrutamiento, solucion, ubicaciones, num_depositos, num_vehiculos):
        """Procesar la solución en un formato legible"""
        problema = self.problemas[numero_problema]
        rutas = []
        distancia_total = 0
        
        for id_vehiculo in range(num_vehiculos):
            indice = enrutamiento.Start(id_vehiculo)
            ruta = []
            distancia_ruta = 0
            
            while not enrutamiento.IsEnd(indice):
                indice_nodo = administrador.IndexToNode(indice)
                ubicacion = ubicaciones[indice_nodo]
                ruta.append(ubicacion['id'])
                indice_anterior = indice
                indice = solucion.Value(enrutamiento.NextVar(indice))
                distancia_ruta += enrutamiento.GetArcCostForVehicle(
                    indice_anterior, indice, id_vehiculo
                )
            
            # Agregar el nodo final (depósito)
            indice_nodo = administrador.IndexToNode(indice)
            ubicacion = ubicaciones[indice_nodo]
            ruta.append(ubicacion['id'])
            
            # Solo agregar rutas no vacías
            if len(ruta) > 2:  # Más que solo depósito -> depósito
                indice_deposito = id_vehiculo % num_depositos
                rutas.append({
                    'id_vehiculo': id_vehiculo,
                    'deposito': problema['depositos'][indice_deposito]['id'],
                    'ruta': ruta,
                    'distancia': distancia_ruta
                })
                distancia_total += distancia_ruta
        
        return {
            'numero_problema': numero_problema,
            'distancia_total': distancia_total,
            'num_vehiculos_usados': len(rutas),
            'rutas': rutas,
            'ubicaciones': ubicaciones,
            'num_depositos': num_depositos
        }
    
    def visualizar_solucion(self, solucion):
        """Visualizar la solución con matplotlib"""
        if not solucion:
            print("No hay solución para visualizar")
            return
            
        plt.figure(figsize=(12, 8))
        
        # Extraer ubicaciones
        ubicaciones = solucion['ubicaciones']
        dict_ubicaciones = {ubic['id']: (ubic['x'], ubic['y']) for ubic in ubicaciones}
        
        # Graficar depósitos
        deposito_graficado = False
        for ubic in ubicaciones:
            if ubic['id'].startswith('D'):
                plt.plot(ubic['x'], ubic['y'], 'rs', markersize=12, 
                        label='Depósito' if not deposito_graficado else "")
                plt.annotate(ubic['id'], (ubic['x'], ubic['y']), xytext=(5, 5), 
                           textcoords='offset points')
                deposito_graficado = True
        
        # Graficar clientes
        cliente_graficado = False
        for ubic in ubicaciones:
            if ubic['id'].startswith('C'):
                plt.plot(ubic['x'], ubic['y'], 'bo', markersize=8,
                        label='Cliente' if not cliente_graficado else "")
                plt.annotate(ubic['id'], (ubic['x'], ubic['y']), xytext=(5, 5), 
                           textcoords='offset points')
                cliente_graficado = True
        
        # Graficar rutas con diferentes colores
        colores = plt.cm.Set3(np.linspace(0, 1, len(solucion['rutas'])))
        for i, ruta in enumerate(solucion['rutas']):
            color = colores[i]
            puntos_ruta = [dict_ubicaciones[nodo] for nodo in ruta['ruta']]
            xs, ys = zip(*puntos_ruta)
            plt.plot(xs, ys, '-', color=color, linewidth=2, 
                    label=f"Vehículo {i+1} desde {ruta['deposito']}")
        
        plt.title(f"Solución MDVRP - Problema {solucion['numero_problema']}\n"
                 f"Distancia Total: {solucion['distancia_total']:.0f}, Vehículos: {solucion['num_vehiculos_usados']}")
        plt.xlabel('Coordenada X')
        plt.ylabel('Coordenada Y')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.show()
    
    def imprimir_info_problemas(self):
        """Imprimir información sobre los problemas cargados"""
        for numero_problema, problema in self.problemas.items():
            print(f"\nProblema {numero_problema}:")
            print(f"  Depósitos: {len(problema['depositos'])}")
            print(f"  Clientes: {len(problema['clientes'])}")
            for deposito in problema['depositos']:
                print(f"    {deposito['id']}: ({deposito['x']}, {deposito['y']})")
            for cliente in problema['clientes'][:5]:  # Solo primeros 5
                print(f"    {cliente['id']}: ({cliente['x']}, {cliente['y']})")
            if len(problema['clientes']) > 5:
                print(f"    ... y {len(problema['clientes'])-5} clientes más")

# Ejemplo de uso
if __name__ == "__main__":
    # Inicializar el resolvedor con el archivo Excel
    resolvedor = ResolveMDVRP('19MDVRP Problem Sets.xlsx')
    
    # Imprimir información de los problemas
    resolvedor.imprimir_info_problemas()
    
    # Resolver un problema específico (ej. Problema 1)
    print("\n" + "="*50)
    print("Resolviendo Problema 1 con 2 vehículos...")
    print("="*50)
    
    solucion = resolvedor.resolver_problema(1, num_vehiculos=2)
    
    if solucion:
        print("\n✅ SOLUCIÓN ENCONTRADA:")
        print(f"📊 Distancia total: {solucion['distancia_total']}")
        print(f"🚛 Vehículos utilizados: {solucion['num_vehiculos_usados']}")
        
        print("\n🛣️ RUTAS:")
        for i, ruta in enumerate(solucion['rutas']):
            print(f"  Vehículo {i+1} desde {ruta['deposito']}: "
                  f"{' → '.join(ruta['ruta'])} (Distancia: {ruta['distancia']})")
        
        # Visualizar la solución
        resolvedor.visualizar_solucion(solucion)
    else:
        print("❌ No se encontró solución para el Problema 1")