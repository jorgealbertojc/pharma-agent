from app.config import settings
import json

print(json.dumps(settings.model_dump(), indent=4, ensure_ascii=False))
