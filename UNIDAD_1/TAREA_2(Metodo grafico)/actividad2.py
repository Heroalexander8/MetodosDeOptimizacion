#ACTIVIDAD 2 (SISTEMA DE ECUACIONES)
print("Maximizar: z = a*x + b*y")
a = float(input("Ingresa el valor de a (coeficiente de x): "))
b = float(input("Ingresa el valor de b (coeficiente de y): "))
print("\nRestricciones:")
c = float(input("Ingresa el valor para la restricción x + y ≤ c: "))
x_max = float(input("Ingresa el valor máximo para x (x ≤ ?): "))
y_max = float(input("Ingresa el valor máximo para y (y ≤ ?): "))
x_vals = np.linspace(0, x_max + 2, 400)
y1 = c - x_vals
y2 = y_max * np.ones_like(x_vals)
y_region = np.minimum(y1, y2)
x_region = np.clip(x_vals, 0, x_max)
plt.figure(figsize=(8, 6))
plt.plot(x_vals, y1, label='x + y ≤ ' + str(c))
plt.axvline(x=x_max, color='red', linestyle='--', label='x ≤ ' + str(x_max))
plt.axhline(y=y_max, color='green', linestyle='--', label='y ≤ ' + str(y_max))
plt.fill_between(x_region, 0, y_region, color='skyblue', alpha=0.5, label='Región factible')
vertices = [(0, 0), (0, min(y_max, c)), (min(x_max, c), 0)]
if x_max + y_max <= c:
    vertices.append((x_max, y_max))
else:
    intersec = c - x_max
    if 0 <= intersec <= y_max:
        vertices.append((x_max, intersec))
    intersec2 = c - y_max
    if 0 <= intersec2 <= x_max:
        vertices.append((intersec2, y_max))
z_vals = []
print("\nEvaluación de z = a*x + b*y en los vértices:")
for v in vertices:
    z = a * v[0] + b * v[1]
    z_vals.append((z, v))
    print(f"z = {a}{v[0]} + {b}{v[1]} = {z}")
z_max, punto = max(z_vals)
plt.plot(punto[0], punto[1], 'ro', label=f'Máximo z={z_max} en {punto}')
plt.xlim(0, x_max + 2)
plt.ylim(0, y_max + 2)
plt.xlabel("x (Horas de estudio en casa)")
plt.ylabel("y (Horas de clase)")
plt.title("Método gráfico - Optimización Lineal")
plt.grid(True)
plt.legend()
plt.show()