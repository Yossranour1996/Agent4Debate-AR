from typing import Dict

from src.agent.backbone import BaseAgent
from src.agent.utils import is_function_call


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
        topic = self.task_prompt.format(
            topic=topic,
            position=position
        )
        
        result = self.user.initiate_chat(
            self.manager,
            message=self.user.message_generator,
            topic=topic,
            prompt = self.system_prompt,
        )
        
        self.record(result)
        
        chat_history = result.chat_history
        reference = self.get_reference(chat_history)
        result = self.get_result(chat_history)
        
        
        return {
            "result": result,
            "reference": reference,
            "chat_history": chat_history
        }