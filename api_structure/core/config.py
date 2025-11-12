import os
from pathlib import Path
from dotenv import load_dotenv

APP_ENV = os.getenv("APP_ENV", "dev").lower()
IS_CLOUD = bool(os.getenv("SCM_DO_BUILD_DURING_DEPLOYMENT") 
                or os.getenv("MYAPP_ENVIRONMENT"))

GITLAB_PROJ_NAME = "email_copilot" # 改成你專案的名稱

if not IS_CLOUD:
    env_file = Path(
        str(
            "//TP-TABLEAU-V05/DSTeam/ResourceNSharing/8.gitLab env資訊"
            f"/{GITLAB_PROJ_NAME}/env/.env.{APP_ENV}"
        )
    )
    if env_file.exists():
        load_dotenv(env_file, override=True)
