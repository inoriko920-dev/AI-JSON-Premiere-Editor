"""Deterministic four-track *candidate*, not an executable Premiere plan.

V1 looping background; V2/V3 image occurrences; A1 narration. Actual FFprobe
duration metadata is converted conservatively to whole frames at 30 fps.
No crop/FX, source decoder, linked-background-audio isolation or host gate is
approved by this module. The sequence always remains non-executable.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .draft_compiler import build_draft, DraftCompileError
from .host_ticks import frame_to_ticks, HostTickDraftError

_DIGEST = re.compile(r"[a-f0-9]{64}\Z")
_TRACKS = {"V1": 0, "V2": 1, "V3": 2, "A1": 0}


class TrackPlanError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _frames(duration_ms: int, fps_num: int, fps_den: int) -> int:
    if (type(duration_ms) is not int or duration_ms <= 0 or
            type(fps_num) is not int or fps_num <= 0 or
            type(fps_den) is not int or fps_den <= 0):
        raise TrackPlanError("E_TRACK_SOURCE_DURATION_UNVERIFIED")
    # floor rather than rounding up and accidentally requesting source past EOF
    return (duration_ms * fps_num) // (1000 * fps_den)


def compile_four_track_candidate(
    edit: dict[str, Any], animation: dict[str, Any], *,
    ticks_per_frame: str,
    audio_duration_ms: int, background_duration_ms: int,
    media_snapshot: dict[str, Any]
) -> dict[str, Any]:
    try:
        draft=build_draft(edit,animation)
        total=draft["total_frames"]
        frame_to_ticks(total,ticks_per_frame)
    except (DraftCompileError,HostTickDraftError) as ex:
        raise TrackPlanError("E_TRACK_SOURCE_CONTRACT_INVALID") from ex
    if (type(media_snapshot) is not dict or
            media_snapshot.get("schema_version")!="verified-media-snapshot-v1" or
            media_snapshot.get("status")!="CANDIDATE_NOT_AUTHORIZED" or
            media_snapshot.get("can_import") is not False or
            media_snapshot.get("can_assemble") is not False or
            not isinstance(media_snapshot.get("inventory_sha256"),str) or
            _DIGEST.fullmatch(media_snapshot["inventory_sha256"]) is None or
            type(media_snapshot.get("import_count")) is not int or
            media_snapshot["import_count"]!=len(edit["assets"])+2):
        raise TrackPlanError("E_TRACK_MEDIA_SNAPSHOT_UNVERIFIED")
    canvas=edit["canvas"]
    fps_num, fps_den=canvas["fps_num"],canvas["fps_den"]
    if (fps_num!=30 or fps_den!=1 or
            edit["sources"]["background"].get("audio_policy")!="MUTE" or
            edit["render"].get("audio_policy")!="NARRATION_ONLY"):
        raise TrackPlanError("E_TRACK_AUDIO_POLICY_UNVERIFIED")
    bg_frames=_frames(background_duration_ms,fps_num,fps_den)
    audio_frames=_frames(audio_duration_ms,fps_num,fps_den)
    if bg_frames<1:
        raise TrackPlanError("E_TRACK_BACKGROUND_TOO_SHORT")
    if audio_frames<total:
        raise TrackPlanError("E_TRACK_NARRATION_TOO_SHORT")
    if len(draft["asset_placements"]) != media_snapshot["import_count"]-2:
        # An asset ID can repeat across scenes. The media snapshot contains
        # UNIQUE assets while the timeline contains occurrences.
        asset_count=len(edit["assets"])
        if len(draft["asset_placements"])<asset_count:
            raise TrackPlanError("E_TRACK_VISUAL_INSTANCES_MISSING")
    placements=[]
    def append(source_key: str, track: str, start: int, end: int,
               source_in: int, item_id: str, instance_key: str) -> None:
        if start<0 or end<=start or source_in<0:
            raise TrackPlanError("E_TRACK_RANGE_INVALID")
        placements.append({
            "instance_key":instance_key,
            "item_id":item_id, "target_track":track,
            "zero_based_track_index":_TRACKS[track],
            "start_frame":start,"end_frame":end,
            "start_ticks":frame_to_ticks(start,ticks_per_frame),
            "end_ticks":frame_to_ticks(end,ticks_per_frame),
            "source_in_frame":source_in,
            "source_out_frame":source_in+(end-start),
            "source_policy":source_key,
            "media_readback":"NOT_TESTED"
        })
    frame=0
    i=0
    while frame<total:
        next_end=min(total,frame+bg_frames)
        append("BACKGROUND_VIDEO_ONLY_UNVERIFIED","V1",frame,next_end,0,
               "SOURCE_BACKGROUND","BG_"+str(i))
        frame=next_end
        i+=1
        if i>100000:
            raise TrackPlanError("E_TRACK_RESOURCE_LIMIT")
    append("NARRATION_AUDIO","A1",0,total,0,"SOURCE_AUDIO","NARRATION_0")
    for x in draft["asset_placements"]:
        append("IMAGE_FX_AND_LAYOUT_UNVERIFIED",x["target_track"],
               x["start_frame"],x["end_frame"],0,
               "ASSET_"+x["asset_id"],x["instance_key"])
    placements.sort(key=lambda x:(
        x["start_frame"],0 if x["target_track"]=="V1" else
        1 if x["target_track"]=="V2" else 2 if x["target_track"]=="V3" else 3,
        x["instance_key"]))
    by_track={"V1":[],"V2":[],"V3":[],"A1":[]}
    for p in placements:
        by_track[p["target_track"]].append((p["start_frame"],p["end_frame"]))
    for track,spans in by_track.items():
        spans.sort()
        for k in range(1,len(spans)):
            if spans[k][0]<spans[k-1][1]:
                raise TrackPlanError("E_TRACK_OVERLAP")
        if track in ("V1","A1") and (
                spans[0][0]!=0 or spans[-1][1]!=total or
                any(a[1]!=b[0] for a,b in zip(spans,spans[1:]))):
            raise TrackPlanError("E_TRACK_COVERAGE_INCOMPLETE")
    canonical={"schema_version":"track-placement-candidate-v1",
       "project_id":edit["project_id"],"source_digest":draft["operation_digest_sha256"],
       "media_digest":media_snapshot["inventory_sha256"],
       "ticks_per_frame":ticks_per_frame,"total_frames":total,
       "placements":placements}
    digest=hashlib.sha256(json.dumps(
        canonical,sort_keys=True,separators=(",",":"),ensure_ascii=False,
        allow_nan=False).encode("utf-8")).hexdigest()
    return {
        **canonical,
        "status":"CANDIDATE_NOT_EXECUTABLE",
        "can_import":False,"can_assemble":False,
        "operation_sha256":digest,
        "track_counts":{k:len(v) for k,v in by_track.items()},
        "pending_requirements":[
            "APPROVED_LAYOUT_CROP_AND_BOTH_ANIMATION",
            "SOURCE_IMAGE_DURATION_AND_VIDEO_DECODER",
            "BACKGROUND_AUDIO_MUTE_ISOLATION",
            "PREMIERE_FRAME_TRIM_AND_TIMEBASE_READBACK",
            "REHASH_MEDIA_AT_HOST_TRANSACTION",
            "OWNER_HOST_CAPABILITY_AND_PREFLIGHT_APPROVAL"
        ]
    }
