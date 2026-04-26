from __future__ import annotations

from app.dataset import generate_rows
from app.reporting import write_outputs
from app.uplift import estimate_uplift


def report() -> None:
    uplift_report = estimate_uplift(generate_rows())
    json_path, markdown_path = write_outputs(uplift_report)
    print(f"recommended_segment={uplift_report['top_recommended_segment']}")
    print(f"uplift_at_top_quartile={uplift_report['uplift_at_top_quartile']}")
    print(f"json_path={json_path}")
    print(f"markdown_path={markdown_path}")


def main() -> None:
    import sys

    if len(sys.argv) != 2 or sys.argv[1] != "report":
        raise SystemExit("usage: python3 -m app.cli report")

    report()


if __name__ == "__main__":
    main()
