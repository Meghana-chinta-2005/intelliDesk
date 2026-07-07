import pytest
from src.vector_store.embed_store import load_store
from src.vector_store.retrieve import retrieve


def test_retrieval_accuracy():
    """Evaluate retrieval accuracy over representative user queries."""
    # Load the real FAISS index and model
    try:
        index, chunks, model = load_store()
    except FileNotFoundError:
        pytest.fail(
            "FAISS index or chunks metadata not found. "
            "Please run `python -m src.vector_store.embed_store` to build the store first."
        )

    # 17 test cases representing the knowledge base contents
    test_cases = [
        {
            "query": "How do I reset my password?",
            "expected_source": "password_reset.txt",
        },
        {
            "query": "What is the leave policy?",
            "expected_source": "leave_policy.txt",
        },
        {
            "query": "How can I request a laptop replacement?",
            "expected_source": "laptop_replacement.txt",
        },
        {
            "query": "How do I submit expense claims?",
            "expected_source": "expense_claims.txt",
        },
        {
            "query": "How do I connect to CorpNet Wi-Fi?",
            "expected_source": "wi_fi_access.txt",
        },
        {
            "query": "What is the health insurance coverage?",
            "expected_source": "health_insurance.txt",
        },
        {
            "query": "What are the remote work guidelines?",
            "expected_source": "remote_work.txt",
        },
        {
            "query": "Which public holidays do we observe?",
            "expected_source": "holiday_calendar.txt",
        },
        {
            "query": "How do I contact the IT Helpdesk?",
            "expected_source": "it_helpdesk.txt",
        },
        {
            "query": "How long is the probation period?",
            "expected_source": "probation_period.txt",
        },
        {
            "query": "Where can I register my vehicle for parking?",
            "expected_source": "office_parking.txt",
        },
        {
            "query": "What is the anti-harassment policy?",
            "expected_source": "anti_harassment.txt",
        },
        {
            "query": "How much maternity leave can I take?",
            "expected_source": "maternity_leave.txt",
        },
        {
            "query": "How do I claim my learning budget?",
            "expected_source": "learning_budget.txt",
        },
        {
            "query": "What happens if my account is locked?",
            "expected_source": "account_lockout.txt",
        },
        {
            "query": "How do I set up MFA?",
            "expected_source": "mfa_setup.txt",
        },
        {
            "query": "How do I update my profile in Workday?",
            "expected_source": "workday_profile_updates.txt",
        },
    ]

    correct = 0
    for case in test_cases:
        # We query the retriever with the test case query
        retrieved = retrieve(
            case["query"], index, chunks, model, top_k=3, threshold=1.2
        )
        sources = {r["source"] for r in retrieved}
        if case["expected_source"] in sources:
            correct += 1

    accuracy = (correct / len(test_cases)) * 100
    print(f"\nRetrieval Evaluation: {correct}/{len(test_cases)} correct.")
    print(f"Retrieval Accuracy: {accuracy:.1f}%")

    # Assert that accuracy is high (at least 80%) to pass CI checks
    assert accuracy >= 80.0, f"Retrieval accuracy too low: {accuracy:.1f}%"
