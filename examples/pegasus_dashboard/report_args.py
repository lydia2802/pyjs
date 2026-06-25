"""Flattens the JSON report into the plain str/int/list[str] arguments dashboard.main() expects.

dashboard.main() is transpiled to JavaScript by pyjs, whose transpiler only supports
a small subset of Python builtins, so any list/dict shaping has to happen here in
plain Python before main() is ever called.
"""


def build_main_args(report: dict) -> tuple:
    android = report["pegasus"]["android_full"]
    ios = report["pegasus"]["ios_full"]
    comparison = report["pegasus"]["comparison"]
    kev = report["kev"]

    top_vendors = list(kev["top_vendors"].items())[:5]
    vendor_labels = [f"{name}: {count}" for name, count in top_vendors]

    return (
        ", ".join(android["platforms"]) or "-",
        android["technique_count"],
        android["subtechnique_count"],
        ", ".join(ios["platforms"]) or "-",
        ios["technique_count"],
        ios["subtechnique_count"],
        comparison["shared_count"],
        comparison["android_only_count"],
        comparison["ios_only_count"],
        kev["record_count"],
        vendor_labels,
    )
