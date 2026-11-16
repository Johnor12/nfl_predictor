# START
# The cache's refresh rules, against a fake nflverse (no network, no real cache): a fresh file is read from
# the cache; the current season's refreshes once stale, a past season's doesn't; offline, the cached copy is
# used; an unpublished file is asked for again once its marker is stale.
# END
import io
import os
import time
import urllib.error

import pandas as pd
import pytest

from shared.nflverse import download
from shared.nflverse.download import MAX_AGE, SEASONS

CURRENT, PAST = SEASONS[-1], SEASONS[0]


@pytest.fixture
def nflverse(tmp_path, monkeypatch):
    """The files the fake nflverse publishes ({url: DataFrame}; a url left out is a 404) and the requests."""
    site = {"published": {}, "requests": [], "offline": False}

    def urlopen(request, timeout=None):
        site["requests"].append(request.full_url)
        if site["offline"]:
            raise urllib.error.URLError("offline")
        if request.full_url not in site["published"]:
            raise urllib.error.HTTPError(request.full_url, 404, "Not Found", {}, None)  # type: ignore[arg-type]
        return io.BytesIO(site["published"][request.full_url].to_parquet())

    monkeypatch.setattr(download, "CACHE", tmp_path)
    monkeypatch.setattr(download, "_FAILED", set())
    monkeypatch.setattr(download.urllib.request, "urlopen", urlopen)
    return site


def _publish(site, name, season, frame):
    site["published"][download.FILES[name].format(season=season)] = frame


def _age(name, season, suffix=".parquet"):
    path = download.CACHE / download.FILES[name].format(season=season).rsplit("/", 1)[1]
    old = time.time() - MAX_AGE - 60
    os.utime(path.with_suffix(suffix), (old, old))


def _weeks(name, season):
    frame = download.load(name, season)
    assert frame is not None
    return frame.week.tolist()


def test_a_fresh_file_is_read_from_the_cache(nflverse):
    _publish(nflverse, "pbp", CURRENT, pd.DataFrame({"week": [1]}))
    download.load("pbp", CURRENT)
    assert _weeks("pbp", CURRENT) == [1]
    assert len(nflverse["requests"]) == 1


def test_the_current_season_refreshes_once_stale(nflverse):
    _publish(nflverse, "pbp", CURRENT, pd.DataFrame({"week": [1]}))
    download.load("pbp", CURRENT)
    _publish(nflverse, "pbp", CURRENT, pd.DataFrame({"week": [1, 2]}))
    _age("pbp", CURRENT)
    assert _weeks("pbp", CURRENT) == [1, 2]


def test_a_past_season_is_not_refreshed(nflverse):
    _publish(nflverse, "pbp", PAST, pd.DataFrame({"week": [1]}))
    download.load("pbp", PAST)
    _age("pbp", PAST)
    download.load("pbp", PAST)
    assert len(nflverse["requests"]) == 1
    download.load("pbp", PAST, refresh=True)
    assert len(nflverse["requests"]) == 2


def test_offline_the_cached_copy_is_used(nflverse):
    _publish(nflverse, "pbp", CURRENT, pd.DataFrame({"week": [1]}))
    download.load("pbp", CURRENT)
    _age("pbp", CURRENT)
    nflverse["offline"] = True
    assert _weeks("pbp", CURRENT) == [1]
    download.load("pbp", CURRENT)  # not asked again in the same process
    assert len(nflverse["requests"]) == 2
    with pytest.raises(urllib.error.URLError):  # nothing cached to fall back on
        download.load("rosters", CURRENT)


def test_an_unpublished_file_is_asked_for_again_once_stale(nflverse):
    assert download.load("participation", CURRENT) is None
    assert download.load("participation", CURRENT) is None
    assert len(nflverse["requests"]) == 1
    _publish(nflverse, "participation", CURRENT, pd.DataFrame({"week": [1]}))
    _age("participation", CURRENT, ".missing")
    assert _weeks("participation", CURRENT) == [1]
    assert not any(download.CACHE.glob("*.missing"))
