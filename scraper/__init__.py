from fastapi import FastAPI

from app.routers import dictionary


def register_routers(app: FastAPI) -> None:
    """Mounts every router onto the main FastAPI app.

    main.py just calls register_routers(app) once, so adding a new
    feature later (e.g. a 'dialects' router) means adding one more
    app.include_router(...) line here, not touching main.py at all.
    """
    app.include_router(dictionary.router)
