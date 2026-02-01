"""
English Learning Application - Main Gradio Interface
"""

import gradio as gr
import json
from typing import List, Dict, Any, Optional

from config import DEFAULT_AGE, DEFAULT_LEXILE
from core.user_manager import (
    list_users, create_user, load_user_info, save_user_info, user_exists
)
from core.word_bank import (
    load_words, save_words, deduplicate_words, add_words, get_word_count
)
from core.ai_client import get_client, load_api_config, save_api_config
from core.content_generator import generate_article_and_questions
from core.evaluator import evaluate_answers, save_test_log
from core.log_manager import get_user_logs, format_log_for_display, get_score_history


# Global state
current_user = None
current_article = None
current_questions = None
current_client = None


def refresh_user_list():
    """Get list of users for dropdown."""
    users = list_users()
    return gr.Dropdown(choices=users, value=users[0] if users else None)


def handle_user_selection(username):
    """Handle user selection/creation."""
    global current_user

    if not username:
        return "Please enter a username", "", "", "", gr.update(visible=False)

    current_user = username

    if user_exists(username):
        # Load existing user
        info = load_user_info(username)
        age = info.get('age', DEFAULT_AGE) if info else DEFAULT_AGE
        lexile = info.get('lexile_level', DEFAULT_LEXILE) if info else DEFAULT_LEXILE

        word_count = get_word_count(username)
        words_text = "\n".join(load_words(username))

        api_config = load_api_config(username)
        api_json = json.dumps(api_config, indent=2, ensure_ascii=False) if api_config else ""

        return (
            f"✓ Loaded user: {username}",
            str(age),
            str(lexile),
            words_text,
            gr.update(visible=True, value=api_json)
        )
    else:
        # Create new user
        create_user(username)
        return (
            f"✓ Created new user: {username}",
            str(DEFAULT_AGE),
            str(DEFAULT_LEXILE),
            "",
            gr.update(visible=True, value="")
        )


def save_user_profile(username, age, lexile, words_text, api_json):
    """Save user profile information."""
    if not username:
        return "Please select or create a user first"

    try:
        # Save user info
        age_int = int(age) if age else DEFAULT_AGE
        lexile_int = int(lexile) if lexile else DEFAULT_LEXILE
        save_user_info(username, age_int, lexile_int)

        # Save words
        words = [w.strip() for w in words_text.split('\n') if w.strip()]
        save_words(username, words)

        # Save API config
        if api_json.strip():
            api_config = json.loads(api_json)
            save_api_config(username, api_config)

        word_count = get_word_count(username)
        return f"✓ Saved profile for {username} ({word_count} words in bank)"
    except Exception as e:
        return f"✗ Error saving profile: {str(e)}"


def handle_deduplicate(username):
    """Deduplicate words in word bank."""
    if not username:
        return "Please select a user first", ""

    removed = deduplicate_words(username)
    words_text = "\n".join(load_words(username))
    return f"✓ Removed {removed} duplicate words", words_text


def get_provider_models(username, api_json):
    """Get available providers and models from API config."""
    if not api_json.strip():
        return gr.update(choices=[]), gr.update(choices=[])

    try:
        api_config = json.loads(api_json)
        providers = list(api_config.keys())
        return gr.update(choices=providers, value=providers[0] if providers else None), gr.update(choices=[])
    except:
        return gr.update(choices=[]), gr.update(choices=[])


def update_model_choices(provider, api_json):
    """Update model choices based on selected provider."""
    if not provider or not api_json.strip():
        return gr.update(choices=[])

    try:
        api_config = json.loads(api_json)
        if provider in api_config and 'models' in api_config[provider]:
            models = api_config[provider]['models']
            return gr.update(choices=models, value=models[0] if models else None)
    except:
        pass

    return gr.update(choices=[])


