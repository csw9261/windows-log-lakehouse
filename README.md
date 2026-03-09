# windows-log-lakehouse

Windows 로그를 수집하여 데이터 레이크하우스에 저장하고 시각화하는 토이 프로젝트.

## 아키텍처

```
Windows Agent (Python)
  |
  | Kafka Producer
  v
Kafka
  |
  | Kafka Consumer
  v
Consumer Server (Python)
  |
  v
MinIO + Apache Iceberg + Hive Metastore
  |
  v
Trino
  |
  v
Node.js API Server
  |
  v
React Frontend
```

## 수집 로그 종류

| 종류 | 설명 | Kafka Topic |
|---|---|---|
| Windows Event Log | 시스템/보안/애플리케이션 이벤트 | `windows_event_logs` |
| 시스템 메트릭 | CPU, 메모리, 프로세스 수 | `system_metrics` |
| 파일 접근 | 파일 생성/수정/삭제 이벤트 | `file_access_logs` |
| 네트워크 | 네트워크 연결 정보 | `network_logs` |

## 기술 스택

| 레이어 | 기술 |
|---|---|
| 수집 | Python, pywin32, psutil, watchdog, kafka-python |
| 메시징 | Apache Kafka, Zookeeper |
| 저장소 | MinIO (S3 호환), Apache Iceberg, Hive Metastore |
| 쿼리 | Trino |
| API | Node.js, Express.js |
| 프론트엔드 | React |
| 인프라 | Docker, Docker Compose |

## 디렉토리 구조

```
windows-log-lakehouse/
├── agent/                  # Windows 로그 수집 에이전트 (Python)
│   ├── collectors/
│   │   ├── event_log.py
│   │   ├── system_metrics.py
│   │   ├── file_access.py
│   │   └── network.py
│   ├── producer.py
│   ├── main.py
│   └── requirements.txt
├── consumer/               # Kafka Consumer + Iceberg 적재 (Python)
│   ├── consumer.py
│   ├── iceberg_writer.py
│   └── requirements.txt
├── api/                    # REST API 서버 (Node.js)
│   └── src/
│       ├── index.js
│       └── routes/
│           └── logs.js
├── frontend/               # 웹 프론트엔드 (React)
│   └── src/
├── infra/                  # 인프라 설정 파일
│   ├── hive-config/
│   │   └── hive-site.xml
│   └── trino/
│       ├── catalog/
│       │   └── iceberg.properties
│       ├── config.properties
│       └── jvm.config
└── docker-compose.yml
```

## 실행 방법

### 1. 인프라 실행

```bash
docker-compose up -d
```

### 2. Consumer 서버 실행

```bash
cd consumer
pip install -r requirements.txt
python consumer.py
```

### 3. Windows Agent 실행 (Windows 환경 필요)

```bash
cd agent
pip install -r requirements.txt
python main.py
```

### 4. API 서버 실행

```bash
cd api
npm install
node src/index.js
```

### 5. 프론트엔드 실행

```bash
cd frontend
npm install
npm start
```

## 검증

인프라 실행 후 Trino CLI로 데이터 적재 여부 확인:

```sql
SELECT * FROM iceberg.warehouse.system_metrics LIMIT 10;
```

## 서비스 포트

| 서비스 | 포트 |
|---|---|
| Kafka | 9092 |
| MinIO Console | 9001 |
| MinIO API | 9000 |
| Hive Metastore | 9083 |
| Trino | 8080 |
| API 서버 | 3000 |
| 프론트엔드 | 5173 |
