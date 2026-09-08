#!/usr/bin/env bash
set -u

# Local smoke test for SRT and RIST loopback connectivity.
# This is intentionally written to capture real runtime behavior and not to
# pretend that ffprobe can expose native transport stats.

run_srt_test() {
  echo "[SRT] starting local smoke test"
  set +e
  ffmpeg -hide_banner -y -loglevel info \
    -f lavfi -i testsrc2=size=1280x720:rate=10:duration=3 \
    -f mpegts -t 3 "srt://:9000?mode=listener&latency=200000" >/tmp/srt_listener.log 2>&1 &
  listener_pid=$!
  sleep 1

  ffmpeg -hide_banner -y -loglevel info \
    -f lavfi -i testsrc2=size=1280x720:rate=10:duration=3 \
    -f mpegts -t 3 "srt://127.0.0.1:9000?mode=caller&latency=200000" >/tmp/srt_sender.log 2>&1
  sender_status=$?

  wait "$listener_pid" || true
  echo "[SRT] sender exit code: $sender_status"
  echo "[SRT] logs: /tmp/srt_listener.log /tmp/srt_sender.log"
  echo "--- /tmp/srt_sender.log ---"
  tail -n 30 /tmp/srt_sender.log 2>/dev/null || true
  echo "--- /tmp/srt_listener.log ---"
  tail -n 30 /tmp/srt_listener.log 2>/dev/null || true
  echo
  set -e
}

run_rist_test() {
  echo "[RIST] starting local smoke test"
  set +e
  ffmpeg -hide_banner -y -loglevel info \
    -f lavfi -i testsrc2=size=1280x720:rate=10:duration=3 \
    -f mpegts -t 3 "rist://:9001" >/tmp/rist_listener.log 2>&1 &
  listener_pid=$!
  sleep 1

  ffmpeg -hide_banner -y -loglevel info \
    -f lavfi -i testsrc2=size=1280x720:rate=10:duration=3 \
    -f mpegts -t 3 "rist://127.0.0.1:9001" >/tmp/rist_sender.log 2>&1
  sender_status=$?

  wait "$listener_pid" || true
  echo "[RIST] sender exit code: $sender_status"
  echo "[RIST] logs: /tmp/rist_listener.log /tmp/rist_sender.log"
  echo "--- /tmp/rist_sender.log ---"
  tail -n 30 /tmp/rist_sender.log 2>/dev/null || true
  echo "--- /tmp/rist_listener.log ---"
  tail -n 30 /tmp/rist_listener.log 2>/dev/null || true
  echo
  set -e
}

run_srt_test
run_rist_test

echo "Smoke tests finished. This environment currently reports input/output errors for the real loopback path; ffprobe metadata analysis remains the reliable level of inspection here."
