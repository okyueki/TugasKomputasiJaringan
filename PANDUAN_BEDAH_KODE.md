# PANDUAN LENGKAP BEDAH KODE & PERSIAPAN TANYA JAWAB DOSEN
## Sistem Asynchronous Task Queue & Routing (Celery + RabbitMQ)

Pegangan presentasi/bedah kode. Fokus: paham alur, siap jawab pertanyaan out-of-the-box, dan aman saat demo.

---

## DAFTAR ISI
1. [Konsep Dasar & Analogi "Restoran"](#1-konsep-dasar--analogi-restoran-the-big-picture)
2. [Diagram Alur Arsitektur Sistem](#2-diagram-alur-arsitektur-sistem)
3. [Bedah Kode File per File](#3-bedah-kode-file-per-file)
4. [Step-by-Step Demo](#4-step-by-step-menjalankan-program--skenario-demo)
5. [Bank Soal "Killer Questions"](#5-bank-soal--jawaban-killer-questions-dosen)
6. [Cheat Sheet 60 Detik](#6-cheat-sheet-60-detik-sebelum-masuk-ruang)

---

## 1. Konsep Dasar & Analogi "Restoran" (The Big Picture)

1. **Producer** (`producer.py` / `producer_routing.py`) = Pelayan  
   Terima pesanan, tulis tiket, taruh di rak dapur. Tidak memasak sendiri agar tidak *blocking*.
2. **RabbitMQ** = Rak / papan tiket dapur (Message Broker AMQP)  
   Menyimpan antrean: `data_processing`, `report_generation`, `default`, antrean fanout & log.
3. **Celery Worker** = Koki spesialis  
   Ambil tiket sesuai sekat antrean, kerja di latar belakang (*asynchronous*).

### Mengapa arsitektur ini?
- **Non-blocking**: UI/API tidak menunggu proses berat.
- **Scalability**: tambah worker tanpa ubah kode bisnis.
- **Fault-tolerance**: pesan di broker tidak hilang saat worker crash (selama belum di-ACK).

---

## 2. Diagram Alur Arsitektur Sistem

```
+-----------------------------------------------------------------------------------+
|                                     PRODUCER                                      |
|  - producer.py (pipeline Cara 1 + Cara 2)                                         |
|  - producer_routing.py (Fanout & Topic)                                           |
+-----------------------------------------------------------------------------------+
                                          |
                                          | AMQP
                                          v
+-----------------------------------------------------------------------------------+
|                               RABBITMQ (BROKER)                                   |
|  Exchanges: default direct | broadcast_fanout_exchange | logs_topic_exchange      |
|  Queues:                                                                              |
|    default | data_processing | report_generation                                      |
|    fanout_queue_1 | fanout_queue_2                                                    |
|    error_logs_queue (logs.*.error) | all_logs_queue (logs.#)                          |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                                 CELERY WORKERS                                    |
|  worker_dp  -Q data_processing      → process_data()                              |
|  worker_rg  -Q report_generation    → generate_report()                           |
|  worker_def -Q default              → process_and_report()                        |
|  worker_log -Q fanout + logs        → log_handler()                               |
+-----------------------------------------------------------------------------------+
```

---

## 3. Bedah Kode File per File

### A. `celery_config.py` — pusat konfigurasi & topologi

Poin yang sering ditanya:
- `Celery('task_chain', include=['tasks'])` → worker wajib tahu daftar task.
- `broker_url='amqp://guest@localhost//'` → koneksi RabbitMQ.
- `result_backend='rpc://'` → hasil sementara agar client bisa `.get()` (demo, bukan produksi).
- `task_queues` mendeklarasikan **semua** queue termasuk `data_processing` & `report_generation`.
- Fanout = broadcast; Topic = cocokkan pola `*` / `#`.
- `task_routes` mengarahkan nama task ke queue tertentu.

### B. `tasks.py` — unit pekerjaan

| Task | Queue | Peran |
|------|-------|-------|
| `process_data` | `data_processing` | ekstrak metrik + sleep 2s |
| `generate_report` | `report_generation` | buat laporan JSON + sleep 3s |
| `log_handler` | (via exchange) | cetak pesan routing |
| `process_and_report` | `default` | orchestrator Cara 1 (blocking) |

- `bind=True` → dapat `self` untuk `self.retry()` / metadata task.
- `self.retry(countdown=60, max_retries=3)` → fault tolerance.
- **Bahaya Cara 1:** `.get()` di dalam worker menyandera worker. Butuh multi-worker. Single-worker + solo = **deadlock**.

### C. `run_chain.py` — Cara 2 (best practice)

```python
chain(process_data.s(raw_data), generate_report.s()).apply_async()
```

Return Task 1 otomatis jadi argumen Task 2. Non-blocking, tidak menyandera worker orchestrator.

### D. `producer.py` — pemicu demo pipeline

Menjalankan Cara 1 lalu Cara 2, lalu `result.get()` di **sisi client** (ini wajar; yang berbahaya adalah `.get()` di dalam task worker).

### E. `producer_routing.py` — uji Fanout & Topic

| Kiriman | Routing key | Diterima oleh |
|---------|-------------|---------------|
| Fanout maintenance | `''` | `fanout_queue_1` + `fanout_queue_2` |
| Error DB | `logs.server.error` | `error_logs_queue` + `all_logs_queue` |
| Info login | `logs.client.info` | hanya `all_logs_queue` |

---

## 4. Step-by-Step Menjalankan Program & Skenario Demo

### Persiapan
1. Aktifkan venv: `.\.venv\Scripts\activate`
2. Pastikan RabbitMQ service running
3. Bekerja dari folder proyek ini (bukan path absolut mesin tertentu)

### Demo 1 — Task Chaining (paling sering diminta)
1. Jalankan `start_workers.bat` **atau** 3 terminal worker (lihat README Opsi A).
2. Jalankan `python producer.py`.
3. Tunjukkan:
   - Terminal producer: JSON Cara 1 & Cara 2
   - Worker DP: `Processing data...` succeeded
   - Worker RG: `Generating report...` succeeded
4. Kalimat kunci: *"Task masuk antrean berbeda; worker spesialis mengerjakan tanpa memblokir producer."*

### Demo 2 — Fanout & Topic
1. `start_routing_worker.bat` atau worker `-Q fanout_queue_1,fanout_queue_2,error_logs_queue,all_logs_queue`
2. `python producer_routing.py`
3. Tunjukkan jumlah kemunculan log: 2 / 2 / 1

### Demo 3 — Flower (nilai tambah)
```powershell
celery -A celery_config flower
```
Buka `http://localhost:5555` → workers + tasks grid.

---

## 5. Bank Soal & Jawaban "Killer Questions" Dosen

### Q1: Kenapa butuh Celery + RabbitMQ, bukan thread biasa?
Thread/fungsi biasa terikat satu proses/mesin; antrean di memori hilang jika crash. Celery+RabbitMQ: terdistribusi, antrean persisten di broker, mudah di-scale.

### Q2: Bedanya RabbitMQ vs Celery?
- RabbitMQ = **message broker** (simpan & routing pesan AMQP)
- Celery = **task framework** Python (produce, consume, canvas, retry)

### Q3: Fanout vs Topic?
- Fanout: broadcast ke semua queue terikat, abaikan routing key
- Topic: selektif berdasarkan pola routing key

### Q4: Bedanya `*` dan `#`?
- `*` = tepat **satu** kata (`logs.*.error` ≠ `logs.error`, ≠ `logs.a.b.error`)
- `#` = **nol atau banyak** kata (`logs.#` menangkap semua awalan `logs.`)

### Q5: Kenapa Windows harus `-P solo`?
Default pool `prefork` mengandalkan `fork()` Unix. Windows tidak punya `fork` native → error. `solo` jalankan di proses utama secara aman (satu task per waktu per worker).

### Q6: `.delay()` vs `.apply_async()`?
`.delay(*args)` = shortcut `.apply_async(args=...)`. `apply_async` lebih lengkap: `queue`, `countdown`, `expires`, `exchange`, dll.

### Q7: Cara 1 vs Cara 2, mana lebih baik?
**Cara 2 (`chain`)**. Cara 1 blocking + risiko deadlock. Chain mendaftarkan pipeline ke broker tanpa menyandera worker.

### Q8: Fungsi `bind=True`?
Supaya parameter pertama adalah instance task (`self`): akses `self.request.id`, panggil `self.retry()`.

### Q9: RabbitMQ mati saat producer kirim?
Producer gagal koneksi (connection refused / error sejenis; kode errno bisa beda di Windows vs Linux). Jika pesan sudah masuk queue & worker mati sebelum ACK, broker bisa redeliver ke worker lain.

### Q10: Kenapa pisah `data_processing` dan `report_generation`?
Separation of concerns + alokasi resource independen (scale worker per jenis pekerjaan).

### Q11 (out-of-the-box): Apa yang terjadi single-worker solo + Cara 1?
Deadlock: worker menunggu `.get()` sementara task anak mengantri di worker yang sama yang sedang diblokir.

### Q12 (out-of-the-box): Apakah `rpc://` cocok produksi?
Untuk demo ya. Produksi biasanya Redis/Database backend yang persisten dan multi-consumer friendly.

---

## 6. Cheat Sheet 60 Detik Sebelum Masuk Ruang

1. Producer kirim pesan → RabbitMQ exchange/queue → Worker eksekusi → hasil via backend → client `.get()`.
2. Fanout = radio; Topic = filter pola.
3. Demo pipeline pakai **3 worker**; jangan Opsi B untuk `producer.py` utuh.
4. Kalau ditanya best practice: jawab **chain**, sebut risiko orchestrator.
5. Kalau ditanya production-ready: jujur — ini lab demo; produksi butuh auth broker, backend persisten, monitoring, retry/ACK ketat.
