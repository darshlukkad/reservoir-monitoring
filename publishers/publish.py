"""Simple CSV-to-MQTT publisher.

This module exposes a small helper `rows_from_csv(file_path, reservoir)` which
yields JSON payload dictionaries for each CSV row. The `publish_file` function
uses that helper to publish messages to MQTT. Splitting the logic makes it
easy to test CSV→JSON conversion without requiring an MQTT broker.

Usage:
  python publish.py --file ../data/Shasta_WML_sample.csv --reservoir SHASTA

Published topic: {RESERVOIR}/WML
"""
import argparse
import csv
import json
import time
from datetime import datetime


def rows_from_csv(file_path, reservoir):
    """Yield payload dicts for each CSV row.

    Args:
        file_path: path to CSV file containing Date,TAF columns
        reservoir: reservoir id string (e.g. SHASTA)

    Yields:
        dict with keys: reservoir_id, date (ISO YYYY-MM-DD), taf (float)
    """
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Normalize date to ISO (accept MM/DD/YYYY)
            dt = datetime.strptime(row['Date'], '%m/%d/%Y').date().isoformat()
            yield {
                'reservoir_id': reservoir,
                'date': dt,
                'taf': float(row['TAF'])
            }


def publish_file(broker, port, file_path, reservoir, delay=0.01):
    # Import paho here to make the module importable even if paho isn't installed
    # (useful for tests that only use rows_from_csv).
    import paho.mqtt.client as mqtt

    client = mqtt.Client()
    client.connect(broker, port, keepalive=60)

    topic = f"{reservoir}/WML"
    for payload in rows_from_csv(file_path, reservoir):
        client.publish(topic, json.dumps(payload))
        print(f"Published to {topic}: {payload}")
        time.sleep(delay)

    client.disconnect()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--broker', default='localhost')
    parser.add_argument('--port', type=int, default=1883)
    parser.add_argument('--file', required=True)
    parser.add_argument('--reservoir', required=True)
    parser.add_argument('--delay', type=float, default=0.01)
    args = parser.parse_args()
    publish_file(args.broker, args.port, args.file, args.reservoir, args.delay)
