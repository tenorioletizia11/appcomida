# AppComida

Aplicación web full-stack para recomendar qué comer sin tener que pensarlo demasiado. Permite recomendar platos para cocinar o pedir delivery según gustos, historial, alergias, tiempo disponible y presupuesto. Además, puede conectarse con OpenAI para personalizar la explicación y los tips de receta/compra.

## Qué incluye

- Perfil alimenticio editable.
- Persistencia local en SQLite.
- Historial de interacciones para aprender del usuario.
- Motor de recomendación por score que evita repeticiones.
- Modo cocinar con pasos y lista exacta de compra.
- Modo delivery para días sin tiempo.
- Integración opcional con OpenAI Responses API mediante `OPENAI_API_KEY`.

## Ejecutar en local

```bash
python3 app.py
```

Luego abre `http://localhost:8000`.

## Variables de entorno

Copia `.env.example` a `.env` o exporta las variables en tu shell si quieres activar la capa de IA:

```bash
cp .env.example .env
# luego reemplaza OPENAI_API_KEY por tu clave real
python3 app.py
```

## Estructura

- `app.py`: servidor HTTP, base de datos SQLite, scoring y llamada a OpenAI.
- `static/index.html`: interfaz principal.
- `static/styles.css`: estilos.
- `static/app.js`: interactividad de frontend.
- `data/appcomida.db`: base de datos creada automáticamente al ejecutar la app.

## Tests

```bash
python3 -m unittest discover -s tests
```
