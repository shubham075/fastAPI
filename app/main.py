from pathlib import Path
from typing import Mapping

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app import auth, crud, models, otp_service, schemas
from app.datbase import engine, get_db

# Create tables in the database if they don't exist
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="FastAPI SQL Server App")
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def get_current_user(request: Request, db: Session):
    user_id = auth.read_session_token(request.cookies.get(auth.COOKIE_NAME))
    if not user_id:
        return None
    return crud.get_user(db, user_id=user_id)


def render_template(
    request: Request,
    template_name: str,
    context: dict | None = None,
    status_code: int = status.HTTP_200_OK,
):
    template_context = {"request": request}
    if context:
        template_context.update(context)
    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context=template_context,
        status_code=status_code,
    )


def form_value(values: Mapping[str, object], field_name: str) -> str:
    value = values.get(field_name, "")
    return str(value).strip()


@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email_id)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    mobile_user = crud.get_user_by_mobile(db, mobile=user.mobile)
    if mobile_user:
        raise HTTPException(status_code=400, detail="Mobile already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=list[schemas.UserResponse])
def read_users(db: Session = Depends(get_db)):
    users = crud.get_users(db)
    return users


@app.put("/users/{user_id}", response_model=schemas.UserResponse)
def update_user(user_id: int, user: schemas.UserUpdate, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    email_owner = crud.get_user_by_email(db, email=user.email_id)
    if email_owner and email_owner.id != user_id:
        raise HTTPException(status_code=400, detail="Email already registered")
    mobile_owner = crud.get_user_by_mobile(db, mobile=user.mobile)
    if mobile_owner and mobile_owner.id != user_id:
        raise HTTPException(status_code=400, detail="Mobile already registered")

    return crud.update_user(db=db, db_user=db_user, user=user)


@app.patch("/users/{user_id}", response_model=schemas.UserResponse)
def patch_user(user_id: int, user: schemas.UserPatch, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.email_id:
        email_owner = crud.get_user_by_email(db, email=user.email_id)
        if email_owner and email_owner.id != user_id:
            raise HTTPException(status_code=400, detail="Email already registered")
    if user.mobile:
        mobile_owner = crud.get_user_by_mobile(db, mobile=user.mobile)
        if mobile_owner and mobile_owner.id != user_id:
            raise HTTPException(status_code=400, detail="Mobile already registered")

    return crud.patch_user(db=db, db_user=db_user, user=user)


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if current_user:
        return RedirectResponse(url="/account", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return render_template(request, "register.html", {"values": {}})


@app.post("/register", response_class=HTMLResponse)
async def register_user(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    values = dict(form)
    password = form_value(values, "password")
    confirm_password = form_value(values, "confirm_password")

    if password != confirm_password:
        return render_template(
            request,
            "register.html",
            {"error": "Password and confirm password do not match.", "values": values},
            status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = schemas.UserCreate.model_validate(
            {
                "first_name": form_value(values, "first_name"),
                "last_name": form_value(values, "last_name"),
                "email_id": form_value(values, "email_id"),
                "mobile": form_value(values, "mobile"),
                "date_of_birth": form_value(values, "date_of_birth"),
                "gender": form_value(values, "gender"),
                "password": password,
            }
        )
    except ValidationError as exc:
        return render_template(
            request,
            "register.html",
            {"error": exc.errors()[0]["msg"], "values": values},
            status.HTTP_400_BAD_REQUEST,
        )

    if crud.get_user_by_email(db, email=user.email_id):
        return render_template(
            request,
            "register.html",
            {"error": "Email already registered.", "values": values},
            status.HTTP_400_BAD_REQUEST,
        )

    if crud.get_user_by_mobile(db, mobile=user.mobile):
        return render_template(
            request,
            "register.html",
            {"error": "Mobile already registered.", "values": values},
            status.HTTP_400_BAD_REQUEST,
        )

    otp = otp_service.create_otp()
    sent, message = otp_service.send_mobile_otp(user.mobile, otp)
    if not sent:
        return render_template(
            request,
            "register.html",
            {"error": message, "values": values},
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    otp_service.save_pending_registration(user.mobile, user.model_dump(), otp)
    return render_template(
        request,
        "verify_otp.html",
        {"mobile": user.mobile, "message": "OTP sent to your mobile number."},
    )


@app.post("/verify-registration", response_class=HTMLResponse)
async def verify_registration(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    values = dict(form)
    mobile = form_value(values, "mobile")
    otp = form_value(values, "otp")
    user_data = otp_service.verify_pending_registration(mobile, otp)

    if not user_data:
        return render_template(
            request,
            "verify_otp.html",
            {"mobile": mobile, "error": "Invalid or expired OTP."},
            status.HTTP_400_BAD_REQUEST,
        )

    user = schemas.UserCreate(**user_data)
    db_user = crud.create_user(db=db, user=user)
    response = RedirectResponse(url="/account", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        auth.COOKIE_NAME,
        auth.create_session_token(db_user.id),
        httponly=True,
        samesite="lax",
    )
    return response


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return render_template(request, "login.html")


@app.post("/login", response_class=HTMLResponse)
async def login_user(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    values = dict(form)
    email_id = form_value(values, "email_id")
    password = form_value(values, "password")
    db_user = crud.get_user_by_email(db, email=email_id)

    if not db_user or not auth.verify_password(password, db_user.password_hash):
        return render_template(
            request,
            "login.html",
            {"error": "Invalid email or password.", "email_id": email_id},
            status.HTTP_400_BAD_REQUEST,
        )

    if not db_user.is_active:
        return render_template(
            request,
            "login.html",
            {"error": "Your account is inactive.", "email_id": email_id},
            status.HTTP_403_FORBIDDEN,
        )

    response = RedirectResponse(url="/account", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        auth.COOKIE_NAME,
        auth.create_session_token(db_user.id),
        httponly=True,
        samesite="lax",
    )
    return response


@app.get("/account", response_class=HTMLResponse)
def account_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return render_template(request, "account.html", {"user": current_user})


@app.post("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(auth.COOKIE_NAME)
    return response
