# test_direct_openai.py
from openai import OpenAI


def test_openai():
    # Använd din projektspecifika API-nyckel
    api_key = "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"

    # Alternativt läs från din config:
    # from config import settings
    # api_key = settings.OPENAI_API_KEY

    # Skapa OpenAI-klient
    client = OpenAI(api_key=api_key)

    try:
        # Enkel test-prompt
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Använd en billigare modell för test
            messages=[
                {"role": "user", "content": "Beskriv kort hur man kan optimera båtplacering i en hamn."}
            ],
            max_tokens=100
        )

        print("OpenAI API svarade:")
        print(response.choices[0].message.content)
        print("\nTest lyckades! API-nyckeln fungerar.")

    except Exception as e:
        print(f"Fel vid kommunikation med OpenAI API:")
        print(str(e))


if __name__ == "__main__":
    test_openai()
