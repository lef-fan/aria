# Aria v2 - Enhanced with LangChain Agents

Aria v2 includes enhanced agent capabilities using LangChain tools for web search, Wikipedia lookup, and mathematical calculations.

## What's New in v2

### 🔧 Enhanced Tool System

- **DuckDuckGo Web Search**: Get current information and news
- **Wikipedia Integration**: Access detailed encyclopedia information
- **Smart Calculator**: Handle natural language math queries
- **Tool Usage Tracking**: Monitor which tools are being used

### 🤖 LangChain Agent Integration

- Automatic tool selection based on user queries
- Seamless integration with existing LLM system
- Enhanced response generation using tool results
- Maintains Aria's sarcastic personality

## Usage

### Running Aria v2

```bash
# Use the enhanced version
python main_v2.py

# Or use the original version
python main.py

# Test tools without full UI (useful for headless testing)
python test_agent.py
```

### Tool Trigger Keywords

#### Calculator Tool

- "calculate", "compute", "math"
- Mathematical operators: +, -, \*, /
- Natural language: "What is 15 \* 7?"

#### Web Search Tool

- "search", "find", "current", "recent", "news", "today"
- Examples: "Search for recent AI news", "What's happening today?"

#### Wikipedia Tool

- "what is", "who is", "definition"
- Examples: "What is machine learning?", "Who is Einstein?"

## Example Interactions

```
🎙 You: What is 25 * 4?
🔧 Tool Used: calculator - Query: What is 25 * 4?
🤖 Aria: 25*4 = 100. Math wizard at your service, human.

🎙 You: Search for recent AI news
🔧 Tool Used: web_search - Query: Search for recent AI news
🤖 Aria: Found some AI drama. The robots are still plotting, apparently.

🎙 You: What is quantum computing?
🔧 Tool Used: wikipedia_search - Query: What is quantum computing?
🤖 Aria: Quantum stuff. Basically computers that exist and don't exist simultaneously.
```

## Files Structure

```
├── main_v2.py                     # Enhanced main file with agent integration
├── components/
│   ├── llm_enhanced.py            # Enhanced LLM wrapper with agent capabilities
│   ├── lungchanAgents/
│   │   └── lungchainAgent.py      # Core LangChain agent implementation
│   └── tools/
│       └── tools.py               # Tool implementations with usage tracking
├── test_agent.py                  # Test script for agent functionality
└── README_v2.md                   # This file
```

## Technical Details

### Enhanced LLM Wrapper

The `EnhancedLLMWithAgent` class wraps the original LLM and adds:

- Automatic tool detection and execution
- Response enhancement using tool results
- Compatibility with existing interface
- Tool usage statistics

### Agent Architecture

- **Tool Selection**: Keyword-based detection determines which tools to use
- **Execution**: Tools are executed with user input and results captured
- **Response Generation**: LLM generates responses based on tool results
- **Logging**: All tool usage is tracked and logged

### Safety Features

- Mathematical expressions are safely evaluated
- Web search results are sanitized
- Error handling with graceful fallbacks
- Tool usage limitations and monitoring

## Dependencies

Additional packages required for v2:

```bash
pip install langchain langchain-community duckduckgo-search ddgs
```

## Troubleshooting

### Import Errors

If you get import errors, make sure you're in the correct directory and all dependencies are installed:

```bash
pip install langchain langchain-community duckduckgo-search ddgs
```

### UI Initialization Error

If you get `AttributeError: 'NoneType' object has no attribute 'get'`, ensure you're using the correct startup method:

```bash
# ✅ Correct way (fixed in v2)
python main_v2.py

# ❌ Wrong way that causes UI errors
python main_v2.py --config missing_file.json
```

### Model Loading Time

The first startup may take 1-2 minutes while loading the 8GB model. You'll see:

```
Loading Aria v2 with LangChain Agent...
Loading model from: /path/to/model.gguf
Model file exists: True
```

### Web Search Issues

If web search returns no results, try more specific queries or check your internet connection.

### Tool Not Triggering

Make sure your query contains the appropriate keywords. You can also check the tool usage logs for debugging.

### UI Issues in Terminal Environments

If running on a headless server or via SSH, you may need X11 forwarding:

```bash
ssh -X username@hostname
# or
export DISPLAY=:0
```

## Configuration

The agent uses the same configuration as the original Aria system. Tool behavior can be customized by modifying the `AgentTools` class in `components/tools/tools.py`.

## Performance

Tool execution adds minimal latency:

- Calculator: <10ms
- Wikipedia: 1-3 seconds
- Web Search: 1-5 seconds depending on network

The system gracefully falls back to regular LLM responses if tools fail.
