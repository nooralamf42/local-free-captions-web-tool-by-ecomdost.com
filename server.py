"""Local web UI: drag & drop many videos, transcribe, edit, render several styles each. http://127.0.0.1:8765"""
import collections
import json
import os
import queue
import shutil
import threading
import time
import uuid
from pathlib import Path

from flask import Flask, Response, abort, jsonify, request, send_file, send_from_directory

from engine.ass import build_ass, resolve_style, to_srt, words_from_transcript
from engine import models, settings
from engine.edit import apply_edits
from engine.preview import style_clip, style_preview
from engine.render import make_proxy, nvenc_available, peaks as wave_peaks, render_frame, render_video
from engine.styles import TEMPLATE_GROUPS, DEFAULT_STYLE, STYLES
from engine.matte import make_matte
from engine.transcribe import cuda_ok, transcribe, unload as unload_models
from engine.util import OUTPUTS, ROOT, WORK, probe, safe_name

JOBS_DIR = WORK / "jobs"
JOBS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS.mkdir(parents=True, exist_ok=True)

TEMPLATE_ORDER = {}
for _ids in TEMPLATE_GROUPS.values():
    for _i in _ids:
        TEMPLATE_ORDER.setdefault(_i, len(TEMPLATE_ORDER))

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 ** 3  # 8 GB per request; no per-video or count limit otherwise

JOBS = {}
LOCK = threading.RLock()
Q = queue.Queue()


# ---------- job persistence ----------
def jdir(jid):
    return JOBS_DIR / jid


