import pandas as pd
import numpy as np
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Leer datos desde Excel
file_path = '/mnt/data/19MDVRP Problem Sets (1).xlsx'
xls = pd.ExcelFile(file_path)
df = pd.read_excel(xls, sheet_name='Problem 1').dropna(subset=['x coordinate', 'y coordinate'])

# Coordenadas
customer_coords = df[['x coordinate', 'y coordinate']].values

depots_df = df.dropna(subset=['Depot x coordinate', 'Depot y coordinate'])

depot_coords = depots_df[['Depot x coordinate', 'Depot y coordinate']].values

# Calcula matriz de distancias
def create_distance_matrix(coords):
    size = len(coords)
    dist_matrix = np.zeros((size, size))
    for i in range(size):
        for j in range(size):
            if i != j:
                dist_matrix[i][j] = np.linalg.norm(coords[i] - coords[j])
    return dist_matrix

distance_matrix = create_distance_matrix(np.vstack([depot_coords, customer_coords]))

# Definir MDVRP con OR-Tools
def solve_mdvrp(dist_matrix, num_depots, num_customers):
    manager = pywrapcp.RoutingIndexManager(len(dist_matrix), num_depots, list(range(num_depots)))
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return dist_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    solution = routing.SolveWithParameters(search_parameters)

    routes = []
    for vehicle_id in range(num_depots):
        index = routing.Start(vehicle_id)
        route = []
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route.append(node_index)
            index = solution.Value(routing.NextVar(index))
        route.append(manager.IndexToNode(index))
        routes.append(route)

    return routes

routes = solve_mdvrp(distance_matrix, len(depot_coords), len(customer_coords))

# Extraer características para SVM
features = []
labels = []

for route in routes:
    route_length = sum(distance_matrix[route[i]][route[i+1]] for i in range(len(route)-1))
    num_customers = len(route) - 2
    features.append([route_length, num_customers])

median_route_length = np.median([f[0] for f in features])
labels = [1 if f[0] <= median_route_length else 0 for f in features]

# Entrenar modelo SVM
X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)

svm = SVC(kernel='linear')
svm.fit(X_train, y_train)

# Evaluar modelo
predictions = svm.predict(X_test)
accuracy = accuracy_score(y_test, predictions)
print(f'Accuracy SVM: {accuracy:.2f}')

# Predicción para nuevas rutas
new_route_feature = [np.mean([f[0] for f in features]), np.mean([f[1] for f in features])]
new_route_prediction = svm.predict([new_route_feature])
print(f'Prediction for new route (1=good, 0=bad): {new_route_prediction[0]}')
