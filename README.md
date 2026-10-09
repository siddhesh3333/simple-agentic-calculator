# SmartCalc AI – AI Calculator Agent

SmartCalc AI is a small first AI-agent project. You type a math question in
normal language, an LLM decides whether it needs the calculator tool, and the
LLM turns the tool's result into a friendly answer.

## 1. What we are building

The project demonstrates this flow:

```text
User question
     ↓
AI agent (LLM interprets the request)
     ↓
Decision: calculator needed?
     ├── No → natural-language answer
     └── Yes
          ↓
     Calculator tool (safe Python operations)
          ↓
     Tool result
          ↓
     AI agent (explains the result)
          ↓
     Final answer
```

## 2. Beginner concepts

### What is an AI agent here?

An agent is an LLM connected to instructions and tools. It does not just
produce text: it can decide to request an action. In this project, the agent
is intentionally small: one LLM, one tool, and one short tool-calling loop.

### What is a tool?

A tool is a normal Python function that the LLM is allowed to request. The
`calculate` function in `tools.py` performs only explicitly supported
operations. It does not use unsafe unrestricted `eval()`.

### How does tool calling work?

1. The first LLM request includes the calculator's name, description, and
   allowed arguments.
2. The LLM either answers directly or returns a structured calculator request.
3. Python validates the request and calls `calculate`.
4. Python sends the result back as a tool message.
5. A second LLM request writes the final natural-language response.

The LLM decides *when* to use the tool, but Python performs the arithmetic.

## 3. Project structure

```text
smartcalc-ai/
├── app.py             # Streamlit chat interface
├── agent.py           # LLM instructions and tool-calling loop
├── tools.py           # Safe calculator function
├── requirements.txt   # Python dependencies
├── .env.example       # Environment-variable template
├── README.md          # This guide
└── .gitignore         # Keeps secrets and generated files out of Git
```

## 4. Installation

Python 3.10 or newer is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If the environment is already created, install dependencies with the
environment's interpreter explicitly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 5. Environment variable setup

Copy `.env.example` to `.env` and replace the placeholder:

```text
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.6-flash
```

Never commit `.env` or share your API key. `python-dotenv` loads these values
for the application.

This project uses Google's `google-genai` SDK and Gemini's native function
calling support. Create a Gemini API key in Google AI Studio.

The `.env` file must be directly inside the project folder, next to
`app.py` and `agent.py`. If a key was ever placed in `.env.example`, posted in
chat, or committed to source control, revoke it in Google AI Studio and create
a new key before continuing.

## 6. Run the application

```powershell
python -m streamlit run app.py
```

Using `python -m streamlit` ensures Streamlit uses the same Python environment
where `google-genai` was installed. If you see `cannot import name 'genai'
from 'google'`, run the explicit installation command above and launch with:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the local URL shown by Streamlit in your browser. Enable **Show debug
details** in the sidebar to see the question, decision, tool input, and result.
The API key is never included in those details.

## 7. Example questions

- `What is 25% of 800?`
- `Calculate 125 multiplied by 48`
- `What is the square root of 144?`
- `If I have 500 rupees and spend 175, how much is left?`
- `Calculate 15% GST on 2000`
- `Hello!`

The calculator supports addition, subtraction, multiplication, division,
percentage, power, and square root. Percentage means `a percent of b`, so
`15% of 2000` is `(15 / 100) * 2000`.

## 8. Complete runtime flow

For “What is 20% of 500?”:

1. Streamlit sends the question to `run_agent`.
2. The first LLM call sees the calculator schema and requests:
   `{"operation": "percentage", "a": 20, "b": 500}`.
3. Python validates the operation and numbers.
4. `calculate` returns `100`.
5. The result is sent to the LLM as a tool result.
6. The second LLM call responds with something like “20% of 500 is 100.”

## 9. Common errors and solutions

- **Missing `GEMINI_API_KEY`**: create `.env` from `.env.example` and add a
  valid key.
- **Gemini API key rejected**: check that the key is copied correctly and active.
- **Could not connect**: check your internet connection and try again.
- **Rate limit**: wait and retry, or check the API account limits.
- **Division by zero**: provide a non-zero divisor.
- **Invalid or unsupported calculation**: ask using a clear operation and
  numbers.
- **No answer**: check the terminal logs and enable the debug section.

The UI shows understandable errors rather than Python stack traces.

## 10. Future improvements

After understanding this version, you could add unit tests, more calculator
operations, conversation-aware follow-up questions, currency conversion via a
separate API tool, or streaming responses. Add one concept at a time before
using larger agent frameworks.