def generate_content(username, provider, model, api_json):
    """Generate article and questions."""
    global current_article, current_questions, current_client

    if not username:
        return "Please select a user first", "", gr.update(visible=False), None, None, None

    if not provider or not model:
        return "Please select AI provider and model", "", gr.update(visible=False), None, None, None

    try:
        # Load user info and words
        info = load_user_info(username)
        if not info:
            return "Please save user profile first", "", gr.update(visible=False), None, None, None

        words = load_words(username)
        if len(words) < 5:
            return "Please add at least 5 words to the word bank", "", gr.update(visible=False), None, None, None

        # Get API key
        api_config = json.loads(api_json)
        if provider not in api_config or 'api_key' not in api_config[provider]:
            return f"API key not found for {provider}", "", gr.update(visible=False), None, None, None

        api_key = api_config[provider]['api_key']

        # Create AI client
        current_client = get_client(provider, model, api_key)

        # Generate content
        result = generate_article_and_questions(
            words, info['age'], info['lexile_level'], current_client
        )

        if not result:
            return "✗ Failed to generate content", "", gr.update(visible=False), None, None, None

        current_article = result['article']
        current_questions = result['questions']

        # Build question UI components
        question_components = []
        for i, q in enumerate(current_questions):
            question_components.append(f"**Question {i+1}** ({q['type']})\n\n{q['question']}")

        return (
            "✓ Content generated successfully!",
            current_article,
            gr.update(visible=True),
            *question_components
        )

    except Exception as e:
        return f"✗ Error: {str(e)}", "", gr.update(visible=False), None, None, None


def submit_answers(username, ans1, ans2, ans3, ans4, ans5):
    """Submit and evaluate answers."""
    global current_article, current_questions, current_client

    if not current_questions or not current_client:
        return "Please generate content first", ""

    try:
        user_answers = [ans1, ans2, ans3, ans4, ans5]

        # Evaluate answers
        evaluation = evaluate_answers(current_questions, user_answers, current_client)

        if not evaluation:
            return "✗ Failed to evaluate answers", ""

        # Save log
        save_test_log(username, current_article, current_questions, user_answers, evaluation)

        # Format results
        result_text = f"# Test Results\n\n**Score: {evaluation['score']}/100**\n\n"
        result_text += f"## Item Analysis\n\n"

        for i, analysis in enumerate(evaluation['item_analysis'], 1):
            correct = analysis.get('correct', False)
            status = "✓" if correct else "✗"
            result_text += f"{status} **Question {i}**: {analysis.get('feedback', 'N/A')}\n\n"

        result_text += f"## Overall Feedback\n\n{evaluation['overall_feedback']}\n\n"
        result_text += f"## Suggestions\n\n{evaluation['suggestions']}"

        return "✓ Answers submitted and evaluated!", result_text

    except Exception as e:
        return f"✗ Error: {str(e)}", ""


def load_history(username):
    """Load test history for user."""
    if not username:
        return "Please select a user first", []

    logs = get_user_logs(username)

    if not logs:
        return "No test history found", []

    # Create list of log summaries
    log_choices = []
    for log in logs:
        timestamp = log.get('timestamp', 'Unknown')
        score = log.get('score', 'N/A')
        log_choices.append(f"{timestamp} - Score: {score}/100")

    return f"Found {len(logs)} test records", log_choices


def display_log_detail(username, selected_log):
    """Display detailed log."""
    if not username or not selected_log:
        return "Please select a log entry"

    logs = get_user_logs(username)

    # Find the selected log by timestamp
    for log in logs:
        timestamp = log.get('timestamp', 'Unknown')
        score = log.get('score', 'N/A')
        log_label = f"{timestamp} - Score: {score}/100"

        if log_label == selected_log:
            return format_log_for_display(log)

    return "Log not found"


