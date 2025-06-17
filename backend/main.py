from fastapi import FastAPI
from routers import chat
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Supervisor Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Hoặc chỉ định ["http://localhost:3000"] nếu bạn dùng frontend riêng
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

app.include_router(chat.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)