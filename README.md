docker build . -t qa-guru-app

docker images
 
docker run --add-host=host.docker.internal:host-gateway \
  -e DATABASE_ENGINE="postgresql+psycopg2://postgres:example@host.docker.internal:5432/postgres" \
  -p 8002:80 \
  qa-guru-app

docker compose up