def save_job(j):
    with LOCK:
        data = {k: v for k, v in j.items() if k != "transcript"}
        (jdir(j["id"]) / "job.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        if j.get("transcript"):
            (jdir(j["id"]) / "transcript.json").write_text(json.dumps(j["transcript"], ensure_ascii=False), encoding="utf-8")


def load_jobs():
    for d in sorted(JOBS_DIR.iterdir(), key=lambda p: p.stat().st_mtime):
        try:
            j = json.loads((d / "job.json").read_text(encoding="utf-8"))
            tp = d / "transcript.json"
            j["transcript"] = json.loads(tp.read_text(encoding="utf-8")) if tp.exists() else None
            if j["status"] in ("queued", "transcribing", "rendering", "error"):
                j["status"] = "ready" if j["transcript"] else "new"
                j["message"] = ""
            JOBS[j["id"]] = j
        except Exception:
            pass


def public(j):
    t = j.get("transcript")
    # outputs the user deleted from the folder disappear from the list (the job itself stays re-renderable)
    outs = [o for o in j.get("outputs", []) if (OUTPUTS / o["file"]).exists()]
    return {k: j.get(k) for k in ("id", "name", "status", "progress", "message", "duration", "width", "height",
                                  "stage", "added", "started", "step", "proxy", "fit", "matte", "matte_fit")} | {
        "outputs": outs,
        "has_transcript": bool(t), "language": t and t.get("language"), "tmode": t and t.get("mode"),
        "tinfo": t and "%s on %s in %.0fs" % (t.get("model"), t.get("device"), t.get("seconds", 0))}


# ---------- activity log (shown in the UI + console) ----------
ACT = collections.deque(maxlen=300)


def act(msg, j=None):
    line = "%s  %s%s" % (time.strftime("%H:%M:%S"), (j["name"] + ": ") if j else "", msg)
    ACT.append(line)
    print(line, flush=True)


# ---------- worker ----------
def set_state(j, **kw):
    with LOCK:
        j.update(kw)


def set_stage(j, msg):
    set_state(j, stage=msg)
    act(msg, j)


def do_transcribe(j, o):
    set_state(j, status="transcribing", progress=0, stage="Starting…", message="", step="transcribe", started=time.time())
    act("Transcribing (mode=%s, lang=%s, model=%s)" % (o.get("mode", "spoken"), o.get("lang", "auto"), o.get("model", "turbo")), j)
    try:
        tr = transcribe(jdir(j["id"]) / j["file"], lang=o.get("lang", "auto"), mode=o.get("mode", "spoken"),
                        model=o.get("model", "turbo"), device="auto", refine=o.get("refine", True),
                        progress=lambda f: set_state(j, progress=f),
                        log=lambda m: set_stage(j, m))
        set_state(j, transcript=tr, status="ready", progress=1, stage="Transcript ready", message="", step="edit")
        act("Transcript ready: %d lines, language=%s, %.0fs on %s" % (len(tr["segments"]), tr["language"], tr["seconds"], tr["device"]), j)
        save_job(j)
        return True
    except Exception as e:
        set_state(j, status="error", message="Transcribe failed: %s" % e)
        act("ERROR transcribing: %s" % e, j)
        save_job(j)
        return False


def do_matte(j, fit="auto", sub=None):
    """Person cut-out video for 'text behind you'. sub=(lo, hi) maps its 0..1 progress into part of a longer job."""
    if j.get("matte") == "ready" and j.get("matte_fit") == fit and (jdir(j["id"]) / "matte.mp4").exists():
        return True
    unload_models()
    set_state(j, matte="making")
    act("Cutting out the person (for text behind you)", j)
    if sub is None:
        set_state(j, status="transcribing", step="matte", stage="Cutting out the person…", progress=0, started=time.time(), message="")
    try:
        r = make_matte(jdir(j["id"]) / j["file"], jdir(j["id"]) / "matte.mp4", fit=fit,
                       progress=lambda f: set_state(j, progress=(f if sub is None else sub[0] + (sub[1] - sub[0]) * f)),
                       log=lambda m: set_stage(j, m) if sub is None else act(m, j))
        set_state(j, matte="ready", matte_fit=fit)
        act("Person cut-out ready (%d frames, %.0fs, %s)" % (r["frames"], r["seconds"], r["provider"]), j)
        if sub is None:
            set_state(j, status="ready" if j.get("transcript") else "new", progress=1, stage="Person cut-out ready", step="edit")
        save_job(j)
        return True
    except Exception as e:
        set_state(j, matte="error", status="error", message="Person cut-out failed: %s" % e)
        act("ERROR cutting out the person: %s" % e, j)
        save_job(j)
        return False


def unique_out(stem, style):
    p = OUTPUTS / ("%s_%s.mp4" % (stem, style))
    n = 2
    while p.exists():
        p = OUTPUTS / ("%s_%s_%d.mp4" % (stem, style, n))
        n += 1
    return p


def do_render(j, o):
    styles = o.get("styles") or [DEFAULT_STYLE]
    ov = o.get("overrides") or {}
    words = words_from_transcript(j["transcript"])
    stem = safe_name(Path(j["name"]).stem)
    OUTPUTS.mkdir(parents=True, exist_ok=True)  # user may have deleted the folder
    set_state(j, started=time.time(), step="render")
    try:
        for si, st in enumerate(styles):
            set_state(j, status="rendering", stage="Rendering %s style (%d of %d)" % (STYLES[st]["label"], si + 1, len(styles)),
                      progress=0, message="")
            act("Rendering %s (%d/%d)" % (STYLES[st]["label"], si + 1, len(styles)), j)
            sov = (o.get("by_style") or {}).get(st, ov)
            behind = resolve_style(st, sov)["behind"]
            matte = None
            if behind:   # hero word BEHIND the person: needs the person cut-out video first
                fit = o.get("fit", "auto")
                set_state(j, stage="Cutting out the person for %s…" % STYLES[st]["label"])
                if not do_matte(j, fit, sub=(si / len(styles), (si + 0.4) / len(styles))):
                    raise RuntimeError(j.get("message") or "person cut-out failed")
                set_state(j, status="rendering", stage="Rendering %s style (%d of %d)" % (STYLES[st]["label"], si + 1, len(styles)))
                matte = jdir(j["id"]) / "matte.mp4"
            # 2K = 1440x2560; the captions are laid out on 1080x1920 and scaled by the renderer, so they stay sharp
            rw, rh = (1440, 2560) if o.get("quality") == "2k" else (1080, 1920)
            ofps = int(o["fps"]) if str(o.get("fps") or "").isdigit() else None
            sov = dict(sov or {}, motion_fps=60 if (ofps or 0) >= 50 else 30)
            doc = build_ass(words, st, sov, offset=float(o.get("offset") or 0), split=bool(behind))
            behind_doc, ass = doc if behind else (None, doc)
            outp = unique_out(stem, st)
            res = render_video(jdir(j["id"]) / j["file"], ass, outp, fit=o.get("fit", "auto"), width=rw, height=rh, fps=ofps,
                               progress=lambda f: set_state(j, progress=(si + (0.4 + 0.6 * f if behind else f)) / len(styles)),
                               log=lambda m: act(m, j), behind_ass=behind_doc, matte=matte,
                               out_size=(720, 1280) if o.get("quality") == "720p" else None)
            act("Saved %s  (%s, %.1fs)" % (outp.name, res["encoder"], res["seconds"]), j)
            with LOCK:
                j["outputs"].append({"style": st, "file": outp.name, "seconds": res["seconds"], "encoder": res["encoder"]})
            save_job(j)
        set_state(j, status="done", progress=1, stage="Done", message="", step="done")
    except Exception as e:
        set_state(j, status="error", message="Render failed: %s" % e)
        act("ERROR rendering: %s" % e, j)
    save_job(j)


def worker():
    while True:
        j, kind, o = Q.get()
        try:
            if j["id"] not in JOBS:
                continue
            if kind in ("transcribe", "auto") and (o.get("force") or not j.get("transcript") or j["transcript"].get("mode") != o.get("mode", "spoken")):
                if not do_transcribe(j, o):
                    continue
            if kind == "transcribe" and j.get("transcript") and j["status"] == "queued":
                set_state(j, status="ready", progress=1, stage="Transcript ready", step="edit")
            if kind == "matte":
                do_matte(j, o.get("fit", "auto"))
                continue
            if kind in ("render", "auto") and j.get("transcript"):
                do_render(j, o)
        except Exception as e:  # never let the worker thread die
            set_state(j, status="error", message="Unexpected error: %s" % e)
            act("ERROR: %s" % e, j)
        finally:
            Q.task_done()


threading.Thread(target=worker, daemon=True).start()


@app.errorhandler(Exception)
def on_error(e):
    import traceback
    from werkzeug.exceptions import HTTPException
    if isinstance(e, HTTPException):
        return e
    traceback.print_exc()
    act("ERROR (server): %s" % e)
    return jsonify({"error": str(e)}), 500


def build_proxy(j, fit):
    """Low-res 9:16 copy of the video used by the editor preview (fit applied exactly like the export)."""
    set_state(j, proxy="making", fit=fit)
    try:
        make_proxy(jdir(j["id"]) / j["file"], jdir(j["id"]) / "proxy.mp4", fit=fit)
        set_state(j, proxy="ready")
    except Exception as e:
        set_state(j, proxy="error")
        act("Preview copy failed: %s" % e, j)
    save_job(j)


# ---------- routes ----------
@app.get("/")
def index():
    return send_from_directory(ROOT / "web", "index.html", max_age=0)


@app.get("/api/state")
def state():
    with LOCK:
        jobs = [public(j) for j in sorted(JOBS.values(), key=lambda x: x["added"])]
    return jsonify({
        "jobs": jobs,
        "styles": [{"id": k, "label": v["label"], "desc": v["desc"], "mode": v["mode"], "words": v["words"], "y": v["y"],
                    "size": v["size"], "color": v["color"], "active": v["active"], "uppercase": v["uppercase"],
                    "behind": bool(v.get("behind")), "groups": [g for g, ids in TEMPLATE_GROUPS.items() if k in ids]}
                   for k, v in sorted(STYLES.items(), key=lambda kv: TEMPLATE_ORDER.get(kv[0], 999))],
        "gpu": cuda_ok(), "nvenc": nvenc_available(), "outputs": str(OUTPUTS), "queue": Q.qsize(),
        "now": time.time(), "log": list(ACT)[-60:],
    })


@app.post("/api/upload")
def upload():
    made = []
    for f in request.files.getlist("files"):
        jid = uuid.uuid4().hex[:10]
        d = jdir(jid)
        d.mkdir(parents=True)
        ext = Path(f.filename).suffix.lower() or ".mp4"
        fn = "source" + ext
        f.save(d / fn)
        try:
            info = probe(d / fn)
        except Exception as e:
            shutil.rmtree(d, ignore_errors=True)
            continue
        j = {"id": jid, "name": Path(f.filename).name, "file": fn, "status": "new", "progress": 0, "message": "",
             "stage": "Uploaded", "outputs": [], "duration": round(info["duration"], 1), "width": info["width"],
             "height": info["height"], "added": time.time(), "transcript": None}
        with LOCK:
            JOBS[jid] = j
        save_job(j)
        threading.Thread(target=build_proxy, args=(j, "auto"), daemon=True).start()
        made.append(public(j))
    return jsonify(made)


def _job(jid):
    j = JOBS.get(jid)
    if not j:
        abort(404)
    return j


@app.post("/api/jobs/<jid>/run")
def run_job(jid):
    j = _job(jid)
    o = request.get_json(force=True) or {}
    kind = o.get("kind", "auto")
    if kind in ("render", "auto") and not o.get("styles"):
        o["styles"] = [DEFAULT_STYLE]
    if j["status"] in ("queued", "transcribing", "rendering"):
        return jsonify({"error": "busy"}), 409
    ahead = Q.qsize() + sum(1 for x in JOBS.values() if x["status"] in ("transcribing", "rendering"))
    set_state(j, status="queued", stage="Waiting in queue (%d ahead)" % ahead if ahead else "Starting…", progress=0, message="",
              step="transcribe" if kind != "render" else "render")
    act("Queued (%s)" % kind, j)
    Q.put((j, kind, o))
    return jsonify(public(j))


@app.route("/api/jobs/<jid>/transcript", methods=["GET", "PUT"])
def transcript(jid):
    j = _job(jid)
    if request.method == "GET":
        return jsonify(j.get("transcript") or {"segments": []})
    texts = (request.get_json(force=True) or {}).get("texts", [])
    if not j.get("transcript"):
        abort(400)
    texts = list(texts) + [None] * (len(j["transcript"]["segments"]) - len(texts))
    new = apply_edits(j["transcript"], texts)  # unchanged lines keep timing; emptied lines are dropped
    set_state(j, transcript=new)
    save_job(j)
    return jsonify(new)


@app.get("/api/jobs/<jid>/media")
def media(jid):
    j = _job(jid)
    return send_file(jdir(jid) / j["file"], conditional=True)


@app.get("/api/jobs/<jid>/frame")
def frame(jid):
    j = _job(jid)
    if not j.get("transcript"):
        abort(400)
    ov = json.loads(request.args.get("ov") or "{}")
    st = request.args.get("style", DEFAULT_STYLE)
    t = float(request.args.get("t", 1))
    ass = build_ass(words_from_transcript(j["transcript"]), st, ov, offset=float(request.args.get("offset") or 0))
    out = WORK / "tmp" / ("frame_%s.png" % uuid.uuid4().hex[:8])
    out.parent.mkdir(parents=True, exist_ok=True)
    render_frame(jdir(jid) / j["file"], ass, out, t, fit=request.args.get("fit", "auto"))
    data = out.read_bytes()
    out.unlink(missing_ok=True)
    return Response(data, mimetype="image/png")


@app.get("/api/jobs/<jid>/srt")
def srt(jid):
    j = _job(jid)
    s = to_srt(words_from_transcript(j["transcript"]))
    return Response(s, mimetype="text/plain; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="%s.srt"' % safe_name(Path(j["name"]).stem)})


@app.delete("/api/jobs/<jid>")
def delete_job(jid):
    j = _job(jid)
    if j["status"] in ("transcribing", "rendering"):
        return jsonify({"error": "busy"}), 409
    with LOCK:
        JOBS.pop(jid, None)
    shutil.rmtree(jdir(jid), ignore_errors=True)
    return jsonify({"ok": True})


@app.get("/api/style-preview")
def sp():
    ov = json.loads(request.args.get("ov") or "{}")
    p = style_preview(request.args.get("style", DEFAULT_STYLE), ov)
    return send_file(p, mimetype="image/png", max_age=60)


@app.get("/outputs/<path:name>")
def outputs(name):
    return send_from_directory(OUTPUTS, name, as_attachment=request.args.get("dl") == "1")


@app.post("/api/open-outputs")
def open_outputs():
    """Open the folder with the finished videos in the system file manager."""
    import subprocess
    import sys
    try:
        if sys.platform == "win32":
            os.startfile(str(OUTPUTS))  # noqa
        else:
            subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(OUTPUTS)])
    except Exception:
        pass
    return jsonify({"ok": True})


