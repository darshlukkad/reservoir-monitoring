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

MQTT overview — What is MQTT? and Architecture
-----------------------------------------------
What is MQTT?
^^^^^^^^^^^^^
MQTT (Message Queuing Telemetry Transport) is a lightweight publish/subscribe messaging protocol designed for low-bandwidth, high-latency, or unreliable networks. It's widely used in IoT and telemetry because of its small footprint, simplicity, and built-in features like topic-based routing, quality-of-service (QoS) levels, retained messages, and Last Will and Testament (LWT).

Key MQTT concepts used in this demo:
- Broker: central server that receives messages from publishers and forwards them to subscribers who have subscribed to matching topics. In this demo we use Eclipse Mosquitto as the broker.
- Topic: a hierarchical string used for routing messages. Publishers send messages to topics, and subscribers register interest in topics. Topics are not pre-created — they exist implicitly when messages are published.
- Publisher: a client that sends messages to a topic. In this project the CSV-to-MQTT scripts act as publishers.
- Subscriber: a client that subscribes to topics to receive messages (the subscriber in this project listens to `+/WML`).
- QoS (Quality of Service): determines delivery guarantees. MQTT defines three levels:
  - QoS 0: "at most once" — message is delivered zero or one time. Fastest, no guarantees.
  - QoS 1: "at least once" — message is retried until an acknowledgement is received; duplicates possible.
  - QoS 2: "exactly once" — two-phase handshake ensuring the message is delivered exactly once (heavier).
- Retained messages: a retained message on a topic means the broker stores the last retained message and delivers it immediately to newly subscribed clients.
- Last Will and Testament (LWT): a message the broker will publish on behalf of a client if it disconnects unexpectedly — useful for signaling failures.

Architecture for this assignment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The demo implements a simple, realistic architecture for collecting Water Mark Levels (WML) from multiple reservoirs and aggregating them centrally.

High-level ASCII diagram:

```
  +-----------+      Publish to      +----------+
  | Reservoir | --- RESERVOIR/WML -->|          |
  |  Sensor   |                      |  Broker  |-- subscribe to +/WML -->
  +-----------+                      |(Mosquitto)|                     
                                      +----------+                     
                                                                   +-----------+
                                                                   | Subscriber|
                                                                   | (Aggregator)
                                                                   +-----------+
                                                                         |
                                                                         | writes
                                                                         v
                                                                    +-----------+
                                                                    |  Reports  |
                                                                    |  (CSV/JSON)
                                                                    +-----------+
```

Explanation:
- Each reservoir sensor publishes a JSON payload with fields {reservoir_id, date, taf} to its topic `RESERVOIR_ID/WML` (e.g., `SHASTA/WML`).
- A single subscriber subscribes to the topic filter `+/WML`. The `+` wildcard matches a single level (the reservoir id). This means the subscriber receives messages from all reservoirs (single aggregator requirement).
- The subscriber aggregates messages by the `date` field and writes daily reports (CSV and JSON) to the `reports/` folder.

Topic conventions used
---------------------
- Topic format: `RESERVOIR_ID/WML` (uppercase reservoir id recommended). For example: `SHASTA/WML`, `OROVILLE/WML`, `SONOMA/WML`.
- Subscriber uses `+/WML` to receive messages from any reservoir.

Message format (JSON)
---------------------
Example message published by a sensor/publisher:

```json
{
  "reservoir_id": "SHASTA",
  "date": "2024-09-29",
  "taf": 2720.0
}
```

Operational considerations
-------------------------
- QoS: For this assignment we use QoS 0 in the demo (fast and simple). In production, consider QoS 1 to avoid missed readings, or QoS 2 if deduplication and strict exactly-once delivery are required.
- Retained messages: Use retained messages if you want new subscribers to automatically receive the last known reading for a reservoir when they connect.
- LWT: Configure LWT for sensors to notify the system if a sensor goes offline unexpectedly (e.g., publish to `reservoir/STATUS` with payload `OFFLINE`).
- Security: Mosquitto in this demo allows anonymous connections for simplicity. For real deployments, enable TLS and client authentication, and restrict access via usernames/certs and topic ACLs.
- Scalability: The broker is horizontally scalable via clustering solutions or by using a managed MQTT service. The single subscriber approach is fine for small-to-medium datasets; for high throughput, scale subscribers or add a message queue / stream processor.

Deployment notes
----------------
- Local demo: use `docker-compose up -d` to start Mosquitto and run the subscriber/publishers locally.
- Cloud or production: run a managed MQTT broker or a hardened Mosquitto deployment with TLS, authentication, monitoring, and persistence.

If you'd like, I can add:
- a diagram image (SVG/PNG) under `docs/` and include it in the README,
- example QoS changes in code and an option to publish with a chosen QoS,
- LWT and retained-message examples in the publishers, or
- a simple script to simulate sensor failures and LWT messages.

