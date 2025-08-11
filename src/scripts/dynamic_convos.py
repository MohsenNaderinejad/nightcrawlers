import sys, pathlib, os, json
parent_dir = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))
from openai import OpenAI
import config

client = OpenAI(api_key="tpsg-QQNyEJBytksu6qJXfeQjd87Frj0Av8h", base_url="https://api.metisai.ir/openai/v1")

def fetch_completion(entity, game):
    prompt_section = config.PROMPTS.get(entity, "")
    prompt = prompt_section.get(str(game.level.phase_number), "")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        reply = response.choices[0].message.content

        if os.path.exists(f"src/scripts/{entity}.json"):
            with open(f"src/scripts/{entity}.json", "r") as f:
                data = json.load(f)
        else:
            data = {}

        if str(game.level.phase_number) not in data:
            data[str(game.level.phase_number)] = []

        data[str(game.level.phase_number)].append(reply)

        with open(f"src/scripts/{entity}.json", "w") as f:
            json.dump(data, f, indent=4)

        game.responses[entity][str(game.level.phase_number)][reply] = False
        game.can_show_reply = True
        game.replier_chosen = True

    except Exception as e:
        reply = f"Error: {e}"