python -m venv .venv
if [[ "$OSTYPE" == "msys" ]]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate	
fi
# pip install -r requirements.txt
pip install -e .
