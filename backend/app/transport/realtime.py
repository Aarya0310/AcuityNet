import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from backend.app.auth.policy import require_nurse_assignment, require_patient_access
from backend.app.auth.service import load_token_user
from backend.app.contracts.realtime import RealtimeInvalidation


def realtime_router(sessions, publisher):
    router = APIRouter()

    @router.websocket("/api/v1/patients/{patient_id}/realtime")
    async def realtime(websocket: WebSocket, patient_id: str):
        token = websocket.query_params.get("access_token")
        if not token:
            await websocket.close(code=1008)
            return
        try:
            with sessions() as session:
                user = load_token_user(session, token)
                require_patient_access(user, patient_id)
                require_nurse_assignment(user, patient_id)
        except Exception:
            await websocket.close(code=1008)
            return

        await websocket.accept()
        queue = asyncio.Queue()
        loop = asyncio.get_running_loop()
        publisher.subscribe(patient_id, loop, queue)
        try:
            while True:
                receive_task = asyncio.create_task(websocket.receive_text())
                notification_task = asyncio.create_task(queue.get())
                done, pending = await asyncio.wait(
                    {receive_task, notification_task},
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()
                completed = done.pop()
                if completed is receive_task:
                    try:
                        payload = json.loads(completed.result())
                        RealtimeInvalidation.model_validate(payload)
                    except (json.JSONDecodeError, ValidationError, TypeError):
                        await websocket.close(code=1003)
                        return
                    await websocket.close(code=1003)
                    return
                message = RealtimeInvalidation.model_validate(completed.result())
                await websocket.send_json(message.model_dump())
        except WebSocketDisconnect:
            return
        finally:
            publisher.unsubscribe(patient_id, loop, queue)

    return router