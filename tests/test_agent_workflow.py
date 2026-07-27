from bughound_agent import BugHoundAgent
from llm_client import MockClient


def test_workflow_runs_in_offline_mode_and_returns_shape():
    agent = BugHoundAgent(client=None)  # heuristic-only
    code = "def f():\n    print('hi')\n    return True\n"
    result = agent.run(code)

    assert isinstance(result, dict)
    assert "issues" in result
    assert "fixed_code" in result
    assert "risk" in result
    assert "logs" in result

    assert isinstance(result["issues"], list)
    assert isinstance(result["fixed_code"], str)
    assert isinstance(result["risk"], dict)
    assert isinstance(result["logs"], list)
    assert len(result["logs"]) > 0


def test_offline_mode_detects_print_issue():
    agent = BugHoundAgent(client=None)
    code = "def f():\n    print('hi')\n    return True\n"
    result = agent.run(code)

    assert any(issue.get("type") == "Code Quality" for issue in result["issues"])


def test_offline_mode_proposes_logging_fix_for_print():
    agent = BugHoundAgent(client=None)
    code = "def f():\n    print('hi')\n    return True\n"
    result = agent.run(code)

    fixed = result["fixed_code"]
    assert "logging" in fixed
    assert "logging.info(" in fixed


def test_no_print_false_positive_or_comment_corruption_on_comment_only_code():
    # GUARDRAIL: "print(" mentioned inside a comment is not real code, so it must
    # not be flagged as a Code Quality issue nor rewritten by the fixer.
    # MockClient forces the offline heuristic path (no API calls / no quota use).
    agent = BugHoundAgent(client=MockClient())
    code = (
        "# Helper notes for reviewers.\n"
        "# Do not use print( for logging in production code.\n"
    )
    result = agent.run(code)

    # Decision 1: the agent declines to treat the commented print( as an issue.
    assert not any(issue.get("type") == "Code Quality" for issue in result["issues"])

    # Decision 2: the agent does not perform a destructive edit on the comment.
    fixed = result["fixed_code"]
    assert "logging.info(" not in fixed          # comment was not rewritten
    assert "print(" in fixed                      # original comment text preserved


def test_mock_client_forces_llm_fallback_to_heuristics_for_analysis():
    # MockClient returns non-JSON for analyzer prompts, so agent should fall back.
    agent = BugHoundAgent(client=MockClient())
    code = "def f():\n    print('hi')\n    return True\n"
    result = agent.run(code)

    assert any(issue.get("type") == "Code Quality" for issue in result["issues"])
    # Ensure we logged the fallback path
    assert any("Falling back to heuristics" in entry.get("message", "") for entry in result["logs"])
