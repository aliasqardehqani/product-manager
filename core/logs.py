import json
import os
from datetime import datetime

class CustomLogger:
    def __init__(self, log_dir="logs", log_file="app_logs.json"):
        self.log_dir = log_dir
        self.log_file = os.path.join(self.log_dir, log_file)
        # os.makedirs(self.log_dir, exist_ok=True)

    def log(self, module_name, class_name, message, error=None):
        log_entry = {
            "module_name": module_name,
            "class_name": class_name,
            "message": message,
            "error": error,
            "created_at": datetime.utcnow().isoformat()
        }

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Logging failed: {e}")

class TMKB2BLogger:
    def __init__(self, log_dir="logs", log_file="tmkb2b_log.json"):
        self.log_dir = log_dir
        self.log_file = os.path.join(self.log_dir, log_file)
        # os.makedirs(self.log_dir, exist_ok=True)

    def log(self, module_name, class_name, message, error=None):
        log_entry = {
            "module_name": module_name,
            "class_name": class_name,
            "message": message,
            "error": error,
            "created_at": datetime.utcnow().isoformat()
        }

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Logging failed: {e}")

class CrwalerMainLogger:
    def __init__(self, log_dir="logs", log_file="crawler_main_log.json"):
        self.log_dir = log_dir
        self.log_file = os.path.join(self.log_dir, log_file)
        # os.makedirs(self.log_dir, exist_ok=True)

    def log(self, module_name, class_name, message, error=None):
        log_entry = {
            "module_name": module_name,
            "class_name": class_name,
            "message": message,
            "error": error,
            "created_at": datetime.utcnow().isoformat()
        }

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Logging failed: {e}")

class UserAppLogger:
    def __init__(self, log_dir="logs", log_file="user_management.json"):
        self.log_dir = log_dir
        self.log_file = os.path.join(self.log_dir, log_file)
        # os.makedirs(self.log_dir, exist_ok=True)

    def log(self, module_name, class_name, message, error=None):
        log_entry = {
            "module_name": module_name,
            "class_name": class_name,
            "message": message,
            "error": error,
            "created_at": datetime.utcnow().isoformat()
        }

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Logging failed: {e}")

class CartLogger:
    def __init__(self, log_dir="logs", log_file="cart_service.json"):
        self.log_dir = log_dir
        self.log_file = os.path.join(self.log_dir, log_file)
        # os.makedirs(self.log_dir, exist_ok=True)

    def log(self, module_name, class_name, message, error=None):
        log_entry = {
            "module_name": module_name,
            "class_name": class_name,
            "message": message,
            "error": error,
            "created_at": datetime.utcnow().isoformat()
        }

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Logging failed: {e}")

class BlogLogger:
    def __init__(self, log_dir="logs", log_file="blog_service.json"):
        self.log_dir = log_dir
        self.log_file = os.path.join(self.log_dir, log_file)
        # os.makedirs(self.log_dir, exist_ok=True)

    def log(self, module_name, class_name, message, error=None):
        log_entry = {
            "module_name": module_name,
            "class_name": class_name,
            "message": message,
            "error": error,
            "created_at": datetime.utcnow().isoformat()
        }

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Logging failed: {e}")