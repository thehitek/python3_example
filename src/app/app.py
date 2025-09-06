from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core import custom_logging
from src.api.auth.router import auth_router
from src.api.game.router import games_router
from src.api.info.router import info_router
from src.api.polygon.router import polygons_router
from src.api.robot.router import robots_router
from src.api.role.router import roles_router
from src.api.team.router import teams_router
from src.api.user.router import user_router
from src.core.backup import database_backup_without_ssh
from src.core.config import Config, Enviroment, Settings
from src.core.database import Database
from src.core.startup import database_startup
from src.core.admin import AdminApp
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.staticfiles import StaticFiles


def get_settings():
    return Settings()


app = FastAPI(title="Geoscan Arena Database API", 
              docs_url=None, 
              redoc_url=None, 
              openapi_url="/db_control/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)

app.mount(
    "/db_control/static/swagger",
    StaticFiles(directory="src/core/static_swagger"),
    name="swagger_static",
)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    res = JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )
    custom_logging.error(res.body)
    return res


app.add_exception_handler(RequestValidationError, validation_exception_handler)

# app.include_router(actions_router)
app.include_router(games_router)
app.include_router(teams_router)
app.include_router(roles_router)
app.include_router(robots_router)
app.include_router(polygons_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(info_router)

app.dependency_overrides[get_settings] = get_settings
settings: Settings = app.dependency_overrides[get_settings]()
Config.setup(settings)
Database.setup(settings, Config())

if settings.ENVIROMENT == Enviroment.Development or settings.ENVIROMENT == Enviroment.Production:
    admin_app = AdminApp.setup(Database.async_engine, app, settings)

# if settings.ENVIROMENT == Enviroment.Development:
#     init_admin(app, Database.SessionLocal)


@app.on_event("startup")
async def startup():
    settings: Settings = app.dependency_overrides[get_settings]()
    Config.setup(settings)
    Database.setup(settings, Config())

    custom_logging.logs_init(settings)
    await database_startup(settings)


@app.on_event("shutdown")
async def shutdown():
    if settings.AUTO_BACKUP:
        database_backup_without_ssh()
        print("It's over...\nBackup has done")
    else:
        print(
            f"It's over...\nBackup hasn't done due 'AUTO_BACKUP={settings.AUTO_BACKUP}'"
        )

@app.get("/db_control/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="static/swagger/swagger-ui-bundle.js",
        swagger_css_url="static/swagger/swagger-ui.css",
    )

@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()
