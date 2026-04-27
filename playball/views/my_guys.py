from __future__ import annotations

import pandas as pd
import streamlit as st

from playball.data.watchlist import (
    WATCHLIST_PATH,
    add_watch_player,
    ensure_watchlist,
    remove_watch_player,
    save_watchlist,
    update_watch_notes,
)
from playball.lib.snapshot import expected_snapshot


# Backwards-compatible alias for any external code that imported the underscored helper.
_expected_snapshot = expected_snapshot


def render_my_guys() -> None:
    st.subheader("My Guys")
    st.markdown("Your personal baseball map: Royals, stars, prospects, and the players you want to understand.")

    # Add form FIRST so submitting it doesn't clobber pending data_editor edits below.
    st.markdown("#### Add Player")
    with st.form("add_watch_player", clear_on_submit=True):
        left, right = st.columns(2)
        name = left.text_input("Name")
        player_id = right.text_input("MLBAM player id", help="Optional, but enables current Statcast snapshots.")
        role = left.selectbox(
            "Role",
            ["Infielder", "Outfielder", "Catcher", "Pitcher", "Prospect", "Two-way", "Unknown"],
            key="my_guys_add_role",
        )
        org = right.text_input("Org/team")
        tags = st.text_input("Tags", placeholder="Royals;prospect;power")
        why = st.text_area("Why I care", height=90)
        submitted = st.form_submit_button("Add to My Guys")
        if submitted:
            if not name.strip():
                st.warning("Name is required.")
            else:
                add_watch_player(name, player_id, role, org, tags, why)
                st.success(f"Added {name}.")
                st.rerun()

    frame = ensure_watchlist()
    if frame.empty:
        st.info("Your watchlist is empty. Add a player above.")
        st.caption(f"Stored at {WATCHLIST_PATH}")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Tracked", len(frame))
    c2.metric("Royals", int((frame["org"] == "Royals").sum()))
    c3.metric("Prospects", int(frame["tags"].str.contains("prospect", case=False, na=False).sum()))

    st.markdown("#### Current Snapshot")
    snapshot = expected_snapshot(frame)
    if snapshot.empty:
        st.caption("No players with stat-enabled IDs yet.")
    else:
        st.dataframe(snapshot, width="stretch", hide_index=True)

    st.markdown("#### Watchlist")
    edited = st.data_editor(
        frame,
        width="stretch",
        hide_index=True,
        num_rows="dynamic",
        key="watchlist_editor",
        column_config={
            "why": st.column_config.TextColumn("why", width="large"),
            "notes": st.column_config.TextColumn("notes", width="large"),
        },
    )
    cols = st.columns([1, 1, 3])
    if cols[0].button("Save edits", width="stretch", key="my_guys_save_edits"):
        save_watchlist(edited)
        st.success("Watchlist saved.")
        st.rerun()

    removable = frame["name"].dropna().tolist()
    if removable:
        victim = cols[1].selectbox(
            "Remove",
            removable,
            label_visibility="collapsed",
            key="my_guys_remove_player",
        )
        if cols[1].button("Remove player", width="stretch", key="my_guys_remove_button"):
            remove_watch_player(victim)
            st.success(f"Removed {victim}.")
            st.rerun()

    selected = st.selectbox(
        "Notes focus",
        frame["name"].dropna().tolist(),
        key="my_guys_notes_focus",
    )
    current_notes = frame.loc[frame["name"] == selected, "notes"].iloc[0]
    notes = st.text_area("Personal notes", value=current_notes, height=120)
    if st.button("Save notes", width="stretch", key="my_guys_save_notes"):
        update_watch_notes(selected, notes)
        st.success("Notes saved.")
        st.rerun()

    st.caption(f"Stored at {WATCHLIST_PATH}")
