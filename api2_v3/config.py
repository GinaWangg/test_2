import os
from pathlib import Path
from dotenv import load_dotenv


APP_ENV = os.getenv("APP_ENV", "dev").lower()
IS_CLOUD = bool(os.getenv("SCM_DO_BUILD_DURING_DEPLOYMENT") or os.getenv("MYAPP_ENVIRONMENT"))

if not IS_CLOUD:
    env_file = Path(f"env/.env.{APP_ENV}")
    if env_file.exists():
        load_dotenv(env_file, override=True)
