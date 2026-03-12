# Windows Event Log 수집기
# pywin32의 win32evtlog로 System, Application, Security 채널에서 이벤트를 읽는다.
# _last_time으로 채널별 마지막 수집 시각을 기억해서 신규 이벤트만 가져온다.

import win32evtlog
import win32evtlogutil
from datetime import datetime, timezone


CHANNELS: list[str] = ["System", "Application", "Security"]

# 채널별 마지막 수집 시각 (TimeGenerated 기준)
# RecordNumber 대신 시각 기준을 쓰는 이유: 로그 클리어 시 RecordNumber가 초기화되면
# 저장된 번호보다 작아져서 신규 이벤트를 영원히 못 읽는 문제가 생기기 때문
_last_time: dict = {}


def collect() -> list[dict]:
    """3개 채널을 순회하며 신규 이벤트를 수집해서 반환"""
    messages: list[dict] = []
    for channel in CHANNELS:
        try:
            # None: 로컬 머신 이벤트 로그 오픈
            handle = win32evtlog.OpenEventLog(None, channel)
            # BACKWARDS_READ: 최신 이벤트부터 읽음
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
            events = win32evtlog.ReadEventLog(handle, flags, 0)
            win32evtlog.CloseEventLog(handle)

            if not events:
                continue

            last = _last_time.get(channel)
            # 첫 실행(last=None)이면 현재 배치 전체를 가져오고, 이후엔 마지막 시각 이후만 가져옴
            new_events = [e for e in events if last is None or e.TimeGenerated > last]

            if not new_events:
                continue

            # 다음 호출에서 중복 수집 방지를 위해 이번 배치의 최신 시각 저장
            _last_time[channel] = max(e.TimeGenerated for e in new_events)

            for event in new_events:
                messages.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "log_type": "windows_event_logs",
                    "data": {
                        "channel": channel,
                        "event_id": event.EventID & 0xFFFF,  # 상위 비트 제거해서 실제 ID 추출
                        "source": str(event.SourceName),
                        "level": event.EventType,
                        "time_generated": str(event.TimeGenerated),
                        "message": _get_message(event, channel),
                    }
                })
        except Exception:
            continue

    return messages


def _get_message(event, channel: str) -> str:
    """이벤트 메시지를 사람이 읽을 수 있는 문자열로 변환
    메시지 DLL이 없거나 포맷 실패 시 빈 문자열 반환
    """
    try:
        return win32evtlogutil.SafeFormatMessage(event, channel)
    except Exception:
        return ""
