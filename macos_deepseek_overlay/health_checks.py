import os
import sys
import time
import traceback
import functools
import platform
import objc
from pathlib import Path


def get_log_dir():
    log_dir = Path.home() / "Library" / "Logs" / "macos-deepseek-overlay"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


LOG_DIR = get_log_dir()
LOG_PATH = LOG_DIR / "macos_deepseek_overlay_error_log.txt"
CRASH_COUNTER_FILE = LOG_DIR / "macos_deepseek_overlay_crash_counter.txt"
CRASH_THRESHOLD = 3
CRASH_TIME_WINDOW = 60


def get_system_info():
    macos_version = platform.mac_ver()[0]
    python_version = platform.python_version()
    pyobjc_version = getattr(objc, '__version__', 'unknown')
    info = (
        "\n"
        "System Information:\n"
        f" macOS version: {macos_version}\n"
        f" Python version: {python_version}\n"
        f" PyObjC version: {pyobjc_version}\n"
    )
    return info

def check_crash_loop():
    current_time = time.time()
    count = 0
    last_time = 0
    if os.path.exists(CRASH_COUNTER_FILE):
        try:
            with open(CRASH_COUNTER_FILE, "r") as f:
                line = f.read().strip()
                if line:
                    last_time_str, count_str = line.split(",")
                    last_time = float(last_time_str)
                    count = int(count_str)
        except Exception:
            count = 0
    if current_time - last_time < CRASH_TIME_WINDOW:
        count += 1
    else:
        count = 1
    try:
        with open(CRASH_COUNTER_FILE, "w") as f:
            f.write(f"{current_time},{count}")
    except Exception as e:
        print("Warning: Could not update crash counter file:", e)

    if count > CRASH_THRESHOLD:
        print("ERROR: Crash loop detected (more than {} crashes within {} seconds). Crash counter file (for reference) at:\n  {}\n\nAborting further restarts. To resume attempts to launch, delete the counter file with:\n  rm {}\n\nError log (most recent) at:\n  {}".format(
            CRASH_THRESHOLD,
            CRASH_TIME_WINDOW,
            CRASH_COUNTER_FILE,
            CRASH_COUNTER_FILE,
            LOG_PATH
        ))
        sys.exit(1)

def reset_crash_counter():
    if os.path.exists(CRASH_COUNTER_FILE):
        try:
            os.remove(CRASH_COUNTER_FILE)
        except Exception as e:
            print("Warning: Could not reset crash counter file:", e)

def health_check_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        check_crash_loop()
        try:
            result = func(*args, **kwargs)
            reset_crash_counter()
            print("SUCCESS")
            return result
        except Exception:
            system_info = get_system_info()
            error_trace = traceback.format_exc()
            with open(LOG_PATH, "w") as log_file:
                log_file.write("An unhandled exception occurred:\n")
                log_file.write(system_info)
                log_file.write(error_trace)
            print("ERROR: Application failed to start properly. Details:")
            print(system_info)
            print(error_trace)
            print(f"Error log saved at: {LOG_PATH}", flush=True)
            sys.exit(1)
    return wrapper