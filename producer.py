import json
from tasks import process_and_report
from run_chain import create_task_chain

if __name__ == "__main__":
    raw_input = "Ini adalah data contoh yang harus diproses dan dilaporkan."

    # Cara 1: orchestrator task (blocking .get() di dalam worker)
    # Wajib jalankan 3 worker terpisah: default, data_processing, report_generation.
    print("=== Cara 1: Dengan orchestrator task ===")
    result = process_and_report.delay(raw_input)
    final_output = result.get()
    print(f"Final result: {json.dumps(final_output, indent=2)}")

    # Cara 2: Celery chain (non-blocking, best practice)
    print("\n=== Cara 2: Dengan chain milik Celery ===")
    chain_result = create_task_chain(raw_input)
    chain_output = chain_result.get()
    print(f"Chain result: {json.dumps(chain_output, indent=2)}")