# ---------- settings and models ----------
@app.get("/api/settings")
def api_settings():
    return jsonify(settings.public())


@app.put("/api/settings/ai")
def api_settings_ai():
    settings.update_ai(request.get_json(force=True) or {})
    return jsonify(settings.public())


@app.post("/api/settings/ai/test")
def api_settings_ai_test():
    """Try the saved (or just typed) AI settings with one small request."""
    from engine import refine
    o = request.get_json(force=True) or {}
    ai = settings.load()["ai"]
    cfg = {"url": o.get("url") or ai["url"], "model": o.get("model") or ai["model"], "fallback": "",
           "key": (o.get("key") or "").strip() or settings.ai_key(ai)[0]}
    if not cfg["key"]:
        return jsonify({"ok": False, "message": "No API key yet."})
    ok, msg = refine.test(cfg)
    return jsonify({"ok": ok, "message": msg})


@app.get("/api/models")
def api_models():
    return jsonify(models.status())


@app.post("/api/models/<mid>/download")
def api_models_download(mid):
    if mid not in models.REGISTRY:
        abort(404)
    models.start_download(mid)
    return jsonify(models.status())


@app.delete("/api/models/<mid>")
def api_models_delete(mid):
    if mid not in models.REGISTRY:
        abort(404)
    models.remove(mid)
    return jsonify(models.status())


