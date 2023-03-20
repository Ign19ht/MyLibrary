from sqlalchemy.orm import Session
import models
from datetime import datetime


def add_word(db: Session, word: str, description: str, image_name: str, approve: int) -> int:
    db_word = models.Words(word=word, description=description, image_name=image_name, approve=approve)
    db.add(db_word)
    db.commit()
    db.refresh(db_word)
    return db_word.id


def update_word(db: Session, word_id: int, word: str, description: str, image_name: str = None):
    if image_name is None:
        db.query(models.Words).filter(models.Words.id == word_id).update({"word": word, "description": description})
    else:
        db.query(models.Words).filter(models.Words.id == word_id).update({"word": word, "description": description,
                                                                          "image_name": image_name})
    db.commit()


def update_word_status(db: Session, word_id: int, new_status: int):
    db.query(models.Words).filter(models.Words.id == word_id).update({"approve": new_status})
    db.commit()


def remove_word(db: Session, word_id: int):
    db.query(models.Words).filter(models.Words.id == word_id).delete()
    db.commit()


def get_word(db: Session, id_item: int) -> models.Words:
    return db.query(models.Words).filter(models.Words.id == id_item).first()


def get_words(db: Session, approve: int, offset: int, page_size: int, filter: str = None) -> ([models.Words], int):
    query = db.query(models.Words).filter(models.Words.approve == approve)
    if filter:
        query = query.filter(models.Words.word.ilike(f"%{filter}%"))
    total_size = len(query.all())
    return query.order_by(models.Words.word).limit(page_size).offset(offset * page_size).all(), total_size


def login(db: Session, username: str, password: str) -> bool:
    user = db.query(models.Admins).filter(models.Admins.password == password)\
                                  .filter(models.Admins.username == username)\
                                  .first()
    return user is not None


def add_cookie(db: Session, cookie: str, date: datetime):
    db_cookie = models.Cookies(cookie=cookie, date=date)
    db.add(db_cookie)
    db.commit()


def get_cookie(db: Session, cookie: str) -> models.Cookies:
    return db.query(models.Cookies).filter(models.Cookies.cookie == cookie).first()


def remove_cookie(db: Session, cookie: str):
    db.query(models.Cookies).filter(models.Cookies.cookie == cookie).delete()
    db.commit()
