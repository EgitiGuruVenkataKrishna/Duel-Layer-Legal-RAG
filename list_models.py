import os
import requests

def list_models():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY environment variable is not set in this terminal.")
        return

    print("Fetching available models from Groq...")
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get("https://api.groq.com/openai/v1/models", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        models = [m["id"] for m in data.get("data", [])]
        print("\n--- AVAILABLE MODELS FOR YOUR KEY ---")
        for m in sorted(models):
            print(m)
        print("-------------------------------------\n")
        print("Please copy and paste the list here so I can set the exact correct one!")
    else:
        print(f"Failed to fetch models. Status: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    list_models()
