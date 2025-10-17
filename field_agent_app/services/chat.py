import json
import os
from typing import Dict, List

class ConversationStore:
    def __init__(self, store_path: str, max_turns: int = 5):
        self.store_path = store_path
        self.max_turns = max_turns
        os.makedirs(os.path.dirname(store_path), exist_ok=True)
        if not os.path.exists(self.store_path):
            with open(self.store_path, 'w') as f:
                json.dump([], f)

    def read_history(self) -> List[Dict[str, str]]:
        with open(self.store_path, 'r') as f:
            return json.load(f)

    def append_to_history(self, user_query: str, assistant_response: str):
        history = self.read_history()
        history.append({
            "user": user_query,
            "assistant": assistant_response
        })
        with open(self.store_path, 'w') as f:
            json.dump(history, f, indent=2)

    def get_recent_history(self) -> List[Dict[str, str]]:
        """Get the most recent N turns of the conversation."""
        history = self.read_history()
        return history[-self.max_turns:]

    @staticmethod
    def format_conversation(history: List[Dict[str, str]]) -> str:
        formatted = ""
        for turn in history:
            formatted += f"\nUser: {turn['user']}\nAssistant: {turn['assistant']}\n"
        return formatted.strip()

    def chat_prompt(self, user_query: str) -> str:
        """Build a chat prompt aligned with the business rules."""
        recent_history = self.get_recent_history()
        formatted_history = self.format_conversation(recent_history)

        prompt = f"""
            You are an expert Insurance Policy Assistant trained on official insurance guideline documents. You are supporting a licensed insurance agent by answering questions using only the information provided in the guidelines.

            ##Agent Query##
            {user_query}

            ##Conversation History##
            {formatted_history}

            ##Your Task##
            - Carefully review the provided guideline content retrieved by the system.
            - Respond clearly, accurately, and professionally to the agent’s question.
            - Structure your response as if advising the insurance agent directly, using the following guidance:
            * Reference specific policy sections, clauses, or guidance documents when applicable.
            * Highlight any conditions, exclusions, or regulatory nuances that the agent should be aware of.
            * Use language that is clear, business-formal, and helpful for client-facing use.

            ##Response Format##
            - Output your answer in **clean Markdown**.
            - Use bullet points or subheadings if needed for clarity.
            - Do not fabricate information or make assumptions beyond the provided guideline context.

            If the information required to answer the question is not found in the retrieved documents, state this explicitly and suggest the agent review the full policy manual or escalate to underwriting.
        """
        return prompt.strip()