from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.endpoints import auth, users, markets, bets, wallet, missions, leaderboard, admin, support, payment
from app.core.s3 import s3_client
import sentry_sdk
import logging

logger = logging.getLogger(__name__)

# Initialize Sentry if DSN provided
if settings.SENTRY_DSN:
    sentry_sdk.init(dsn=settings.SENTRY_DSN)

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    version="1.0.0",
    description="ThePred - Prediction Markets Platform"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(markets.router, prefix="/markets", tags=["markets"])
app.include_router(bets.router, prefix="/bets", tags=["bets"])
app.include_router(wallet.router, prefix="/wallet", tags=["wallet"])
app.include_router(missions.router, prefix="/missions", tags=["missions"])
app.include_router(leaderboard.router, prefix="/leaderboard", tags=["leaderboard"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(support.router, prefix="/support", tags=["support"])
app.include_router(payment.router, prefix="/payment", tags=["payment"])


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Initializing S3 bucket...")
    await s3_client.init_bucket()
    logger.info("S3 bucket initialized")

    # Initialize default missions
    logger.info("Initializing default missions...")
    from app.init_missions import init_default_missions
    await init_default_missions()
    logger.info("Default missions initialized")

    # Start scheduler for mission resets
    logger.info("Starting scheduler...")
    from app.scheduler import start_scheduler
    start_scheduler()
    logger.info("Scheduler started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Stopping scheduler...")
    from app.scheduler import stop_scheduler
    stop_scheduler()
    logger.info("Scheduler stopped")


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
