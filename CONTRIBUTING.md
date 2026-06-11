# Contributing

Thanks for your interest in contributing.

## Local setup

```bash
npm install
python -m venv backend/.venv
source backend/.venv/bin/activate
pip install fastapi uvicorn pymongo pydantic "python-jose[cryptography]" bcrypt python-dotenv
cp .env.example .env.local
cp backend/.env.example backend/.env
```

Run the backend with `cd backend && python main.py` and the frontend with `npm run dev`.

## Making changes

- Keep frontend and backend changes scoped and documented
- Use `python setup_database.py` when you need demo data locally
- Run `npm run build` and `npm run lint` before opening a pull request

## Pull requests

1. Fork the repository
2. Create a branch for your change
3. Make and document your changes
4. Open a pull request with context and screenshots when helpful

## Reporting issues

Open a GitHub issue with clear reproduction steps, expected behavior, and environment details.
