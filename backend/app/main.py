from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import engine, Base
from app.routes import product, review, cart, address, order, chat, user

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dress E-Commerce API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(product.router)
app.include_router(review.router)
app.include_router(cart.router)
app.include_router(address.router)
app.include_router(order.router)
app.include_router(chat.router)
app.include_router(user.router)

@app.get("/")
def root():
    return {"message": "Dress E-Commerce API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
