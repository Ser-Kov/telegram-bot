from fastapi import FastAPI, Request
from aiogram.types import FSInputFile
import hashlib
from bot_aiogram_v3 import bot, PRODUCTS, ROBO_PASSWORD2

app = FastAPI()

@app.get("/")
def root():
    return {"status": "alive"}

@app.post("/payment_callback")
async def robokassa_payment_handler(request: Request):
    form = await request.form()
    OutSum = form.get("OutSum")
    InvId = form.get("InvId")
    SignatureValue = form.get("SignatureValue")
    IS_TEST = form.get("IsTest", "0") == "1"

    if IS_TEST:
        base = f"{OutSum}:{InvId}:R8C0KfOaLgJs9e0PD5bp"  # тестовый пароль #1
    else:
        base = f"{OutSum}:{InvId}:{ROBO_PASSWORD2}"

    expected_signature = hashlib.md5(base.encode()).hexdigest().upper()
    if SignatureValue.upper() != expected_signature:
        return "bad sign"

    try:
        tg_user_id, product_code = InvId.split("_")
        pdf_path = PRODUCTS.get(product_code)
        if not pdf_path:
            return "product not found"

        file = FSInputFile(pdf_path)
        await bot.send_document(chat_id=int(tg_user_id), document=file,
                                 caption="✅ Спасибо за оплату! Вот ваш PDF.")
        return "OK"
    except Exception as e:
        return f"error: {e}"

