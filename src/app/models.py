from pydantic import BaseModel
from typing import List, Dict, Optional

class MethodList(BaseModel):
    Method: List[str]

class BaseInput(BaseModel):
    Topic: str
    Position: str
    Language: str = "ar"
    Model: Optional[str] = "deepseek-chat"
    
class RebuttalInput(BaseInput):
    PositiveArgument: str
    NegativeArgument: str
    PositiveRebuttal: Optional[str] = ""
    Reference: Optional[str] = ""
    
class SummaryInput(RebuttalInput):
    NegativeRebuttal: str
    NegativeSummary: Optional[str] = ""
    Reference: Optional[str] = ""
    
class AgentOutput(BaseModel):
    Reference: str
    Result: str
    ChatHistory: List[Dict]

class AgentDebugInput(BaseModel):
    Language: str
    Position: str
    
class AgentDebugOutput(BaseModel):
    ArgumentPrompt: Dict[str, str]
    RebuttalPrompt: Dict[str, str]
    SummaryPrompt: Dict[str, str]
    