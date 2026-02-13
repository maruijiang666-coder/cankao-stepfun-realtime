import asyncio
import json
import os
import urllib.parse
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import aiohttp
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_WS_URL = "wss://api.stepfun.com/v1/realtime"
DEFAULT_MODEL = "step-audio-2"
API_KEY = os.getenv("API_KEY", "")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    client_host = websocket.client.host
    print(f"[{client_host}] Client connected to proxy")
    
    # Get parameters from query string
    params = websocket.query_params
    client_api_key = params.get("apiKey")
    client_model = params.get("model", DEFAULT_MODEL)
    custom_ws_url = params.get("wsUrl")
    
    if custom_ws_url:
        custom_ws_url = urllib.parse.unquote(custom_ws_url)
    
    api_key = client_api_key or API_KEY
    if not api_key:
        await websocket.send_json({
            "type": "error",
            "message": "API Key is required"
        })
        await websocket.close()
        return

    # Construct final Stepfun WebSocket URL
    if custom_ws_url:
        final_ws_url = custom_ws_url
        if "model=" not in final_ws_url:
            separator = "&" if "?" in final_ws_url else "?"
            final_ws_url += f"{separator}model={client_model}"
    else:
        final_ws_url = f"{DEFAULT_WS_URL}?model={client_model}"

    print(f"Connecting to Stepfun: {final_ws_url}")

    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {api_key}"}
            async with session.ws_connect(final_ws_url, headers=headers) as stepfun_ws:
                print("Connected to Stepfun")

                stop_event = asyncio.Event()

                async def forward_to_client():
                    try:
                        async for msg in stepfun_ws:
                            if stop_event.is_set():
                                break
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)
                                msg_type = data.get("type", "unknown")
                                if msg_type in ["response.audio.delta", "server.response.audio.delta"]:
                                    delta = data.get("delta") or data.get("audio", "")
                                    print(f"[{client_host}] Stepfun -> Client: {msg_type} (audio size: {len(delta)})")
                                elif msg_type == "error":
                                    print(f"[{client_host}] Stepfun -> Client ERROR: {json.dumps(data, indent=2)}")
                                else:
                                    print(f"[{client_host}] Stepfun -> Client: {msg_type}")
                                    # Log full data for session events or other important events
                                    if msg_type.startswith("session.") or msg_type.startswith("response."):
                                         print(f"[{client_host}] Event details: {json.dumps(data, indent=2)}")
                                await websocket.send_text(msg.data)
                            elif msg.type == aiohttp.WSMsgType.BINARY:
                                print(f"[{client_host}] Stepfun -> Client: BINARY (size: {len(msg.data)})")
                                await websocket.send_bytes(msg.data)
                            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                                print(f"[{client_host}] Stepfun connection closed: {msg.type}")
                                break
                    except Exception as e:
                        if not stop_event.is_set():
                            print(f"[{client_host}] Error forwarding to client: {e}")
                    finally:
                        stop_event.set()

                async def forward_to_stepfun():
                    try:
                        while not stop_event.is_set():
                            try:
                                message = await asyncio.wait_for(websocket.receive(), timeout=1.0)
                                if "text" in message:
                                    text_data = message["text"]
                                    try:
                                        data = json.loads(text_data)
                                        msg_type = data.get("type", "unknown")
                                        if msg_type == "input_audio_buffer.append":
                                            audio = data.get("audio", "")
                                            print(f"[{client_host}] Client -> Stepfun: {msg_type} (audio size: {len(audio)})")
                                        else:
                                            print(f"[{client_host}] Client -> Stepfun: {msg_type}")
                                    except:
                                        print(f"[{client_host}] Client -> Stepfun: Raw Text")
                                    await stepfun_ws.send_str(text_data)
                                elif "bytes" in message:
                                    print(f"[{client_host}] Client -> Stepfun: BINARY (size: {len(message['bytes'])})")
                                    await stepfun_ws.send_bytes(message["bytes"])
                                elif message["type"] == "websocket.disconnect":
                                    print(f"[{client_host}] Client disconnected from proxy")
                                    break
                            except asyncio.TimeoutError:
                                continue
                    except Exception as e:
                        if not stop_event.is_set():
                            print(f"[{client_host}] Error forwarding to Stepfun: {e}")
                    finally:
                        stop_event.set()

                # Use wait to run both and cancel the other when one finishes
                done, pending = await asyncio.wait(
                    [asyncio.create_task(forward_to_client()), asyncio.create_task(forward_to_stepfun())],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                stop_event.set()
                for task in pending:
                    task.cancel()

    except Exception as e:
        print(f"Connection error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Connection error: {str(e)}"
            })
            await websocket.close()
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
