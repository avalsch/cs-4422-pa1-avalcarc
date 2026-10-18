from pathlib import Path

import pytest

from crawl_config import Config


def test_config_post_init_rejects_bad_budget():
    with pytest.raises(ValueError):
        Config(seeds=[], budget=0, delay=1.0, output_dir=Path("out"))


def test_config_post_init_rejects_negative_delay():
    with pytest.raises(ValueError):
        Config(seeds=[], budget=1, delay=-1.0, output_dir=Path("out"))