# Build Gradio interface
with gr.Blocks(title="English Learning System", theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🎓 English Learning System")
    gr.Markdown("AI-powered English reading practice with personalized content generation")

    with gr.Tabs():
        # Tab 1: User Management
        with gr.Tab("👤 User Management"):
            with gr.Row():
                with gr.Column():
                    user_dropdown = gr.Dropdown(
                        choices=list_users(),
                        label="Select Existing User",
                        allow_custom_value=True
                    )
                    refresh_btn = gr.Button("🔄 Refresh User List", size="sm")
                    user_status = gr.Textbox(label="Status", interactive=False)

                with gr.Column():
                    age_input = gr.Number(label="Age", value=DEFAULT_AGE, precision=0)
                    lexile_input = gr.Number(label="Lexile Level", value=DEFAULT_LEXILE, precision=0)

            api_config_box = gr.TextArea(
                label="API Configuration (JSON)",
                placeholder='{"anthropic": {"api_key": "sk-ant-...", "models": ["claude-3-5-sonnet-20241022"]}}',
                lines=10,
                visible=False
            )

            save_profile_btn = gr.Button("💾 Save Profile", variant="primary")
            save_status = gr.Textbox(label="Save Status", interactive=False)

        # Tab 2: Word Bank
        with gr.Tab("📚 Word Bank"):
            word_bank_box = gr.TextArea(
                label="Word Bank (one word per line)",
                placeholder="apple\nbanana\ncomputer",
                lines=15
            )

            with gr.Row():
                dedupe_btn = gr.Button("🔧 Remove Duplicates")
                dedupe_status = gr.Textbox(label="Status", interactive=False)

        # Tab 3: Learning
        with gr.Tab("✏️ Start Learning"):
            with gr.Row():
                provider_dropdown = gr.Dropdown(label="AI Provider", choices=[])
                model_dropdown = gr.Dropdown(label="Model", choices=[])

            generate_btn = gr.Button("🚀 Generate Article & Questions", variant="primary")
            gen_status = gr.Textbox(label="Status", interactive=False)

            article_box = gr.Textbox(label="Article", lines=10, interactive=False)

            with gr.Column(visible=False) as questions_section:
                gr.Markdown("## Questions")

                q1_text = gr.Markdown()
                a1_input = gr.Textbox(label="Your Answer", placeholder="Enter your answer")

                q2_text = gr.Markdown()
                a2_input = gr.Textbox(label="Your Answer", placeholder="Enter your answer")

                q3_text = gr.Markdown()
                a3_input = gr.Textbox(label="Your Answer", placeholder="Enter your answer")

                q4_text = gr.Markdown()
                a4_input = gr.Textbox(label="Your Answer", placeholder="Enter your answer")

                q5_text = gr.Markdown()
                a5_input = gr.Textbox(label="Your Answer", placeholder="Enter your answer")

                submit_btn = gr.Button("📝 Submit Answers", variant="primary")

            submit_status = gr.Textbox(label="Status", interactive=False)
            results_box = gr.Markdown()

        # Tab 4: History
        with gr.Tab("📊 Learning History"):
            history_user = gr.Textbox(label="Username", interactive=False)
            load_history_btn = gr.Button("📖 Load History")
            history_status = gr.Textbox(label="Status", interactive=False)

            log_selector = gr.Radio(label="Select Test Record", choices=[])
            log_detail = gr.Markdown()

    # Event handlers
    refresh_btn.click(
        fn=lambda: gr.update(choices=list_users()),
        outputs=user_dropdown
    )

    user_dropdown.change(
        fn=handle_user_selection,
        inputs=user_dropdown,
        outputs=[user_status, age_input, lexile_input, word_bank_box, api_config_box]
    )

    save_profile_btn.click(
        fn=save_user_profile,
        inputs=[user_dropdown, age_input, lexile_input, word_bank_box, api_config_box],
        outputs=save_status
    )

    dedupe_btn.click(
        fn=handle_deduplicate,
        inputs=user_dropdown,
        outputs=[dedupe_status, word_bank_box]
    )

    # Update provider/model dropdowns when API config changes
    api_config_box.change(
        fn=get_provider_models,
        inputs=[user_dropdown, api_config_box],
        outputs=[provider_dropdown, model_dropdown]
    )

    provider_dropdown.change(
        fn=update_model_choices,
        inputs=[provider_dropdown, api_config_box],
        outputs=model_dropdown
    )

    generate_btn.click(
        fn=generate_content,
        inputs=[user_dropdown, provider_dropdown, model_dropdown, api_config_box],
        outputs=[gen_status, article_box, questions_section, q1_text, q2_text, q3_text, q4_text, q5_text]
    )

    submit_btn.click(
        fn=submit_answers,
        inputs=[user_dropdown, a1_input, a2_input, a3_input, a4_input, a5_input],
        outputs=[submit_status, results_box]
    )

    # History tab
    user_dropdown.change(
        fn=lambda x: x,
        inputs=user_dropdown,
        outputs=history_user
    )

    load_history_btn.click(
        fn=load_history,
        inputs=history_user,
        outputs=[history_status, log_selector]
    )

    log_selector.change(
        fn=display_log_detail,
        inputs=[history_user, log_selector],
        outputs=log_detail
    )


if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)