# ---------- editor API (React UI) ----------
def _ov():
    return json.loads(request.args.get("ov") or "{}")


@app.get("/api/style-clip.mp4")
def api_style_clip():
    mp4, _ = style_clip(request.args.get("style", DEFAULT_STYLE), _ov())
    return send_file(mp4, mimetype="video/mp4", conditional=True, max_age=3600)


@app.get("/api/style-poster.png")
def api_style_poster():
    _, png = style_clip(request.args.get("style", DEFAULT_STYLE), _ov())
    return send_file(png, mimetype="image/png", max_age=3600)


@app.get("/api/jobs/<jid>/ass")
def api_ass(jid):
    j = _job(jid)
    if not j.get("transcript"):
        abort(400)
    st = request.args.get("style", DEFAULT_STYLE)
    ov = _ov()
    doc = build_ass(words_from_transcript(j["transcript"]), st, ov, offset=float(request.args.get("offset") or 0),
                    split=True)
    behind, front = doc
    if request.args.get("split") == "1":
        return jsonify({"behind": behind, "front": front, "is_behind": bool(behind)})
    return Response(front if not behind else build_ass(words_from_transcript(j["transcript"]), st, ov,
                    offset=float(request.args.get("offset") or 0)), mimetype="text/plain; charset=utf-8",
                    headers={"Cache-Control": "no-store"})


