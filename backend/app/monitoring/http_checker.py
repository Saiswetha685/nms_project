import time
import httpx
from typing import Dict, Any

async def check_http(url: str, timeout_seconds: float = 5.0) -> Dict[str, Any]:
    """
    Asynchronously checks an HTTP/HTTPS endpoint.
    Measures latency in milliseconds, tracks HTTP status code.
    """
    start_time = time.perf_counter()
    headers = {"User-Agent": "SLA-Predict-NMS-Probe/1.0"}
    
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True, verify=False) as client:
            response = await client.get(url, headers=headers)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            
            is_success = (200 <= response.status_code < 400)
            error_msg = None if is_success else f"HTTP Status {response.status_code}"
            
            return {
                "success": is_success,
                "response_time_ms": round(elapsed_ms, 2),
                "packet_loss_percent": 0.0 if is_success else 100.0 if response.status_code >= 500 else 0.0,
                "error": error_msg,
                "details": {
                    "status_code": response.status_code,
                    "url": str(response.url)
                }
            }
    except httpx.TimeoutException:
        return {
            "success": False,
            "response_time_ms": round(timeout_seconds * 1000.0, 2),
            "packet_loss_percent": 100.0,
            "error": "Request timed out",
            "details": {"timeout": timeout_seconds}
        }
    except httpx.ConnectError as ce:
        return {
            "success": False,
            "response_time_ms": 0.0,
            "packet_loss_percent": 100.0,
            "error": f"Connection refused/error: {str(ce)[:80]}",
            "details": {}
        }
    except Exception as e:
        return {
            "success": False,
            "response_time_ms": 0.0,
            "packet_loss_percent": 100.0,
            "error": f"HTTP Probe error: {str(e)[:80]}",
            "details": {}
        }
