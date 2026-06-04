from datetime import date
from paper_intensive_reading.paper_store import (
    init_db, add_paper, get_paper, list_papers,
    update_status, get_progress, mark_section_done
)


class TestInitDb:
    def test_init_creates_tables(self, tmp_db):
        init_db(tmp_db)
        # 验证：能 add 一个 paper
        add_paper(tmp_db, {
            "arxiv_id": "2302.13971",
            "title": "LLaMA",
            "authors": ["Touvron"],
            "affiliations": ["Meta AI"],
            "abstract": "We introduce LLaMA.",
            "published": date(2023, 2, 27),
            "pdf_path": "/tmp/x.pdf",
        })
        p = get_paper(tmp_db, "2302.13971")
        assert p is not None
        assert p["title"] == "LLaMA"


class TestPaperCrud:
    def test_add_and_get(self, tmp_db):
        init_db(tmp_db)
        add_paper(tmp_db, {
            "arxiv_id": "2302.13971", "title": "LLaMA",
            "authors": ["Touvron"], "affiliations": ["Meta AI"],
            "abstract": "x", "published": date(2023, 2, 27),
            "pdf_path": "/tmp/x.pdf",
        })
        p = get_paper(tmp_db, "2302.13971")
        assert p["arxiv_id"] == "2302.13971"

    def test_add_duplicate_updates(self, tmp_db):
        init_db(tmp_db)
        meta = {"arxiv_id": "2302.13971", "title": "LLaMA v1",
                "authors": [], "affiliations": [], "abstract": "x",
                "published": date(2023, 2, 27), "pdf_path": "/tmp/x.pdf"}
        add_paper(tmp_db, meta)
        meta["title"] = "LLaMA v2"
        add_paper(tmp_db, meta)
        p = get_paper(tmp_db, "2302.13971")
        assert p["title"] == "LLaMA v2"

    def test_get_nonexistent_returns_none(self, tmp_db):
        init_db(tmp_db)
        assert get_paper(tmp_db, "0000.00000") is None


class TestStatus:
    def test_update_status(self, tmp_db):
        init_db(tmp_db)
        add_paper(tmp_db, {
            "arxiv_id": "2302.13971", "title": "LLaMA",
            "authors": [], "affiliations": [], "abstract": "x",
            "published": date(2023, 2, 27), "pdf_path": "/tmp/x.pdf",
        })
        update_status(tmp_db, "2302.13971", "已读完")
        p = get_paper(tmp_db, "2302.13971")
        assert p["status"] == "已读完"

    def test_list_by_status(self, tmp_db):
        init_db(tmp_db)
        for i, status in enumerate(["待读", "在读", "已读完", "已读完"]):
            add_paper(tmp_db, {
                "arxiv_id": f"2302.1397{i}", "title": f"Paper {i}",
                "authors": [], "affiliations": [], "abstract": "x",
                "published": date(2023, 2, 27), "pdf_path": f"/tmp/{i}.pdf",
            })
            update_status(tmp_db, f"2302.1397{i}", status)

        done = list_papers(tmp_db, status="已读完")
        assert len(done) == 2


class TestProgress:
    def test_mark_section_done(self, tmp_db):
        init_db(tmp_db)
        add_paper(tmp_db, {
            "arxiv_id": "2302.13971", "title": "LLaMA",
            "authors": [], "affiliations": [], "abstract": "x",
            "published": date(2023, 2, 27), "pdf_path": "/tmp/x.pdf",
        })
        mark_section_done(tmp_db, "2302.13971", "1")
        mark_section_done(tmp_db, "2302.13971", "2")
        progress = get_progress(tmp_db, "2302.13971")
        assert progress["sections_done"] == ["1", "2"]
        assert progress["percent"] > 0


class TestFormulaAttempts:
    def test_record_attempt(self, tmp_db):
        from paper_intensive_reading.paper_store import record_formula_attempt, get_formula_attempts
        init_db(tmp_db)
        record_formula_attempt(tmp_db, "2302.13971", "(1)", passed=True, feedback="ok")
        record_formula_attempt(tmp_db, "2302.13971", "(1)", passed=False, feedback="didn't know softmax")
        record_formula_attempt(tmp_db, "2302.13971", "(1)", passed=True, feedback="ok after re-explain")

        attempts = get_formula_attempts(tmp_db, "2302.13971", "(1)")
        assert len(attempts) == 3
        assert attempts[0]["passed"] is True
        assert attempts[1]["passed"] is False
        assert attempts[2]["passed"] is True


class TestUserState:
    def test_set_get_state(self, tmp_db):
        from paper_intensive_reading.paper_store import set_user_state, get_user_state
        init_db(tmp_db)
        set_user_state(tmp_db, "2302.13971", {
            "depth_pref": "elementary",
            "skipped_formulas": ["(3)", "(7)"],
            "pending_questions": ["What is RoPE?"],
        })
        state = get_user_state(tmp_db, "2302.13971")
        assert state["depth_pref"] == "elementary"
        assert state["skipped_formulas"] == ["(3)", "(7)"]
        assert state["pending_questions"] == ["What is RoPE?"]

    def test_update_partial(self, tmp_db):
        from paper_intensive_reading.paper_store import set_user_state, get_user_state
        init_db(tmp_db)
        set_user_state(tmp_db, "2302.13971", {"depth_pref": "medium"})
        # 部分更新
        set_user_state(tmp_db, "2302.13971", {"pending_questions": ["new q"]})
        state = get_user_state(tmp_db, "2302.13971")
        assert state["depth_pref"] == "medium"  # 保留
        assert state["pending_questions"] == ["new q"]  # 新增
