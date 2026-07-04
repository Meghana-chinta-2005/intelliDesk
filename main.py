"""FastAPI backend entrypoint for IntelliDesk."""

from fastapi import FastAPI


app = FastAPI(title="IntelliDesk API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Return a basic service health check."""
    return {"status": "ok"}
