from time import sleep
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from autogen import config_list_from_json
from autogen.agentchat import Agent, UserProxyAgent
from autogen.code_utils import UNKNOWN, execute_code, extract_code, infer_lang
from autogen.math_utils import get_answer
from openai import OpenAI

from src.agent.database.db import get_cached_answer, save_query
from src.agent.tool.tavily_ai_unwarp import TavilySearchAPIWrapper


SYN_SYSTEM="""# Role: Intelligent Information Synthesizer
## Profile:
You are an advanced Information Synthesizer AI. Your primary function is to process user queries and raw answers, organizing and synthesizing the information to provide a comprehensive and structured response.
### Core Competencies:
1. Information Analysis
2. Content Organization
3. Data Synthesis
4. Conclusion Drawing

## Workflow:
1. Carefully analyze the user's query/queries to fully comprehend the information request.
2. Thoroughly examine the provided raw answer(s) to understand the available information.
3. Match and categorize relevant information from raw answers to corresponding queries.
4. Remove extraneous symbols or formatting from raw answers during categorization.
5. Synthesize the organized information to identify common themes and draw conclusions.
6. Identify important information unrelated to the query and list it under "Others".

## Rules:
- Strictly adhere to the provided information; do not invent or add non-existent details.
- Process multiple queries and raw answers when provided.
- Discard any raw answers that are not important.
- Maintain the original language of the query in your response.
- Keep URLs in their original format without adding Markdown formatting.

## Output Format:
1. [Query 1]
- [Relevant answer excerpt, Source URL]
- [Additional relevant answer excerpt, Source URL]
...
2. [Query 2]
- [Relevant answer excerpt, Source URL]
- [Additional relevant answer excerpt, Source URL]
...

Synthesized Conclusions:
- [Key finding or conclusion 1]
- [Key finding or conclusion 2]
...
Others:
- [Important information unrelated to the queries]
- [Important information unrelated to the queries]
..."""


def get_synthesized_output(sys_config: dict, query: str, answer: str):
    sys_config = sys_config["config_list"][0]
    print(sys_config)
    client = OpenAI(
        api_key=sys_config.get("api_key"),
        base_url=sys_config.get("base_url", "https://api.openai.com"),
    )
    
    inputs_query = """User's query/queries: {query}
    Raw answers: {answer}
    Please process the above input according to the specified workflow and rules, and provide your synthesized output."""
    
    while True:
        try:
            response = client.chat.completions.create(
                model = sys_config.get("model"),
                messages=[
                    {"role": "system", "content": SYN_SYSTEM},
                    {"role": "user", "content": inputs_query.format(
                        query = query, answer=answer
                    )}
                ]
            )
            output = response.choices[0].message.content
            save_query(
                query = query + "\n" + answer,
                answer = output
            )
            return output
        except:
            print("Error: ", response.text)
            sleep(1)
            continue

def _is_termination_msg_debatechat(message):
    """Check if a message is a termination message."""
    if isinstance(message, dict):
        message = message.get("content")
        if message is None:
            return False
    cb = extract_code(message)
    contain_code = False
    for c in cb:
        if c[0] == "python" or c[0] == "wolfram" or c[0] == "tavily":
            contain_code = True
            break

    if "\\boxed{finished}" in message or "\\boxed{FINISHED}" in message or "\\boxed{Finished}" in message:
        return True
    
    return not contain_code and get_answer(message) is not None and get_answer(message) != ""

