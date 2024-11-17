from typing import Dict, List
from src.agent.backbone import BaseAgent
from src.agent.utils import is_function_call
import traceback  # Make sure this import is included

class SummaryAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def select_speaker_function(self, last_speaker, groupchat):
        messages = groupchat.messages
        last_message = messages[-1].get("content", None)
        
        if len(messages) <= 1:
            return self.get_agent(name="analyzer")
        if len(last_message) > 1 and is_function_call(last_message):
            return self.user
        
        if last_speaker is self.get_agent(name = "searcher"):
            if is_function_call(last_message) or "```tavily" in last_message:
                return self.user
            if messages[-2]["name"] == "user" and "Error" in messages[-2]["content"]:
                return self.get_agent(name="writer")
            return self.user
        
        if last_speaker is self.user:
            if "Error" in last_message:
                return self.get_agent(name="searcher")
            if messages[-2]["name"] == "searcher":
                return self.get_agent(name="writer")
        
        if last_speaker is self.get_agent(name="analyzer"):
            return self.get_agent(name="writer")
        
        if last_speaker is self.get_agent(name="writer"):
            if "FINISHED" in last_message:
                return self.get_agent(name="reviewer")
            elif "SEARCH" in last_message:
                return self.get_agent(name="searcher")
            else:
                return self.get_agent(name="reviewer")
            
        if last_speaker is self.get_agent(name="reviewer"):
            if "REVISION" in last_message or "revise" in last_message:
                return self.get_agent(name="writer")
            if "FINISHED" in last_message or "\\boxed{finished}" in last_message:
                return self.user
            return self.get_agent(name="writer")
        
        return "auto"
    
    def get_reference(self, reference: str, chat_history) -> str:
        for his in chat_history[1:]:
            if "URL" in his["content"] or "url" in his["content"] or "http" in his["content"]:
                if "URL" in his["content"]:
                    reference += his["content"]
        return reference
    
    def get_result(self, chat_history) -> str:
        for his in reversed(chat_history):
            if his["name"] == "writer" and "<review>" not in his["content"] and "<fix>" not in his["content"]:
                result = his["content"]
                break
        return self.postprocess(result)
    
    def postprocess(self, result) -> str:
        result = result.split("<output>")
        if len(result) > 1:
            result = result[1]
        else:
            result = result[0]
            
        result = result.replace("FINISHED", "")
        result = result.replace("SEARCH", "")
        result = result.replace("REVISION", "")
        result = result.replace("<output>", "").replace("</output>", "")
        
        return result
    

    def run(self, topic: str, position: str,
            positive_argument: str, negative_argument: str, 
            positive_rebuttal: str, negative_rebuttal: str, 
            negative_summary: str, reference: str) -> Dict:
        
        # Format the topic with relevant arguments
        topic = self.task_prompt.format(
            Topic=topic,
            Position=position,
            PositiveArgument=positive_argument,
            NegativeArgument=negative_argument,
            PositiveRebuttal=positive_rebuttal,
            NegativeRebuttal=negative_rebuttal,
            NegativeSummary=negative_summary,
            Reference=reference
        )

        # Try to initiate chat and handle exceptions
        try:
            result = self.user.initiate_chat(
                self.manager,
                message=self.user.message_generator,
                topic=topic,
                prompt=self.system_prompt
            )
        except Exception as e:
            print("Error during initiate_chat:", str(e))
            print("Error (UTF-8):", str(e).encode("utf-8", errors="replace").decode("utf-8"))
            print("Traceback:")
            traceback.print_exc()
            return {
                "result": "Error occurred during chat initiation",
                "reference": "N/A",
                "chat_history": []
            }

        # Log the raw result for debugging

        # Ensure 'chat_history' exists in the result
        if not hasattr(result, 'chat_history'):
            print("Error: 'chat_history' not found in result")
            return {
                "result": "No chat history",
                "reference": "N/A",
                "chat_history": []
            }

        # Process the chat history
        chat_history = result.chat_history
        _reference = self.get_reference(reference=reference, chat_history=chat_history)
        result_text = self.get_result(chat_history)

        return {
            "result": result_text,
            "reference": _reference,
            "chat_history": chat_history
        }
