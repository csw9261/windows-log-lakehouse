# Kafka Producer
# KafkaProducer 싱글톤을 관리하고 메시지를 각 topic으로 전송한다.
# log_type 값이 곧 topic 이름 (windows_event_logs, system_metrics)

import json
from kafka import KafkaProducer


_producer: KafkaProducer | None = None


def get_producer(bootstrap_servers: str) -> KafkaProducer:
    """KafkaProducer 싱글톤 반환
    이미 생성된 경우 재사용, 없으면 새로 연결
    value_serializer: 메시지(dict)를 JSON 문자열 → bytes로 변환해서 전송
    """
    global _producer
    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
    return _producer


def send(kafka_producer: KafkaProducer, messages: list[dict], host: str) -> None:
    """messages를 각 topic으로 전송
    각 메시지에 host(머신 이름)를 붙이고 log_type에 해당하는 topic으로 전송
    send()는 즉시 전송이 아닌 내부 버퍼에 적재, flush()에서 실제 전송
    """
    for msg in messages:
        msg["host"] = host
        topic = msg["log_type"]  # log_type = topic 이름
        kafka_producer.send(topic, msg)
    kafka_producer.flush()  # 버퍼에 남은 메시지 전부 전송


def close() -> None:
    """Agent 종료 시 Kafka 연결 정리
    연결을 닫지 않으면 미전송 메시지가 유실될 수 있음
    """
    global _producer
    if _producer:
        _producer.close()
        _producer = None
