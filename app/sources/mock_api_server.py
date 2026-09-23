"""
mock_api_server.py
-------------------
A tiny, self-contained REST API used to simulate the "academic data"
source described in the assignment (GPA / attendance / status per
student).

Why a mock server?
    The assignment explicitly allows building a local Mock API when a
    real internet connection is not available ("يمكن استخدام API عام
    مناسب، أو بناء Mock API محلي إذا تعذر الاتصال بالإنترنت"). This
    server behaves exactly like a real REST API from the client's
    point of view: it is reached over HTTP with `requests`, returns
    JSON, and can fail in the same ways a real API can (timeouts,
    connection errors, bad status codes, malformed JSON).

Endpoints
    GET /api/academic            -> list of all academic records
    GET /api/academic/<id>       -> single record for one student
    GET /api/health              -> simple health check

Run standalone for manual testing:
    python -m app.sources.mock_api_server
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# Academic records keyed by student_id.
# Intentionally includes a few data-quality problems (missing / invalid
# values) that the validation & cleaning stages are expected to catch.
ACADEMIC_RECORDS = [
    {"student_id": 1001, "gpa": 3.45, "attendance": 92, "status": "Active"},
    {"student_id": 1002, "gpa": 3.9, "attendance": 88, "status": "Active"},
    {"student_id": 1003, "gpa": 2.6, "attendance": 75, "status": "Active"},
    {"student_id": 1004, "gpa": 2.1, "attendance": 60, "status": "Active"},
    {"student_id": 1005, "gpa": 3.2, "attendance": 95, "status": "Active"},
    {"student_id": 1006, "gpa": None, "attendance": 80, "status": "Active"},        # missing GPA
    {"student_id": 1007, "gpa": 4.8, "attendance": 70, "status": "Active"},          # invalid GPA (>4)
    {"student_id": 1008, "gpa": 3.0, "attendance": 65, "status": "Active"},
    {"student_id": 1009, "gpa": 2.9, "attendance": 110, "status": "Active"},         # invalid attendance (>100)
    {"student_id": 1010, "gpa": 3.6, "attendance": 91, "status": "Active"},
    {"student_id": 1011, "gpa": 3.1, "attendance": 84, "status": "Inactive"},
    {"student_id": 1012, "gpa": 2.4, "attendance": 55, "status": "Active"},
    {"student_id": 1013, "gpa": 3.3, "attendance": 89, "status": "Active"},
    {"student_id": 1014, "gpa": 1.9, "attendance": 40, "status": "Active"},
    {"student_id": 1015, "gpa": 3.0, "attendance": None, "status": "Active"},       # missing attendance
    {"student_id": 1016, "gpa": 3.7, "attendance": 93, "status": "Active"},
    {"student_id": 1017, "gpa": 2.8, "attendance": 77, "status": "Active"},
    {"student_id": 1018, "gpa": 3.95, "attendance": 97, "status": "Active"},
    {"student_id": 1019, "gpa": 2.2, "attendance": 66, "status": "Active"},
]


class _AcademicAPIHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802 (http.server naming convention)
        if self.path == "/api/health":
            self._send_json({"status": "ok"})
            return

        if self.path == "/api/academic":
            self._send_json(ACADEMIC_RECORDS)
            return

        if self.path.startswith("/api/academic/"):
            try:
                student_id = int(self.path.rsplit("/", 1)[-1])
            except ValueError:
                self._send_json({"error": "invalid student_id"}, status=400)
                return
            record = next(
                (r for r in ACADEMIC_RECORDS if r["student_id"] == student_id), None
            )
            if record is None:
                self._send_json({"error": "not found"}, status=404)
            else:
                self._send_json(record)
            return

        self._send_json({"error": "not found"}, status=404)

    # Silence default request logging to keep pipeline logs clean.
    def log_message(self, format, *args):  # noqa: A002
        return


class MockAPIServer:
    """Starts the mock API on a background thread on an ephemeral port."""

    def __init__(self, host="127.0.0.1", port=0):
        self._server = HTTPServer((host, port), _AcademicAPIHandler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def base_url(self):
        host, port = self._server.server_address
        return f"http://{host}:{port}"

    def start(self):
        self._thread.start()
        return self

    def stop(self):
        self._server.shutdown()
        self._server.server_close()


if __name__ == "__main__":
    server = MockAPIServer(port=8000).start()
    print(f"Mock academic API running at {server.base_url}")
    print("Press Ctrl+C to stop.")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        server.stop()
