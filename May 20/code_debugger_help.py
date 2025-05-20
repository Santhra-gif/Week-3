import asyncio
import subprocess
import tempfile
import re
import google.generativeai as genai

GOOGLE_API_KEY = "your_api_key" # replace during execution
genai.configure(api_key=GOOGLE_API_KEY)

# === Helper to clean markdown code fences ===
def clean_code(code: str) -> str:
    code = re.sub(r"^```(?:python)?\n", "", code)
    code = re.sub(r"\n```$", "", code)
    return code.strip()


async def gemini_llm(prompt: str) -> str:
    try:
        model = genai.GenerativeModel(model_name="models/gemini-1.5-pro")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"# Gemini Error: {e}\nprint('Failed to generate code.')"

# === TOOL: Python Executor ===
async def python_executor(code: str) -> str:
    code = clean_code(code)
    try:
        exec_globals = {}
        exec(code, exec_globals)
        return "✅ Execution successful."
    except Exception as e:
        return f"❌ Execution error: {e}"

# === TOOL: Linter (pylint) ===
async def lint_code(code: str) -> str:
    code = clean_code(code)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w") as tmp_file:
        tmp_file.write(code)
        tmp_path = tmp_file.name
    result = subprocess.run(["pylint", tmp_path], capture_output=True, text=True)
    return result.stdout

# === AGENT: Coder ===
async def coder_agent(problem_statement: str) -> str:
    prompt = f"Write clean Python code for the following task. Only return code, no explanation.\n\nTask: {problem_statement}"
    raw_code = await gemini_llm(prompt)
    return clean_code(raw_code)

# === AGENT: Debugger ===
async def debugger_agent(code: str) -> str:
    import re

    def extract_lint_issues(lint_output: str) -> list:
        pattern = r"^(.*?):(\d+):(\d+): (\w\d+): (.*)$"
        matches = re.findall(pattern, lint_output, re.MULTILINE)
        return [f"{msg_id} at line {line}: {message}" for _, line, _, msg_id, message in matches]

    code = clean_code(code)
    lint_results = await lint_code(code)
    lint_issues_before = extract_lint_issues(lint_results)

    if "error" in lint_results.lower() or "syntax-error" in lint_results.lower():
        fix_prompt = (
            "The following Python code has lint or syntax errors:\n"
            f"{code}\n\n"
            f"Lint results:\n{lint_results}\n\n"
            "Fix the code and return only the corrected Python code."
        )
        fixed_code_raw = await gemini_llm(fix_prompt)
        fixed_code = clean_code(fixed_code_raw)
        fixed_lint_results = await lint_code(fixed_code)
        lint_issues_after = extract_lint_issues(fixed_lint_results)
        execution_result = await python_executor(fixed_code)

        return (
            f"⚠️ Lint errors detected and code was auto-corrected by Gemini.\n\n"
            f"🔍 Issues Detected Before Fix:\n" +
            ("\n".join(f"- {issue}" for issue in lint_issues_before) if lint_issues_before else "✅ No issues found.") + "\n\n"
            f"🛠️ Fixed Code:\n{fixed_code}\n\n"
            f"📋 Linter Results After Fix:\n" +
            ("\n".join(f"- {issue}" for issue in lint_issues_after) if lint_issues_after else "✅ No remaining issues.") + "\n\n"
            f"🚀 Execution Feedback:\n{execution_result}"
        )
    else:
        execution_result = await python_executor(code)
        return (
            f"\n📋 Linter Results:\n" +
            ("\n".join(f"- {issue}" for issue in lint_issues_before) if lint_issues_before else "✅ No issues found.") + "\n\n"
            f"🚀 Execution Feedback:\n{execution_result}"
        )

# === COLLABORATIVE CHAT CONTROLLER ===
async def round_robin_group_chat():
    print("👋 Welcome to Code Debugging Helper!")
    choice = input("Do you want to:\n1️⃣ Describe a task to generate code\n2️⃣ Provide a Python file path\n👉 Enter 1 or 2: ").strip()

    if choice == "1":
        task = input("\n💬 Describe the task (e.g., 'check if number is prime'):\n👉 ")
        print("\n🧠 [Coder Agent] Generating code...")
        code = await coder_agent(task)
        print(f"\n📝 Generated Code:\n{code}")
    elif choice == "2":
        file_path = input("\n📄 Enter the path to your Python file (e.g., my_script.py):\n👉 ").strip()
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            print("\n📥 Code loaded successfully from file.")
        except FileNotFoundError:
            print(f"❌ File not found: {file_path}")
            return
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return
    else:
        print("❌ Invalid option. Please restart and enter 1 or 2.")
        return

    print("\n🔍 [Debugger Agent] Analyzing and executing code...")
    feedback = await debugger_agent(code)
    print(f"\n🛠️ Debugger Feedback:\n{feedback}")


def run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        return loop.create_task(coro)
    else:
        return asyncio.run(coro)


if __name__ == "__main__":
    run_async(round_robin_group_chat())
