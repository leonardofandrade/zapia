# MySQL local (Docker)

Suba apenas o banco:

```bash
docker compose -f infra/docker-compose.mysql.yml up -d
```

Para usar no Django, copie `app/.env.mysql.example` para um `.env` carregado pela sua execução (ou exporte as variaveis no terminal) e rode as migracoes.
