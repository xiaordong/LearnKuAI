import os

import dotenv
dotenv.load_dotenv()

# 必要环境变量校验
_REQUIRED_VARS = {
    "ZHIPU_API_KEY": "智谱 API Key",
    "ZHIPU_URL": "智谱 API 地址",
    "MODEL": "模型名称",
}

_missing = [f"{k}（{desc}）" for k, desc in _REQUIRED_VARS.items() if not os.getenv(k)]
if _missing:
    raise EnvironmentError(
        f"缺少必要环境变量，请在 .env 中配置：\n  " +
        "\n  ".join(_missing)
    )

API_KEY = os.getenv("ZHIPU_API_KEY")
BASE_URL = os.getenv("ZHIPU_URL")
MODEL = os.getenv("MODEL")
