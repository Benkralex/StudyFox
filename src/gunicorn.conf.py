import multiprocessing
import struct
from socket import socket
import fcntl
from config import ip

ip_address = ip
bind = f'{ip_address}:8000'
workers = multiprocessing.cpu_count() * 2 + 1

timeout = 2
preload = True

loglevel = 'info'