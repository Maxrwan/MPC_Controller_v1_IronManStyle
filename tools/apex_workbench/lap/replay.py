"""Window-bound V2 transport over the unchanged accepted native browser component."""

import hashlib
import json
from time import monotonic_ns

import streamlit as st

from tools.apex_workbench import scratch_replay

from . import evidence


def replay(view):
    source = view["raw"]["states"]
    window = [source[0]["time"], source[-1]["time"], len(source)]
    epoch = hashlib.sha256(
        json.dumps({"anchor": view["anchor"], "window": window}, sort_keys=True).encode()
    ).hexdigest()
    run_key = "lap_replay_" + view["directory"].name
    key = run_key + "_" + epoch[:16]
    latch, ack = run_key + "_quarantine", key + "_ack"
    if st.session_state.get(latch):
        st.error(st.session_state[latch])
        if st.button("Reopen verified V2 recording", key=run_key + "_reopen"):
            del st.session_state[latch]
            st.rerun()
        return
    data = scratch_replay.payload(view)
    # A full presentation operation can recreate its iframe (navigation/window/back).
    # Send one verified payload for that operation, then only fragment heartbeats.
    st.session_state.pop(ack, None)

    @st.fragment(run_every=1.0)
    def present():
        try:
            evidence.current(view)
            result = scratch_replay.component()(
                payload=data if st.session_state.get(ack) != epoch else None,
                epoch=epoch,
                valid=True,
                error=None,
                heartbeat=monotonic_ns(),
                key=key,
                default=None,
            )
            evidence.current(view)
            if isinstance(result, dict):
                st.session_state[ack] = (
                    epoch if result.get("epoch") == epoch and result.get("loaded") is True else None
                )
        except (OSError, ValueError, RuntimeError) as error:
            st.session_state[latch] = "V2 evidence changed or unavailable: " + str(error)
            st.rerun()

    present()
