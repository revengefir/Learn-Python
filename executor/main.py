import asyncio
import os
import pty
import subprocess
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import select
import signal

app = FastAPI()

# Разрешаем фронтенд
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions = {}
MAX_EXECUTION_TIME = 10  # секунда таймаут для бесконечных циклов


@app.post("/run")
async def run_code(payload: dict):
    code = payload.get("code", "")
    session_id = str(uuid.uuid4())

    # Сохраняем код в tmp файл
    os.makedirs(f"/tmp/{session_id}", exist_ok=True)
    code_path = f"/tmp/{session_id}/main.py"
    with open(code_path, "w") as f:
        f.write(code)

    # Создаем pty
    master, slave = pty.openpty()
    proc = subprocess.Popen(
        ["python3", "-u", code_path],
        stdin=slave,
        stdout=slave,
        stderr=slave,
        preexec_fn=os.setsid  # чтобы можно было убить процесс и все дочерние
    )

    sessions[session_id] = {
        "proc": proc,
        "pty": master,
        "start_time": asyncio.get_event_loop().time(),
        "waiting_input": False,
    }

    return JSONResponse({"session_id": session_id})


@app.websocket("/ws/run/{session_id}/")
async def ws_run(ws: WebSocket, session_id: str):
    await ws.accept()

    if session_id not in sessions:
        await ws.close()
        return

    session = sessions[session_id]
    proc = session["proc"]
    master_fd = session["pty"]
    start_time = session["start_time"]

    try:
        while True:
            # Таймаут на бесконечные циклы
            if asyncio.get_event_loop().time() - start_time > MAX_EXECUTION_TIME:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                await ws.send_json({"type": "output", "data": "\n[ERROR] Execution timeout"})
                break

            # Проверка вывода
            rlist, _, _ = select.select([master_fd], [], [], 0.05)
            if rlist:
                try:
                    output = os.read(master_fd, 1024).decode()
                    if output:
                        await ws.send_json({"type": "output", "data": output})
                        # Если Python ждёт input, помечаем
                        if output.strip().endswith(":"):
                            session["waiting_input"] = True
                except OSError:
                    pass

            # Получаем ввод пользователя
            if session["waiting_input"]:
                try:
                    msg = await asyncio.wait_for(ws.receive_text(), timeout=0.05)
                    os.write(master_fd, (msg + "\n").encode())
                    session["waiting_input"] = False
                except asyncio.TimeoutError:
                    pass
                except WebSocketDisconnect:
                    break

            # Проверка завершения процесса
            if proc.poll() is not None:
                break

    except WebSocketDisconnect:
        pass
    finally:
        if proc.poll() is None:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        await ws.send_json({"type": "exit", "data": proc.returncode})
        await ws.close()
        del sessions[session_id]



