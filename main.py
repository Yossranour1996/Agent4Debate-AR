import argparse
import os

import autogen
import uvicorn
import yaml

from src.agent import (ArgumentAgent, CustomDebateUserProxyAgent,
                       RebuttalAgent, Role, SummaryAgent)
from src.app import create_app


def get_args():
    parser = argparse.ArgumentParser(description='Debate Agent')
    parser.add_argument('--port', type=int, default=8081, help='Port number')
    parser.add_argument('--seed', type=int, default=3347, help='Seed number')
    parser.add_argument('--use_synthesizer', type=bool, default=True, help='Use synthesizer')
    return parser.parse_args()

def load_agent(name, config):
    analyzer = Role("analyzer", prompt_map=config.get("analyzer"), llm_config=llm_config)
    writer = Role("writer", prompt_map=config.get("writer"), llm_config=llm_config)
    reviewer = Role("reviewer", prompt_map=config.get("reviewer"), llm_config=llm_config)
    if name == "argument":
        agent = ArgumentAgent(
            roles = [searcher, writer, reviewer, analyzer], 
            user = user, 
            llm_config=llm_config,
            task_prompt_map = config.get("task"),
            system_prompt_map = config.get("system"),
            max_round=15,
        )
    elif name == "rebuttal":
        agent = RebuttalAgent(
            roles = [searcher, writer, reviewer, analyzer], 
            user = user, 
            llm_config=llm_config,
            task_prompt_map = config.get("task"),
            system_prompt_map = config.get("system"),
            max_round=15,
        )
    elif name == "summary":
        agent = SummaryAgent(
            roles = [searcher, writer, reviewer, analyzer], 
            user = user, 
            llm_config=llm_config,
            task_prompt_map = config.get("task"),
            system_prompt_map = config.get("system"),
            max_round=15,
        )
    else:
        raise ValueError(f"Agent {name} not found.")
    
    return agent

# init config
config = get_args() 

llm_config = autogen.config_list_from_json(
    "OAI_CONFIG_LIST", filter_dict={"model": "google/gemini-pro-1.5"}
)
argument_config = yaml.load(
    open("config/argument.yaml", 'r'), Loader=yaml.FullLoader
)
rebuttal_config = yaml.load(
    open("config/rebuttal.yaml", 'r'), Loader=yaml.FullLoader
)
summary_config = yaml.load(
    open("config/summary.yaml", 'r'), Loader=yaml.FullLoader
)

# load prompt
searcher = Role("searcher", prompt_map=argument_config.get("searcher"), llm_config=llm_config, seed=config.seed)

user = CustomDebateUserProxyAgent(
    name = "admin",
    human_input_mode="NEVER",
    code_execution_config={"use_docker": False},
    use_synthesizer=True,
    llm_config=llm_config
)
## argument
argument_agent = load_agent(name = "argument", config = argument_config)
## rebuttal
rebuttal_agent = load_agent(name = "rebuttal", config = rebuttal_config)
## summary
summary_agent = load_agent(name = "summary", config = summary_config)

app = create_app(argument_agent, rebuttal_agent, summary_agent)

uvicorn.run(app, host="127.0.0.1", port=config.port, log_level="info")