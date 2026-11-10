from celery import chain
from tasks import process_data, generate_report


def create_task_chain(raw_data):
    """
    Cara 2 (direkomendasikan): pipeline non-blocking dengan Canvas chain().

    - process_data.s(raw_data)  → signature Task 1
    - generate_report.s()       → argumen diisi otomatis dari return Task 1
    - apply_async()             → kirim seluruh rantai ke broker
    """
    job = chain(
        process_data.s(raw_data),
        generate_report.s(),
    )
    return job.apply_async()
