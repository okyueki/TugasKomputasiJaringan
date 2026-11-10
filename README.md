# IFK Celery & RabbitMQ — Distributed Task Processing

Sistem antrean tugas terdistribusi (*distributed task queue*) menggunakan **Python**, **Celery**, dan **RabbitMQ** sebagai *message broker*.

Dokumen pendukung:
- `PANDUAN_BEDAH_KODE.md` — bedah kode + bank soal untuk presentasi
- `Laporan_Bedah_Kode_Celery_RabbitMQ.docx` — ringkasan laporan siap serah

---

## Fitur & Alur Kerja

1. **Task Chaining & Pipelines**
   - `tasks.process_data` → validasi/ekstraksi metrik (antrean `data_processing`)
   - `tasks.generate_report` → laporan JSON (antrean `report_generation`)
   - Orkestrasi: Cara 1 orchestrator task, Cara 2 Celery `chain()` (**direkomendasikan**)

2. **Advanced Message Routing (AMQP)**
   - **Fanout** `broadcast_fanout_exchange` → salin pesan ke `fanout_queue_1` & `fanout_queue_2`
   - **Topic** `logs_topic_exchange`
     - `logs.*.error` → `error_logs_queue`
     - `logs.#` → `all_logs_queue`

3. **Web Monitoring** dengan **Flower** (`http://localhost:5555`)

---

## Prasyarat

- Python 3.10+ (disarankan virtual environment `.venv`)
- RabbitMQ aktif di `localhost:5672` (kredensial default `guest:guest`)

### Instalasi Dependensi

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

---

## Panduan Menjalankan Program

> **Catatan Windows:** Celery di Windows wajib memakai `-P solo` (atau `--pool=solo`). Pool default `prefork` tidak didukung Windows.

> **Peringatan deadlock:** Cara 1 (`process_and_report` + `.get()` di dalam worker) **wajib** multi-worker. Jangan pakai single-worker + pool solo untuk Cara 1.

### Skenario 1: Task Chaining (`producer.py`)

#### Opsi A: Multi-Worker (WAJIB untuk demo lengkap Cara 1 + Cara 2)

Buka 4 terminal (atau jalankan `start_workers.bat` lalu 1 terminal producer):

**Terminal 1 — Worker Data Processing**
```powershell
.\.venv\Scripts\activate
celery -A celery_config worker --loglevel=info -P solo -n worker_dp@%h -Q data_processing
```

**Terminal 2 — Worker Report Generation**
```powershell
.\.venv\Scripts\activate
celery -A celery_config worker --loglevel=info -P solo -n worker_rg@%h -Q report_generation
```

**Terminal 3 — Worker Default / Orchestrator**
```powershell
.\.venv\Scripts\activate
celery -A celery_config worker --loglevel=info -P solo -n worker_def@%h -Q default
```

**Terminal 4 — Producer**
```powershell
.\.venv\Scripts\activate
python producer.py
```

#### Opsi B: Single-Worker (hanya aman untuk uji cepat Cara 2 / chain)

```powershell
.\.venv\Scripts\activate
celery -A celery_config worker --loglevel=info -P solo -Q default,data_processing,report_generation
```

Lalu di terminal lain:
```powershell
python -c "from run_chain import create_task_chain; print(create_task_chain('uji chain').get())"
```

> Opsi B **tidak** cocok untuk `python producer.py` utuh karena Cara 1 akan deadlock pada pool solo.

---

### Skenario 2: Routing Fanout & Topic (`producer_routing.py`)

**Terminal 1 — Worker Routing** (atau `start_routing_worker.bat`)
```powershell
.\.venv\Scripts\activate
celery -A celery_config worker --loglevel=info -P solo -Q fanout_queue_1,fanout_queue_2,error_logs_queue,all_logs_queue
```

**Terminal 2 — Producer Routing**
```powershell
.\.venv\Scripts\activate
python producer_routing.py
```

Hasil yang diharapkan di log worker:
1. Fanout → pesan muncul **2×** (`fanout_queue_1` + `fanout_queue_2`)
2. `logs.server.error` → muncul **2×** (`error_logs_queue` + `all_logs_queue`)
3. `logs.client.info` → muncul **1×** (hanya `all_logs_queue`)

---

### Skenario 3: Flower Dashboard

```powershell
.\.venv\Scripts\activate
celery -A celery_config flower
```

Buka: `http://localhost:5555`

---

## Struktur File

```
├── celery_config.py       # Konfigurasi Celery, exchange, queue, task_routes
├── tasks.py               # process_data, generate_report, log_handler, process_and_report
├── run_chain.py           # Pipeline chain() (Cara 2)
├── producer.py            # Demo Cara 1 + Cara 2
├── producer_routing.py    # Demo Fanout & Topic
├── start_workers.bat      # Helper Windows: buka 3 worker pipeline
├── start_routing_worker.bat
├── requirements.txt       # celery, flower, kombu
├── README.md
├── PANDUAN_BEDAH_KODE.md
├── Laporan_Bedah_Kode_Celery_RabbitMQ.docx
└── generate_doc.py        # opsional: regenerate laporan DOCX (`python generate_doc.py`)
```

**Wajib dikumpulkan:** source `.py` runtime, `requirements.txt`, README, panduan, laporan DOCX, file `.bat`.  
**Jangan dikumpulkan:** `.venv/`, `myenv/`, `__pycache__/`, `.env`, file rahasia.
