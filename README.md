# titicaca

## Development

```bash
```

## Run

There are two ways to run the project:

The first one is to run the project with wsgi server, for example gunicorn:

```bash
gunicorn titicaca.cmd.api:app_ --workers 4 -k uvicorn.workers.UvicornWorker
```

or

In development mode, you can run the project with uvicorn:

```bash
uvicorn titicaca.cmd.api:app_ --reload
``` 

or

```bash
python titicaca-api --config-file ./etc/titicaca-api.conf
```