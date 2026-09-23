"""Internal-only HTTP adapter. No host port is published by Compose."""
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from .store import Hub, ollama_order


def make_handler(hub):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass  # Do not log report content, recipients or credentials.

        def reply(self, code, value):
            data = json.dumps(value).encode()
            self.send_response(code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            self.reply(200, hub.status()) if self.path == '/health' else self.reply(404, {'error': 'Unknown route'})

        def do_POST(self):
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if length > 65536 or length < 0: raise ValueError('Body too large')
                body = json.loads(self.rfile.read(length) or b'{}')
                if not isinstance(body, dict): raise ValueError('JSON object required')
                if self.path == '/monitor':
                    configured_day = os.getenv('DEMO_AS_OF', '2026-09-23')
                    day = datetime.now(ZoneInfo('Europe/Berlin')).date().isoformat() if configured_day in ('', 'live') else configured_day
                    if os.getenv('DEMO_AS_OF') == '2026-09-23' and not hub.status()['snapshots']:
                        hub.monitor('2026-09-22', hub.data_dir / 'baseline')
                    result = hub.monitor(day)
                elif self.path == '/escalate': result = hub.escalate()
                elif self.path == '/report': result = hub.report(ollama_order if os.getenv('OLLAMA_ENABLED') == 'true' else None)
                elif self.path == '/notifications/claim': result = hub.claim(os.getenv('NOTIFICATION_MODE', 'dry-run'))
                elif self.path == '/notifications/ack':
                    if not isinstance(body.get('success'), bool) or not isinstance(body.get('simulated', False), bool):
                        raise ValueError('Boolean acknowledgement fields required')
                    result = hub.ack(body['notification_id'], body['lease_token'], body['success'], body.get('simulated', False))
                elif self.path == '/digest': result = hub.digest()
                elif self.path == '/analytics': result = hub.analytics()
                else: return self.reply(404, {'error': 'Unknown route'})
                self.reply(200, result)
            except (ValueError, KeyError, FileNotFoundError) as error:
                hub.log('validation_error', type(error).__name__)
                self.reply(422, {'error': str(error)})
            except Exception as error:
                hub.log('stage_error', type(error).__name__)
                self.reply(500, {'error': 'Stage failed; inspect service state and n8n execution'})
    return Handler


if __name__ == '__main__':
    hub = Hub(os.getenv('DATA_DIR', '/data'), os.getenv('STATE_DIR', '/state'), os.getenv('OUTPUT_DIR', '/output'))
    ThreadingHTTPServer(('0.0.0.0', 8000), make_handler(hub)).serve_forever()
