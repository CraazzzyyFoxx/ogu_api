from starlette import status
import uvicorn

from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, RedirectResponse
from tortoise.contrib.fastapi import register_tortoise
from cashews import cache

from app.services.schedule import ScheduleService
from config import tortoise_config
from app.api import router

app = FastAPI()
app.include_router(router)


@app.get("/")
async def read_root():
    return {"Hello": "World"}



# @app.middleware("http")
# async def add_process_time_header(request: Request, call_next):
#     response = JSONResponse({"detail": "Not authenticated"}, status_code=status.HTTP_401_UNAUTHORIZED)
#     try:
#         response = await call_next(request)
#     except hikari.errors.UnauthorizedError:
#         pass
#     return response

origins = [
    "https://crypto.asuscomm.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_tortoise(
    app,
    config=tortoise_config,
    add_exception_handlers=True,
    generate_schemas=True
)


@app.on_event("startup")
async def startup_event():
    await ScheduleService.init()

if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host="192.168.1.88",
        port=80,
        reload=True,
    )
