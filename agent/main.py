# Windows Agent 진입점
# 10초(기본값) 간격으로 2개 collector를 실행하고 Kafka로 전송한다.
#
# 환경변수:
#   KAFKA_BOOTSTRAP  - Kafka 브로커 주소 (기본값: localhost:9092)
#   COLLECT_INTERVAL - 수집 주기(초) (기본값: 10)

import os
import time
import socket
import logging
from kafka import KafkaProducer
from collectors import event_log, system_metrics
import producer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

KAFKA_BOOTSTRAP: str = os.environ.get("KAFKA_BOOTSTRAP", "localhost:9092")  # Kafka 브로커 접속 주소 (WSL IP:9092)
INTERVAL: int = int(os.environ.get("COLLECT_INTERVAL", "10"))              # 수집 주기 (초)
HOST: str = socket.gethostname()                                            # 이 머신의 호스트명 (메시지에 포함)


def run() -> None:
    """Agent 메인 루프
    각 collector를 개별 try-except로 감싸서 하나가 실패해도 나머지는 계속 수집
    """
    kafka_producer: KafkaProducer = producer.get_producer(KAFKA_BOOTSTRAP)
    log.info(f"connected to kafka: {KAFKA_BOOTSTRAP}")

    try:
        while True:
            messages: list[dict] = []

            for name, collector in [
                ("event_log", event_log.collect),
                ("system_metrics", system_metrics.collect),
            ]:
                try:
                    messages += collector()
                except Exception as e:
                    log.error(f"{name} collect error: {e}")

            try:
                producer.send(kafka_producer, messages, HOST)
                log.info(f"sent {len(messages)} messages")
            except Exception as e:
                log.error(f"producer send error: {e}")

            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        log.info("stopping agent")
    finally:
        # 예외 여부와 관계없이 항상 실행: Kafka 연결 정리
        producer.close()


if __name__ == "__main__":
    run()
