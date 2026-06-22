# Administrador de Productos (Python + Flask)

Aplicación web para administrar productos con operaciones CRUD:

- Crear productos
- Listar productos
- Editar productos
- Eliminar productos

Incluye persistencia en SQLite y una interfaz web responsiva.

## Requisitos

- Python 3.10+ (recomendado)

## Instalación

1. Crear entorno virtual:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

## Ejecución

```bash
python app.py
```

La app quedará disponible en:

- http://127.0.0.1:5000

## Estructura principal

- `app.py`: lógica del servidor y rutas CRUD.
- `templates/`: vistas HTML (listado y formulario).
- `static/styles.css`: estilos de la interfaz.
- `products.db`: base de datos SQLite (se crea automáticamente al iniciar).