#!/usr/bin/env python3
import uvicorn
from src.app.app import get_settings
from src.core.config import Config, Enviroment


def main():
    Config.setup(get_settings())

    if Config.settings.ENVIROMENT == Enviroment.Development:
        uvicorn.run(
            app="src.app.app:app",
            host=Config.settings.FASTAPI_HOST,
            port=Config.settings.FASTAPI_PORT,
            timeout_keep_alive=3,
            reload=True,
            use_colors=True,
        )

    elif Config.settings.ENVIROMENT == Enviroment.Production:
        uvicorn.run(
            app="src.app.app:app",
            host=Config.settings.FASTAPI_HOST,
            port=Config.settings.FASTAPI_PORT,
            timeout_keep_alive=3,
            # log_level="info",
            workers=1,
            use_colors=True,
        )


if __name__ == "__main__":
    main()
