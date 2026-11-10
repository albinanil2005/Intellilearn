import google.generativeai as genai

# Configure your key
genai.configure(api_key="AIzaSyBtAajpD5wct7fcB-8sZaD90vm_02g69EU")

print("--- Checking Available Models ---")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Found Model: {m.name}")
except Exception as e:
    print(f"Error: {e}")
print("-------------------------------")