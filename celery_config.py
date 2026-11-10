from celery import Celery
from kombu import Exchange, Queue

# Inisialisasi aplikasi Celery.
# include=['tasks'] wajib agar worker mengimpor tasks.py saat start
# (tanpa ini muncul error NotRegistered).
app = Celery('task_chain', include=['tasks'])

# Exchange kustom untuk uji routing AMQP
logs_exchange = Exchange('logs_topic_exchange', type='topic')
broadcast_exchange = Exchange('broadcast_fanout_exchange', type='fanout')

app.conf.update(
    # Broker RabbitMQ (default guest:guest @ localhost:5672)
    broker_url='amqp://guest@localhost//',

    # Backend hasil sementara via RabbitMQ RPC (cukup untuk demo/.get())
    result_backend='rpc://',

    # Default jika task tidak punya queue khusus
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',

    # Deklarasi queue + binding ke exchange
    task_queues=(
        Queue('default', routing_key='default'),

        # Queue pipeline (dipakai task_routes / decorator @app.task)
        Queue('data_processing', routing_key='data_processing'),
        Queue('report_generation', routing_key='report_generation'),

        # Fanout: setiap pesan di-copy ke SEMUA queue yang terikat
        Queue('fanout_queue_1', broadcast_exchange, routing_key='any'),
        Queue('fanout_queue_2', broadcast_exchange, routing_key='any'),

        # Topic:
        #   *  = tepat 1 kata   → logs.*.error cocok dengan logs.server.error
        #   #  = 0 atau lebih   → logs.# menangkap semua awalan logs.
        Queue('error_logs_queue', logs_exchange, routing_key='logs.*.error'),
        Queue('all_logs_queue', logs_exchange, routing_key='logs.#'),
    ),

    # Routing otomatis berdasarkan nama task
    task_routes={
        'tasks.process_data': {'queue': 'data_processing'},
        'tasks.generate_report': {'queue': 'report_generation'},
    },

    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)
