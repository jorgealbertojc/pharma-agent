# Desarrollo Python

## Configuración

Copia el archivo de ejemplo y ajusta los valores según tu entorno local:

```bash
cp .env.example .env
```

Las variables disponibles están definidas en `.env.example`:

| Variable      | Descripción                          | Valor por defecto          |
|---------------|--------------------------------------|----------------------------|
| `DEBUG`       | Activa el modo debug                 | `False`                    |
| `OLLAMA_HOST` | URL del servidor Ollama              | `http://localhost:11434`   |
| `LOG_LEVEL`   | Nivel de logging (`DEBUG`, `INFO`…)  | `INFO`                     |

La aplicación carga estas variables mediante [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) desde el archivo `.env` en la raíz del proyecto (`app/config/settigns.py`).

## Verificar la configuración

Para comprobar que las variables de entorno se cargan correctamente, ejecuta:

```bash
uv run python -m tools.check_settings
```

Este comando imprime los valores actuales de `debug`, `ollama_host` y `log_level` tal como los resuelve la aplicación. Úsalo durante el desarrollo después de modificar `.env` o al configurar el entorno por primera vez.
