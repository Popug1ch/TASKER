"""
Схемы для аутентификации и управления пользователями.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegister(BaseModel):
    """
    Схема для регистрации нового пользователя.

    Атрибуты:
        username (str): уникальное имя пользователя.
        email (EmailStr): электронная почта (проверяется формат).
        password (str): пароль (длина от 6 до 72 символов в UTF-8).
    """

    username: str
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)

    @field_validator("password")
    def validate_password(cls, v: str) -> str:
        """
        Проверяет длину пароля в байтах (ограничение bcrypt).
        """
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Пароль слишком длинный (максимум 72 символа)")
        return v


class UserLogin(BaseModel):
    """
    Схема для входа пользователя.

    Атрибуты:
        email (EmailStr): электронная почта.
        password (str): пароль.
    """

    email: EmailStr
    password: str


class UserOut(BaseModel):
    """
    Схема для ответа с данными пользователя (без пароля).

    Атрибуты:
        id (int): идентификатор пользователя.
        username (str): имя пользователя.
        email (str): электронная почта.
    """

    id: int
    username: str
    email: str


class TokenResponse(BaseModel):
    """
    Схема для ответа после успешного входа.

    Атрибуты:
        token (str): сессионный токен (cookie).
        user (UserOut): данные пользователя.
    """

    token: str
    user: UserOut
