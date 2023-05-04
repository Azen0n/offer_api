from fastapi import FastAPI

from routers import offer_router, approval_process_router

app = FastAPI()

app.include_router(offer_router)
app.include_router(approval_process_router)
