from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 🔐 CORS CORRETO (já blindado)
origins = [
    "https://viabilidade-sobral-mvp-clean.vercel.app",
    "https://viabilidadeteste.streamlit.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ HEALTHCHECK (NOVO)
@app.get("/health")
def health():
    return {"ok": True}

# ⚠️ IMPORTANTE: garantir resposta rápida
@app.options("/api/auth/session/verify")
def options_verify():
    return {"ok": True}

# 🔁 VERIFY (exemplo seguro)
@app.post("/api/auth/session/verify")
def verify_session():
    # aqui entra sua lógica real depois
    return {"ok": True}
