from typing import Dict

from src.agent.backbone import BaseAgent
from src.agent.utils import is_function_call

import traceback

class ArgumentAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def select_speaker_function(self, last_speaker, groupchat):
        messages = groupchat.messages
        last_message = messages[-1].get("content", None)
        
        if len(messages) <= 1:
            return self.get_agent(name="searcher")

        if len(last_message) > 1 and is_function_call(last_message):
            return self.user
        
        if last_speaker is self.get_agent(name="searcher"):
            if is_function_call(last_message) or "```tavily" in last_message:
                return self.user
            return self.user

        if last_speaker is self.get_agent(name="analyzer"):
            return self.get_agent(name="writer")
        
        if last_speaker is self.user:
            if "Error" in last_message:
                return self.get_agent(name="searcher")
            if messages[-2]["name"] == "searcher":
                if len(messages) > 3 and messages[-3]["name"] == "writer":
                    return self.get_agent(name="writer")
                elif messages[-3]["name"] == "analyzer":
                    return self.get_agent(name="analyzer")
                elif messages[-3]["name"] == "admin":
                    return self.get_agent(name="analyzer")
                else:
                    return self.get_agent(name="searcher")
        
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
            if "FINISHED" in last_message:
                return self.user
            return self.get_agent(name="writer")

        return "auto"
    
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
    
    def get_reference(self, chat_history) -> str:
        reference = ""
        for his in chat_history[1:]:
            if his["role"] == "assistant":
                if "URL" in his["content"] or "url" in his["content"] or "http" in his["content"]:
                    reference += his["content"]
        return reference
    
    def get_result(self, chat_history) -> str:
        print(chat_history)
        for his in reversed(chat_history):
            if his.get("name", None) == "writer":
                result = his["content"]
                if "REVISION" not in result and "revise" not in result and "SEARCH" not in result:
                    break
            else:
                continue
            
        return self.postprocess(result)
    
    def run(self, topic, position) -> Dict:
    # Format the topic and enforce UTF-8 for debug
        topic = self.task_prompt.format(
            topic=topic,
            position=position
        )

        # Try to initiate chat and handle any exceptions
        try:
            result = self.user.initiate_chat(
                self.manager,
                message=self.user.message_generator,
                topic=topic,
                prompt=self.system_prompt,
            )
        except Exception as e:
            print("Error during initiate_chatkkl:", str(e))
            print("Error during initiate_chatkk:", str(e).encode("utf-8", errors="replace").decode("utf-8"))
            print("Traceback:")
            traceback.print_exc()
            return {
                "result": "Error occurred during chat initiation",
                "reference": "N/A",
                "chat_history": []
            }

        # Log the result to debug


        # Ensure chat_history exists
        if not hasattr(result, 'chat_history'):
            print("Error: 'chat_history' not found in result")
            return {
                "result": "No chat history",
                "reference": "N/A",
                "chat_history": []
            }

        # Process the chat history
        chat_history = result.chat_history
        reference = self.get_reference(chat_history)
        result_text = self.get_result(chat_history)

        return {
            "result": result_text,
            "reference": reference,
            "chat_history": chat_history
        }