from analyze import q3_errors


def test_q3_ranks_by_count_then_name():
    log = [
        {"event": "error", "failure_reason": "timeout"},
        {"event": "error", "failure_reason": "timeout"},
        {"event": "error", "failure_reason": "http_error"},
        {"event": "error", "failure_reason": "connection_error"},
        {"event": "fetch", "failure_reason": None},
    ]

    assert q3_errors(log) == (
        "## Q3: most common fetch failures\n"
        "\n"
        "| rank | failure_reason | count |\n"
        "| --- | --- | --- |\n"
        "| 1 | timeout | 2 |\n"
        "| 2 | connection_error | 1 |\n"
        "| 3 | http_error | 1 |\n"
        "\n"
        "Total: 4 errors."
    )


def test_q3_limits_to_five_rows():
    log = [{"event": "error", "failure_reason": f"r{i}"} for i in range(7)]

    text = q3_errors(log)

    assert "| 5 | r4 | 1 |" in text
    assert "r5" not in text


def test_q3_with_no_errors():
    assert q3_errors([]) == (
        "## Q3: most common fetch failures\n"
        "\n"
        "| rank | failure_reason | count |\n"
        "| --- | --- | --- |\n"
        "\n"
        "Total: 0 errors."
    )
