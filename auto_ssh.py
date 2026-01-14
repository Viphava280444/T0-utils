#!/usr/bin/env python3
import pexpect
import sys
import os
import struct
import fcntl
import termios
import signal
from dotenv import load_dotenv

load_dotenv()

JUMP_HOST = os.getenv('JUMP_HOST', 'lxplus9.cern.ch')
JUMP_USER = os.getenv('JUMP_USER')
JUMP_PASSWORD = os.getenv('JUMP_PASSWORD')

DEST_HOST = os.getenv('DEST_HOST', 'lxplus9.cern.ch')
DEST_USER = os.getenv('DEST_USER')
DEST_PASSWORD = os.getenv('DEST_PASSWORD')

def get_terminal_size():
    try:
        s = struct.pack('HHHH', 0, 0, 0, 0)
        result = fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, s)
        rows, cols = struct.unpack('HHHH', result)[:2]
        return rows, cols
    except:
        return 24, 80

def validate_config():
    missing = []
    if not JUMP_USER:
        missing.append('JUMP_USER')
    if not JUMP_PASSWORD:
        missing.append('JUMP_PASSWORD')
    if not DEST_USER:
        missing.append('DEST_USER')
    if not DEST_PASSWORD:
        missing.append('DEST_PASSWORD')

    if missing:
        print("Error: Missing configuration:")
        for m in missing:
            print(f"  - {m}")
        print("\nPlease create a .env file with your SSH credentials")
        sys.exit(1)

def connect_ssh():
    validate_config()

    rows, cols = get_terminal_size()
    ssh_command = f'ssh -t {JUMP_USER}@{JUMP_HOST}'

    print(f"=== Step 1: Connecting to {JUMP_USER}@{JUMP_HOST} ===")

    try:
        child = pexpect.spawn(ssh_command, encoding='utf-8', timeout=60,
                              dimensions=(rows, cols))

        def sigwinch_handler(sig, frame):
            rows, cols = get_terminal_size()
            child.setwinsize(rows, cols)

        signal.signal(signal.SIGWINCH, sigwinch_handler)

        index = child.expect([
            '[Pp]assword:',
            'Are you sure you want to continue connecting',
            'Connection refused',
            'No route to host',
            pexpect.EOF,
            pexpect.TIMEOUT
        ], timeout=30)

        if index == 0:
            child.sendline(JUMP_PASSWORD)
        elif index == 1:
            print("Accepting host key...")
            child.sendline('yes')
            child.expect('[Pp]assword:')
            child.sendline(JUMP_PASSWORD)
        elif index == 2:
            print("Error: Connection refused")
            return
        elif index == 3:
            print("Error: No route to host")
            return
        elif index == 4:
            print("Connection closed unexpectedly")
            return
        elif index == 5:
            print("Connection timeout")
            return

        index = child.expect([
            '2nd factor',
            'Permission denied',
            '\\$',
            pexpect.TIMEOUT
        ], timeout=10)

        if index == 0:
            print("\n2FA Required!")
            otp_code = input("Enter your 2FA code: ")
            child.sendline(otp_code)
        elif index == 1:
            print("\nError: Permission denied. Check your password.")
            return
        elif index == 2:
            pass

        try:
            child.expect(['\\$', '\\]\\$', '\\] \\$'], timeout=30)
            print(f"Connected to {JUMP_HOST}!\n")
        except pexpect.TIMEOUT:
            pass

        print(f"=== Step 2: Connecting to {DEST_USER}@{DEST_HOST} ===")

        ssh_command_2 = f'ssh -t {DEST_USER}@{DEST_HOST}'
        child.sendline(ssh_command_2)

        index = child.expect([
            '[Pp]assword:',
            'Are you sure you want to continue connecting',
            'Permission denied',
            pexpect.TIMEOUT
        ], timeout=30)

        if index == 0:
            child.sendline(DEST_PASSWORD)
        elif index == 1:
            child.sendline('yes')
            child.expect('[Pp]assword:')
            child.sendline(DEST_PASSWORD)
        elif index == 2:
            print("Error: Permission denied on second hop")
            return
        elif index == 3:
            print("Timeout on second hop")
            return

        try:
            index = child.expect([
                'Permission denied',
                '\\$',
                pexpect.TIMEOUT
            ], timeout=15)

            if index == 0:
                print("\nError: Permission denied. Check DEST_PASSWORD.")
                return
        except:
            pass

        print(f"\nConnected to {DEST_USER}@{DEST_HOST}!")
        print("Type 'exit' twice to disconnect.\n")

        child.interact()

    except KeyboardInterrupt:
        print("\n\nConnection interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    connect_ssh()
