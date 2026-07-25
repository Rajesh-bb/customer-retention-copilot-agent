from dotenv import load_dotenv
import os
from backend.prompts.csm_prompt import csm_prompt
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool

from backend.action.action_agent import execute_action_agent
from backend.RAG.chatbot import chatbot
from backend.prompts.rewriter_prompt import rewrite_question_prompt
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    ToolMessage,
)

load_dotenv()

rewriter_llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    api_key=os.getenv("GOOGLE_API_KEY_2"),
    temperature=0,
)

def rewrite_question(messages, question: str) -> str:
    """
    Convert follow-up questions into standalone questions.

    Parameters
    ----------
    messages : list
        Last few conversation messages
        (recommend messages[-8:]).

    question : str
        Latest user question.

    Returns
    -------
    str
        Standalone question.
    """

    prompt = rewrite_question_prompt.invoke(
        {
             "chat_history": messages[-8:],
            "input": question,
        }
    )

    response = rewriter_llm.invoke(prompt)

    return response.content[0]["text"]

llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    api_key=os.getenv("GOOGLE_API_KEY_1"),
)

messages = []

@tool
def ask_about_analysis(question: str) -> str:
    """
    Answer questions about an analysis that has already been completed.

    Use this tool whenever the user asks follow-up questions about the existing analysis, such as:
    - Why is an account high risk?
    - What is the major problem?
    - How can we solve the churn risk?
    - Which accounts need attention?
    - What are the recommendations?
    - Summarize the analysis.
    - Explain the business insights.
    - What trends did you find?
    - Tell me more about a specific customer or recommendation.

    DO NOT use this tool if the user is asking you to perform a NEW analysis.

    If the user's message is an instruction or command such as:
    - "Analyze all accounts for 2025-05-01"
    - "Run the analysis for yesterday"
    - "Generate a new report"

    then do NOT use this tool. Use `run_customer_analysis` instead.
    """
    standalone_question = rewrite_question(
            messages,
            question,
            )

    print("Standalone Question:", standalone_question)
    tool_result = chatbot(standalone_question)

    if isinstance(tool_result, list):
        tool_result_text = "\n".join(
            block["text"]
            for block in tool_result
            if block.get("type") == "text"
        )
    else:
        tool_result_text = str(tool_result)

    # print("\n========== CHATBOT OUTPUT ==========")
    # print(tool_result_text)
    # print("====================================\n")

    return tool_result_text




def csm_agent(user_input: str,execute_action : bool):

    @tool
    def run_customer_analysis(query: str) -> str:
        """
    Run a NEW customer retention analysis for a specific analysis date.

    Use this tool ONLY when the user explicitly instructs you to perform a new analysis,
    for example:
    - "Analyze all accounts for 2025-05-01"
    - "Run customer analysis for June 1st"
    - "Generate a customer retention report for 2025-05-01"
    - "Analyze customer health for 2025-05-01"

    The user must be requesting a NEW analysis, typically for a specific date.

    DO NOT use this tool for:
    - Follow-up questions about an existing analysis.
    - Questions starting with "why", "what", "how", "which", "who", or "summarize".
    - Requests asking to explain recommendations, risks, trends, or business insights.
    - Any conversational question after an analysis has already been completed.
    """

        result = execute_action_agent(
            query=query,
            execute_actions=execute_action
        )

        return result
    
    llm_with_tools = llm.bind_tools([
        run_customer_analysis,
        ask_about_analysis,
        ])
    
    tool_map = {
        "run_customer_analysis": run_customer_analysis,
        "ask_about_analysis": ask_about_analysis,
    }

    global messages

    messages.append(HumanMessage(content=user_input))

    prompt = csm_prompt.invoke(
        {
            "messages": messages
        }
    )

    response = llm_with_tools.invoke(prompt)

    # print("\n========== CSM ==========")
    # print("User:", user_input)
    # print("Tool calls:", response.tool_calls)
    # print("=========================\n")

    messages.append(response)

    if response.tool_calls:

        for tool_call in response.tool_calls:

            selected_tool = tool_map[tool_call["name"]]
            tool_name = tool_call["name"]

            tool_result = selected_tool.invoke(tool_call)

            tool_message = ToolMessage(
                content=tool_result,
                # artifact=tool_result,
                tool_call_id=tool_call["id"],
                name=tool_call["name"],
            )

            messages.append(tool_message)

        prompt = csm_prompt.invoke(
            {
                "messages": messages
            }
        )

        final_response = llm_with_tools.invoke(prompt)

        messages.append(final_response)

        return {
            "response": final_response,
            "graph_state": tool_result,
            "analysis_ran": tool_name == "run_customer_analysis"
        }

    return {
        "response": response,
        "analysis_ran": False
    }


if __name__ == "__main__":
    # reset_chat_history()
    messages.clear()

    print("Customer Success Manager initialized.")
    print("Type 'quit' to exit.\n")

    while True:

        user_input = input("\nUser: ")

        if user_input.lower() == "quit":
            break

        response = csm_agent(user_input,execute_action=True)

        ai_response = response["response"]

        print("\nAssistant:")

        if isinstance(ai_response.content, str):
            print(ai_response.content)
        else:
            print(ai_response.content[0]["text"])
