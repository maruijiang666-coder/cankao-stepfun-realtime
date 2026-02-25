import asyncio
import json
import os
import urllib.parse
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import aiohttp
from dotenv import load_dotenv
from tools import TOOLS, HANDLERS, WANDA_SYSTEM_PROMPT_SEGMENT

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
                
                # Initialize Session with Tools
                # We send this immediately to ensure tools are available
                # If the client sends session.update later, we will intercept it to preserve the system prompt
                initial_session_update = {
                    "type": "session.update",
                    "session": {
                        "tools": TOOLS,
                        "instructions": f"你是一个智能助手。{WANDA_SYSTEM_PROMPT_SEGMENT}"
                    }
                }
                print(f"[{client_host}] Sending Initial Instructions with Wanda Prompt")
                await stepfun_ws.send_json(initial_session_update)
                print(f"[{client_host}] Initialized session with tools")

                stop_event = asyncio.Event()

                async def forward_to_client():
                    try:
                        async for msg in stepfun_ws:
                            if stop_event.is_set():
                                break
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)
                                msg_type = data.get("type", "unknown")
                                
                                # Handle Tool Calls from Stepfun
                                if msg_type == "response.function_call_arguments.done":
                                    print(f"[{client_host}] 🛠️ Tool Call Requested: {data}")
                                    call_id = data.get("call_id")
                                    name = data.get("name")
                                    args_str = data.get("arguments")
                                    
                                    if name in HANDLERS:
                                        # Run tool asynchronously
                                        asyncio.create_task(handle_tool_call(stepfun_ws, call_id, name, args_str, client_host))
                                
                                if msg_type in ["response.audio.delta", "server.response.audio.delta"]:
                                    delta = data.get("delta") or data.get("audio", "")
                                    print(f"[{client_host}] Stepfun -> Client: {msg_type} (audio size: {len(delta)})")
                                elif msg_type == "error":
                                    print(f"[{client_host}] Stepfun -> Client ERROR: {json.dumps(data, indent=2)}")
                                else:
                                    print(f"[{client_host}] Stepfun -> Client: {msg_type}")
                                    # Log full data for session events or other important events
                                    if msg_type.startswith("session.") or msg_type.startswith("response."):
                                         print(f"[{client_host}] Event details: {json.dumps(data, indent=2, ensure_ascii=False)}")
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

                async def handle_tool_call(ws, call_id, name, args_str, host):
                    try:
                        args = json.loads(args_str)
                        result = await HANDLERS[name](args)
                        
                        # Send Tool Output
                        tool_output_event = {
                            "type": "conversation.item.create",
                            "item": {
                                "type": "function_call_output",
                                "call_id": call_id,
                                "output": result
                            }
                        }
                        await ws.send_json(tool_output_event)
                        print(f"[{host}] Sent tool output for {name}")
                        
                        # Trigger Response
                        await ws.send_json({"type": "response.create"})
                        
                    except Exception as e:
                        print(f"[{host}] Tool execution error: {e}")
                        # Optionally send error back

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
                                        
                                        # Intercept session.update to inject Wanda prompt and tools
                                        if msg_type == "session.update":
                                            session_data = data.get("session", {})
                                            
                                            # 1. Inject Tools (Always ensure tools are present)
                                            session_data["tools"] = TOOLS
                                            
                                            # 2. Inject Instructions
                                            if "instructions" in session_data:
                                                original_instructions = session_data["instructions"]
                                                # Check if prompt already exists to avoid duplication
                                                # Using "万达" as keyword since it's in the prompt text
                                                if "万达" not in original_instructions:
                                                    session_data["instructions"] = f"{original_instructions}\n\n{WANDA_SYSTEM_PROMPT_SEGMENT}"
                                                    print(f"[{client_host}] Injected Wanda prompt into client instructions")
                                                else:
                                                    print(f"[{client_host}] Wanda prompt already present in client instructions")
                                            
                                            data["session"] = session_data
                                            text_data = json.dumps(data, ensure_ascii=False)


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
