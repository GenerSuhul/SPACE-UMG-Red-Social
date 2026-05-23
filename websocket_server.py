import asyncio
import json
import logging
from datetime import datetime, timezone
import websockets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("websocket_server")

# Group active websocket connections by stream_id
# stream_id -> set of WebSocketServerProtocol
STREAMS = {}

async def handle_connection(websocket, path=None):
    logger.info("New connection established")
    current_stream_id = None
    current_username = None
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON message")
                continue
                
            msg_type = data.get("type")
            
            if msg_type == "join":
                current_stream_id = data.get("streamId")
                current_username = data.get("username")
                
                if not current_stream_id or not current_username:
                    continue
                    
                if current_stream_id not in STREAMS:
                    STREAMS[current_stream_id] = set()
                    
                STREAMS[current_stream_id].add(websocket)
                logger.info(f"User @{current_username} joined room {current_stream_id}")
                
            elif msg_type == "comment":
                content = data.get("content")
                if not current_stream_id or not current_username or not content:
                    continue
                    
                # Format response payload
                payload_str = json.dumps({
                    "username": current_username,
                    "content": content,
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
                
                # Send to all users connected to this stream_id room
                room_sockets = STREAMS.get(current_stream_id, set())
                if room_sockets:
                    await asyncio.gather(
                        *[ws.send(payload_str) for ws in room_sockets],
                        return_exceptions=True
                    )
                    logger.info(f"Broadcast comment from @{current_username} in room {current_stream_id}")
                    
    except websockets.exceptions.ConnectionClosed:
        logger.info("Connection closed")
    finally:
        # Cleanup connection on disconnect
        if current_stream_id and current_stream_id in STREAMS:
            STREAMS[current_stream_id].discard(websocket)
            if not STREAMS[current_stream_id]:
                del STREAMS[current_stream_id]
            logger.info(f"Cleaned up connection for @{current_username} from room {current_stream_id}")

async def main():
    # Bind to 0.0.0.0 so it is accessible inside docker networks and from outside
    host = "0.0.0.0"
    async with websockets.serve(handle_connection, host, 8888):
        logger.info(f"WebSocket Server started on ws://{host}:8888")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("WebSocket Server stopped.")
