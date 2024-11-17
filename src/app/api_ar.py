from fastapi import FastAPI, HTTPException, status
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from src.agent.argument import ArgumentAgent
from src.agent.rebuttal import RebuttalAgent
from src.agent.summary import SummaryAgent
from src.app.models import (AgentDebugInput, AgentDebugOutput, AgentOutput,
                            BaseInput, MethodList, RebuttalInput, SummaryInput)
import traceback

def create_app(argument_agent: "ArgumentAgent", rebuttal_agent: "RebuttalAgent", summary_agent: "SummaryAgent"):
    app = FastAPI(
        title="DebateAgent",
        summary="A multi-agent system of debate process, including argument, rebuttal, and summary agents."
    )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        print("Unhandled Exception:", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An unexpected error occurred.",
                "input": str(request),
                "error": str(exc)
            },
        )

    app.add_exception_handler(Exception, global_exception_handler)

    @app.get(
        "/v1/methods",
        response_model=MethodList,
        status_code=status.HTTP_200_OK,
    )
    async def list_methods():
        return MethodList(Method=["argument", "rebuttal", "summary"])

    @app.get(
        "/v1/prompts",
        response_model=AgentDebugOutput,
        status_code=status.HTTP_200_OK,
    )
    async def get_prompt(input: AgentDebugInput):
        language = input.Language
        position = input.Position
        if position in ["positive", "正方", "مؤيد"]:
            position = "pos"
        elif position in ["negative", "反方", "معارض"]:
            position = "neg"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Position must be 'positive'/'正方'/'مؤيد' or 'negative'/'反方'/'معارض'."
            )
        
        argument_agent.switch_prompt(lang=language, position=position)
        rebuttal_agent.switch_prompt(lang=language, position=position)
        summary_agent.switch_prompt(lang=language, position=position)
        
        return AgentDebugOutput(
            ArgumentPrompt=argument_agent.get_prompt(),
            RebuttalPrompt=rebuttal_agent.get_prompt(),
            SummaryPrompt=summary_agent.get_prompt()
        )

    @app.post(
        "/v1/argument",
        response_model=AgentOutput,
        status_code=status.HTTP_200_OK,
    )
    async def argument(input: BaseInput):
        lang = input.Language
        position = input.Position
        model = input.Model
        
        if position in ["positive", "正方", "مؤيد"]:
            position = "pos"
        elif position in ["negative", "反方", "معارض"]:
            position = "neg"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Position must be 'positive'/'正方'/'مؤيد' or 'negative'/'反方'/'معارض'."
            )
        
        argument_agent.switch_prompt(lang=lang, position=position)
        argument_agent.switch_model(model=model)
        
        result = argument_agent.run(
            topic=input.Topic,
            position=input.Position
        )
        return AgentOutput(
            Reference=result["reference"],
            Result=result["result"],
            ChatHistory=result["chat_history"]
        )

    @app.post(
        "/v1/rebuttal",
        response_model=AgentOutput,
        status_code=status.HTTP_200_OK,
    )
    async def rebuttal(input: RebuttalInput):
        lang = input.Language
        position = input.Position
        model = input.Model

        if position in ["positive", "正方", "مؤيد"]:
            position = "pos"
        elif position in ["negative", "反方", "معارض"]:
            position = "neg"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Position must be 'positive'/'正方'/'مؤيد' or 'negative'/'反方'/'معارض'."
            )

        rebuttal_agent.switch_prompt(lang=lang, position=position)
        rebuttal_agent.switch_model(model=model)

        result = rebuttal_agent.run(
            topic=input.Topic,
            position=input.Position,
            positive_argument=input.PositiveArgument,
            negative_argument=input.NegativeArgument,
            positive_rebuttal=input.PositiveRebuttal,
            reference=input.Reference
        )
        return AgentOutput(
            Reference=result["reference"],
            Result=result["result"],
            ChatHistory=result["chat_history"]
        )

    @app.post(
        "/v1/summary",
        response_model=AgentOutput,
        status_code=status.HTTP_200_OK,
    )
    async def summary(input: SummaryInput):
        lang = input.Language
        position = input.Position
        model = input.Model

        if position in ["positive", "正方", "مؤيد"]:
            position = "pos"
        elif position in ["negative", "反方", "معارض"]:
            position = "neg"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Position must be 'positive'/'正方'/'مؤيد' or 'negative'/'反方'/'معارض'."
            )

        summary_agent.switch_prompt(lang=lang, position=position)
        summary_agent.switch_model(model=model)

        result = summary_agent.run(
            topic=input.Topic,
            position=input.Position,
            positive_argument=input.PositiveArgument,
            negative_argument=input.NegativeArgument,
            positive_rebuttal=input.PositiveRebuttal,
            negative_rebuttal=input.NegativeRebuttal,
            negative_summary=input.NegativeSummary,
            reference=input.Reference
        )
        return AgentOutput(
            Reference=result["reference"],
            Result=result["result"],
            ChatHistory=result["chat_history"]
        )

    return app
