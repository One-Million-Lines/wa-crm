# WaCRM

WaCRM is a full-stack WhatsApp CRM and shared inbox demo built with a React frontend and a FastAPI backend. It combines contact management, conversation handling, task tracking, reusable reply templates, automation rules, analytics, and business settings in one workspace.

## What it does

It gives a team a browser-based interface for managing WhatsApp-style customer conversations and the supporting CRM data around them.

## Why it exists

Customer communication often ends up spread across chat threads, spreadsheets, and manual follow-ups. WaCRM brings those workflows into a single app so a team can track contacts, conversations, tasks, and repeatable responses in one place.

## Features

- Token-based authentication flow for the admin UI
- Shared inbox with conversation search, filters, unread counts, and message history
- Contact management with stages, owners, tags, notes, and opt-in state
- Task management linked to contacts and conversations
- Automation rules with triggers, actions, and approval flags
- Template library with categories and quick replies
- Analytics endpoints and dashboard views
- Business, WhatsApp, and team settings screens
- Mock WhatsApp Business API client and webhook verification helpers
- Database seed script with demo contacts, conversations, automations, templates, and tasks

## How it works

1. The React frontend calls the FastAPI API through `VITE_API_BASE`.
2. The backend stores users, contacts, conversations, messages, tasks, templates, automations, settings, and modules in MongoDB through the `vtstorage` layer.
3. The inbox page polls conversations and messages so the UI stays fresh.
4. Automation rules, templates, analytics, and settings are exposed as API routes and surfaced in dedicated pages.
5. The WhatsApp integration layer is mocked in `backend/whatsapp_api.py`, so the current project is suited to local demos and product exploration before wiring real Meta API calls.

## Tech stack

- React
- TypeScript
- Vite
- Tailwind CSS
- TanStack Query
- FastAPI
- PyMongo
- python-jose
- bcrypt

## Project structure

```text
src/
  components/        shared UI
  contexts/          auth state
  pages/             inbox, contacts, tasks, automations, templates, analytics, modules, settings
  services/          frontend API client
backend/
  api_*.py           FastAPI route modules
  data_models.py     request and response schemas
  main.py            API entry point
  setup_database.py  demo data seed script
  vtconf.d/          backend config definitions
```

## Getting started

```bash
git clone <repo-url>
cd wa-crm
npm install
python -m venv backend/.venv
source backend/.venv/bin/activate
pip install fastapi uvicorn pymongo pydantic "python-jose[cryptography]" bcrypt python-dotenv
cp .env.example .env.local
cp backend/.env.example backend/.env
```

Start the backend:

```bash
cd backend
python main.py
```

In a second terminal, start the frontend:

```bash
cd wa-crm
npm run dev
```

Open:

- Frontend: `http://localhost:5313`
- API: `http://localhost:5213`
- API docs: `http://localhost:5213/docs`

To load demo data:

```bash
cd backend
python setup_database.py
```

## Configuration

The frontend reads:

```env
VITE_API_BASE=http://localhost:5213
```

The backend loads `backend/.env` and expects:

```env
APP_HOST=0.0.0.0
APP_PORT=5213
JWT_SECRET=change-me
PERMANENT_STORAGE=mongodb
PERMANENT_DB=wacrm
json_MONGO_CONN1={"string":"mongodb://localhost:27017","user":"","password":""}
META_WHATSAPP_PHONE_ID=mock-phone-id
META_WHATSAPP_BUSINESS_ID=mock-business-id
META_WHATSAPP_TOKEN=mock-token
META_WHATSAPP_VERIFY_TOKEN=mock-verify-token
```

## Usage

1. Log in to the frontend.
2. Open the inbox to review conversations and send replies.
3. Manage contacts, tasks, and templates from the side navigation.
4. Create automation rules for common message-handling workflows.
5. Review analytics and settings from the admin screens.

## Development

```bash
npm run dev
npm run build
npm run lint
npm run preview
cd backend && python main.py
cd backend && python setup_database.py
```

## Roadmap

- Replace the mock WhatsApp client with real Meta API calls
- Add a pinned Python dependency manifest for backend setup
- Add automated tests for API routes and frontend flows
- Add deployment and containerization docs

## Contributing

This project is public and open for collaboration. If you’re interested in contributing, improving the project, or discussing ideas, feel free to reach out.

LinkedIn: https://linkedin.com/in/alexrada

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Open a pull request

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE).
