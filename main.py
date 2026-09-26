from dotenv import load_dotenv
load_dotenv()

from utils.audio_processor import process_input, cleanup_temp_files
from core.transcription import transcribe_all, transcribe_all_with_segments
from core.intelligence import (
    summarize,
    generate_title,
    extract_action_items,
    extract_key_decisions,
    extract_questions,
    extract_meeting_intelligence,
    format_action_items,
    format_key_decisions,
    format_open_questions,
)
from core.retrieval import (
    build_vector_store,
    build_rag_chain,
    ask_question,
    ask_conversational_question,
)
from core.memory import SessionConversationMemory
from core.voice import transcribe_voice_input
from core.workflow import run_assistant_workflow
from core.actions import DEFAULT_TOOL_REGISTRY


from core.session_store import process_meeting_source


def run_pipeline(source: str, language: str = "english", session_id: str = None) -> dict:
    return process_meeting_source(source=source, language=language, session_id=session_id)



if __name__ == "__main__":
    # CLI entry point
    source = input("Enter YouTube URL or local file path: ").strip()
    language = input("Language (english/hinglish): ").strip() or "english"
    result = run_pipeline(source, language)

    print("\n" + "=" * 60)
    print(f"[SESSION ID] {result['session_id']}")
    print(f"[TITLE]      {result['title']}")
    print(f"\n[SUMMARY]\n{result['summary']}")
    print(f"\n[ACTION ITEMS]\n{result['action_items']}")
    print(f"\n[KEY DECISIONS]\n{result['key_decisions']}")
    print(f"\n[OPEN QUESTIONS]\n{result['open_questions']}")
    print("=" * 60)

    # Phase 4 — Context-aware Chat with your meeting
    rag_chain = result.get("rag_chain")
    vector_store = result.get("vector_store")
    memory = SessionConversationMemory(session_id=result["session_id"])
    if rag_chain:
        print("\n[CHAT] Context-aware chat with your meeting (type 'exit' to quit, or 'voice:<path>' for audio questions)\n")
        while True:
            question = input("You: ").strip()
            if question.lower() in ["exit", "quit", "q"]:
                print("Goodbye!")
                break
            if not question:
                continue

            if question.lower().startswith("voice:"):
                audio_fpath = question[6:].strip()
                try:
                    print(f"[Voice] Transcribing voice input from: {audio_fpath}")
                    question = transcribe_voice_input(audio_fpath, language=language)
                    print(f"[Voice] Recognized question: '{question}'")
                except Exception as v_err:
                    print(f"[Voice] Transcription error: {v_err}")
                    continue
            if vector_store:
                workflow_res = run_assistant_workflow(
                    query=question,
                    session_id=result["session_id"],
                    history=memory.get_recent_turns() if memory else [],
                    vector_store=vector_store,
                    rag_chain=rag_chain,
                    tool_registry=DEFAULT_TOOL_REGISTRY,
                    action_items=result.get("action_items_structured", []),
                )
                answer = workflow_res.get("answer", "")
                if memory and workflow_res.get("intent") in ("question", "clarify"):
                    ev_ids = [ev.evidence_id for ev in workflow_res.get("evidence", [])]
                    memory.add_turn(
                        user_message=question,
                        assistant_message=answer,
                        evidence_ids=ev_ids,
                        resolved_query=workflow_res.get("resolved_query", question),
                    )
            else:
                answer = ask_question(rag_chain, question)
            print(f"\n[Assistant] {answer}\n")
    else:
        print("\n[RAG] Chat unavailable for this session.\n")