@app.get("/api/jobs/<jid>/proxy.mp4")
def api_proxy(jid):
    _job(jid)
    p = jdir(jid) / "proxy.mp4"
    if not p.exists():
        abort(404)
    return send_file(p, mimetype="video/mp4", conditional=True, max_age=0)


@app.post("/api/jobs/<jid>/proxy")
def api_proxy_make(jid):
    j = _job(jid)
    fit = (request.get_json(force=True, silent=True) or {}).get("fit", "auto")
    threading.Thread(target=build_proxy, args=(j, fit), daemon=True).start()
    return jsonify({"ok": True})


@app.get("/api/jobs/<jid>/peaks")
def api_peaks(jid):
    j = _job(jid)
    f = jdir(jid) / "peaks.json"
    if not f.exists():
        f.write_text(json.dumps(wave_peaks(jdir(jid) / j["file"])), encoding="utf-8")
    return Response(f.read_text(encoding="utf-8"), mimetype="application/json")


@app.put("/api/jobs/<jid>/segments")
def api_segments(jid):
    """Full replace from the timeline editor: segments -> words {w,s,e}."""
    j = _job(jid)
    segs = []
    for s in (request.get_json(force=True) or {}).get("segments", []):
        ws = [{"w": str(w["w"]), "s": float(w["s"]), "e": float(w["e"]), **({"hero": True} if w.get("hero") else {})}
              for w in s.get("words", []) if str(w.get("w", "")).strip()]
        if ws:
            segs.append({"start": ws[0]["s"], "end": ws[-1]["e"], "text": " ".join(w["w"] for w in ws), "words": ws,
                         **({"behind": False} if s.get("behind") is False else {})})
    tr = dict(j.get("transcript") or {})
    tr["segments"] = segs
    set_state(j, transcript=tr)
    save_job(j)
    return jsonify({"ok": True, "segments": len(segs)})


