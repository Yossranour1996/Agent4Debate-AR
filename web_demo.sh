export TAVILY_API_KEY=fill your taily api key here

nohup python main.py > output/api.log 2>&1 &
streamlit run src/arena.py