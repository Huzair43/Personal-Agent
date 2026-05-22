import json
import os
import tempfile
import unittest
from pathlib import Path

from agent.config import Config


class TestConfig(unittest.TestCase):
    def test_from_env(self) -> None:
        old = dict(os.environ)
        try:
            os.environ["OLLAMA_HOST"] = "http://example:11434"
            os.environ["OLLAMA_MODEL"] = "my-model"
            os.environ["AGENT_MEMORY_DIR"] = ".mem"
            os.environ["LOG_LEVEL"] = "DEBUG"
            os.environ["API_HOST"] = "0.0.0.0"
            os.environ["API_PORT"] = "9999"
            os.environ["TELEGRAM_TOKEN"] = "token"
            cfg = Config.from_env()
        finally:
            os.environ.clear()
            os.environ.update(old)

        self.assertEqual(cfg.ollama_host, "http://example:11434")
        self.assertEqual(cfg.ollama_model, "my-model")
        self.assertEqual(cfg.memory_dir, ".mem")
        self.assertEqual(cfg.log_level, "DEBUG")
        self.assertEqual(cfg.api_host, "0.0.0.0")
        self.assertEqual(cfg.api_port, 9999)
        self.assertEqual(cfg.telegram_token, "token")

    def test_from_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "cfg.json"
            p.write_text(
                json.dumps(
                    {
                        "ollama_host": "http://x",
                        "ollama_model": "m",
                        "memory_dir": ".m",
                        "log_level": "INFO",
                        "api_host": "127.0.0.1",
                        "api_port": 8081,
                        "telegram_token": None,
                    }
                ),
                encoding="utf-8",
            )
            cfg = Config.from_file(p)
            self.assertEqual(cfg.ollama_host, "http://x")
            self.assertEqual(cfg.api_port, 8081)

    def test_load_prefers_config_file_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cwd = os.getcwd()
            try:
                os.chdir(td)
                Path("config.json").write_text(json.dumps({"ollama_model": "from-file"}), encoding="utf-8")
                old = dict(os.environ)
                os.environ.pop("OLLAMA_MODEL", None)
                cfg = Config.load()
            finally:
                os.environ.clear()
                os.environ.update(old)
                os.chdir(cwd)
        self.assertEqual(cfg.ollama_model, "from-file")
