# Architecture

This project follows a CLEAN/SOLID layout.

## Layers and dependency direction
- domain -> pure entities and value objects
- application -> use cases and ports (interfaces)
- infrastructure -> concrete implementations (exchange, storage)
- adapters -> CLI/API/presentation
- shared -> cross-cutting utilities

Dependencies flow inward only. Outer layers may import inner layers, never the reverse.

## Patterns (only when justified)
- Strategy: interchangeable signal/risk logic
- Factory: build pipeline objects from config
- Repository: data access interfaces
- Observer/Event bus: stream events and callbacks

## Package layout
```
trading_bot/
  domain/
  application/
  infrastructure/
  adapters/
  shared/
```
