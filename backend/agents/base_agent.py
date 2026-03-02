"""
Base agent implementation using Groq with tool calling.
"""
import json
import os
from agents.llm_clients import github_client, groq_client, GITHUB_MODEL, GROQ_MODEL

def _call_with_fallback(messages, tools=None):
    params = {
        "model": GITHUB_MODEL,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 4000
    }
    if tools:
        params["tools"] = tools
        params["tool_choice"] = "auto"
    
    try:
        return github_client.chat.completions.create(**params)
    except Exception:
        params["model"] = GROQ_MODEL
        try:
            return groq_client.chat.completions.create(**params)
        except Exception:
            # Last resort - GitHub without tools
            params.pop("tools", None)
            params.pop("tool_choice", None)
            params["model"] = GITHUB_MODEL
            return github_client.chat.completions.create(**params)

def run_agent(system_prompt: str, user_message: str, tools: list, tool_functions: dict) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    max_iterations = 8
    
    for iteration in range(max_iterations):
        response = _call_with_fallback(messages, tools)
        message = response.choices[0].message
        finish_reason = response.choices[0].finish_reason
        
        # Check for raw function call text (model bug) and clean it
        if message.content and "<function" in message.content:
            # Model printed tool call as text instead of executing it
            # Force it to try again with explicit instruction
            messages.append({
                "role": "assistant", 
                "content": message.content
            })
            messages.append({
                "role": "user",
                "content": "Please use the actual tools/functions available to you to answer this. Do not write function calls as text."
            })
            continue
        
        # No tool calls - return text response
        if finish_reason == "stop" or not message.tool_calls:
            if message.content:
                return message.content
            return "I was unable to process that request."
        
        # Add assistant message with tool calls to history
        messages.append({
            "role": "assistant",
            "content": message.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in message.tool_calls
            ]
        })
        
        # Execute each tool call
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            try:
                tool_args = json.loads(tool_call.function.arguments)
            except:
                tool_args = {}
            
            if tool_name in tool_functions:
                try:
                    result = tool_functions[tool_name](**tool_args)
                    result_str = json.dumps(result) if not isinstance(result, str) else result
                except Exception as e:
                    result_str = json.dumps({"error": str(e)})
            else:
                result_str = json.dumps({"error": f"Tool '{tool_name}' not found"})
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result_str
            })
    
    return "I completed the maximum steps. Please try a more specific question."


def make_tool_definition(name: str, description: str, parameters: dict) -> dict:
    """Helper to create a Groq tool definition."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": parameters
        }
    }
