Reservoir Monitoring Demo

This demo simulates three reservoir sensors (SHASTA, OROVILLE, SONOMA) that publish Water Mark Levels (WML) to MQTT topics and a single subscriber that aggregates daily reports.

Structure:
- `publishers/publish.py` : CSV-to-MQTT publisher. Publishes JSON messages to {RESERVOIR}/WML
- `subscriber/subscriber.py` : Single subscriber that listens to `+/WML`, aggregates by date, and writes reports to `reports/`.
- `data/` : Sample CSV files for three reservoirs.
- `docker-compose.yml` : Runs an Eclipse Mosquitto broker for local testing.
- `run_all.sh` : Helper script to start the broker, run the subscriber, and publish the sample data.

Data model (JSON published by publishers):
{
  "reservoir_id": "SHASTA",
  "date": "2024-09-29",
  "taf": 2720.0
}

How it works:
1. Start the Mosquitto broker:

```bash
docker-compose up -d
```

2. Start the subscriber (in another terminal):

```bash
python3 subscriber/subscriber.py --outdir reports
```

3. Run publishers to send sample data (or use `run_all.sh`):

```bash
python3 publishers/publish.py --file data/Shasta_WML_sample.csv --reservoir SHASTA
python3 publishers/publish.py --file data/Oroville_WML_sample.csv --reservoir OROVILLE
python3 publishers/publish.py --file data/Sonoma_WML_sample.csv --reservoir SONOMA
```

4. Stop the subscriber with Ctrl-C to generate reports. Reports will be written to `reports/` as CSV and JSON files, one per date.

Sample report excerpt (report_2024-09-29.csv):

```
date,reservoir_id,observations,taf_mean,taf_min,taf_max
2024-09-29,SHASTA,1,2720.0,2720.0,2720.0
2024-09-29,OROVILLE,1,2000.0,2000.0,2000.0
2024-09-29,SONOMA,1,192.0,192.0,192.0
```

Assumptions & notes:
- The demo uses a local Mosquitto broker via Docker. If you don't have Docker, you can point the scripts to a public broker.
- The subscriber aggregates messages in memory until it receives SIGINT/SIGTERM, then writes reports. For production, you'd want persistent storage and periodic flush.
- Only one subscriber is used to aggregate all reservoirs as required.

Next steps (optional):
- Add timestamps to messages and windowing logic for daily rollups.
- Use a database for long-term storage and scheduled report generation.
- Add unit tests and CI.

Verification / quick tests
-------------------------
1) Run the quick unit test that validates CSV → JSON payload conversion (no broker required):

```bash
cd reservoir_monitoring_demo
python3 tests/test_publish_rows.py
```

Expected output:

```
test_rows_from_csv passed
```

2) Run end-to-end locally (requires Docker)

```bash
# Start broker
docker-compose up -d

# In a terminal: start subscriber
python3 subscriber/subscriber.py --outdir reports

# In another terminal: publish sample data
python3 publishers/publish.py --file data/Shasta_WML_sample.csv --reservoir SHASTA
python3 publishers/publish.py --file data/Oroville_WML_sample.csv --reservoir OROVILLE
python3 publishers/publish.py --file data/Sonoma_WML_sample.csv --reservoir SONOMA

# Stop subscriber with Ctrl-C -> reports will be in ./reports
```

If you want, you can run the bundled helper which starts the broker, runs the subscriber, publishes the data, and stops the subscriber:

```bash
chmod +x run_all.sh
./run_all.sh
```

Troubleshooting
---------------
- If Python complains about missing modules, run:

```bash
pip install -r requirements.txt
```

- If Docker isn't available, change `--broker` to point at a public MQTT broker for testing (e.g., test.mosquitto.org) and run the publisher/subscriber commands without docker-compose.

