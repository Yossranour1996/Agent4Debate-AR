from autogen.code_utils import extract_code

def is_function_call(msg):
    if isinstance(msg, dict):
        msg = msg.get("content", None)
        if msg is None:
            return False
    cb = extract_code(msg)
    contain_code = False
    for c in cb:
        if c[0] == "tavily":
            return True
    return False