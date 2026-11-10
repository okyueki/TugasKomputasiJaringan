"""
Generator ringkasan laporan DOCX untuk pengumpulan.
Jalankan:  python generate_doc.py
Output:    Laporan_Bedah_Kode_Celery_RabbitMQ.docx

Catatan: file ini hanya alat bantu dokumentasi, bukan bagian runtime Celery.
"""
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Inches, Pt, RGBColor


PRIMARY = RGBColor(31, 78, 121)
DARK = RGBColor(38, 38, 38)
MUTED = RGBColor(89, 89, 89)


def set_cell_bg(cell, hex_color: str) -> None:
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def add_heading(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    for run in p.runs:
        run.font.color.rgb = PRIMARY
    return p


def add_para(doc, text, bold=False, italic=False, size=11):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.size = Pt(size)
    run.font.color.rgb = DARK
    run.bold = bold
    run.italic = italic
    p.paragraph_format.space_after = Pt(6)
    return p


def add_bullets(doc, items):
    for item in items:
        p = doc.add_paragraph(item, style="List Bullet")
        for run in p.runs:
            run.font.size = Pt(11)
            run.font.color.rgb = DARK


def add_code(doc, text):
    table = doc.add_table(rows=1, cols=1)
    cell = table.cell(0, 0)
    set_cell_bg(cell, "F3F4F6")
    p = cell.paragraphs[0]
    run = p.add_run(text)
    run.font.name = "Consolas"
    run.font.size = Pt(9)
    run.font.color.rgb = DARK
    doc.add_paragraph()


def add_table(doc, headers, rows):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        set_cell_bg(cell, "1F4E79")
        for p in cell.paragraphs:
            for run in p.runs:
                run.bold = True
                run.font.color.rgb = RGBColor(255, 255, 255)
                run.font.size = Pt(10)
    for r_idx, row in enumerate(rows, start=1):
        for c_idx, value in enumerate(row):
            cell = table.rows[r_idx].cells[c_idx]
            cell.text = value
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(10)
                    run.font.color.rgb = DARK
    doc.add_paragraph()


def build() -> Path:
    doc = Document()
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Cover
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("LAPORAN RINGKAS BEDAH KODE")
    run.bold = True
    run.font.size = Pt(18)
    run.font.color.rgb = PRIMARY

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run(
        "Sistem Asynchronous Task Queue & Message Routing\n"
        "Python + Celery + RabbitMQ"
    )
    run.font.size = Pt(12)
    run.font.color.rgb = MUTED

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = meta.add_run(
        "Dokumen ini merangkum arsitektur, fungsi tiap file, cara demo, "
        "dan poin tanya-jawab inti untuk presentasi."
    )
    run.italic = True
    run.font.size = Pt(10)
    run.font.color.rgb = MUTED
    doc.add_paragraph()

    # 1
    add_heading(doc, "1. Ringkasan Proyek", level=1)
    add_para(
        doc,
        "Proyek mengimplementasikan antrean tugas terdistribusi: producer "
        "mengirim pekerjaan ke RabbitMQ, worker Celery mengambil dan "
        "mengerjakan secara asinkron. Ada dua fokus utama: (1) pipeline "
        "pemrosesan data → laporan, dan (2) routing pesan Fanout & Topic.",
    )
    add_bullets(
        doc,
        [
            "Non-blocking: producer tidak menunggu proses berat di thread yang sama.",
            "Scalable: jumlah worker bisa ditambah tanpa mengubah logika bisnis.",
            "Fault-tolerant: pesan di broker dapat dikerjakan ulang jika worker gagal sebelum ACK.",
        ],
    )

    # 2
    add_heading(doc, "2. Arsitektur Singkat", level=1)
    add_code(
        doc,
        "Producer  -->  RabbitMQ (Exchange + Queue)  -->  Celery Worker  -->  Result (rpc://)\n"
        "\n"
        "Queue pipeline : default | data_processing | report_generation\n"
        "Queue routing  : fanout_queue_1/2 | error_logs_queue | all_logs_queue\n"
        "Exchange       : default direct | broadcast_fanout_exchange | logs_topic_exchange",
    )
    add_para(
        doc,
        "Analogi cepat: Producer = pelayan, RabbitMQ = rak tiket dapur, "
        "Worker = koki spesialis per sekat antrean.",
        italic=True,
    )

    # 3
    add_heading(doc, "3. Peran File Sumber", level=1)
    add_table(
        doc,
        ["File", "Fungsi"],
        [
            ["celery_config.py", "Inisialisasi app, broker, exchange, queue, task_routes, serializer JSON"],
            ["tasks.py", "process_data, generate_report, log_handler, process_and_report"],
            ["run_chain.py", "Pipeline best-practice dengan Celery chain()"],
            ["producer.py", "Demo Cara 1 (orchestrator) + Cara 2 (chain)"],
            ["producer_routing.py", "Demo Fanout broadcast + Topic wildcard"],
            ["requirements.txt", "Dependensi: celery, flower, kombu"],
            ["start_workers.bat", "Helper Windows membuka 3 worker pipeline"],
            ["start_routing_worker.bat", "Helper Windows worker routing/log"],
        ],
    )

    # 4
    add_heading(doc, "4. Dua Cara Pipeline (Inti Presentasi)", level=1)
    add_heading(doc, "4.1 Cara 1 — Orchestrator Task", level=2)
    add_para(
        doc,
        "Task process_and_report memanggil process_data.delay() lalu .get(), "
        "kemudian generate_report.delay() lalu .get(). Mudah dipahami, tetapi "
        "blocking dan berisiko deadlock jika hanya ada satu worker pool solo.",
    )
    add_heading(doc, "4.2 Cara 2 — Celery chain() (direkomendasikan)", level=2)
    add_code(
        doc,
        "chain(process_data.s(raw_data), generate_report.s()).apply_async()",
    )
    add_para(
        doc,
        "Return value Task 1 otomatis menjadi argumen Task 2. Pipeline "
        "didaftarkan ke broker tanpa menyandera worker orchestrator.",
    )

    # 5
    add_heading(doc, "5. Routing Fanout & Topic", level=1)
    add_table(
        doc,
        ["Skenario", "Routing Key", "Hasil di Worker"],
        [
            ["Fanout maintenance", "(kosong)", "Muncul 2x (fanout_queue_1 + fanout_queue_2)"],
            ["Error log", "logs.server.error", "Muncul 2x (error_logs_queue + all_logs_queue)"],
            ["Info log", "logs.client.info", "Muncul 1x (hanya all_logs_queue)"],
        ],
    )
    add_bullets(
        doc,
        [
            "Fanout = broadcast ke semua queue terikat; routing key diabaikan.",
            "Topic = filter pola. * = tepat satu kata; # = nol atau banyak kata.",
        ],
    )

    # 6
    add_heading(doc, "6. Cara Menjalankan (Windows)", level=1)
    add_para(doc, "Prasyarat: Python 3.10+, RabbitMQ aktif di localhost:5672, venv terpasang.", bold=True)
    add_para(doc, "Worker Windows wajib memakai flag -P solo.", bold=True)
    add_heading(doc, "6.1 Demo Pipeline (multi-worker)", level=2)
    add_code(
        doc,
        "Terminal 1: celery -A celery_config worker --loglevel=info -P solo -n worker_dp@%h -Q data_processing\n"
        "Terminal 2: celery -A celery_config worker --loglevel=info -P solo -n worker_rg@%h -Q report_generation\n"
        "Terminal 3: celery -A celery_config worker --loglevel=info -P solo -n worker_def@%h -Q default\n"
        "Terminal 4: python producer.py\n"
        "\n"
        "Alternatif: jalankan start_workers.bat, lalu python producer.py",
    )
    add_heading(doc, "6.2 Demo Routing", level=2)
    add_code(
        doc,
        "Terminal 1: celery -A celery_config worker --loglevel=info -P solo "
        "-Q fanout_queue_1,fanout_queue_2,error_logs_queue,all_logs_queue\n"
        "Terminal 2: python producer_routing.py",
    )
    add_heading(doc, "6.3 Monitoring Flower", level=2)
    add_code(doc, "celery -A celery_config flower\nBuka http://localhost:5555")
    add_para(
        doc,
        "Peringatan: jangan demo Cara 1 dengan single-worker + solo. "
        "Worker yang menunggu .get() tidak bisa mengambil subtask → deadlock.",
        bold=True,
    )

    # 7
    add_heading(doc, "7. Poin Tanya-Jawab yang Wajib Dihafal", level=1)
    qa = [
        (
            "Kenapa Celery + RabbitMQ, bukan thread biasa?",
            "Thread terikat satu proses/mesin dan antrean di memori hilang saat crash. "
            "Celery+RabbitMQ terdistribusi, antrean di broker, mudah di-scale.",
        ),
        (
            "Peran RabbitMQ vs Celery?",
            "RabbitMQ = message broker AMQP. Celery = framework task Python "
            "(produce/consume/canvas/retry).",
        ),
        (
            "Fanout vs Topic? * vs #?",
            "Fanout broadcast; Topic selektif. * = satu kata; # = banyak kata.",
        ),
        (
            "Kenapa -P solo di Windows?",
            "Pool prefork butuh fork() Unix. Windows memakai solo agar worker aman.",
        ),
        (
            "Cara 1 atau Cara 2?",
            "Cara 2 (chain) lebih baik: non-blocking dan menghindari deadlock orchestrator.",
        ),
        (
            "Apa fungsi bind=True?",
            "Agar task menerima self: akses request.id dan self.retry().",
        ),
        (
            "Apakah siap produksi?",
            "Ini demo lab. Produksi perlu auth broker, result backend persisten "
            "(Redis/DB), monitoring, serta kebijakan retry/ACK yang ketat.",
        ),
    ]
    for i, (q, a) in enumerate(qa, start=1):
        add_para(doc, f"Q{i}. {q}", bold=True)
        add_para(doc, f"Jawaban: {a}")

    # 8
    add_heading(doc, "8. Checklist Pengumpulan", level=1)
    add_bullets(
        doc,
        [
            "Sertakan: semua file .py runtime, requirements.txt, README.md, "
            "PANDUAN_BEDAH_KODE.md, file .bat helper, dan laporan DOCX ini.",
            "Jangan sertakan: .venv/, myenv/, __pycache__/, .env, file rahasia.",
            "Latihan demo sekali dengan 3 worker sebelum presentasi.",
            "Siap menjelaskan perbedaan Cara 1 vs Cara 2 dengan kata sendiri.",
        ],
    )

    footer = doc.add_paragraph()
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run(
        "— Akhir ringkasan. Detail lengkap ada di PANDUAN_BEDAH_KODE.md dan README.md —"
    )
    run.italic = True
    run.font.size = Pt(9)
    run.font.color.rgb = MUTED

    out = Path(__file__).resolve().parent / "Laporan_Bedah_Kode_Celery_RabbitMQ.docx"
    doc.save(out)
    return out


if __name__ == "__main__":
    path = build()
    print(f"OK: {path}")
