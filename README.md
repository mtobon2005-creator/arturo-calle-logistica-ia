# Arturo Calle · Alternativa nueva

Propuesta independiente de `fundamentosdeia`. Reúne los sprints 1–3 en una experiencia de planificación logística y agrega prioridad difusa y distribución de carga.

## Publicación

- GitHub Pages: `site/`, interfaz ligera que calcula en el navegador para que no requiera descargar un runtime Python.
- Streamlit: `app/streamlit_app.py`, versión Python para Streamlit Community Cloud.
- Flujo de Pages: `.github/workflows/pages.yml`, publica el sitio en cada cambio a `main`.

## Funciones

- Panel editable de datos para nueve tiendas.
- Diez reglas del sistema experto y sus condiciones.
- Comparación de prioridad discreta y prioridad difusa Sugeno.
- Asignación de unidades por necesidad, prioridad y capacidad disponible.
- Red vial estimada, rutas Dijkstra y optimización genética de visitas.
- Escenario competitivo y explicación de supuestos.

## Ejecutar Streamlit localmente

```bash
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

Los datos de tiendas, tiempos, umbrales y pagos son supuestos académicos de los materiales de los sprints 1–3. No se consultan inventarios reales ni tráfico en vivo.
