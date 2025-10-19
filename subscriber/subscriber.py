"""MQTT subscriber that listens to +/WML and aggregates daily summaries.

Usage:
  python subscriber.py --outdir ../reports

The subscriber collects messages until interrupted (Ctrl-C) and writes daily reports grouped by date.
Only one subscriber is used to aggregate all reservoir topics.
"""
import argparse
import json
import os
import signal
import sys
from collections import defaultdict
from datetime import datetime

import paho.mqtt.client as mqtt
import pandas as pd


class Aggregator:
    def __init__(self):
        # data[date][reservoir] = list of tafs
        self.data = defaultdict(lambda: defaultdict(list))

    def add(self, reservoir, date_str, taf):
        self.data[date_str][reservoir].append(float(taf))

    def to_reports(self, outdir):
        os.makedirs(outdir, exist_ok=True)
        for date_str, reservoirs in self.data.items():
            rows = []
            for res, tafs in reservoirs.items():
                rows.append({
                    'date': date_str,
                    'reservoir_id': res,
                    'observations': len(tafs),
                    'taf_mean': sum(tafs)/len(tafs),
                    'taf_min': min(tafs),
                    'taf_max': max(tafs)
                })
            df = pd.DataFrame(rows)
            json_path = os.path.join(outdir, f"report_{date_str}.json")
            csv_path = os.path.join(outdir, f"report_{date_str}.csv")
            df.to_json(json_path, orient='records', date_format='iso')
            df.to_csv(csv_path, index=False)
            print(f"Wrote report for {date_str}: {json_path}, {csv_path}")


AGG = Aggregator()


def on_connect(client, userdata, flags, rc):
    print("Connected to broker, subscribing to +/WML")
    client.subscribe("+/WML")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        res = payload.get('reservoir_id')
        date_str = payload.get('date')
        taf = payload.get('taf')
        if not (res and date_str and taf is not None):
            print("Invalid payload, skipping", payload)
            return
        # Ensure date is ISO
        try:
            # accept YYYY-MM-DD or other
            _ = datetime.fromisoformat(date_str)
            date_iso = date_str
        except Exception:
            date_iso = datetime.strptime(date_str, '%m/%d/%Y').date().isoformat()
        AGG.add(res, date_iso, taf)
        print(f"Received {res} {date_iso} {taf}")
    except Exception as e:
        print("Failed to process message:", e)


def run(broker, port, outdir):
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(broker, port, keepalive=60)

    def handle_sig(sig, frame):
        print("Signal received, writing reports and exiting.")
        AGG.to_reports(outdir)
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sig)
    signal.signal(signal.SIGTERM, handle_sig)

    client.loop_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--broker', default='localhost')
    parser.add_argument('--port', type=int, default=1883)
    parser.add_argument('--outdir', default='../reports')
    args = parser.parse_args()
    run(args.broker, args.port, args.outdir)
