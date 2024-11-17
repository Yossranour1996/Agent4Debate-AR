import yaml
from typing import List, Dict
import glob
import os

def calculate_id(file_root):
    file_list = glob.glob(os.path.join(file_root, "motion", "*.yml"))
    return len(file_list) + 1

model_map = {
    "google/gemini-pro-1.5": "GeminiPro15",
    "google/gemini-flash-1.5": "GeminiFlash15",
    "anthropic/claude-3-haiku": "ClaudeHaiku3",
    "anthropic/claude-3.5-sonnet": "ClaudeSonnet35",
    "openai/gpt-4o-mini": "GPT4oMini",
    "openai/gpt-4o": "GPT4o",
    "deepseek-chat": "DeepSeekChat",
    "qwen/qwen-2-72b-instruct": "Qwen72b",
    "glm-4-air": "GLM4",
    "human": "human",
    "baseline": "baseline",
}

def save_ar_result(preset: str, topic: str, messages: List[Dict], pos_model: str, neg_model: str):
    template = dict(
        motion=topic,
        pro_side=[dict(name=" المؤيد")],
        con_side=[dict(name=" المعارض")],
        pro_model=[dict(model=pos_model)],
        con_model=[dict(model=neg_model)],
        info_slide="لدى الطرفين المؤيد والمعارض مسؤولية إثبات متساوية",
        speech_order=[" المؤيد", " المعارض", " المؤيد", " المعارض", " المعارض", " المؤيد"],
    )

    speech = [
        dict(
            debater_name=" المؤيد",
            content=messages[0]["content"]
        ),
        dict(
            debater_name=" المعارض",
            content=messages[1]["content"]
        ),
        dict(
            debater_name=" المؤيد",
            content=messages[2]["content"]
        ),
        dict(
            debater_name=" المعارض",
            content=messages[3]["content"]
        ),
        dict(
            debater_name=" المعارض",
            content=messages[4]["content"]
        ),
        dict(
            debater_name=" المؤيد",
            content=messages[5]["content"]
        ),
    ]
    
    file_root = os.path.join("output", preset)
    os.makedirs(os.path.join(file_root, "motion"), exist_ok=True)
    os.makedirs(os.path.join(file_root, "speech"), exist_ok=True)
    
    ids = str(calculate_id(file_root)).zfill(4)

    try:
        pos_model = model_map[pos_model]
        neg_model = model_map[neg_model]
    except KeyError:
        raise ValueError("Model not found")
    except Exception as e:
        raise e
    
    yaml.dump(
        template,
        open(f"{file_root}/motion/{preset}_ar_{pos_model}_{neg_model}_{ids}.yml", "w"),
        allow_unicode=True, sort_keys=False,
    )
    
    yaml.dump(
        speech,
        open(f"{file_root}/speech/{preset}_ar_{pos_model}_{neg_model}_{ids}.yml", "w"),
        allow_unicode=True, sort_keys=False,
    )
    
    with open(f"{file_root}/motion/motion_list.txt", "a") as f:
        content = f"{preset}_ar_{pos_model}_{neg_model}_{ids}  {topic}\n"
        f.write(content)
