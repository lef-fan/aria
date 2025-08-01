from typing import List, Dict, Any
from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
import requests
import json
import time
from datetime import datetime
try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    try:
        from ddgs import DDGS
        DDGS_AVAILABLE = True
    except ImportError:
        DDGS_AVAILABLE = False


class AgentTools:
    def __init__(self):
        # Try to initialize DuckDuckGo search with fallback
        try:
            self.search = DuckDuckGoSearchRun()
            self.ddg_available = True
        except Exception as e:
            print(f"⚠️ DuckDuckGo LangChain tool failed: {e}")
            self.ddg_available = False
            
        self.wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
        self.tool_usage_log = []
        
    def _log_tool_usage(self, tool_name: str, query: str, result: str, success: bool = True):
        """Log tool usage for tracking"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'tool_name': tool_name,
            'query': query,
            'result_length': len(result),
            'success': success,
            'execution_time': time.time()
        }
        self.tool_usage_log.append(log_entry)
        print(f"🔧 Tool Used: {tool_name} - Query: {query[:50]}{'...' if len(query) > 50 else ''}")
        
    def get_tool_usage_stats(self) -> Dict[str, Any]:
        """Get statistics about tool usage"""
        return {
            'total_uses': len(self.tool_usage_log),
            'recent_tools': self.tool_usage_log[-5:] if self.tool_usage_log else [],
            'tool_counts': {}
        }
    
    def web_search(self, query: str) -> str:
        """Search the web for current information using multiple fallback methods"""
        try:
            start_time = time.time()
            
            # Method 1: Try LangChain DuckDuckGo
            if self.ddg_available:
                try:
                    result = self.search.run(query)
                    if result and len(result.strip()) > 10:  # Check if we got meaningful results
                        formatted_result = f"🌐 Web Search Results:\n{result}"
                        self._log_tool_usage("web_search", query, formatted_result, True)
                        return formatted_result
                except Exception as e:
                    print(f"⚠️ LangChain DuckDuckGo failed: {e}")
            
            # Method 2: Direct DDGS if available
            if DDGS_AVAILABLE:
                try:
                    with DDGS() as ddgs:
                        results = list(ddgs.text(query, max_results=3))
                        if results:
                            formatted_results = []
                            for i, result in enumerate(results[:3], 1):
                                title = result.get('title', 'No title')
                                body = result.get('body', 'No description')
                                url = result.get('href', 'No URL')
                                formatted_results.append(f"{i}. {title}\n   {body}\n   Source: {url}")
                            
                            final_result = f"🌐 Web Search Results:\n" + "\n\n".join(formatted_results)
                            self._log_tool_usage("web_search", query, final_result, True)
                            return final_result
                except Exception as e:
                    print(f"⚠️ Direct DDGS failed: {e}")
            
            # Method 3: Simple web scraping fallback for weather
            if any(word in query.lower() for word in ['weather', 'temperature', 'forecast']):
                try:
                    weather_result = self._get_weather_fallback(query)
                    if weather_result:
                        self._log_tool_usage("web_search", query, weather_result, True)
                        return weather_result
                except Exception as e:
                    print(f"⚠️ Weather fallback failed: {e}")
            
            # If all methods fail
            error_msg = "🚫 All web search methods failed. Please try a different query or check your internet connection."
            self._log_tool_usage("web_search", query, error_msg, False)
            return error_msg
            
        except Exception as e:
            error_msg = f"Web search completely failed: {str(e)}"
            self._log_tool_usage("web_search", query, error_msg, False)
            return error_msg
    
    def _get_weather_fallback(self, query: str) -> str:
        """Fallback weather information using a free weather API"""
        try:
            # Extract city name from query
            city = "Athens"  # Default
            if "in " in query.lower():
                parts = query.lower().split("in ")
                if len(parts) > 1:
                    city = parts[1].strip().replace(".", "").replace("?", "").replace(",", "")
            
            # Try wttr.in - a free weather service
            try:
                url = f"http://wttr.in/{city}?format=3"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    weather_data = response.text.strip()
                    return f"🌤️ Current Weather:\n{weather_data}\n\nSource: wttr.in"
            except Exception as e:
                print(f"wttr.in failed: {e}")
            
            # Fallback message
            return f"🌤️ Weather for {city.title()}:\nUnable to fetch current weather data. Please check weather.com or your local weather app."
            
        except Exception as e:
            return f"Weather lookup failed: {str(e)}"
    
    def wikipedia_search(self, query: str) -> str:
        """Search Wikipedia for detailed information"""
        try:
            start_time = time.time()
            result = self.wikipedia.run(query)
            execution_time = time.time() - start_time
            
            formatted_result = f"📖 Wikipedia:\n{result}"
            self._log_tool_usage("wikipedia_search", query, formatted_result, True)
            
            return formatted_result
        except Exception as e:
            error_msg = f"Wikipedia search failed: {str(e)}"
            self._log_tool_usage("wikipedia_search", query, error_msg, False)
            return error_msg
    
    def calculate(self, expression: str) -> str:
        """Perform mathematical calculations"""
        try:
            start_time = time.time()
            
            # Extract mathematical expression from natural language
            import re
            
            # Look for mathematical patterns in the text
            math_patterns = [
                r'(\d+(?:\.\d+)?)\s*[\*×]\s*(\d+(?:\.\d+)?)',  # multiplication
                r'(\d+(?:\.\d+)?)\s*[\/÷]\s*(\d+(?:\.\d+)?)',  # division
                r'(\d+(?:\.\d+)?)\s*[\+]\s*(\d+(?:\.\d+)?)',   # addition
                r'(\d+(?:\.\d+)?)\s*[\-]\s*(\d+(?:\.\d+)?)',   # subtraction
                r'(\d+(?:\.\d+)?)\s*\^\s*(\d+(?:\.\d+)?)',     # exponentiation
            ]
            
            # Try to extract a mathematical expression
            math_expr = expression
            
            # Handle common natural language patterns
            if 'what is' in expression.lower():
                math_expr = expression.lower().replace('what is', '').strip()
            if 'calculate' in expression.lower():
                math_expr = expression.lower().replace('calculate', '').strip()
            if '?' in math_expr:
                math_expr = math_expr.replace('?', '').strip()
                
            # Replace common symbols
            math_expr = math_expr.replace('×', '*').replace('÷', '/').replace('^', '**')
            math_expr = math_expr.replace('x', '*').replace('X', '*')
            
            # Remove extra whitespace and check if it's a valid expression
            math_expr = ''.join(math_expr.split())
            
            # Allowed characters for safe evaluation
            allowed_chars = set('0123456789+-*/.() ')
            if all(c in allowed_chars for c in math_expr):
                result = eval(math_expr)
                execution_time = time.time() - start_time
                
                formatted_result = f"🧮 Calculation: {math_expr} = {result}"
                self._log_tool_usage("calculator", expression, formatted_result, True)
                
                return formatted_result
            else:
                error_msg = f"Could not extract a valid mathematical expression from: '{expression}'"
                self._log_tool_usage("calculator", expression, error_msg, False)
                return error_msg
        except Exception as e:
            error_msg = f"Calculation failed: {str(e)}"
            self._log_tool_usage("calculator", expression, error_msg, False)
            return error_msg
        
    def get_current_datetime(self, query: str = "") -> str:
        """Get current date and time information"""
        try:
            from datetime import datetime
            
            now = datetime.now()
            utc_now = datetime.utcnow()
            
            # Format different time representations
            local_time = now.strftime("%Y-%m-%d %H:%M:%S")
            utc_time = utc_now.strftime("%Y-%m-%d %H:%M:%S UTC")
            
            # Day of week and other useful info
            day_of_week = now.strftime("%A")
            month = now.strftime("%B")
            
            result = f"""📅 Current Date & Time:
• Local: {local_time}
• UTC: {utc_time}
• Day: {day_of_week}
• Month: {month}
• Year: {now.year}"""
            
            self._log_tool_usage("datetime", query, result, True)
            return result
            
        except Exception as e:
            error_msg = f"Failed to get current date/time: {str(e)}"
            self._log_tool_usage("datetime", query, error_msg, False)
            return error_msg