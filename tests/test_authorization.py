import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from backend import main


class AuthorizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.sqlite3"
        self.database_patch = patch.object(main, "DATABASE_PATH", self.database_path)
        self.database_patch.start()
        main.initialize_database()

    def tearDown(self) -> None:
        self.database_patch.stop()
        self.temp_dir.cleanup()

    def user(self, email: str) -> dict[str, str]:
        with main.connect_db() as db:
            row = db.execute(
                """SELECT id, organization_id, name, email, role, department
                   FROM users WHERE email = ?""",
                (email,),
            ).fetchone()
        return dict(row)

    def test_employee_retrieval_excludes_restricted_documents(self) -> None:
        with main.connect_db() as db:
            docs = main.accessible_documents(db, self.user("employee@knowsphere.local"))
        titles = {doc["title"] for doc in docs}
        self.assertIn("HR Policy & Employee Handbook Sample", titles)
        self.assertIn("Internal Emails & KB Sample", titles)
        self.assertNotIn("Customer Information Sample", titles)
        self.assertNotIn("Financial Report Sample", titles)
        self.assertNotIn("Legal Agreement Sample", titles)
        self.assertNotIn("Project Report & SOP Sample", titles)

    def test_hr_retrieval_does_not_include_compliance_documents(self) -> None:
        with main.connect_db() as db:
            docs = main.accessible_documents(db, self.user("hr@knowsphere.local"))
        scopes = {doc["access_level"] for doc in docs}
        self.assertIn("org", scopes)
        self.assertNotIn("compliance", scopes)
        self.assertNotIn("restricted", scopes)

    def test_organization_admin_can_access_every_document_scope(self) -> None:
        with main.connect_db() as db:
            docs = main.accessible_documents(db, self.user("admin@knowsphere.local"))
        self.assertEqual(
            {doc["access_level"] for doc in docs},
            {"org", "team", "compliance", "restricted"},
        )

    def test_manager_cannot_retrieve_another_department_document(self) -> None:
        with main.connect_db() as db:
            db.execute(
                """INSERT INTO documents
                   (id, organization_id, title, category, source, status, access_level, department, updated_at, snippet)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                ("doc_finance", "org_northstar", "Finance Team Plan", "SOP", "Finance", "Published", "team", "Finance", "2026-11-01", "Restricted finance material."),
            )
        with main.connect_db() as db:
            docs = main.accessible_documents(db, self.user("manager@knowsphere.local"))
        titles = {doc["title"] for doc in docs}
        self.assertIn("Project Report & SOP Sample", titles)
        self.assertNotIn("Finance Team Plan", titles)

    def test_retrieval_never_returns_unauthorized_content_as_a_source(self) -> None:
        embedded_texts: list[str] = []

        def embed_authorized_texts(texts: list[str]) -> list[list[float]]:
            embedded_texts.extend(texts)
            return [[1.0, 0.0] for _ in texts]

        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}), patch.object(
            main, "embed_query", return_value=[1.0, 0.0]
        ), patch.object(
            main,
            "embed_document_batch",
            side_effect=embed_authorized_texts,
        ), patch.object(
            main,
            "call_gemini",
            return_value=json.dumps({"answer": "No support.", "source_ids": []}),
        ) as generation:
            result = main.ask(
                main.AskRequest(question="What is in the customer profile?"),
                self.user("employee@knowsphere.local"),
            )
        self.assertEqual(result["mode"], "no_evidence")
        prompt = generation.call_args.args[0]
        self.assertNotIn("Vanguard Logistics", prompt)
        self.assertNotIn("Vanguard Logistics", "\n".join(embedded_texts))

    def test_question_returns_matching_source_text_not_a_generic_answer(self) -> None:
        chunk = {
            "chunk_id": "chunk_policy_page_1",
            "document_id": "doc_policy",
            "title": "Remote & hybrid work policy",
            "source": "policyinfo/HR Policy & Employee Handbook Sample.pdf",
            "page_number": 1,
            "text": "Core hours are 10:00 AM to 4:00 PM in the employee's local time zone.",
            "score": 0.82,
        }
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}), patch.object(
            main, "retrieve_relevant_chunks", return_value=[chunk]
        ), patch.object(
            main,
            "call_gemini",
            return_value=json.dumps(
                {"answer": "Core hours are 10:00 AM to 4:00 PM local time.", "source_ids": ["chunk_policy_page_1"]}
            ),
        ):
            result = main.ask(
                main.AskRequest(question="What are the core hours?"),
                self.user("employee@knowsphere.local"),
            )
        self.assertIn("10:00 AM to 4:00 PM", result["answer"])
        self.assertEqual(result["sources"][0]["title"], "Remote & hybrid work policy")
        self.assertEqual(result["sources"][0]["pages"], [1])

    def test_follow_up_questions_keep_conversation_context_for_search_and_answer(self) -> None:
        history = [
            main.ConversationMessage(role="user", content="How much annual leave is allowed?"),
            main.ConversationMessage(role="assistant", content="The policy says 20 days."),
        ]
        chunk = {
            "chunk_id": "leave-follow-up",
            "document_id": "doc_policy",
            "title": "Employee leave policy",
            "source": "policy.pdf",
            "page_number": 2,
            "text": "Unused annual leave may be carried forward for up to five days.",
            "score": 0.88,
        }
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}), patch.object(
            main, "retrieve_relevant_chunks", return_value=[chunk]
        ) as retrieval, patch.object(
            main,
            "call_gemini",
            return_value=json.dumps(
                {"answer": "Up to five unused days may be carried forward.", "source_ids": ["leave-follow-up"]}
            ),
        ) as generation:
            result = main.ask(
                main.AskRequest(question="Can I carry it over?", history=history),
                self.user("employee@knowsphere.local"),
            )

        retrieval_query = retrieval.call_args.args[0]
        self.assertIn("How much annual leave is allowed?", retrieval_query)
        self.assertIn("Can I carry it over?", retrieval_query)
        answer_prompt = generation.call_args.args[0]
        self.assertIn("The policy says 20 days.", answer_prompt)
        self.assertIn("Unused annual leave may be carried forward for up to five days.", answer_prompt)
        self.assertEqual(result["sources"][0]["pages"], [2])

    def test_greeting_is_conversational_and_does_not_require_document_search(self) -> None:
        with patch.dict("os.environ", {"GEMINI_API_KEY": ""}), patch.object(
            main, "retrieve_relevant_chunks"
        ) as retrieval:
            result = main.ask(
                main.AskRequest(question="Hi!"),
                self.user("employee@knowsphere.local"),
            )

        self.assertEqual(result["mode"], "conversation")
        self.assertIn("What would you like to know?", result["answer"])
        self.assertEqual(result["sources"], [])
        retrieval.assert_not_called()

    def test_greeting_is_excluded_from_follow_up_search_context(self) -> None:
        history = [
            main.ConversationMessage(role="user", content="hi"),
            main.ConversationMessage(role="assistant", content="Hello! What can I help with?"),
        ]
        self.assertEqual(
            main.conversation_search_query(history, "hr policy"),
            "hr policy",
        )

    def test_employee_can_search_general_benefits_guide(self) -> None:
        with patch.object(main, "embed_query", return_value=[1.0, 0.0]), patch.object(
            main,
            "embed_document_batch",
            side_effect=lambda texts: [
                [1.0, 0.0] if "stipend" in text.lower() or "subsidy" in text.lower() else [0.0, 1.0]
                for text in texts
            ],
        ):
            chunks = main.retrieve_relevant_chunks(
                "As an employee what benefits can I get?",
                self.user("employee@knowsphere.local"),
            )
        self.assertTrue(chunks)
        self.assertEqual(chunks[0]["title"], "HR Policy & Employee Handbook Sample")
        self.assertTrue(any(term in chunks[0]["text"].lower() for term in ("stipend", "subsidy")))

    def test_gemini_is_required_and_no_keyword_fallback_is_used(self) -> None:
        with patch.dict("os.environ", {"GEMINI_API_KEY": ""}):
            with self.assertRaises(main.HTTPException) as error:
                main.ask(
                    main.AskRequest(question="What are the remote work core hours?"),
                    self.user("employee@knowsphere.local"),
                )
        self.assertEqual(error.exception.status_code, 503)
        self.assertIn("GEMINI_API_KEY", error.exception.detail)

    def test_gemini_retries_a_temporary_service_unavailable_response(self) -> None:
        unavailable = main.urllib.error.HTTPError(
            "https://example.test/generate",
            503,
            "Service Unavailable",
            None,
            io.BytesIO(b""),
        )
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'{"ok": true}'
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}), patch(
            "backend.main.urllib.request.urlopen",
            side_effect=[unavailable, response],
        ) as urlopen, patch("backend.main.time.sleep"):
            result = main.gemini_post("gemini-3.8-flash", "generateContent", {})

        self.assertEqual(result, {"ok": True})
        self.assertEqual(urlopen.call_count, 2)

    def test_answer_generation_defaults_to_supported_flash_model(self) -> None:
        response = {"candidates": [{"content": {"parts": [{"text": '{"answer":"ok","source_ids":[]}'}]}}]}
        with patch.dict("os.environ", {}, clear=True), patch.object(
            main, "gemini_post", return_value=response
        ) as request:
            result = main.call_gemini("test prompt")

        self.assertEqual(json.loads(result)["answer"], "ok")
        self.assertEqual(request.call_args.args[:2], ("gemini-3.6-flash", "generateContent"))

    def test_answer_generation_uses_fallback_model_when_primary_is_unavailable(self) -> None:
        response = {"candidates": [{"content": {"parts": [{"text": '{"answer":"ok","source_ids":[]}'}]}}]}
        unavailable = main.HTTPException(status_code=503, detail="temporarily unavailable")
        with patch.dict(
            "os.environ",
            {"GEMINI_MODEL": "gemini-3.6-flash", "GEMINI_FALLBACK_MODEL": "gemini-3.5-flash-lite"},
        ), patch.object(
            main, "gemini_post", side_effect=[unavailable, response]
        ) as request:
            result = main.call_gemini("test prompt")

        self.assertEqual(json.loads(result)["answer"], "ok")
        self.assertEqual(request.call_args_list[0].args[0], "gemini-3.6-flash")
        self.assertEqual(request.call_args_list[1].args[0], "gemini-3.5-flash-lite")

    def test_gemini_answer_uses_and_returns_only_retrieved_citations(self) -> None:
        document_id = "chunk_benefits_page_1"
        chunk = {
            "chunk_id": document_id,
            "document_id": "doc_benefits",
            "title": "HR Policy & Employee Handbook Sample",
            "source": "policyinfo/HR Policy & Employee Handbook Sample.pdf",
            "page_number": 1,
            "text": "The handbook includes a home office stipend.",
            "score": 0.9,
        }
        response = {
            "answer": "The handbook includes a home office stipend.",
            "source_ids": [document_id],
        }
        with patch.object(
            main, "call_gemini", return_value=json.dumps(response)
        ):
            result = main.generate_grounded_answer("What benefit is offered?", [chunk])
        self.assertEqual(result["mode"], "gemini")
        self.assertEqual(result["sources"][0]["id"], "doc_benefits")
        self.assertEqual(result["sources"][0]["pages"], [1])

    def test_gemini_cannot_cite_a_document_outside_retrieved_context(self) -> None:
        chunk = {
            "chunk_id": "retrieved-chunk",
            "document_id": "document-1",
            "title": "Allowed document",
            "source": "allowed.pdf",
            "page_number": 1,
            "text": "Allowed source text.",
            "score": 0.9,
        }
        response = {"answer": "Unsupported claim.", "source_ids": ["another-tenant-document"]}
        with patch("backend.main.call_gemini", return_value=json.dumps(response)):
            with self.assertRaises(main.HTTPException) as error:
                main.generate_grounded_answer("Question", [chunk])
        self.assertEqual(error.exception.status_code, 502)

    def test_gemini_abstains_when_it_returns_no_supported_citations(self) -> None:
        chunk = {
            "chunk_id": "retrieved-chunk",
            "document_id": "document-1",
            "title": "Allowed document",
            "source": "allowed.pdf",
            "page_number": 1,
            "text": "A source passage.",
            "score": 0.9,
        }
        response = {"answer": "", "source_ids": []}
        with patch("backend.main.call_gemini", return_value=json.dumps(response)):
            result = main.generate_grounded_answer("Unsupported question", [chunk])
        self.assertEqual(result["mode"], "no_evidence")
        self.assertEqual(result["sources"], [])

    def test_question_without_sufficient_evidence_returns_no_citation(self) -> None:
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}), patch.object(
            main, "retrieve_relevant_chunks", return_value=[]
        ):
            result = main.ask(
                main.AskRequest(question="What are the office core hours?"),
                self.user("hr@knowsphere.local"),
            )
        self.assertEqual(result["sources"], [])
        self.assertIn("couldn’t find a reliable answer", result["answer"])

    def test_all_policy_pdfs_are_ingested_with_page_chunks(self) -> None:
        with main.connect_db() as db:
            documents = db.execute(
                """SELECT title, source FROM documents
                   WHERE organization_id = ? AND source LIKE 'policyinfo/%'""",
                ("org_northstar",),
            ).fetchall()
            chunks = db.execute(
                """SELECT COUNT(*) FROM document_chunks
                   WHERE organization_id = ? AND document_id IN (
                     SELECT id FROM documents WHERE organization_id = ? AND source LIKE 'policyinfo/%'
                   )""",
                ("org_northstar", "org_northstar"),
            ).fetchone()[0]
        self.assertEqual(len(documents), 7)
        self.assertGreaterEqual(chunks, 7)

    def test_employee_cannot_read_organization_analytics(self) -> None:
        with self.assertRaises(main.HTTPException) as error:
            main.admin_overview(self.user("employee@knowsphere.local"))
        self.assertEqual(error.exception.status_code, 403)

    def test_manager_cannot_read_organization_analytics(self) -> None:
        with self.assertRaises(main.HTTPException) as error:
            main.admin_overview(self.user("manager@knowsphere.local"))
        self.assertEqual(error.exception.status_code, 403)

    def test_knowledge_manager_does_not_receive_organization_user_or_audit_counts(self) -> None:
        result = main.admin_overview(self.user("knowledge@knowsphere.local"))
        self.assertIsNone(result["users"])
        self.assertIsNone(result["events"])

    def test_only_organization_admin_can_list_and_update_members(self) -> None:
        admin = self.user("admin@knowsphere.local")
        members = main.admin_users(admin)["users"]
        employee = next(member for member in members if member["email"] == "employee@knowsphere.local")
        result = main.update_user(
            employee["id"],
            main.UserUpdate(role="hr", department="People"),
            admin,
        )
        self.assertEqual(result["user"]["role"], "hr")
        self.assertEqual(result["user"]["department"], "People")
        with self.assertRaises(main.HTTPException) as error:
            main.admin_users(self.user("knowledge@knowsphere.local"))
        self.assertEqual(error.exception.status_code, 403)

    def test_admin_cannot_change_own_role(self) -> None:
        admin = self.user("admin@knowsphere.local")
        with self.assertRaises(main.HTTPException) as error:
            main.update_user(
                admin["id"],
                main.UserUpdate(role="employee", department="Operations"),
                admin,
            )
        self.assertEqual(error.exception.status_code, 400)

    def test_uploaded_documents_require_review_before_retrieval(self) -> None:
        admin = self.user("admin@knowsphere.local")
        created = main.create_document(
            main.DocumentUpload(
                title="New policy",
                category="Policy",
                source="new-policy.txt",
                access_level="hr",
                content="This policy should only appear after publication.",
            ),
            admin,
        )["document"]
        self.assertEqual(created["status"], "Pending Review")
        with main.connect_db() as db:
            hr_docs = main.accessible_documents(db, self.user("hr@knowsphere.local"), published_only=True)
        self.assertNotIn(created["id"], {doc["id"] for doc in hr_docs})
        main.update_document_status(
            created["id"],
            main.DocumentStatusUpdate(status="Published"),
            admin,
        )
        with main.connect_db() as db:
            hr_docs = main.accessible_documents(db, self.user("hr@knowsphere.local"), published_only=True)
        self.assertIn(created["id"], {doc["id"] for doc in hr_docs})

    def test_login_stores_only_a_hash_of_the_session_token(self) -> None:
        from fastapi import Response

        response = Response()
        result = main.login(
            main.LoginRequest(email="employee@knowsphere.local", password="KnowSphereDemo2026!"),
            response,
        )
        self.assertEqual(result["user"]["role"], "employee")
        self.assertIn("HttpOnly", response.headers["set-cookie"])
        with main.connect_db() as db:
            stored_token = db.execute("SELECT token_hash FROM sessions").fetchone()["token_hash"]
        self.assertEqual(len(stored_token), 64)


if __name__ == "__main__":
    unittest.main()
