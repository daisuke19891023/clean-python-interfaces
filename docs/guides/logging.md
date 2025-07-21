# Logging Guide

Clean Interfaces provides comprehensive logging capabilities with structured logging, multiple output formats, and OpenTelemetry integration.

## Overview

The logging system is built on:
- **structlog**: For structured logging with context
- **OpenTelemetry**: For distributed tracing and log export
- **Multiple formats**: JSON, console, and custom formatters

## Basic Configuration

Configure logging using environment variables:

```bash
# Set log level
export LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Set log format
export LOG_FORMAT=json  # json or console

# Enable file logging
export LOG_FILE=/path/to/app.log
```

## Structured Logging

All components use structured logging with context:

```python
from clean_interfaces.base import BaseComponent

class MyComponent(BaseComponent):
    def process(self, item_id: str) -> None:
        # Logs include component context automatically
        self.logger.info("processing_item", item_id=item_id)
        
        # Add temporary context
        log = self.logger.bind(user_id="user123")
        log.info("user_action", action="update")
```

## OpenTelemetry Integration

Enable OpenTelemetry export for distributed tracing:

```bash
# Enable OpenTelemetry export
export OTEL_EXPORT_ENABLED=true

# Configure export modes
export OTEL_EXPORT_MODE=file  # file, otlp, or both

# File export
export OTEL_LOG_FILE=/path/to/otel.log

# OTLP export
export OTEL_ENDPOINT=http://localhost:4317
export OTEL_HEADERS="api-key=your-key"
export OTEL_TIMEOUT=30
```

## Log Formats

### JSON Format

Best for production and log aggregation:

```json
{
  "timestamp": "2025-01-20T12:00:00.123Z",
  "level": "info",
  "logger": "clean_interfaces.app",
  "message": "Application started",
  "component": "Application",
  "trace_id": "abc123",
  "span_id": "def456"
}
```

### Console Format

Human-readable format for development:

```
2025-01-20 12:00:00 [INFO] clean_interfaces.app: Application started component=Application
```

## Performance Logging

Use the performance decorator for timing operations:

```python
from clean_interfaces.utils.logger import log_performance

@log_performance
def slow_operation(data: list[str]) -> dict[str, int]:
    # Function execution time is automatically logged
    return process_data(data)
```

## Error Logging

Exceptions are automatically logged with full context:

```python
try:
    risky_operation()
except Exception as e:
    self.logger.error("operation_failed", 
                     error=str(e),
                     error_type=type(e).__name__)
    raise
```

## Best Practices

1. **Use structured logging**: Pass data as keyword arguments, not in messages
2. **Add context**: Use `bind()` to add request IDs, user IDs, etc.
3. **Log at appropriate levels**:
   - DEBUG: Detailed diagnostic information
   - INFO: General informational messages
   - WARNING: Warning messages for recoverable issues
   - ERROR: Error messages for failures
   - CRITICAL: Critical failures requiring immediate attention

4. **Avoid logging sensitive data**: Never log passwords, tokens, or PII
5. **Use consistent field names**: Standardize on field names across the application

## Integration with Monitoring

The logging system integrates with various monitoring solutions:

- **ELK Stack**: JSON logs can be ingested by Elasticsearch
- **Datadog**: OpenTelemetry export to Datadog agent
- **Jaeger**: Distributed tracing with OTLP export
- **Local Development**: File-based logs for debugging

## Next Steps

- Configure [Environment Variables](environment.md) for your deployment
- Learn about the [REST API](restapi.md) logging features
- Explore the [API Reference](../api/utils.md) for logging utilities