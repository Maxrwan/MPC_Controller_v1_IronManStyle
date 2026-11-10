"""Window-bound V2 transport over the unchanged accepted native browser component."""

import hashlib
import json
from functools import lru_cache
from time import monotonic_ns

import streamlit as st
from streamlit.components.v1 import declare_component

from . import ui_data
from .ui_theme import ASSETS


@lru_cache(maxsize=1)
def component():
    return declare_component("apex_v2_engineering_replay", path=str(ASSETS))


def replay(view):
    source = view["raw"]["states"]
    window = [source[0]["time"], source[-1]["time"], len(source)]
    epoch = hashlib.sha256(
        json.dumps(
            {"anchor": view["anchor"], "window": window, "renderer": renderer_identity()},
            sort_keys=True,
        ).encode()
    ).hexdigest()
    run_key = "engineering_replay_" + view["directory"].name
    key = run_key + "_" + epoch[:16]
    latch, ack = run_key + "_quarantine", key + "_ack"
    if st.session_state.get(latch):
        st.error(st.session_state[latch])
        if st.button("Reopen verified V2 recording", key=run_key + "_reopen"):
            del st.session_state[latch]
            st.rerun()
        return
    data = ui_data.payload(view)
    # A full presentation operation can recreate its iframe (navigation/window/back).
    # Send one verified payload for that operation, then only fragment heartbeats.
    st.session_state.pop(ack, None)

    @st.fragment(run_every=1.0)
    def present():
        try:
            ui_data.current(view)
            result = component()(
                payload=data if st.session_state.get(ack) != epoch else None,
                epoch=epoch,
                valid=True,
                error=None,
                heartbeat=monotonic_ns(),
                key=key,
                default=None,
            )
            ui_data.current(view)
            if isinstance(result, dict):
                st.session_state[ack] = (
                    epoch if result.get("epoch") == epoch and result.get("loaded") is True else None
                )
        except (OSError, ValueError, RuntimeError) as error:
            st.session_state[latch] = "V2 evidence changed or unavailable: " + str(error)
            st.rerun()

    present()


def renderer_identity():
    return {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(ASSETS.iterdir())
        if p.is_file()
    }
