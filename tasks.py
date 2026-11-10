from celery_config import app
import time


@app.task(bind=True, queue='data_processing')
def process_data(self, raw_data):
    """
    Task 1: validasi/ekstraksi metrik dari data mentah.
    Masuk antrean: data_processing
    """
    try:
        print(f"Processing data: {raw_data}")
        time.sleep(2)  # simulasi pekerjaan I/O berat

        processed_data = {
            'original': raw_data,
            'processed_at': time.time(),
            'word_count': len(str(raw_data).split()) if isinstance(raw_data, str) else 0,
            'status': 'processed',
        }
        print(f"Data processing completed: {processed_data}")
        return processed_data

    except Exception as exc:
        print(f"Error in process_data: {exc}")
        # Jadwalkan ulang; self.retry() akan melempar exception Retry
        self.retry(countdown=60, max_retries=3, exc=exc)


@app.task
def log_handler(message):
    """Task sederhana untuk demo Fanout & Topic routing."""
    print(f"[Log Worker] Menerima pesan: {message}")
    return message


@app.task(bind=True, queue='report_generation')
def generate_report(self, processed_data):
    """
    Task 2: buat laporan terstruktur dari hasil process_data.
    Masuk antrean: report_generation
    """
    try:
        print(f"Generating report from: {processed_data}")
        time.sleep(3)  # simulasi pekerjaan berat (mis. compile laporan)

        report = {
            'report_id': f"RPT_{int(time.time())}",
            'data_summary': {
                'original_data': processed_data.get('original'),
                'word_count': processed_data.get('word_count', 0),
                'processed_at': processed_data.get('processed_at'),
            },
            'generated_at': time.time(),
            'status': 'completed',
        }
        print(f"Report generation completed: {report}")
        return report

    except Exception as exc:
        print(f"Error in generate_report: {exc}")
        self.retry(countdown=60, max_retries=3, exc=exc)


@app.task(bind=True)
def process_and_report(self, raw_data):
    """
    Orchestrator (Cara 1): panggil Task 1 lalu Task 2 secara berurutan.

    Catatan penting:
    - Memakai .get() di dalam worker bersifat BLOCKING.
    - Butuh worker TERPISAH untuk data_processing & report_generation.
    - Jangan dijalankan dengan single-worker + pool solo (risiko deadlock).
    - Untuk produksi, lebih baik pakai Celery chain() di run_chain.py.
    """
    try:
        process_result = process_data.delay(raw_data)
        processed_data = process_result.get(disable_sync_subtasks=False)

        report_result = generate_report.delay(processed_data)
        final_report = report_result.get(disable_sync_subtasks=False)

        return final_report

    except Exception as exc:
        print(f"Error in process_and_report: {exc}")
        raise