@app.get("/api/fonts")
def api_fonts():
    from engine.styles import FONT_FILES
    return jsonify([{"family": k, "file": v} for k, v in FONT_FILES.items()])


@app.get("/fonts/<path:name>")
def font_file(name):
    from engine.util import FONTS
    return send_from_directory(FONTS, name, max_age=86400)


@app.get("/api/styles")
def api_styles():
    return jsonify([{"id": k, **v, "groups": [g for g, ids in TEMPLATE_GROUPS.items() if k in ids]}
                    for k, v in sorted(STYLES.items(), key=lambda kv: TEMPLATE_ORDER.get(kv[0], 999))])

@app.get("/assets/<path:name>")
def web_assets(name):
    import mimetypes
    mimetypes.add_type("application/wasm", ".wasm")
    return send_from_directory(ROOT / "web" / "assets", name, max_age=3600)


@app.get("/legacy")
def legacy():
    return send_from_directory(ROOT / "legacy", "index.html")


@app.get("/api/jobs/<jid>/matte.mp4")
def api_matte_file(jid):
    _job(jid)
    p = jdir(jid) / "matte.mp4"
    if not p.exists():
        abort(404)
    return send_file(p, mimetype="video/mp4", conditional=True, max_age=0)



def run(port=8765, open_browser=True):
    load_jobs()
    print("Captions UI: http://127.0.0.1:%d   (outputs -> %s)" % (port, OUTPUTS))
    if open_browser:
        threading.Timer(1.2, lambda: __import__("webbrowser").open("http://127.0.0.1:%d" % port)).start()
    def _prewarm():
        """Render every template's preview clip in the background, in the reference style's order, so the grid is ready by the time it is opened."""
        time.sleep(5)
        for sid in sorted(STYLES, key=lambda k: TEMPLATE_ORDER.get(k, 999)):
            try:
                style_clip(sid, {})
            except Exception as e:  # a failed preview must not stop the rest
                act("preview %s failed: %s" % (sid, e))
    threading.Thread(target=_prewarm, daemon=True).start()
    app.run(host="127.0.0.1", port=port, threaded=True, debug=False)


if __name__ == "__main__":
    run()







