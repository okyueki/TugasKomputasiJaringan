from celery_config import app, broadcast_exchange, logs_exchange

if __name__ == "__main__":
    print("=== PENGUJIAN MESSAGE HANDLING ===")

    # 1) FANOUT: pesan di-copy ke fanout_queue_1 DAN fanout_queue_2
    print("\n[1] Mengirim pesan dengan skema FAN-OUT...")
    app.send_task(
        'tasks.log_handler',
        args=["Peringatan Sistem: Server akan maintenance!"],
        exchange=broadcast_exchange,
        routing_key='',
    )

    # 2) TOPIC error: cocok logs.*.error + logs.#
    #    → diterima error_logs_queue DAN all_logs_queue
    print("\n[2] Mengirim pesan Error Log dengan Wildcard (logs.server.error)...")
    app.send_task(
        'tasks.log_handler',
        args=["Database connection timeout!"],
        exchange=logs_exchange,
        routing_key='logs.server.error',
    )

    # 3) TOPIC info: hanya cocok logs.#
    #    → hanya all_logs_queue (error_logs_queue mengabaikan)
    print("\n[3] Mengirim pesan Info Log (logs.client.info)...")
    app.send_task(
        'tasks.log_handler',
        args=["User berhasil login."],
        exchange=logs_exchange,
        routing_key='logs.client.info',
    )

    print("\nPesan berhasil dikirim ke broker. Silakan cek worker!")
