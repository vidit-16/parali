from datetime import date

import pytest

from parali import firms

CSV = """latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight
29.80000,76.40000,330.1,0.4,0.4,2025-11-02,0805,N,VIIRS,n,2,290.0,5.2,D
29.81000,76.40000,340.0,0.4,0.4,2025-11-05,0805,N,VIIRS,h,2,291.0,9.1,D
"""


class FakeSession:
    def __init__(self):
        self.urls = []

    def get(self, url, timeout):
        self.urls.append(url)

        class R:
            text = CSV

            def raise_for_status(self):
                pass
        return R()


def test_parse():
    fires = firms.parse_csv(CSV, "VIIRS_SNPP_SP")
    assert len(fires) == 2
    assert fires[0].date == date(2025, 11, 2) and fires[0].frp == pytest.approx(5.2)


def test_fetch_chunks_by_max_days():
    s = FakeSession()
    firms.fetch((76, 29, 77, 30), date(2025, 10, 1), date(2025, 10, 12), sources=("X",), key="k", session=s)
    assert [u.rsplit("/", 2)[-2:] for u in s.urls] == [["5", "2025-10-01"], ["5", "2025-10-06"], ["2", "2025-10-11"]]


def test_fires_near_radius_and_dates():
    fires = firms.parse_csv(CSV, "S")
    assert len(firms.fires_near(fires, 29.8, 76.4, 500)) == 1      # second point is ~1.1 km north
    assert len(firms.fires_near(fires, 29.8, 76.4, 1500)) == 2
    assert len(firms.fires_near(fires, 29.8, 76.4, 1500, start=date(2025, 11, 3))) == 1


def test_save_load(tmp_path):
    fires = firms.parse_csv(CSV, "S")
    firms.save(fires, tmp_path / "f.csv")
    assert firms.load(tmp_path / "f.csv") == fires


def test_missing_key(monkeypatch):
    monkeypatch.delenv("FIRMS_MAP_KEY", raising=False)
    with pytest.raises(RuntimeError):
        firms.map_key()
