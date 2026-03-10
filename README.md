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
| 메시징 | Apache Kafka (KRaft 모드) |
| 저장소 | MinIO (S3 호환), Apache Iceberg, Hive Metastore, PostgreSQL |
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

## 인프라 설정 파일

### infra/hive-config/hive-site.xml

Hive Metastore가 MinIO를 S3 스토리지로 바라보기 위한 설정.

| 항목 | 설명 |
|---|---|
| `hive.metastore.warehouse.dir` | Iceberg 웨어하우스 경로 (`s3a://windows-logs/warehouse`) |
| `fs.s3a.endpoint` | MinIO 엔드포인트 (`http://minio:9000`) |
| `fs.s3a.path.style.access` | MinIO는 path-style 접근 사용 |

### infra/trino/config.properties

Trino 서버 기본 설정. 단일 노드(coordinator가 worker 역할 겸임)로 실행.

| 항목 | 설명 |
|---|---|
| `coordinator=true` | 이 노드가 coordinator 역할 수행 |
| `node-scheduler.include-coordinator=true` | coordinator가 worker도 겸함 (별도 worker 없음) |
| `http-server.http.port` | Trino UI 및 API 포트 (8080) |

### infra/trino/jvm.config

Trino JVM 설정. 힙 메모리는 2GB로 설정.

### infra/trino/catalog/iceberg.properties

Trino가 Iceberg 테이블을 조회하기 위한 카탈로그 설정.

| 항목 | 설명 |
|---|---|
| `iceberg.catalog.type` | Hive Metastore를 카탈로그로 사용 |
| `hive.metastore.uri` | Hive Metastore Thrift 주소 |
| `hive.s3.endpoint` | MinIO 엔드포인트 |
| `hive.s3.path-style-access` | MinIO path-style 접근 활성화 |

## 실행 방법

### 1. 환경 변수 설정

`.env` 파일에 WSL IP를 설정합니다. WSL IP는 재시작마다 바뀔 수 있으므로 매번 확인 후 업데이트합니다.

```bash
ip addr show eth0 | grep "inet "
```

`.env`:
```
WSL_HOST=172.27.242.219
```

### 2. 인프라 실행

```bash
docker-compose up -d
```

### 3. Consumer 서버 실행

```bash
cd consumer
pip install -r requirements.txt
python consumer.py
```

### 4. Windows Agent 실행 (Windows 환경 필요)

```bash
cd agent
pip install -r requirements.txt
python main.py
```

### 5. API 서버 실행

```bash
cd api
npm install
node src/index.js
```

### 6. 프론트엔드 실행

```bash
cd frontend
npm install
npm start
```

## 검증

인프라 실행 후 Trino CLI로 데이터 적재 여부 확인:

```sql
SELECT * FROM iceberg.windows_logs.system_metrics LIMIT 10;
```

## 서비스 포트

| 서비스 | 포트 |
|---|---|
| Kafka | 9092 |
| MinIO Console | 9001 |
| MinIO API | 9000 |
| PostgreSQL | 5432 |
| Hive Metastore | 9083 |
| Trino | 8080 |
| API 서버 | 3000 |
| 프론트엔드 | 5173 |
