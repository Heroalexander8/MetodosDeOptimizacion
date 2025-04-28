from flask import Flask, render_template, request
import numpy as np
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            a = float(request.form['a'])
            b = float(request.form['b'])
            c = float(request.form['c'])
            x_max = float(request.form['x_max'])
            y_max = float(request.form['y_max'])

            # Preparar los datos para graficar
            x_vals = np.linspace(0, x_max + 2, 400)
            y1 = c - x_vals
            y2 = y_max * np.ones_like(x_vals)
            y_region = np.minimum(y1, y2)
            x_region = np.clip(x_vals, 0, x_max)

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
            for v in vertices:
                z = a * v[0] + b * v[1]
                z_vals.append((z, v))
            z_max, punto = max(z_vals)

            # Crear gráfico
            fig, ax = plt.subplots(figsize=(8,6))
            ax.plot(x_vals, y1, label=f'x + y ≤ {c}')
            ax.axvline(x=x_max, color='red', linestyle='--', label=f'x ≤ {x_max}')
            ax.axhline(y=y_max, color='green', linestyle='--', label=f'y ≤ {y_max}')
            ax.fill_between(x_region, 0, y_region, color='skyblue', alpha=0.5)
            ax.plot(punto[0], punto[1], 'ro', label=f'Máximo z={z_max} en {punto}')
            ax.set_xlim(0, x_max + 2)
            ax.set_ylim(0, y_max + 2)
            ax.set_xlabel('x (Horas de estudio en casa)')
            ax.set_ylabel('y (Horas de clase)')
            ax.set_title('Método gráfico - Optimización Lineal')
            ax.grid(True)
            ax.legend()

            # Guardar imagen en memoria
            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            plot_url = base64.b64encode(img.getvalue()).decode()

            return render_template('resultado.html', plot_url=plot_url)

        except Exception as e:
            error = f"Error en el cálculo: {e}"
            return render_template('index.html', error=error)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=4000)
