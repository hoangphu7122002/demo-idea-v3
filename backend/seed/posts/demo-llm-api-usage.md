---
slug: demo-llm-api-usage
title: Integrating Claude API in Python Applications
---

# Integrating Claude API in Python Applications

This guide walks through setting up the Claude API and building a simple Python application to interact with Claude. Whether you're building a chatbot or content generation tool, these fundamentals apply.

## Getting Started with the API

The Claude API is straightforward to use. Start by installing the SDK and setting your API key. The `anthropic` Python package handles all the HTTP details for you.

```python
import anthropic

client = anthropic.Anthropic(api_key="your-api-key-here")
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello, Claude!"}],
)
print(message.content[0].text)
```

This simple example demonstrates the basic pattern: create a client, call the messages API, and process the response.

## Working with Different Model Versions

Claude has multiple model versions available, each optimized for different use cases. As of October 2024, the latest model available is Claude 3.5 Sonnet. This model offers excellent performance for most general-purpose tasks including text analysis, code generation, and reasoning.

For production applications, consider using the `claude-3-opus-20250219` model which provides the best performance for complex reasoning tasks. However, be aware that Opus has higher latency and cost compared to other models.

## Managing Tokens and Costs

Tokens are the basic unit of pricing in the Claude API. Both input and output tokens are counted. A typical English word is about 1.3 tokens. When building applications, it's important to estimate token usage to manage costs effectively.

You can calculate approximate costs by multiplying tokens by the per-token rate. Input tokens typically cost around $3 per million, while output tokens cost around $15 per million for the latest models.

## Error Handling and Retries

The API can experience temporary failures. Implement exponential backoff retry logic to handle these gracefully:

```python
import time
import anthropic


def call_with_retry(messages, max_retries=3):
    client = anthropic.Anthropic()
    for attempt in range(max_retries):
        try:
            return client.messages.create(
                model="claude-3-5-sonnet-20241022", max_tokens=1024, messages=messages
            )
        except anthropic.RateLimitError:
            if attempt < max_retries - 1:
                wait_time = 2**attempt
                time.sleep(wait_time)
            else:
                raise
```

This pattern ensures your application remains resilient to temporary issues.

## Using System Prompts Effectively

System prompts define Claude's behavior for a conversation. Effective system prompts are specific and concise. They help guide the model toward your desired output format and behavior.

```python
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    system="You are a helpful assistant. Always respond in JSON format.",
    messages=[{"role": "user", "content": "List three colors"}],
)
```

## Best Practices for Production

When deploying Claude-powered applications to production, follow these guidelines:

- Always use environment variables for API keys, never hardcode them
- Implement request timeouts (typically 30 seconds)
- Log API usage for monitoring and debugging
- Use streaming for long-form content generation to improve perceived latency
- Cache prompts when using the same context repeatedly

These practices ensure your application is secure, efficient, and maintainable.
