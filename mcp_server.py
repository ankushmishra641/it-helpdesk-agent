"""Retired unsafe demo endpoint. This project does not implement MCP."""
if __name__ == '__main__':
    raise SystemExit('The unauthenticated tool server has been retired. Run: uvicorn api:app --port 8000. Use the session-scoped /api routes; see docs/API.md.')
