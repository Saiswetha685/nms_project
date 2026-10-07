import asyncio
import time
from typing import Dict, Any

async def check_tcp(target: str, port: int, timeout_seconds: float = 4.0) -> Dict[str, Any]:
    """
    Checks TCP connectivity to target:port by attempting a 3-way handshake.
    Measures TCP handshake latency in ms.
    """
    start_time = time.perf_counter()
    try:
        conn = asyncio.open_connection(host=target, port=port)
        reader, writer = await asyncio.wait_for(conn, timeout=timeout_seconds)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        
        # Close connection gracefully
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
            
        return {
            "success": True,
            "response_time_ms": round(elapsed_ms, 2),
            "packet_loss_percent": 0.0,
            "error": None,
            "details": {"port": port, "target": target}
        }
    except asyncio.TimeoutError:
        return {
            "success": False,
            "response_time_ms": round(timeout_seconds * 1000.0, 2),
            "packet_loss_percent": 100.0,
            "error": f"TCP connection timed out after {timeout_seconds}s",
            "details": {"port": port, "target": target}
        }
    except ConnectionRefusedError:
        return {
            "success": False,
            "response_time_ms": 0.0,
            "packet_loss_percent": 100.0,
            "error": f"TCP connection refused on port {port}",
            "details": {"port": port, "target": target}
        }
    except Exception as e:
        return {
            "success": False,
            "response_time_ms": 0.0,
            "packet_loss_percent": 100.0,
            "error": f"TCP connection failed: {str(e)[:80]}",
            "details": {"port": port, "target": target}
        }
