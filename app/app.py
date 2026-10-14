import sys
from pathlib import Path

_app_dir = str(Path(__file__).resolve().parent)
_root_dir = str(Path(__file__).resolve().parent.parent)
if _app_dir in sys.path:
    sys.path.remove(_app_dir)
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)
if "app" in sys.modules and getattr(sys.modules["app"], "__file__", "") == __file__:
    del sys.modules["app"]

import streamlit as st  # type: ignore # pyrefly: ignore
from app import config
from app.orchestrator import load_demo_files, run_pipeline, set_review_status
from app.render import render_evidence
from app.export import build_brd_markdown, build_brd_docx

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit (Requirement F-04)

st.set_page_config(
    page_title="BRD Agent",
    page_icon="📋",
    layout="wide",
)

# Sidebar
with st.sidebar:
    st.title("📋 BRD Agent")
    st.caption("From messy files to a verified, traceable BRD.")
    st.divider()

    st.subheader("Settings")
    project_id = st.text_input("Project Name", value="Demo Project")
    demo_mode = st.toggle("Demo Mode", value=config.DEMO_MODE)
    st.caption(f"Backend Model: `{config.GEMINI_MODEL}`")

    if st.button("Reset Session", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# Global Demo Mode Warning Banner
if demo_mode:
    st.warning("⚠️ **Demo Mode is active**: Replaying cached Gemini output while running real verification, conflict, and gap checks.")

# Session State Initialization
if "files" not in st.session_state:
    st.session_state["files"] = {}
if "result" not in st.session_state:
    st.session_state["result"] = None

tab_upload, tab_reqs, tab_conflicts, tab_brd = st.tabs(
    ["📁 Upload", "📝 Requirements & Evidence", "⚠️ Conflicts & Gaps", "📄 BRD Export"]
)

# -------------------------------------------------------------
# Tab 1: Upload (Task F-1, F-01 to F-05, F-53, F-70, F-72)
# -------------------------------------------------------------
with tab_upload:
    st.subheader("Source Artifacts")

    oversized_files = []

    if demo_mode:
        st.markdown("#### Sample Demo Data")
        c1, c2 = st.columns(2)
        with c1:
            use_stage1 = st.checkbox("Use sample demo files (Stage 1)", value=True)
        with c2:
            use_stage2 = st.checkbox("Include Stage-2 file (meeting_notes_v2.txt) to demo conflict detection", value=False)

        if use_stage1:
            all_demo = load_demo_files()
            selected_demo = {}
            # Stage 1 files
            for k in ["auth_wireframe.jpg", "client_notes.pdf", "meeting_notes.txt"]:
                if k in all_demo:
                    selected_demo[k] = all_demo[k]
            # Stage 2 file
            if use_stage2 and "meeting_notes_v2.txt" in all_demo:
                selected_demo["meeting_notes_v2.txt"] = all_demo["meeting_notes_v2.txt"]

            st.session_state["files"] = selected_demo
            st.info(f"Loaded {len(selected_demo)} demo files: {', '.join(selected_demo.keys())}")
    else:
        uploaded = st.file_uploader(
            "Upload project artifacts (whiteboard photos, PDFs, notes)",
            type=["jpg", "jpeg", "png", "pdf", "txt"],
            accept_multiple_files=True,
            help="Supported formats: JPG, PNG, PDF, TXT. Max 10MB per file.",
        )
        if uploaded:
            new_files = {}
            for f in uploaded:
                f_bytes = f.read()
                if len(f_bytes) > MAX_FILE_SIZE_BYTES:
                    oversized_files.append((f.name, len(f_bytes)))
                new_files[f.name] = f_bytes
            st.session_state["files"] = new_files

    # Check for oversized files
    if oversized_files:
        for fname, fsize in oversized_files:
            st.error(f"❌ File **{fname}** is {(fsize / (1024*1024)):.2f} MB, which exceeds the 10 MB per-file limit.")

    # Show active files table/list
    current_files = st.session_state.get("files", {})
    if current_files:
        st.write("#### Active Files Ready for Processing")
        file_summary = []
        for name, data in current_files.items():
            file_summary.append({"File Name": name, "Size (KB)": f"{len(data) / 1024:.1f}"})
        st.dataframe(file_summary, use_container_width=True)

        can_process = len(oversized_files) == 0
        if st.button("Process Files", type="primary", disabled=not can_process):
            with st.status("Executing BRD extraction & verification pipeline...", expanded=True) as status_box:
                def on_progress_msg(msg: str):
                    status_box.write(f"• {msg}")

                res = run_pipeline(
                    project_id=project_id,
                    files=current_files,
                    demo_mode=demo_mode,
                    on_progress=on_progress_msg,
                )
                st.session_state["result"] = res
                status_box.update(label="Pipeline processing complete!", state="complete", expanded=False)

            st.success("Artifacts processed and requirements verified!")
            st.rerun()

    # Show pipeline timings/warnings notes
    res = st.session_state.get("result")
    if res and res.notes:
        with st.expander("Pipeline Execution Notes & Timings", expanded=False):
            for note in res.notes:
                st.write(f"- {note}")

# -------------------------------------------------------------
# Tab 2: Requirements & Evidence Viewer (Task F-2, F-50 to F-52)
# -------------------------------------------------------------
with tab_reqs:
    res = st.session_state.get("result")
    if not res:
        st.info("No requirements extracted yet. Upload files and click 'Process Files' in the Upload tab.")
    else:
        # Top summary metrics
        total_reqs = len(res.requirements)
        verified_count = sum(1 for r in res.requirements if r.verification_status == "verified")
        unverified_count = total_reqs - verified_count
        approved_count = sum(1 for r in res.requirements if r.review_status == "approved")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Requirements", total_reqs)
        m2.metric("Verified", verified_count)
        m3.metric("Unverified", unverified_count)
        m4.metric("Approved", approved_count)

        if unverified_count > 0:
            st.warning("⚠️ **Notice**: Requirements marked as **Unverified** have unsupported or unconfirmed evidence and will be excluded from the confirmed sections of the BRD.")

        # Requirements Table
        st.subheader("Requirements Overview")
        table_rows = []
        for r in res.requirements:
            sources = ", ".join(sorted(set(ev.file_name for ev in r.evidence)))
            table_rows.append(
                {
                    "ID": r.id,
                    "Requirement": r.text,
                    "Type": r.type.title(),
                    "Sources": sources,
                    "Evidence Status": "✅ Verified" if r.verification_status == "verified" else "❌ Unverified",
                    "Review Status": r.review_status.title(),
                }
            )
        st.dataframe(table_rows, use_container_width=True)

        st.divider()
        st.subheader("🔍 Evidence Viewer & Review Sign-off")

        req_ids = [r.id for r in res.requirements]
        selected_id = st.selectbox("Inspect evidence for requirement:", req_ids)
        selected_req = next((r for r in res.requirements if r.id == selected_id), None)

        if selected_req:
            st.markdown(f"### **{selected_req.id}**: {selected_req.text}")
            st.caption(f"Category: {selected_req.type.title()} | Current Review: **{selected_req.review_status.title()}**")

            # Evidence details
            col_left, col_right = st.columns([1, 1])

            with col_left:
                st.markdown("#### Evidence Items")
                for idx, ev in enumerate(selected_req.evidence):
                    with st.container(border=True):
                        st.markdown(f"**Item {idx+1}: `{ev.file_name}`** ({ev.kind})")
                        if ev.verified:
                            st.success(f"**Verified**: {ev.verify_note}")
                        else:
                            st.error(f"**Not Verified**: {ev.verify_note}")

                        if ev.kind == "text" and ev.quote:
                            st.markdown(f"> *\"{ev.quote}\"* (Line {ev.line or 'unknown'})")
                        elif ev.kind == "pdf" and ev.quote:
                            st.markdown(f"> *\"{ev.quote}\"* (Page {ev.page or 1})")
                        elif ev.kind == "image" and ev.box_2d:
                            st.markdown(f"Normalized Bounding Box: `{ev.box_2d}`")

            with col_right:
                st.markdown("#### Visual Source Evidence")
                for ev in selected_req.evidence:
                    rendered = render_evidence(ev, st.session_state["files"].get(ev.file_name))
                    if rendered["type"] == "image" and rendered["image"]:
                        st.image(rendered["image"], caption=rendered["caption"], use_container_width=True)
                    elif rendered["text"]:
                        st.caption(rendered["caption"])
                        st.code(rendered["text"], language="text")

            # Human Review Controls
            st.markdown("#### Review Sign-off")
            r1, r2, _ = st.columns([1, 1, 4])
            with r1:
                if st.button("✅ Approve", key=f"app_{selected_req.id}", use_container_width=True):
                    set_review_status(res, selected_req.id, "approved")
                    st.rerun()
            with r2:
                if st.button("❌ Reject", key=f"rej_{selected_req.id}", use_container_width=True):
                    set_review_status(res, selected_req.id, "rejected")
                    st.rerun()

# -------------------------------------------------------------
# Tab 3: Conflicts & Gaps (Task F-3, F-33, Acceptance A4 & A5)
# -------------------------------------------------------------
with tab_conflicts:
    res = st.session_state.get("result")
    if not res:
        st.info("No active run results.")
    else:
        st.subheader("⚠️ Contradiction Detection")
        if not res.conflicts:
            st.success("No contradictions detected across requirements.")
        else:
            for idx, c in enumerate(res.conflicts):
                with st.container(border=True):
                    header = f"[{c.severity.upper()} SEVERITY] Contradiction between: {', '.join(c.requirement_ids)}"
                    if c.severity == "high":
                        st.error(header)
                    elif c.severity == "medium":
                        st.warning(header)
                    else:
                        st.info(header)

                    st.write(c.description)

                    # Mark as resolved checkbox
                    resolved_checked = st.checkbox(
                        "Mark as resolved",
                        value=c.resolved,
                        key=f"conf_res_{idx}_{'_'.join(c.requirement_ids)}",
                    )
                    if resolved_checked != c.resolved:
                        c.resolved = resolved_checked
                        st.rerun()

        st.divider()
        st.subheader("❓ Gap Analysis & Clarification Questions")
        if not res.gaps:
            st.success("All standard requirement categories are covered by verified requirements.")
        else:
            for idx, g in enumerate(res.gaps):
                with st.expander(f"Category: {g.category.title()}", expanded=True):
                    st.write(f"**Clarification Question**: {g.question}")
                    user_ans = st.text_input(
                        "Stakeholder Clarification / Answer:",
                        value=g.answer or "",
                        key=f"gap_ans_{idx}_{g.category}",
                        placeholder="Enter clarification or answer here...",
                    )
                    if user_ans != (g.answer or ""):
                        g.answer = user_ans if user_ans.strip() else None

# -------------------------------------------------------------
# Tab 4: BRD Export (Tasks F-4 & F-5, F-60 to F-62, Acceptance A3 & A7)
# -------------------------------------------------------------
with tab_brd:
    res = st.session_state.get("result")
    if not res:
        st.info("No BRD generated yet.")
    else:
        app_only = st.checkbox("Approved requirements only", value=False)
        md_content = build_brd_markdown(project_id, res, approved_only=app_only)
        docx_bytes = build_brd_docx(project_id, res, approved_only=app_only)

        d_col1, d_col2, _ = st.columns([1, 1, 3])
        with d_col1:
            st.download_button(
                "📥 Download BRD (Markdown)",
                data=md_content,
                file_name=f"BRD_{project_id.replace(' ', '_')}.md",
                mime="text/markdown",
                type="primary",
                use_container_width=True,
            )
        with d_col2:
            if docx_bytes:
                st.download_button(
                    "📄 Download BRD (DOCX)",
                    data=docx_bytes,
                    file_name=f"BRD_{project_id.replace(' ', '_')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )

        st.divider()
        st.markdown(md_content)
