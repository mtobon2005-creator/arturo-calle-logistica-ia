# Arturo Calle · Alternativa nueva

Segunda propuesta, independiente de `fundamentosdeia`. Reúne los sprints 1–3 en un flujo operativo y añade prioridad difusa y distribución de carga.

## Qué cambia en esta propuesta

- Panel único con prioridad, capacidad, cobertura de inventario y ruta sugerida.
- Una tabla editable para los datos de las tiendas.
- Base de conocimiento con las diez reglas explicadas.
- Módulo de estrategia competitiva y búsqueda de ruta con algoritmo genético.
- Prioridad continua y distribución de unidades según necesidad y capacidad.
- Sitio informativo de Pages en `site/` y la app interactiva en `site/app/`.

## Probar localmente

```bash
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

## Publicar en GitHub Pages

Sube el contenido del proyecto a un repositorio propio. En **Settings → Pages**, selecciona **GitHub Actions**. El workflow publica `site/` y copia el punto de entrada de Streamlit a `site/app/`.

La URL de la app quedará en `https://<usuario>.github.io/<repositorio>/app/`. Pages ejecuta Streamlit con stlite/Pyodide dentro del navegador; la primera carga requiere descargar el runtime.

## Publicar en Streamlit Community Cloud

Conecta el repositorio en [Streamlit Community Cloud](https://share.streamlit.io/) y selecciona `app/streamlit_app.py` como archivo principal. Esta opción ejecuta la app en un servidor Streamlit.

## Alcance y supuestos

Los datos de las nueve tiendas, los tiempos de viaje, la capacidad, los umbrales y los pagos competitivos son supuestos académicos de los adjuntos. No se conectan inventarios reales ni tráfico en tiempo real.
