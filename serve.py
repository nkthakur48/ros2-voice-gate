#!/usr/bin/env python3
"""Static server with the COOP/COEP headers Moonshine's multithreaded WASM needs. Usage: python3 serve.py [port]"""
import http.server, sys, webbrowser

class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        super().end_headers()

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
webbrowser.open(f"http://localhost:{port}")
http.server.test(H, port=port)
