from run_once import parse_internaldate, select_window


def test_select_window_skips_old_and_stops_at_first_old():
    ages = [
        (b"9", 5),       # new -> relay
        (b"8", None),    # unreadable date -> skip
        (b"7", 100),     # old -> stop here
        (b"6", 50),      # older -> never evaluated
    ]
    assert select_window(ages, max_age_seconds=60) == [b"9"]


def test_select_window_empty_when_all_old():
    ages = [(b"5", 9999), (b"4", 5000)]
    assert select_window(ages, max_age_seconds=60) == []


def test_select_window_all_new_returns_oldest_first():
    ages = [(b"3", 10), (b"2", 20), (b"1", 30)]
    assert select_window(ages, max_age_seconds=60) == [b"1", b"2", b"3"]


def test_select_window_boundary_inclusive():
    ages = [(b"2", 61), (b"1", 60)]
    assert select_window(ages, max_age_seconds=60) == []


def test_parse_internaldate():
    raw = b'115 (INTERNALDATE " 2-Oct-2026 10:30:00 +0000")'
    ts = parse_internaldate(raw)
    assert ts is not None
    import email.utils
    expected = email.utils.parsedate_to_datetime(
        "2-Oct-2026 10:30:00 +0000"
    ).timestamp()
    assert abs(ts - expected) < 1
    assert parse_internaldate(b"no date here") is None


if __name__ == "__main__":
    test_select_window_skips_old_and_stops_at_first_old()
    test_select_window_empty_when_all_old()
    test_select_window_all_new_returns_oldest_first()
    test_select_window_boundary_inclusive()
    test_parse_internaldate()
    print("ALL RUN_ONCE TESTS PASSED")
