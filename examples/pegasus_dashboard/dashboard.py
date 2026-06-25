from pyjs import js
from pyjs.domx import div, h1, p, tw


@js
def stat_card(title: str, value: str):
    return div(tw("bg-white shadow-md rounded-xl p-4"),
        p(tw("text-sm text-gray-500"), title),
        div(tw("text-2xl font-bold"), value),
    )


@js
def platform_section(title: str, platforms: str, technique_count: int, subtechnique_count: int):
    return div(tw("bg-white shadow-md rounded-xl p-6 space-y-4"),
        h1(tw("text-xl font-semibold"), title),
        div(tw("grid grid-cols-3 gap-4"),
            stat_card("Total teknik", str(technique_count)),
            stat_card("Teknik bersubteknik", str(subtechnique_count)),
            stat_card("Platform", platforms),
        ),
    )


@js
def comparison_section(shared_count: int, android_only_count: int, ios_only_count: int):
    return div(tw("bg-white shadow-md rounded-xl p-6 space-y-4"),
        h1(tw("text-xl font-semibold"), "Perbandingan Android vs iOS"),
        div(tw("grid grid-cols-3 gap-4"),
            stat_card("Teknik sama", str(shared_count)),
            stat_card("Hanya Android", str(android_only_count)),
            stat_card("Hanya iOS", str(ios_only_count)),
        ),
    )


@js
def kev_section(record_count: int, vendor_labels: list[str]):
    rows = [p(tw("text-sm border-b border-gray-100 py-1"), label) for label in vendor_labels]
    return div(tw("bg-white shadow-md rounded-xl p-6 space-y-4"),
        h1(tw("text-xl font-semibold"), "Known Exploited Vulnerabilities (CISA KEV)"),
        stat_card("Jumlah record", str(record_count)),
        div(tw("space-y-1"),
            p(tw("text-sm text-gray-500 mb-1"), "Top 5 vendor terdampak"),
            *rows,
        ),
    )


def main(
    android_platforms: str,
    android_technique_count: int,
    android_subtechnique_count: int,
    ios_platforms: str,
    ios_technique_count: int,
    ios_subtechnique_count: int,
    shared_count: int,
    android_only_count: int,
    ios_only_count: int,
    kev_record_count: int,
    vendor_labels: list[str],
):
    return div(tw("bg-gray-100 min-h-screen p-8 space-y-6 font-sans"),
        h1(tw("text-3xl font-bold mb-2"), "Pegasus / ATT&CK Threat Intel Dashboard"),
        p(tw("text-gray-500 mb-4"), "Data dirangkum oleh Python, ditampilkan via pyjs (di-transpile ke JavaScript)."),
        platform_section("Pegasus - Android (S0316)", android_platforms, android_technique_count, android_subtechnique_count),
        platform_section("Pegasus - iOS (S0289)", ios_platforms, ios_technique_count, ios_subtechnique_count),
        comparison_section(shared_count, android_only_count, ios_only_count),
        kev_section(kev_record_count, vendor_labels),
    )


if __name__ == "__main__":
    import json
    from pathlib import Path
    from pyjs.server import serve
    from report_args import build_main_args

    report_file = Path(__file__).resolve().parent / "output" / "ringkasan_data.json"
    with report_file.open("r", encoding="utf-8") as file:
        report = json.load(file)
    serve(Path(__file__).stem, "", main.__name__, *build_main_args(report))
