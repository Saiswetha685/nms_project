import time
import dns.asyncresolver
from typing import Dict, Any

async def check_dns(target: str, timeout_seconds: float = 4.0, record_type: str = "A") -> Dict[str, Any]:
    """
    Asynchronously queries DNS server for target hostname.
    Measures query lookup time in milliseconds and collects answer records.
    """
    start_time = time.perf_counter()
    resolver = dns.asyncresolver.Resolver()
    resolver.timeout = timeout_seconds
    resolver.lifetime = timeout_seconds

    try:
        answers = await resolver.resolve(target, record_type)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        records = [str(rdata) for rdata in answers]
        
        return {
            "success": True,
            "response_time_ms": round(elapsed_ms, 2),
            "packet_loss_percent": 0.0,
            "error": None,
            "details": {
                "records": records[:5],
                "record_type": record_type,
                "nameserver": resolver.nameservers[0] if resolver.nameservers else "default"
            }
        }
    except dns.resolver.NXDOMAIN:
        return {
            "success": False,
            "response_time_ms": 0.0,
            "packet_loss_percent": 100.0,
            "error": f"DNS Non-Existent Domain (NXDOMAIN): {target}",
            "details": {}
        }
    except dns.exception.Timeout:
        return {
            "success": False,
            "response_time_ms": round(timeout_seconds * 1000.0, 2),
            "packet_loss_percent": 100.0,
            "error": f"DNS query timed out after {timeout_seconds}s",
            "details": {}
        }
    except Exception as e:
        return {
            "success": False,
            "response_time_ms": 0.0,
            "packet_loss_percent": 100.0,
            "error": f"DNS resolution error: {str(e)[:80]}",
            "details": {}
        }
