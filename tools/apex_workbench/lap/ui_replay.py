"""Bounded current/next-window display, with full evidence checks at every publication."""

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from time import monotonic_ns

import streamlit as st
from streamlit.components.v1 import declare_component

from . import ui_data
from .ui_theme import ASSETS


@lru_cache(maxsize=1)
def component():
    return declare_component("apex_v2_engineering_replay", path=str(ASSETS))


@lru_cache(maxsize=1)
def prefetch_executor():
    return ThreadPoolExecutor(max_workers=1, thread_name_prefix="readonly-replay-window")


def renderer_identity():
    return {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(ASSETS.iterdir())
        if p.is_file()
    }


def replay(view, start_window=None):
    windows = ui_data.windows(view)
    selected = windows.index(start_window) if start_window is not None else 0
    renderer = renderer_identity()

    def epoch(index):
        return hashlib.sha256(
            json.dumps(
                {"anchor": view["anchor"], "window": windows[index], "renderer": renderer},
                sort_keys=True,
            ).encode()
        ).hexdigest()

    run_key = "engineering_replay_" + view["directory"].name
    key = run_key + "_" + epoch(selected)[:16]
    latch, ack, cursor, advance, future_key = [
        key + suffix for suffix in ("_quarantine", "_ack", "_cursor", "_advance", "_future")
    ]
    # Quarantine spans every window and presentation of this run.
    latch = run_key + "_quarantine"
    if st.session_state.get(latch):
        st.error(st.session_state[latch])
        if st.button("Reopen verified recording", key=run_key + "_reopen"):
            del st.session_state[latch]
            st.rerun()
        return
    previous = st.session_state.pop(future_key, None)
    if previous is not None:
        previous.cancel()
    st.session_state[cursor] = selected
    st.session_state.pop(advance, None)
    st.session_state.pop(ack, None)
    with st.spinner("Preparing source-verified Planning reference and replay…"):
        cache = {selected: ui_data.payload(ui_data.window(view, windows[selected]))}

    def prepare_next(index):
        if index + 1 < len(windows):
            st.session_state[future_key] = prefetch_executor().submit(
                ui_data.payload, ui_data.window(view, windows[index + 1])
            )
        else:
            st.session_state.pop(future_key, None)

    prepare_next(selected)

    @st.fragment(run_every=1.0)
    def present():
        try:
            ui_data.current(view)
            index = st.session_state[cursor]
            resume = None
            requested = st.session_state.get(advance)
            future = st.session_state.get(future_key)
            if requested == epoch(index) and future is not None and future.done():
                data = (
                    future.result()
                )  # A failed prefetch quarantines rather than silently retries.
                ui_data.current(
                    view
                )  # Recheck the whole anchor immediately before next-window publication.
                resume = {"from_epoch": requested}
                index += 1
                cache.clear()  # Only current and the single in-flight next payload are retained.
                cache[index] = data
                st.session_state[cursor] = index
                st.session_state.pop(advance, None)
                prepare_next(index)
            data = cache[index]
            data["meta"]["next_window"] = index + 1 < len(windows)
            current_epoch = epoch(index)
            result = component()(
                payload=data if st.session_state.get(ack) != current_epoch else None,
                epoch=current_epoch,
                resume=resume,
                valid=True,
                error=None,
                heartbeat=monotonic_ns(),
                key=key,
                default=None,
            )
            ui_data.current(view)
            if isinstance(result, dict) and result.get("epoch") == current_epoch:
                if result.get("loaded") is True:
                    st.session_state[ack] = current_epoch
                    if result.get("advance") is True and index + 1 < len(windows):
                        st.session_state[advance] = current_epoch
                else:
                    st.session_state.pop(ack, None)
        except (OSError, ValueError, RuntimeError, KeyError, TypeError, IndexError) as error:
            pending = st.session_state.pop(future_key, None)
            if pending is not None:
                pending.cancel()
            st.session_state[latch] = "Evidence changed or unavailable: " + str(error)
            st.rerun()

    present()
