import datetime
import random
from copy import copy
from typing import Union

import uvicorn
from fastapi import FastAPI, Request, Form, Cookie, status, File, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import schemas
from enum import Enum
import sys
from db_manager import create_db, get_db
import crud
import string


class DataBaseType(Enum):
    POSTGRES = 1
    MARIA = 2


create_db()


def cookie_gen():
    symbols = string.ascii_letters + string.digits
    return ''.join(random.choice(symbols) for _ in range(128))


def check_cookie(db: Session, session_cookie: str) -> bool:
    cookie = crud.get_cookie(db, session_cookie)
    if cookie is None:
        return False
    print(cookie.date)
    return True


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/item/static", StaticFiles(directory="static"), name="static")
app.mount("/edit_item/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates/library")


# @app.get("/filter", response_class=HTMLResponse)
# async def use_filter(request: Request, category: str, session: str = Cookie("")):
#     check_cookie(session)
#     query = f"SELECT title, body, image_name FROM news WHERE category='{category}' AND hidden=0"
#     rows = None
#     if db_type == DataBaseType.MARIA:
#         rows = db_request_maria(query)
#     else:
#         rows = db_request_postgres(query)
#     response = templates.TemplateResponse("index.html",
#                                           {"request": request, "news_rows": get_news(rows), "category": category})
#     if not session:
#         response.set_cookie("session", get_new_cookie())
#     return response


@app.get("/", response_class=HTMLResponse)
async def library(request: Request, session: str = Cookie("")):
    db = get_db()
    words = crud.get_words(db, 1)
    is_admin = check_cookie(db, session)
    db.close()
    response = templates.TemplateResponse("library.html", {"request": request, "data": words, "is_admin": is_admin})
    return response


@app.get("/proposed_words", response_class=HTMLResponse)
async def proposed_words(request: Request, session: str = Cookie("")):
    db = get_db()
    words = crud.get_words(db, 0)
    is_admin = check_cookie(db, session)
    db.close()
    if is_admin:
        response = templates.TemplateResponse("library.html", {"request": request, "data": words, "is_admin": is_admin})
    else:
        response = templates.TemplateResponse("error.html", {"request": request, "is_admin": is_admin,
                                                             "message": "У вас нет доступа"}, status_code=401)
    return response


@app.post("/approve_word", response_class=Response)
async def create_new_word(data: schemas.ApproveRequest, session: str = Cookie("")):
    db = get_db()
    is_admin = check_cookie(db, session)
    if not is_admin:
        db.close()
        return Response(status_code=401)

    if data.approve == 0:
        crud.update_word_status(db, data.word_id, -1)
    elif data.approve == 1:
        crud.update_word_status(db, data.word_id, 1)
    db.close()
    return Response(status_code=200)


@app.get("/edit_item/{item_id}", response_class=HTMLResponse)
async def edit_word(request: Request, item_id: int, session: str = Cookie("")):
    db = get_db()
    word = crud.get_word(db, item_id)
    is_admin = check_cookie(db, session)
    db.close()
    if is_admin:
        response = templates.TemplateResponse("edit_word.html", {"request": request, "word": word,
                                                                 "is_admin": is_admin})
    else:
        response = templates.TemplateResponse("error.html", {"request": request, "is_admin": is_admin,
                                                             "message": "У вас нет доступа"}, status_code=401)
    return response


@app.post("/update_word/{item_id}", response_class=RedirectResponse)
async def update_word(request: Request, item_id: int, word: str = Form(), description: str = Form(),
                          file: UploadFile = File(), session: str = Cookie("")):
    db = get_db()
    is_admin = check_cookie(db, session)

    if is_admin:
        if file and file.filename:
            image_extension = file.filename.split(".")[-1]
            with open(f"Images/{item_id}.{image_extension}", "wb") as f:
                f.write(file.file.read())
            crud.update_word(db, item_id, word, description, image_extension)
        else:
            crud.update_word(db, item_id, word, description)

    db.close()

    return RedirectResponse(f'/item/{item_id}', status_code=status.HTTP_303_SEE_OTHER)


@app.get("/item/{item_id}", response_class=HTMLResponse)
async def show_item(request: Request, item_id: int, session: str = Cookie("")):
    db = get_db()
    is_admin = check_cookie(db, session)
    word = crud.get_word(db, item_id)
    db.close()
    response = templates.TemplateResponse("item.html", {"request": request, "word": word, "is_admin": is_admin,
                                                        "is_propose": True if word.approve == 0 else False})
    return response


@app.get("/new_word", response_class=HTMLResponse)
async def field_new_word(request: Request, session: str = Cookie("")):
    db = get_db()
    is_admin = check_cookie(db, session)
    db.close()
    response = templates.TemplateResponse("new_word.html", {"request": request, "is_admin": is_admin})
    return response


@app.post("/new_word", response_class=RedirectResponse)
async def create_new_word(request: Request, word: str = Form(), description: str = Form(),
                          file: UploadFile = File(...), session: str = Cookie("")):
    image_extension = file.filename.split(".")[-1]

    db = get_db()
    is_admin = check_cookie(db, session)
    word_id = crud.add_word(db, word, description, image_extension, 1 if is_admin else 0)
    db.close()

    with open(f"Images/{word_id}.{image_extension}", "wb") as f:
        f.write(file.file.read())

    redirect_url = request.url_for('field_new_word')
    return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@app.get("/image/{image_name}")
async def get_image(image_name: str):
    return FileResponse(f'Images/{image_name}')


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request, session: str = Cookie("")):
    db = get_db()
    is_admin = check_cookie(db, session)
    db.close()
    if is_admin:
        response = templates.TemplateResponse("error.html", {"request": request, "is_admin": is_admin,
                                                             "message": "Вы уже авторизованы"})
    else:
        response = templates.TemplateResponse("auth.html", {"request": request, "is_admin": is_admin})
    return response


@app.post("/login")
async def login(request: Request, username: str = Form(), password: str = Form(), session: str = Cookie("")):
    db = get_db()
    is_admin = check_cookie(db, session)

    if is_admin:
        response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    else:
        is_auth = crud.login(db, username, password)
        if is_auth:
            response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
            session_cookie = cookie_gen()
            date = datetime.datetime.now()
            crud.add_cookie(db, session_cookie, date)
            response.set_cookie(key="session", value=session_cookie)
        else:
            response = RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    db.close()
    return response


@app.get("/logout")
async def logout(request: Request, session: str = Cookie("")):
    db = get_db()
    is_admin = check_cookie(db, session)
    if is_admin:
        crud.remove_cookie(db, session)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
