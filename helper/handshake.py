#!/usr/bin/env python3
"""STEP03 P0 stand-alone helper handshake. No media writes or FFmpeg execution."""
import argparse
import json
import platform


def response():
    return {
        "protocol": "AIJSON_STEP03_P0",
        "status": "OK",
        "helper_version": "0.0.3",
        "python_version": platform.python_version(),
        "capabilities": {
            "schema_validation": False,
            "media_probe": False,
            "ffmpeg_prerender": False,
            "premiere_mutation": False,
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", action="store_true", required=True)
    args = parser.parse_args(argv)
    if args.probe:
        print(json.dumps(response(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
