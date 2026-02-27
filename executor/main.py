import asyncio
import os
import pty
import subprocess
import uuid
import select
import signal

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions = {}
MAX_EXECUTION_TIME = 60


@app.post("/run")
async def run_code(payload: dict):
    code = payload.get("code", "")
    session_id = str(uuid.uuid4())

    workdir = f"/tmp/{session_id}"
    os.makedirs(workdir, exist_ok=True)

    code_path = f"{workdir}/main.py"

    with open(code_path, "w") as f:
        f.write(code)

    master_fd, slave_fd = pty.openpty()

    proc = subprocess.Popen(
        ["python3", "-u", code_path],
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        cwd=workdir,
        preexec_fn=os.setsid
    )

    os.close(slave_fd)

    sessions[session_id] = {
        "proc": proc,
        "pty": master_fd,
        "start_time": asyncio.get_event_loop().time(),
        "workdir": workdir,
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
            if asyncio.get_event_loop().time() - start_time > MAX_EXECUTION_TIME:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)

                await ws.send_json({
                    "type": "output",
                    "data": "\n[ERROR] Лимит времени на исполнение программы превышен\n"
                })
                break

            rlist, _, _ = select.select([master_fd], [], [], 0)

            if rlist:
                try:
                    output = os.read(master_fd, 65536).decode(
                        errors="ignore"
                    )

                    if output:
                        await ws.send_json({
                            "type": "output",
                            "data": output
                        })

                except OSError:
                    pass

            try:
                msg = await asyncio.wait_for(
                    ws.receive_text(),
                    timeout=0.01
                )

                os.write(master_fd, (msg + "\n").encode())

            except asyncio.TimeoutError:
                pass
            except WebSocketDisconnect:
                break

            # =====================
            # PROCESS EXIT
            # =====================
            if proc.poll() is not None:
                break

            await asyncio.sleep(0.01)

    except WebSocketDisconnect:
        pass

    finally:
        try:
            if proc.poll() is None:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            pass

        await ws.send_json({
            "type": "exit",
            "data": proc.returncode
        })

        await ws.close()

        try:
            os.close(master_fd)
        except Exception:
            pass

        try:
            import shutil
            shutil.rmtree(session["workdir"], ignore_errors=True)
        except Exception:
            pass

        sessions.pop(session_id, None)
