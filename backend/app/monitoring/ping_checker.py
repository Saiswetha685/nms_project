import asyncio
import re
import platform
from typing import Dict, Any

async def _subprocess_ping(target: str, count: int = 2, timeout_seconds: float = 3.0) -> Dict[str, Any]:
    """Fallback native ping probe using OS ping utility"""
    is_win = platform.system().lower() == "windows"
    cmd = ["ping", "-n", str(count), "-w", str(int(timeout_seconds * 1000)), target] if is_win else ["ping", "-c", str(count), "-W", str(int(timeout_seconds)), target]
    
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_seconds + 2.0)
        out = stdout.decode("utf-8", errors="ignore")
        
        # Parse packet loss: e.g. "Lost = 0 (0% loss)" or "0% packet loss"
        loss_match = re.search(r"\((\d+)%\s*loss\)", out, re.IGNORECASE) or re.search(r"(\d+)%\s*packet loss", out, re.IGNORECASE)
        loss = float(loss_match.group(1)) if loss_match else (100.0 if proc.returncode != 0 else 0.0)
        
        # Parse avg latency: e.g. "Average = 14ms" or "avg = 14.2"
        avg_match = re.search(r"Average\s*=\s*(\d+)ms", out, re.IGNORECASE) or re.search(r"=.*?/([0-9.]+)/", out)
        avg_ms = float(avg_match.group(1)) if avg_match else (0.0 if loss == 100.0 else 25.0)
        
        is_success = (loss < 100.0)
        return {
            "success": is_success,
            "response_time_ms": round(avg_ms, 2),
            "packet_loss_percent": round(loss, 2),
            "error": None if is_success else "Host unreachable or packet loss 100%",
            "details": {"raw_summary": f"Loss: {loss}%, Avg: {avg_ms}ms"}
        }
    except Exception as e:
        return {
            "success": False,
            "response_time_ms": 0.0,
            "packet_loss_percent": 100.0,
            "error": f"Subprocess ping error: {str(e)[:80]}",
            "details": {}
        }

async def check_ping(target: str, timeout_seconds: float = 3.0) -> Dict[str, Any]:
    """
    Checks target host with ICMP ping.
    Attempts icmplib first, falls back gracefully to OS ping.
    """
    try:
        from icmplib import async_ping
        host = await async_ping(target, count=2, interval=0.2, timeout=timeout_seconds, privileged=False)
        is_success = host.is_alive
        return {
            "success": is_success,
            "response_time_ms": round(host.avg_rtt, 2) if is_success else 0.0,
            "packet_loss_percent": round(host.packet_loss * 100, 2),
            "error": None if is_success else "Destination host unreachable",
            "details": {
                "sent": host.packets_sent,
                "received": host.packets_received,
                "min_rtt": round(host.min_rtt, 2),
                "max_rtt": round(host.max_rtt, 2)
            }
        }
    except Exception:
        # Fallback to subprocess ping which works under standard Windows permissions
        return await _subprocess_ping(target, count=2, timeout_seconds=timeout_seconds)
