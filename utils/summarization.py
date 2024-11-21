import openai

def summarize_text(text, max_tokens=100):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a summarization assistant."},
                {"role": "user", "content": f"Summarize the following text:\n\n{text}"}
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Error summarizing text: {e}")
        return text[:max_tokens]  # Fallback to truncation if summarization fails
