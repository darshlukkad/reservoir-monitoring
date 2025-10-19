import sys
from pathlib import Path

# Ensure project root is on sys.path so package imports work when running the file
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from publishers.publish import rows_from_csv


def test_rows_from_csv():
    rows = list(rows_from_csv('data/Shasta_WML_sample.csv', 'SHASTA'))
    assert len(rows) == 9
    first = rows[0]
    assert first['reservoir_id'] == 'SHASTA'
    assert first['date'] == '2024-09-29'
    assert first['taf'] == 2720.0


if __name__ == '__main__':
    test_rows_from_csv()
    print('test_rows_from_csv passed')
