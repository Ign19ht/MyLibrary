import datetime
import os
import random
from typing import List

import uvicorn
from fastapi import FastAPI, Request, Form, Cookie, status, File, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

import models
import schemas
from db_manager import create_db, get_db
import crud
import string
import hashlib

create_db()


def get_hash(data) -> str:
    return hashlib.sha256(data).hexdigest()


def write_image(file: UploadFile) -> str:
    image_extension = file.filename.split(".")[-1]
    data = file.file.read()
    hash = get_hash(data)
    image_name = f"{hash}.{image_extension}"
    if not os.path.exists("Images"):
        os.makedirs("Images")
    with open(f"Images/{image_name}", "wb") as f:
        f.write(data)
    return image_name


def remove_image(image_name: str):
    if os.path.exists(f"Images/{image_name}"):
        os.remove(f"Images/{image_name}")


def cookie_gen():
    symbols = string.ascii_letters + string.digits
    return ''.join(random.choice(symbols) for _ in range(128))


def check_cookie(db: Session, session_cookie: str) -> bool:
    cookie = crud.get_cookie(db, session_cookie)
    if cookie is None:
        return False
    print(cookie.date)
    return True


def get_words_data(words: List[models.Words]):
    data = []
    for word in words:
        des = word.description.split(".")[0]
        data.append([word.word, des, word.id])
    return data


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/item/static", StaticFiles(directory="static"), name="static")
app.mount("/edit_item/static", StaticFiles(directory="static"), name="static")
app.mount("/remove/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates/library")


@app.get("/", response_class=HTMLResponse)
async def library(request: Request, session: str = Cookie("")):
    db = get_db()
    words = crud.get_words(db, 1)
    is_admin = check_cookie(db, session)
    db.close()
    response = templates.TemplateResponse("library.html", {"request": request, "data": get_words_data(words), "is_admin": is_admin})
    return response


@app.get("/proposed_words", response_class=HTMLResponse)
async def proposed_words(request: Request, session: str = Cookie("")):
    db = get_db()
    words = crud.get_words(db, 0)
    is_admin = check_cookie(db, session)
    db.close()
    if is_admin:
        response = templates.TemplateResponse("library.html", {"request": request, "data": get_words_data(words), "is_admin": is_admin})
    else:
        response = templates.TemplateResponse("error.html", {"request": request, "is_admin": is_admin,
                                                             "message": "У вас нет доступа"}, status_code=401)
    return response


@app.get("/filter", response_class=HTMLResponse)
async def use_filter(request: Request, filter: str, session: str = Cookie("")):
    db = get_db()
    words = crud.get_words_filter(db, 1, filter)
    is_admin = check_cookie(db, session)
    db.close()
    response = templates.TemplateResponse("library.html", {"request": request, "data": get_words_data(words), "is_admin": is_admin})
    return response


@app.get("/remove/{word_id}", response_class=HTMLResponse)
async def remove_form(request: Request, word_id: int, session: str = Cookie("")):
    db = get_db()
    word = crud.get_word(db, word_id)
    is_admin = check_cookie(db, session)
    db.close()
    if is_admin:
        if word:
            response = templates.TemplateResponse("confirm.html",
                                                  {"request": request, "word": word, "is_admin": is_admin})
        else:
            response = templates.TemplateResponse("error.html", {"request": request, "is_admin": is_admin,
                                                                 "message": "Слово не найдено"}, status_code=404)
    else:
        response = templates.TemplateResponse("error.html", {"request": request, "is_admin": is_admin,
                                                             "message": "У вас нет доступа"}, status_code=401)
    return response


@app.get("/remove_word/{word_id}", response_class=Response)
async def remove_word(request: Request, word_id: int, session: str = Cookie("")):
    db = get_db()
    is_admin = check_cookie(db, session)
    if is_admin:
        word = crud.get_word(db, word_id)
        remove_image(word.image_name)
        if word:
            crud.remove_word(db, word_id)
        response = RedirectResponse(f'/', status_code=status.HTTP_303_SEE_OTHER)
    else:
        response = templates.TemplateResponse("error.html", {"request": request, "is_admin": is_admin,
                                                             "message": "У вас нет доступа"}, status_code=401)
    db.close()
    return response


@app.post("/approve_word", response_class=Response)
async def approve_word(data: schemas.ApproveRequest, session: str = Cookie("")):
    db = get_db()
    is_admin = check_cookie(db, session)
    if not is_admin:
        db.close()
        return Response(status_code=401)
    if crud.get_word(db, data.word_id):
        if data.approve == 0:
            word = crud.get_word(db, data.word_id)
            remove_image(word)
            crud.remove_word(db, word.id)
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
        if word:
            response = templates.TemplateResponse("edit_word.html", {"request": request, "word": word,
                                                                     "is_admin": is_admin})
        else:
            response = templates.TemplateResponse("error.html", {"request": request, "is_admin": is_admin,
                                                                 "message": "Слово не найдено"}, status_code=404)
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
            word_db = crud.get_word(db, item_id)
            remove_image(word_db.image_name)
            image_name = write_image(file)
            crud.update_word(db, item_id, word, description, image_name)
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
    if word:
        response = templates.TemplateResponse("item.html", {"request": request, "word": word, "is_admin": is_admin,
                                                            "is_propose": word.approve == 0})
    else:
        response = templates.TemplateResponse("error.html", {"request": request, "is_admin": is_admin,
                                                             "message": "Слово не найдено"}, status_code=404)
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

    db = get_db()
    is_admin = check_cookie(db, session)
    image_name = write_image(file)
    crud.add_word(db, word, description, image_name, 1 if is_admin else 0)
    db.close()

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
    uvicorn.run(app, host="0.0.0.0", port=8000)
    # uvicorn.run(app, host="127.0.0.1", port=8000)
