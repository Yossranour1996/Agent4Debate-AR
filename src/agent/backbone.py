import json
import warnings
from abc import ABC, abstractmethod
from typing import Dict, List

import autogen
from autogen import ChatResult, OpenAIWrapper

class BaseAgent(ABC):
    def __init__(self, roles: List, user, system_prompt_map: Dict, task_prompt_map: Dict, llm_config: List[Dict], max_round: int = 25):
        self.roles = roles
        self.user = user
        self.llm_config = llm_config
        self.system_prompt_map = {k: open(v, 'r').read() for k, v in system_prompt_map.items()}
        self.task_prompt_map = {k: open(v, 'r').read() for k, v in task_prompt_map.items()}
        
        group = [user] + [role.agent for role in self.roles]
        self.groupchat = autogen.GroupChat(
            agents=group,
            messages=[],
            max_round=max_round,
            admin_name="admin",
            speaker_selection_method=self.select_speaker_function,
            speaker_transitions_type="allowed"
        )
        self.manager = autogen.GroupChatManager(
            groupchat=self.groupchat,
            llm_config={
                "config_list": self.llm_config
            }
        )
        
    def get_agent(self, name: str):
        if name == "admin":
            return self.user
        
        for role in self.roles:
            if role.name == name:
                return role.agent
        raise ValueError(f"Role {name} not found.")
    
    def get_prompt(self):
        prompts = dict(
            task = self.task_prompt,
            system = self.system_prompt,
        )
        for role in self.roles:
            prompts.update(
                {
                    role.name: role.agent._oai_system_message[0]["content"]
                }
            )
        return prompts
    
    def switch_language(self, lang="zh"):
        self.task_prompt = self.task_prompt_map.get(lang)
        self.system_prompt = self.system_prompt_map.get(lang)
        
        for role in self.roles:
            role.switch_language(lang)
    
    def get_model_config(self, model: str):
        try:
            llm_config = autogen.config_list_from_json(
                "OAI_CONFIG_LIST",
                filter_dict={
                    "model": model
                }    
            )
            return llm_config
        except Exception as e:
            ValueError(f"get {model} from config error, {e}")
            
    def switch_model(self, model: str):
        for role in self.roles:
            role.switch_model(self.get_model_config(model=model))
        
        llm_config = {
            "config_list": self.get_model_config(model=model)
        }
        self.manager.client = OpenAIWrapper(**llm_config)
        self.groupchat.agents[0].llm_config = llm_config
        
        warning_info = f"switch model to {model}"
        warnings.warn(warning_info)
        
    def switch_prompt(self, lang: str, position: str):
        try:
            self.task_prompt = self.task_prompt_map[f"{lang}_{position}"]
        except:
            warning_info = f"Task Prompt {lang}_{position} not found, using default {lang} instead."
            warnings.warn(warning_info)
            self.task_prompt = self.task_prompt_map.get(lang)
        
        try:
            self.system_prompt = self.system_prompt_map[f"{lang}_{position}"]
        except:
            warning_info = f"System Prompt {lang}_{position} not found, using default {lang} instead."
            warnings.warn(warning_info)
            self.system_prompt = self.system_prompt_map.get(lang)
        
        for role in self.roles:
            role.switch_prompt(lang, position)
    
    def record(self, result: ChatResult):
        record = dict(
            chat_id= result.chat_id,
            chat_history= result.chat_history,
            cost= result.cost,
        )
        with open("log/agent/log.jsonl", "a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
          
    @abstractmethod
    def select_speaker_function(self, last_speaker, groupchat):
        pass
    
    @abstractmethod
    def run(self):
        pass
    
    @abstractmethod
    def get_result(self, **kwargs):
        pass
    
    @abstractmethod
    def get_reference(self, **kwargs):
        pass