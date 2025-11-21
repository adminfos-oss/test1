# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
from pathlib import Path

# Добавьте путь к вашему коду, чтобы Sphinx видел модули
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# или если у вас пакет лежит в подпапке, например src/mypackage
# sys.path.insert(0, os.path.abspath('../src'))

# Чтобы модели Django красиво отображались
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "f_app.settings")
import django

django.setup()


# Включите автодокументацию модулей
extensions = [
    "sphinx.ext.autodoc",  # автоматическая документация из docstrings
    "sphinx.ext.napoleon",  # поддержка Google/NumPy стиля docstrings
    "sphinx.ext.viewcode",  # ссылки на исходный код
    "sphinx.ext.autosummary",  # генерация сводных таблиц
    "myst_parser",  # поддержка Markdown
]

# Главный файл — index (без расширения)
master_doc = "index"
source_suffix = ".rst"

# Это ключевые настройки — делают всё автоматом
autosummary_generate = True  # генерирует .rst для всех модулей автоматически
autoclass_content = "both"  # docstring класса + docstring __init__
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "private-members": False,
    "special-members": "__str__",
    "inherited-members": True,
    "show-inheritance": True,
}


# Тема
html_theme = "sphinx_rtd_theme"

# Поддержка русского языка
language = "ru"

project = "iShop"
copyright = "2025, Igor K."
author = "Igor K."
release = "1.0.1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

templates_path = ["_templates"]

exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    ".venv",
    "venv",
    "**/.git",
    "**/__pycache__",
    "**/.pytest_cache",
    "**/*migrations*",  # ← миграции Django
    "**/*tests*",  # ← тесты (если не нужны в docs)
    "**/*management*",
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output


html_static_path = ["_static"]
