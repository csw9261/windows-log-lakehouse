# 시스템 메트릭 수집기
# psutil로 CPU 사용률, 메모리, 프로세스 목록을 수집한다.
# cpu_percent(interval=None)은 논블로킹이지만 첫 호출은 항상 0을 반환하므로
# 첫 실행 시 초기화 호출만 하고 실제 값은 두 번째 호출부터 사용한다.

import psutil
from datetime import datetime, timezone

_cpu_initialized: bool = False


def collect() -> list[dict]:
    """CPU, 메모리, 프로세스 메트릭을 수집해서 반환"""
    global _cpu_initialized

    if not _cpu_initialized:
        # 첫 호출은 기준점 설정용 - 항상 0.0 반환하므로 버림
        # psutil은 이전 호출과의 시간 차이로 CPU 사용률을 계산하기 때문에
        # 첫 호출에는 비교 기준이 없어서 무조건 0.0을 반환함
        psutil.cpu_percent(interval=None)
        _cpu_initialized = True
        cpu: float = 0.0
    else:
        cpu = psutil.cpu_percent(interval=None)

    mem = psutil.virtual_memory()
    processes = _collect_processes()

    return [{
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "log_type": "system_metrics",
        "data": {
            "cpu_percent": cpu,
            "memory_percent": mem.percent,
            "memory_total_mb": mem.total // (1024 * 1024),
            "memory_used_mb": mem.used // (1024 * 1024),
            "process_count": len(processes),
            "processes": processes[:50],
        }
    }]


def _collect_processes() -> list[dict]:
    """실행 중인 전체 프로세스를 수집하고 CPU 사용률 높은 순으로 정렬
    NoSuchProcess: 수집 도중 프로세스가 종료된 경우
    AccessDenied: 시스템 프로세스 등 접근 권한 없는 경우
    """
    processes: list[dict] = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "status"]):
        try:
            processes.append({
                "pid": proc.info["pid"],
                "name": proc.info["name"],
                "cpu_percent": proc.info["cpu_percent"],
                "memory_percent": round(proc.info["memory_percent"], 2),
                "status": proc.info["status"],
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    processes.sort(key=lambda p: p["cpu_percent"] or 0, reverse=True)
    return processes
