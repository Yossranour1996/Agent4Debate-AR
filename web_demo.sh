set -x
export TAVILY_API_KEY=""
nohup python main.py > output/api.log 2>&1 &
streamlit run src/arena_eng.py