"""Configuration loader — reads .env and provides typed access."""

import os
from dotenv import load_dotenv

load_dotenv()


def _bool(key, default='false'):
    return os.getenv(key, default).lower() == 'true'


def _int(key, default='0'):
    return int(os.getenv(key, default))


class Config:
    # Server
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = _int('PORT', '5000')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key')
    DEBUG = _bool('DEBUG')

    # Auth
    AUTH_MAX_ATTEMPTS = _int('AUTH_MAX_ATTEMPTS', '10')
    AUTH_LOCKOUT_MINUTES = _int('AUTH_LOCKOUT_MINUTES', '15')
    AUTH_SESSION_HOURS = _int('AUTH_SESSION_HOURS', '24')

    # AP Primary
    AP_INTERFACE = os.getenv('AP_INTERFACE', 'wlan0')
    AP_SSID = os.getenv('AP_SSID', 'RaspberryPi-AP')
    AP_PASSWORD = os.getenv('AP_PASSWORD', 'ChangeMe123!')
    AP_CHANNEL = os.getenv('AP_CHANNEL', '6')
    AP_HW_MODE = os.getenv('AP_HW_MODE', 'g')
    AP_WPA = os.getenv('AP_WPA', '2')
    AP_HIDDEN = os.getenv('AP_HIDDEN', '0')
    AP_COUNTRY_CODE = os.getenv('AP_COUNTRY_CODE', 'US')
    AP_MAX_CLIENTS = _int('AP_MAX_CLIENTS', '20')

    # AP Secondary
    AP2_INTERFACE = os.getenv('AP2_INTERFACE', 'wlan1')
    AP2_SSID = os.getenv('AP2_SSID', 'RaspberryPi-AP-5G')
    AP2_PASSWORD = os.getenv('AP2_PASSWORD', 'ChangeMe123!')
    AP2_CHANNEL = os.getenv('AP2_CHANNEL', '36')
    AP2_HW_MODE = os.getenv('AP2_HW_MODE', 'a')

    # Network
    AP_SUBNET = os.getenv('AP_SUBNET', '10.0.0.0/24')
    AP_GATEWAY = os.getenv('AP_GATEWAY', '10.0.0.1')
    DHCP_RANGE_START = os.getenv('DHCP_RANGE_START', '10.0.0.10')
    DHCP_RANGE_END = os.getenv('DHCP_RANGE_END', '10.0.0.200')
    DHCP_LEASE_TIME = os.getenv('DHCP_LEASE_TIME', '12h')
    ETH_INTERFACE = os.getenv('ETH_INTERFACE', 'eth0')

    # DNS
    DNS_PRIMARY = os.getenv('DNS_PRIMARY', '1.1.1.1')
    DNS_SECONDARY = os.getenv('DNS_SECONDARY', '8.8.8.8')

    # MAC Filter
    MAC_FILTER_MODE = os.getenv('MAC_FILTER_MODE', 'whitelist')
    MAC_WHITELIST_FILE = os.getenv('MAC_WHITELIST_FILE', 'config/mac_whitelist.txt')
    MAC_BLACKLIST_FILE = os.getenv('MAC_BLACKLIST_FILE', 'config/mac_blacklist.txt')

    # QoS
    QOS_DEFAULT_DOWN_KBPS = _int('QOS_DEFAULT_DOWN_KBPS', '10000')
    QOS_DEFAULT_UP_KBPS = _int('QOS_DEFAULT_UP_KBPS', '5000')

    # Captive Portal
    CAPTIVE_PORTAL_TITLE = os.getenv('CAPTIVE_PORTAL_TITLE', 'Welcome')
    CAPTIVE_PORTAL_MESSAGE = os.getenv('CAPTIVE_PORTAL_MESSAGE', 'Accept terms to connect')
    CAPTIVE_PORTAL_PASSWORD = os.getenv('CAPTIVE_PORTAL_PASSWORD', '')

    # WiFi Schedule
    WIFI_ON_TIME = os.getenv('WIFI_ON_TIME', '07:00')
    WIFI_OFF_TIME = os.getenv('WIFI_OFF_TIME', '23:00')
    WIFI_SCHEDULE_DAYS = os.getenv('WIFI_SCHEDULE_DAYS', 'mon,tue,wed,thu,fri,sat,sun')

    # VPN
    VPN_TYPE = os.getenv('VPN_TYPE', 'wireguard')
    VPN_CONFIG_PATH = os.getenv('VPN_CONFIG_PATH', '/etc/wireguard/wg0.conf')

    # Auto Channel
    CHANNEL_SCAN_INTERVAL_MIN = _int('CHANNEL_SCAN_INTERVAL_MIN', '60')

    # Health Monitor
    HEALTH_PING_TARGET = os.getenv('HEALTH_PING_TARGET', '1.1.1.1')
    HEALTH_CHECK_INTERVAL_SEC = _int('HEALTH_CHECK_INTERVAL_SEC', '30')

    # Notifications
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL', '')
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = _int('SMTP_PORT', '587')
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASS = os.getenv('SMTP_PASS', '')
    SMTP_TO = os.getenv('SMTP_TO', '')

    # Database
    DB_PATH = os.getenv('DB_PATH', 'data/wifi_extender.db')

    # Feature Toggles
    ENABLE_AUTO_SETUP = _bool('ENABLE_AUTO_SETUP', 'true')
    ENABLE_SSID_MANAGER = _bool('ENABLE_SSID_MANAGER', 'true')
    ENABLE_CLIENT_LIST = _bool('ENABLE_CLIENT_LIST', 'true')
    ENABLE_BANDWIDTH_MONITOR = _bool('ENABLE_BANDWIDTH_MONITOR', 'true')
    ENABLE_MAC_FILTER = _bool('ENABLE_MAC_FILTER')
    ENABLE_CAPTIVE_PORTAL = _bool('ENABLE_CAPTIVE_PORTAL')
    ENABLE_QOS = _bool('ENABLE_QOS')
    ENABLE_WIFI_SCHEDULE = _bool('ENABLE_WIFI_SCHEDULE')
    ENABLE_AUTO_CHANNEL = _bool('ENABLE_AUTO_CHANNEL', 'true')
    ENABLE_DNS_CONFIG = _bool('ENABLE_DNS_CONFIG', 'true')
    ENABLE_DUAL_BAND = _bool('ENABLE_DUAL_BAND')
    ENABLE_VPN_PASSTHROUGH = _bool('ENABLE_VPN_PASSTHROUGH')
    ENABLE_NOTIFICATIONS = _bool('ENABLE_NOTIFICATIONS')
    ENABLE_CONNECTION_LOG = _bool('ENABLE_CONNECTION_LOG', 'true')
    ENABLE_HEALTH_MONITOR = _bool('ENABLE_HEALTH_MONITOR', 'true')
