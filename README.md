# 📝 Los Geht's — Todo API & CI/CD

![CI/CD](https://github.com/VictorGorgal/C14-CICD/actions/workflows/ci.yml/badge.svg?branch=main)

Pipeline de CI/CD com testes automatizados para a API REST **Los-Gehts-backend**, construída com **FastAPI**, **PostgreSQL** e **Prisma** (Python).

---
# Rodando o projeto
---
## Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (necessário para o PostgreSQL)
- Python 3.x

---

## Configuração inicial

> Realize esses passos apenas na **primeira vez** que for usar o projeto.

1. **Inicie o Docker Desktop** e aguarde até que ele esteja completamente em execução.
2. Execute o script de instalação:

```bash
installDependencies.bat
```

Esse script irá:
- Baixar e configurar o container do **PostgreSQL** via Docker
- Criar um **ambiente virtual Python** local
- Instalar todas as **dependências do projeto**

Após a conclusão, o ambiente estará pronto para uso.

---

## Rodando o servidor

Com o projeto já configurado, execute:

```bash
RunServer.bat
```

Esse script irá:
1. Ativar o ambiente virtual Python
2. Sincronizar o **Prisma** com o banco de dados
3. Iniciar o servidor

> Certifique-se de que o **Docker Desktop está aberto** antes de rodar o servidor.

---

# Pipeline CI/CD

O pipeline é acionado apenas em **commits na branch `main`** e possui **4 jobs**:

```
test ──┬── build ──── deploy
       └── notify  (paralelo ao build)
```

| Job | Descrição |
|---|---|
| `test` | Instala dependências e executa os 40 cenários de teste unitário com pytest |
| `build` | Constrói a imagem Docker com o backend, armazenada como artifact |
| `notify` | Envia e-mail com o resultado dos testes (roda em paralelo com o build) |
| `deploy` | Publica a imagem Docker e o relatório de testes como **GitHub Release** (somente após build + notify com sucesso) |

### Artifacts gerados

- `test-report` — relatório JUnit XML dos testes
- `docker-image` — imagem Docker empacotada (`.tar`)

---

## ⚙️ Configuração dos Secrets e Variables no GitHub

Acesse **Settings → Secrets and variables → Actions** no repositório e adicione:

### Secrets

| Nome | Descrição |
|---|---|
| `SMTP_USER` | E-mail usado para enviar notificações |
| `SMTP_PASSWORD` | Senha de app do Gmail (ou senha SMTP) |

### Variables

| Nome | Descrição |
|---|---|
| `NOTIFY_EMAIL` | E-mail que receberá as notificações do pipeline |

> O `GITHUB_TOKEN` usado no deploy é gerado automaticamente pelo GitHub Actions — nenhuma configuração extra necessária.

---

## Rodando os testes localmente

```bash
pytest tests/ -v
```

---

## 🐳 Rodando com Docker

```bash
# Build
docker build -t todo-api .

# Run (necessário banco PostgreSQL)
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:pass@host:5432/dbname" \
  todo-api
```

---

## Resolução de problemas

### Resetar o banco de dados

Caso precise limpar todos os dados do banco e começar do zero:

```bash
wipeDB.bat
```

---

## 🤖 Uso de IA

Este projeto utilizou **Claude (Anthropic)** como auxiliar no desenvolvimento dos testes unitários, workflow de CI/CD, script de notificação e estrutura do README.

**Prompts utilizados:**

1. Análise da atividade e definição da estrutura do projeto
2. Discussão sobre como integrar um repositório externo no pipeline (git clone vs submodules)
3. Geração dos testes unitários com mocks para `AuthService` e `TaskService`
4. Geração do workflow `.github/workflows/ci.yml`
5. Discussão e escolha da estratégia de deploy (Docker Hub vs GitHub Releases)
6. Atualização do `ci.yml` para usar GitHub Releases e clonar o repositório alvo
7. Geração do script `scripts/notify.py`
8. Geração do `Dockerfile`, `.gitignore` e `README.md`

**Resultado:** Satisfatório. Todo o código gerado foi revisado e adaptado ao projeto real. Os testes refletem o comportamento real dos services e cobrem tanto fluxos normais quanto casos de erro.
