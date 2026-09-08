#!/usr/bin/env python3
"""Simple SRT/RIST/URL analyser using ffprobe.

This provides a lightweight inspector for SRT, RIST, and other URL-based inputs.
It queries ffprobe for format and stream metadata, and can optionally include
frame- and packet-level output.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from urllib.parse import parse_qs, urlparse
from typing import Any, Dict, List, Optional


def ffprobe_json(url: str, args: List[str]) -> Optional[Dict[str, Any]]:
    cmd = ["ffprobe", "-v", "error", "-of", "json"] + args + [url]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, encoding="utf-8")
        return json.loads(out)
    except subprocess.CalledProcessError as exc:
        print(f"ffprobe failed: {exc}")
        return None
    except json.JSONDecodeError as exc:
        print(f"failed to decode ffprobe output as JSON: {exc}")
        return None


def parse_transport_url(url: str) -> Dict[str, Any]:
    parsed = urlparse(url)
    query = {key: values[-1] for key, values in parse_qs(parsed.query, keep_blank_values=True).items()}
    protocol = (parsed.scheme or "").lower()
    transport = {
        "protocol": protocol,
        "host": parsed.hostname,
        "port": parsed.port,
        "path": parsed.path,
        "query": query,
        "supports_live_transport_stats": False,
        "capabilities": {
            "runtime_stats": False,
            "rtt": False,
            "retransmissions": False,
            "packet_loss": False,
            "jitter": False,
        },
        "limitations": [
            "Live RTT, retransmission, and packet-loss counters are not available in this ffprobe-based inspector.",
            "Native libsrt/librist stats access is required to expose true live transport counters."
        ],
        "notes": [],
    }

    if protocol == "srt":
        transport["notes"].append("This build can open SRT URLs through FFmpeg, but runtime SRT stats are not exposed without a native libsrt binding.")
        transport["notes"].append("URL options such as mode, latency, streamid, nakreport, tlpktdrop, and encryption settings are reported when present.")
        transport["configured_options"] = {k: query[k] for k in sorted(query)}
    elif protocol == "rist":
        transport["notes"].append("This build can open RIST URLs through FFmpeg, but runtime librist transport stats are not exposed here.")
        transport["configured_options"] = {k: query[k] for k in sorted(query)}
    else:
        transport["notes"].append("URL is not using the SRT or RIST transport protocol.")

    return transport


def analyze_url(url: str, show_frames: bool = False, show_packets: bool = False) -> None:
    data = ffprobe_json(url, ["-show_format", "-show_streams"]) or {}
    out = {
        "url": url,
        "transport": parse_transport_url(url),
        "format": data.get("format"),
        "streams": data.get("streams", []),
    }

    if show_frames:
        frames = ffprobe_json(url, ["-show_frames"]) or {}
        out["frames"] = frames.get("frames", [])

    if show_packets:
        packets = ffprobe_json(url, ["-show_packets"]) or {}
        out["packets"] = packets.get("packets", [])

    print(json.dumps(out, indent=2))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="SRT/RIST/URL analyser using ffprobe")
    parser.add_argument("urls", nargs="+", help="SRT/RIST/RTMP/HTTP/etc. URL(s) to analyze")
    parser.add_argument("--frames", action="store_true", help="Attempt to show frame-level info")
    parser.add_argument("--packets", action="store_true", help="Attempt to show packet-level info")
    args = parser.parse_args(argv)

    for url in args.urls:
        try:
            analyze_url(url, show_frames=args.frames, show_packets=args.packets)
        except KeyboardInterrupt:
            print("Interrupted by user")
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
