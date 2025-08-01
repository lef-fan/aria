from typing import List, Dict, Any
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
from langchain.memory import ConversationBufferWindowMemory
from langchain_community.utilities import WikipediaAPIWrapper
from langchain.schema import SystemMessage, HumanMessage
from ..tools.tools import AgentTools
import requests
import json
import re
import sys


class LangChainAgent:
    def __init__(self, llm_wrapper, system_message: str = None):
        self.llm_wrapper = llm_wrapper
        self.agent_tools = AgentTools()
        self.conversation_history = []
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history", 
            return_messages=True,
            k=10
        )
        
        # Define available tools
        self.tools = [
            {
                "name": "web_search",
                "func": self.agent_tools.web_search,
                "description": "Search the web for current information, news, or recent events or whatever the user"
            },
            {
                "name": "wikipedia",
                "func": self.agent_tools.wikipedia_search,
                "description": "Search Wikipedia for detailed encyclopedia information"
            },
            {
                "name": "calculator",
                "func": self.agent_tools.calculate,
                "description": "Perform mathematical calculations"
            },
            {
                "name": "datetime",
                "func": self.agent_tools.get_current_datetime,
                "description": "Get current date, time, day of week, or temporal information"
            }
        ]
        
        # Get current date/time to include in system message
        from datetime import datetime
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S %A")
        
        self.system_message = system_message
    
    def create_agent_prompt(self, user_input: str) -> str:
        """Create a prompt that encourages tool use when appropriate"""
        tool_descriptions = "\n".join([f"- {tool['name']}: {tool['description']}" for tool in self.tools])
        
        prompt = f"""System: {self.system_message}

Available tools:
{tool_descriptions}

Use tools when:
- User asks for current information, news, or recent events (use web_search)
- User asks about historical facts, people, or concepts (use wikipedia)
- User asks for calculations (use calculator)
- User asks about time, date, or temporal information (use datetime)

User: {user_input}

Think about whether you need to use any tools, then respond appropriately."""
        
        return prompt
    
    def should_use_tools(self, user_input: str) -> bool:
        """Determine if the query requires tool usage"""
        tool_keywords = [
            'search', 'find', 'what is', 'who is', 'when did', 'calculate', 
            'compute', 'math', 'current', 'recent', 'news', 'today', 
            'weather', 'price', 'definition', 'time', 'date', 'what time',
            'what day', 'when is', 'now', 'current time', 'current date'
        ]
        return any(keyword in user_input.lower() for keyword in tool_keywords)
    
    def execute_tool(self, tool_name: str, tool_input: str) -> str:
        """Execute a specific tool"""
        for tool in self.tools:
            if tool['name'] == tool_name:
                return tool['func'](tool_input)
        return "Tool not found"
    
    def process_with_tools(self, user_input: str) -> str:
        """Process user input and use tools if necessary"""
        if self.should_use_tools(user_input):
            # Determine which tool to use based on keywords
            if any(word in user_input.lower() for word in ['calculate', 'compute', 'math', '+', '-', '*', '/']):
                # Extract mathematical expression
                return self.execute_tool('calculator', user_input)
            elif any(word in user_input.lower() for word in ['time', 'date', 'what time', 'what day', 'when is', 'now', 'current time', 'current date', 'today']):
                return self.execute_tool('datetime', user_input)
            elif any(word in user_input.lower() for word in ['current', 'recent', 'news', 'weather']):
                return self.execute_tool('web_search', user_input)
            elif any(word in user_input.lower() for word in ['what is', 'who is', 'definition']):
                return self.execute_tool('wikipedia', user_input)
            else:
                return self.execute_tool('web_search', user_input)
        
        return None  # No tool needed
        
    def get_response(self, user_input: str, ui=None, ap=None, tts=None) -> str:
        """Get response from the agent, using tools if needed"""
        # Check if tools should be used
        tool_result = self.process_with_tools(user_input)
        
        if tool_result:
            # Tool was used, provide feedback and create a combined prompt
            print(f"🔧 Tool used successfully for: {user_input}")
            prompt = f"""Based on this information: {tool_result}

User asked: {user_input}

Please provide a concise, sarcastic response using the tool information. Keep it under 20 words and maintain your rude, funny personality."""
        else:
            # No tool needed, use regular prompt
            prompt = user_input
        
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # Use the LLM wrapper's streaming method
        try:
            response = self._get_streaming_response(prompt, ui, ap, tts)
        except Exception as e:
            print(f"Streaming error: {e}")
            response = self._call_llm_directly(prompt)
            
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return response
    
    def _get_streaming_response(self, prompt: str, ui, ap, tts) -> str:
        """Get streaming response using the LLM wrapper's existing method"""
        # Use the LLM wrapper's message system and streaming
        original_messages = self.llm_wrapper.messages.copy()
        
        # Temporarily replace with our prompt
        self.llm_wrapper.messages = [{"role": "system", "content": self.system_message}]
        self.llm_wrapper.messages.append({"role": "user", "content": prompt})
        
        # Define stop tokens
        stop_tokens = [
            "<|im_end|>", "<|im_start|>", "<|end_of_text|>", "<|eot_id|>",
            "User:", "Human:", "Assistant:", "\nUser:", "\nHuman:",
            "\nWhat", "What is the capital", "I found this information",
            "Next question", "Please provide"
        ]

        # Get streaming response
        outputs = self.llm_wrapper.llm.create_chat_completion(
            self.llm_wrapper.messages, 
            stream=self.llm_wrapper.streaming_output,
            stop=stop_tokens,
            max_tokens=100,  # Increase slightly for tool responses
            temperature=0.7
        )

        if self.llm_wrapper.streaming_output:
            llm_output = ""
            tts_text_buffer = []
            color_code_block = False
            backticks = 0
            skip_code_block_on_tts = False
            
            if ui:
                ui.add_message("Aria", "", new_entry=True)
                
            for i, out in enumerate(outputs):
                if "content" in out["choices"][0]["delta"]:
                    output_chunk_txt = out["choices"][0]["delta"]["content"]
                    
                    # Handle code blocks
                    if output_chunk_txt == "```" and backticks == 0:
                        skip_code_block_on_tts = not skip_code_block_on_tts
                        color_code_block = not color_code_block
                        backticks += 3
                    if backticks > 0 and backticks <= 3:
                        backticks += 1
                    else:
                        backticks = 0
                    
                    # Print and add to UI
                    if i == 1:
                        print("Aria:", output_chunk_txt.strip(), end="")
                        if ui and backticks == 0:
                            ui.add_message("Aria", output_chunk_txt.strip(), new_entry=False, color_code_block=color_code_block)
                    else:
                        print(output_chunk_txt, end="")
                        if ui and backticks == 0:
                            ui.add_message("Aria", output_chunk_txt, new_entry=False, color_code_block=color_code_block)
                    
                    sys.stdout.flush()
                    llm_output += output_chunk_txt
                    
                    # Handle TTS
                    if tts and not skip_code_block_on_tts:
                        tts_text_buffer.append(output_chunk_txt)
                        if tts_text_buffer[-1] in [".", "!", "?", ":", "..", "..."]:
                            from ..utils import remove_emojis
                            txt_for_tts = remove_emojis("".join(tts_text_buffer).strip())
                            if len(txt_for_tts) > 1 and not all(char.isspace() for char in txt_for_tts):
                                tts.run_tts(txt_for_tts)
                            tts_text_buffer = []
            
            # Handle remaining TTS buffer
            if tts and not skip_code_block_on_tts and len(tts_text_buffer) != 0:
                from ..utils import remove_emojis
                txt_for_tts = remove_emojis("".join(tts_text_buffer).strip())
                if len(txt_for_tts) > 1 and not all(char.isspace() for char in txt_for_tts):
                    tts.run_tts(txt_for_tts)
            
            if ap:
                ap.check_audio_finished()
            print()
            llm_output = llm_output.strip()
        else:
            llm_output = outputs["choices"][0]["message"]["content"].strip()

        # Restore original messages
        self.llm_wrapper.messages = original_messages
        self.llm_wrapper.messages.append({"role": "assistant", "content": llm_output})

        return llm_output
        
    def _call_llm_directly(self, prompt: str) -> str:
        """Fallback method to call LLM directly"""
        try:
            # This would need to be adapted based on your LLM interface
            messages = [{"role": "system", "content": self.system_message}]
            messages.append({"role": "user", "content": prompt})
            
            # Assuming the llm_wrapper has a create_chat_completion method
            if hasattr(self.llm_wrapper, 'llm'):
                outputs = self.llm_wrapper.llm.create_chat_completion(messages, stream=False)
                return outputs['choices'][0]['message']['content']
            else:
                return "Sorry, I can't process that right now."
        except Exception as e:
            print(f"Error in direct LLM call: {e}")
            return "Something went wrong with my brain circuits."
            
    def get_tool_stats(self) -> Dict[str, Any]:
        """Get statistics about tool usage"""
        return self.agent_tools.get_tool_usage_stats()