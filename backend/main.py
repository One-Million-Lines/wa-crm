import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api_shared import vtlog, package_name, config
from api_auth import router as auth_router
from api_contacts import router as contacts_router
from api_conversations import router as conversations_router
from api_messages import router as messages_router
from api_tasks import router as tasks_router
from api_automations import router as automations_router
from api_templates import router as templates_router
from api_analytics import router as analytics_router
from api_settings import router as settings_router
import signal
import sys

app = FastAPI(
    title="WaCRM API",
    description="WhatsApp CRM and Team Inbox API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5313",
        "http://127.0.0.1:5313",
        "https://onemillionlines.com",
        "https://www.onemillionlines.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(contacts_router)
app.include_router(conversations_router)
app.include_router(messages_router)
app.include_router(tasks_router)
app.include_router(automations_router)
app.include_router(templates_router)
app.include_router(analytics_router)
app.include_router(settings_router)


@app.get("/")
async def root():
    return {"service": package_name, "status": "running"}


@app.get("/health")
async def health():
    return {"status": "ok"}


def exit_handler(sig_num, frame):
    vtlog.info("Stopping application: {0}".format(package_name))
    sys.exit()


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, exit_handler)
    signal.signal(signal.SIGINT, exit_handler)

    port = int(config.get("APP_PORT", "5213"))
    host = config.get("APP_HOST", "0.0.0.0")

    vtlog.info("Starting WaCRM API", port=port, host=host)
    uvicorn.run(app, port=port, host=host, log_level="info")
