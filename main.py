import json
import logging
import os

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import requests

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from chat.schemas import Query
from database import get_db, engine

from models.Conversation import Conversation as ConvModel
from models.Message import Message as MsgModel
from models.User import User

from models.Base import Base

from authentication.routes import router as auth_router
from chat.routes import router as gen_router
from dependencies import get_current_user

app = FastAPI()
app.include_router(auth_router)
app.include_router(gen_router)





@app.get("/conversation/list")
async def list_conversations(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ConvModel)
        .filter_by(user_id=current_user.id)
    )
    conversations = result.scalars().all()
    return [
        {"id": conv.id, "conversation_name": conv.conversation_name}
        for conv in conversations
    ]

@app.post("/conversation/start")
async def start_conversation(
        conv_id: str,
        conv_name: str = "New Chat",
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    exists = await db.execute(
        select(ConvModel)
        .filter_by(id=conv_id, user_id=current_user.id)
    )
    if exists.scalars().first():
        raise HTTPException(status_code=400, detail="Conversation ID already exists")

    new_conv = ConvModel(
        id=conv_id,
        conversation_name=conv_name,
        user_id=current_user.id
    )
    db.add(new_conv)
    await db.commit()
    await db.refresh(new_conv)
    return {"id": new_conv.id, "conversation_name": new_conv.conversation_name}

@app.post("/conversation/{conv_id}/rename")
async def rename_conversation(
        conv_id: str,
        conv_name: str,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ConvModel).filter_by(id=conv_id, user_id=current_user.id)
    )
    conv = result.scalars().first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conv.conversation_name = conv_name
    await db.commit()
    await db.refresh(conv)
    return {"id": conv.id, "conversation_name": conv.conversation_name}

@app.get("/conversation/{conv_id}")
async def get_conversation(
        conv_id: str,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ConvModel).filter_by(id=conv_id, user_id=current_user.id)
    )
    conv = result.scalars().first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msg_res = await db.execute(select(MsgModel).filter_by(conversation_id=conv_id))
    msgs = msg_res.scalars().all()

    messages = [
        {"role": msg.role, "content": msg.content}
        for msg in msgs
    ]
    return {
        "id": conv.id,
        "conversation_name": conv.conversation_name,
        "messages": messages
    }


@app.post("/conversation/{conv_id}/message")
async def add_message(
        conv_id: str,
        query: Query,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ConvModel).filter_by(id=conv_id, user_id=current_user.id)
    )
    conversation = result.scalars().first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msg_res = await db.execute(select(MsgModel).filter_by(conversation_id=conv_id))
    msgs = msg_res.scalars().all()

    conversation_history = ""
    for message in msgs:
        conversation_history += (f"{message.role} "
                   f": {message.content}\n")

    user_msg = MsgModel(
        role="user",
        content=query.prompt,
        conversation_id=conv_id
    )
    db.add(user_msg)
    await db.flush()

    prompt = f"Conversation history:\n{conversation_history}\nuser: {query.prompt}\nassistant:"


    try:
        logging.info(f"Sending request to external API with prompt: {query.prompt}")
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": query.model, "prompt": prompt, "stream": query.stream},
        )
        response.raise_for_status()
        generated_text = response.json().get("response")
        if not generated_text:
            raise ValueError("Missing 'response' in external API response")

        model_msg = MsgModel(
            role="model",
            content=generated_text,
            conversation_id=conv_id
        )
        db.add(model_msg)
        await db.commit()

        return {"generated_text": generated_text}

    except Exception as e:
        await db.rollback()
        logging.error(f"Error during chat generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def on_startup():
    # Асинхронно создаём схему
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)