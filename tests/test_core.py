"""
Core local test suite for BRD Agent:
1. test_demo_pipeline_end_to_end: verifies full pipeline run with demo files
2. test_fake_quote_is_unverified: strict verification check
3. test_bad_box_rejected: invalid image bounding box check
4. test_unverified_requirement_excluded_from_brd: export check
5. test_every_evidence_kind_renders: render check
6. test_gap_keywords_match_whole_words: regex word boundary check
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import orchestrator, verify, gaps, render, export
from app.schemas import (
    ExtractedRequirement,
    ExtractedEvidence,
    Requirement,
    Evidence,
    RunResult,
)


class TestCore(unittest.TestCase):
    def test_demo_pipeline_end_to_end(self):
        """Pipeline runs in demo mode, produces verified reqs, detects gaps and conflicts."""
        files = orchestrator.load_demo_files()
        self.assertIn("auth_wireframe.jpg", files)
        self.assertIn("client_notes.pdf", files)
        self.assertIn("meeting_notes.txt", files)

        result = orchestrator.run_pipeline("test-proj", files, demo_mode=True)
        self.assertIsInstance(result, RunResult)
        self.assertGreaterEqual(len(result.requirements), 3)

        # FR-01 should be verified
        fr01 = next((r for r in result.requirements if r.id == "FR-01"), None)
        self.assertIsNotNone(fr01)
        self.assertEqual(fr01.verification_status, "verified")

        # Gap check must include data retention and privacy
        gap_categories = [g.category for g in result.gaps]
        self.assertIn("data retention and privacy", gap_categories)

        # Stage-2 conflict check if meeting_notes_v2.txt is present
        if "meeting_notes_v2.txt" in files:
            self.assertGreaterEqual(len(result.conflicts), 1)

    def test_fake_quote_is_unverified(self):
        """Fake quotes must NEVER pass verification."""
        files = orchestrator.load_demo_files()
        fake_req = ExtractedRequirement(
            id="FR-FAKE",
            text="The system will automatically order pizza for developers.",
            type="functional",
            evidence=[
                ExtractedEvidence(
                    file_name="client_notes.pdf",
                    kind="pdf",
                    page=1,
                    quote="The system will automatically order pizza for developers.",
                ),
                ExtractedEvidence(
                    file_name="meeting_notes.txt",
                    kind="text",
                    line=1,
                    quote="The system will automatically order pizza for developers.",
                ),
            ],
        )

        verified = verify.verify_requirements([fake_req], files)
        self.assertEqual(len(verified), 1)
        self.assertEqual(verified[0].verification_status, "unverified")
        self.assertFalse(verified[0].evidence[0].verified)
        self.assertFalse(verified[0].evidence[1].verified)

    def test_bad_box_rejected(self):
        """Invalid bounding boxes (negative area, out of bounds, wrong count) are rejected."""
        files = orchestrator.load_demo_files()
        bad_boxes = [
            [700, 200, 500, 800],  # ymin > ymax
            [500, 800, 700, 200],  # xmin > xmax
            [-10, 200, 700, 800],  # negative coord
            [500, 200, 1100, 800], # out of 0-1000 range
            [500, 200, 700],       # wrong count
        ]

        for idx, box in enumerate(bad_boxes):
            bad_req = ExtractedRequirement(
                id=f"FR-BAD-{idx}",
                text="Test bad box",
                type="functional",
                evidence=[
                    ExtractedEvidence(
                        file_name="auth_wireframe.jpg",
                        kind="image",
                        box_2d=box,
                    )
                ],
            )
            res = verify.verify_requirements([bad_req], files)
            self.assertEqual(res[0].verification_status, "unverified", f"Box {box} was not rejected")

    def test_unverified_requirement_excluded_from_brd(self):
        """Unverified requirements must never appear in confirmed sections of the BRD."""
        req_unverified = Requirement(
            id="FR-99",
            text="Unconfirmed speculative requirement",
            type="functional",
            evidence=[Evidence(file_name="client_notes.pdf", kind="pdf", verified=False, verify_note="fake quote")],
            verification_status="unverified",
            review_status="pending",
        )
        req_verified = Requirement(
            id="FR-01",
            text="Verified requirement",
            type="functional",
            evidence=[Evidence(file_name="client_notes.pdf", kind="pdf", verified=True, verify_note="Found on page 1", page=1)],
            verification_status="verified",
            review_status="approved",
        )

        dummy_result = RunResult(
            run_id="test-run",
            project_id="test-proj",
            mode="demo",
            requirements=[req_unverified, req_verified],
        )

        md = export.build_brd_markdown("Test Project", dummy_result)
        # FR-01 should be under Functional Requirements
        self.assertIn("## 2. Functional requirements", md)
        func_section = md.split("## 2. Functional requirements")[1].split("## 3.")[0]
        self.assertIn("FR-01", func_section)
        self.assertNotIn("FR-99", func_section)

        # FR-99 must only appear under Section 5
        self.assertIn("## 5. Unverified items (not confirmed)", md)
        unverified_section = md.split("## 5. Unverified items (not confirmed)")[1].split("## 6.")[0]
        self.assertIn("FR-99", unverified_section)

    def test_every_evidence_kind_renders(self):
        """Image, PDF, and text evidence kinds render into visual structures."""
        files = orchestrator.load_demo_files()

        # Image evidence
        ev_img = Evidence(file_name="auth_wireframe.jpg", kind="image", box_2d=[550, 200, 700, 800], verified=True)
        r_img = render.render_evidence(ev_img, files.get("auth_wireframe.jpg"))
        self.assertEqual(r_img["type"], "image")
        self.assertIsNotNone(r_img.get("image"))

        # PDF evidence
        ev_pdf = Evidence(file_name="client_notes.pdf", kind="pdf", page=1, quote="OAuth2.0", verified=True)
        r_pdf = render.render_evidence(ev_pdf, files.get("client_notes.pdf"))
        self.assertEqual(r_pdf["type"], "image")
        self.assertIsNotNone(r_pdf.get("image"))

        # Text evidence
        ev_txt = Evidence(file_name="meeting_notes.txt", kind="text", line=3, quote="15 minutes", verified=True)
        r_txt = render.render_evidence(ev_txt, files.get("meeting_notes.txt"))
        self.assertEqual(r_txt["type"], "text")
        self.assertIn(">>", r_txt["text"])

    def test_gap_keywords_match_whole_words(self):
        """Keywords match whole words only (e.g. 'log' doesn't match 'login')."""
        req_login = Requirement(
            id="FR-01",
            text="User can login with username and password.",
            type="functional",
            verification_status="verified",
        )
        # login text covers authentication, but should NOT cover 'audit and logging'
        gaps_list = gaps.coverage_gaps([req_login])
        categories_found = [g.category for g in gaps_list]
        self.assertIn("audit and logging", categories_found)

        # Now add actual audit logging requirement
        req_audit = Requirement(
            id="FR-02",
            text="Administrators can view audit logs.",
            type="functional",
            verification_status="verified",
        )
        gaps_list_2 = gaps.coverage_gaps([req_login, req_audit])
        categories_found_2 = [g.category for g in gaps_list_2]
        self.assertNotIn("audit and logging", categories_found_2)

    def test_smart_quotes_and_multiline_verification(self):
        """Smart quotes and multi-line text match accurately while paraphrased fake quotes fail."""
        # Multi-line snippet with smart quotes in text
        mock_text = (
            "Section A: System Governance\n"
            "The client states: “All sensitive credentials\n"
            "must be encrypted using AES-256.”\n"
            "Review date: 2026-10-14\n"
        ).encode("utf-8")

        mock_files = {"governance.txt": mock_text}

        # 1. Exact quote with standard ASCII quotes should match the smart quotes across lines
        req_smart = ExtractedRequirement(
            id="FR-SEC-01",
            text="Credentials must be encrypted.",
            type="non-functional",
            evidence=[
                ExtractedEvidence(
                    file_name="governance.txt",
                    kind="text",
                    quote='"All sensitive credentials must be encrypted using AES-256."',
                )
            ],
        )

        res_smart = verify.verify_requirements([req_smart], mock_files)
        self.assertEqual(res_smart[0].verification_status, "verified")
        self.assertTrue(res_smart[0].evidence[0].verified)

        # 2. Paraphrased fake quote should NOT pass
        req_paraphrased = ExtractedRequirement(
            id="FR-SEC-02",
            text="Credentials must be encrypted.",
            type="non-functional",
            evidence=[
                ExtractedEvidence(
                    file_name="governance.txt",
                    kind="text",
                    quote="Every credential should always use strong encryption",
                )
            ],
        )
        res_para = verify.verify_requirements([req_paraphrased], mock_files)
        self.assertEqual(res_para[0].verification_status, "unverified")
        self.assertFalse(res_para[0].evidence[0].verified)

    def test_demo_pipeline_all_four_files_conflict_and_gap(self):
        """Running pipeline with all 4 demo files detects FR-03 vs FR-04 conflict and privacy gap."""
        files = orchestrator.load_demo_files()
        self.assertIn("meeting_notes_v2.txt", files)

        result = orchestrator.run_pipeline("demo-full", files, demo_mode=True)
        self.assertEqual(len(result.requirements), 4)

        # Check conflict detection
        self.assertEqual(len(result.conflicts), 1)
        conflict = result.conflicts[0]
        self.assertIn("FR-03", conflict.requirement_ids)
        self.assertIn("FR-04", conflict.requirement_ids)
        self.assertEqual(conflict.severity, "high")
        self.assertIn("15 minutes (FR-03) vs 30 minutes (FR-04)", conflict.description)

        # Check data retention and privacy gap question
        gap_categories = [g.category for g in result.gaps]
        self.assertIn("data retention and privacy", gap_categories)

        # Check notes contain timings
        has_timing = any("in " in note and "s" in note for note in result.notes)
        self.assertTrue(has_timing, "result.notes must record stage timings")

    def test_export_markdown_with_answers_and_resolved_conflict(self):
        """Answered gap questions and resolved conflict statuses appear correctly in build_brd_markdown."""
        result = orchestrator.run_pipeline("demo-test", orchestrator.load_demo_files(), demo_mode=True)
        self.assertTrue(len(result.conflicts) > 0)
        self.assertTrue(len(result.gaps) > 0)

        # Mark conflict as resolved
        result.conflicts[0].resolved = True

        # Provide answer to first gap
        result.gaps[0].answer = "Data will be retained for 90 days in compliance with local regulations."

        md = export.build_brd_markdown("Test Project", result)

        # Conflict section must state [Resolved]
        self.assertIn("## 6. Conflicts", md)
        conflict_sec = md.split("## 6. Conflicts")[1].split("## 7.")[0]
        self.assertIn("[Resolved]", conflict_sec)

        # Gap section must display the answer
        self.assertIn("## 7. Open questions", md)
        gap_sec = md.split("## 7. Open questions")[1]
        self.assertIn("Answer: Data will be retained for 90 days in compliance with local regulations.", gap_sec)

    def test_build_brd_docx(self):
        """build_brd_docx returns valid bytes and strictly excludes unverified requirements from confirmed sections."""
        unverified_req = Requirement(
            id="FR-FAKE-DOCX",
            text="Unverified requirement that must be excluded.",
            type="functional",
            verification_status="unverified",
            review_status="pending",
        )
        verified_req = Requirement(
            id="FR-REAL-DOCX",
            text="Verified requirement that must be included.",
            type="functional",
            verification_status="verified",
            review_status="approved",
            evidence=[Evidence(file_name="client_notes.pdf", kind="pdf", verified=True, verify_note="Found on page 1", page=1)],
        )

        dummy_result = RunResult(
            run_id="docx-test-run",
            project_id="docx-proj",
            mode="demo",
            requirements=[unverified_req, verified_req],
        )

        docx_bytes = export.build_brd_docx("DOCX Test Project", dummy_result)
        self.assertIsNotNone(docx_bytes)
        self.assertIsInstance(docx_bytes, bytes)
        self.assertGreater(len(docx_bytes), 1000)

        # Verify Word document structure using docx
        import docx  # type: ignore # pyrefly: ignore
        import io
        assert docx_bytes is not None
        doc = docx.Document(io.BytesIO(docx_bytes))
        full_text = "\n".join(p.text for p in doc.paragraphs)

        self.assertIn("2. Functional requirements", full_text)
        self.assertIn("FR-REAL-DOCX", full_text)

        # Check section boundaries: FR-FAKE-DOCX must not appear before section 5
        sec2_to_sec5 = full_text.split("2. Functional requirements")[1].split("5. Unverified items (not confirmed)")[0]
        self.assertNotIn("FR-FAKE-DOCX", sec2_to_sec5)

        # Section 5 must contain FR-FAKE-DOCX
        sec5 = full_text.split("5. Unverified items (not confirmed)")[1]
        self.assertIn("FR-FAKE-DOCX", sec5)


if __name__ == "__main__":
    unittest.main()
