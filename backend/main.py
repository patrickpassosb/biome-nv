from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from db import db
from backboard import BACKBOARD_API_KEY
from routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.connect()
    db.setup()
    db.seed_default_profile()
    if not BACKBOARD_API_KEY:
        print("Warning: BACKBOARD_API_KEY not set. /chat and /recommend will return a configuration error.")
    yield
    if db.conn:
        db.conn.close()


app = FastAPI(title="Biome AI Strength Coach", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
app.include_router(router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
