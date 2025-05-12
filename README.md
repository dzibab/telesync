# telesync

## Initial Setup (First Run)

Before running the application in a Docker container, you must initialize the Telegram session interactively to avoid authentication errors:

1. Ensure your `.env` file contains your `API_ID` and `API_HASH`.
2. Run the following command locally (not in Docker):

```sh
uv run main.py
```

3. Follow the prompts to enter your phone number, Telegram code, and (if enabled) cloud password. This will create the `telesync_session.session` file.

4. After successful authentication, you can run the application in Docker. The session file will be reused and you will not be prompted again.

## Running with Docker Compose

Build and start the service:

```sh
docker compose up --build
```

The `/tmp/telegram_saved_messages` directory and `telesync_session.session` will be mounted for persistence.