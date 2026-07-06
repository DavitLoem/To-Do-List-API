from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from dotenv import load_dotenv
import os

load_dotenv()

# Determine environment for documentation visibility
app_env = os.getenv("APP_ENV", "local")
show_docs = app_env in ["local", "staging"]

# Define Security Scheme for Swagger UI (Authorize Button)
security = HTTPBearer()

app = FastAPI(
    title="To Do List API",
    description="API for To Do List Application with JWT Authentication",
    docs_url="/docs" if show_docs else None,
    redoc_url="/redoc" if show_docs else None,
    swagger_ui_parameters={"docExpansion": "none"},
    components={
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }
    }
)

# CORS configuration
origins = [
    "http://localhost:3000",
    "http://localhost:8080",
    "http://localhost:5000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Validation Error Handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    formatted_errors = []

    for error in errors:
        field = error["loc"][-1] if len(error["loc"]) > 0 else "unknown_field"
        formatted_errors.append({
            "field": field,
            "message": error["msg"]
        })

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Data validation error",
            "errors": formatted_errors
        }
    )


# Root Redirect
@app.get("/", include_in_schema=False)
async def root():
    if show_docs:
        return RedirectResponse(url="/docs")
    return {"message": "To Do List API is running."}


# Import and Include Routers
from src.controllers.auth_controller import auth_router
from src.controllers.todo_controller import todo_router
from src.controllers.category_controller import category_router

app.include_router(auth_router)
app.include_router(todo_router)
app.include_router(category_router)