class CustomDebateUserProxyAgent(UserProxyAgent):
    """(Experimental) A MathChat agent that can handle Tavily queries."""
    MAX_CONSECUTIVE_AUTO_REPLY = 15  # maximum number of consecutive auto replies (subject to future change)
    DEFAULT_REPLY = "Continue. Please keep complete the instruction until you need to query. (If you have completed the task, please organize and refine your deliverables, then output \\boxed{finished}.)"
    
    def __init__(
        self,
        name: Optional[str] = "DebateAgent",
        is_termination_msg: Optional[
            Callable[[Dict], bool]
        ] = _is_termination_msg_debatechat,  # terminate if \boxed{} in message
        human_input_mode: Optional[str] = "NEVER",  # Fully automated
        default_auto_reply: Optional[Union[str, Dict, None]] = DEFAULT_REPLY,
        max_invalid_q_per_step=3,
        use_synthesizer: Optional[bool] = False,
        llm_config: Optional[Dict] = None,
        **kwargs,
    ):
        super().__init__(
            name=name,
            is_termination_msg=is_termination_msg,
            human_input_mode=human_input_mode,
            default_auto_reply=default_auto_reply,
            **kwargs,
        )
        self.register_reply([Agent, None], CustomDebateUserProxyAgent._generate_debate_reply, position=2)
        # fixed var
        self._max_invalid_q_per_step = max_invalid_q_per_step
        # mutable
        self._valid_q_count = 0
        self._total_q_count = 0
        self._accum_invalid_q_per_step = 0
        self._previous_code = ""
        self.last_reply = None
        self.use_systhesizer = use_synthesizer
        self.llm_config = llm_config
        
    @staticmethod
    def message_generator(sender, recipient, context):
        sender._reset()
        topic = context.get("topic")
        prompt = context.get("prompt", None)
        assert prompt is not None, "The prompt is not provided in the context."
        return prompt + topic

    def _reset(self):
        # super().reset()
        self._valid_q_count = 0
        self._total_q_count = 0
        self._accum_invalid_q_per_step = 0
        self._previous_code = ""
        self.last_reply = None
    
    def execute_one_tavily_query(self, query: str):
        # search query in the local da
        cached_answer = get_cached_answer(query)
        if cached_answer is not None:
            return cached_answer[0], True
        
        #TODO
        tavily = TavilySearchAPIWrapper()
        output, is_success = tavily.run(query, max_results=5)
        if output == "":
            output = "Error: The tavily query is invalid."
            is_success = False
        
        # save query to the local db
        if is_success:
            save_query(query, output)
        return output, is_success

    def execute_batch_tavily_query(self, query: str):
        queies = query.split("\n")
        is_success = False
        outputs = ""
        for q in queies:
            output, is_success = self.execute_one_tavily_query(q)
            if is_success:
                outputs += output + "\n"
        if is_success is False:
            outputs = "Error: The tavily query is invalid."
            return outputs, is_success

        return outputs, True
            
    def _generate_debate_reply(
        self, 
        messages: Optional[List[Dict]]=None,
        sender: Optional[Agent]=None,
        config: Optional[Dict]=None,
    ):
        if messages is None:
            messages = self._oai_messages[sender]
        message = messages[-1]
        message = message.get("content", "")
        code_blocks = extract_code(message)
        
        if len(code_blocks) == 1 and code_blocks[0][0] == UNKNOWN:
            return True, self._default_auto_reply
        is_success, all_success = True, True
        reply = ""
        for code_block in code_blocks:
            lang, code = code_block
            if lang == "tavily":
                # output, is_success = self.execute_one_tavily_query(code)
                output, is_success = self.execute_batch_tavily_query(code)
            else:
                output = "Error: Unknown language or Tool name, please check it."
                is_success = False
            reply += output + "\n"
            if not is_success:
                all_success = False
                self._valid_q_count -= 1

        reply = reply.strip()
        
        if self.use_systhesizer:
            query = "\n".join([c[1] for c in code_blocks])
            _reply = get_cached_answer(
                query=query + "\n" + reply
            )
            if _reply is not None:
                reply = _reply[0]
            else:
                reply = get_synthesized_output(sys_config=self.llm_config, query=query, answer=reply)
        
        if self.last_reply == reply:
            return True, reply + "\nYour query or result is same from the last, please try a new approach."
        self.last_reply = reply
        
        if not all_success:
            self._accum_invalid_q_per_step += 1
            if self._accum_invalid_q_per_step > self._max_invalid_q_per_step:
                self._accum_invalid_q_per_step = 0
                reply = "Error. Please revisit the problem statement and your reasoning. If you think this step is correct, solve it yourself and continue the next step. Otherwise, correct this step."
        return True, reply