import autogen
from typing import List, Dict
import warnings
from autogen.oai import OpenAIWrapper

class Role(object):
    def __init__(self, name, prompt_map: Dict, llm_config: List[Dict], seed:int = 42):
        self.name = name
        # load prompt file
        self.prompt_map = {k: open(v, 'r').read() for k, v in prompt_map.items()}
        
        self.llm_config = llm_config
        self.seed = seed
        
        self.agent = self.init_agent()
        
    def get_name(self):
        return self.name
    
    def init_agent(self):
        agent = autogen.AssistantAgent(
            name = self.name,
            system_message=self.prompt_map.get("zh"),
            llm_config={
                "timeout": 600,
                "seed": self.seed,
                "config_list": self.llm_config,
            }
        )
        return agent

            
    def switch_model(self, model_config: dict):
        llm_config = {
            "timeout": 600,
            "seed": self.seed,
            "config_list": model_config,
        }
        self.agent.client = OpenAIWrapper(**llm_config)
    
    def switch_language(self, lang="zh"):
        self.agent._oai_system_message = [
            {
                "content": self.prompt_map.get(lang),
                "role": "system"
            }
        ]
        return self.agent
    
    def switch_prompt(self, lang: str, position: str):
        target = f"{lang}_{position}"
        try:
            content = self.prompt_map[target]
            self.agent._oai_system_message = [
                {
                    "content": content,
                    "role": "system"
                }
            ]
            return self.agent
        except Exception as e:
            warning_info = f"{self.name}'s Prompt {target} not found, using default {lang} instead."
            warnings.warn(warning_info)
            self.switch_language(lang)
        
