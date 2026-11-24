# Brainrot Mania

Loja local de demonstração construída com Flask, SQLite e JavaScript sem framework. O catálogo inicial de 22 personagens é criado automaticamente na primeira inicialização.

## Executar localmente em dois terminais

Instale [uv](https://docs.astral.sh/uv/) e Node.js/npm. No primeiro terminal, inicie o backend:

```powershell
cd backend
uv run python app.py
```

No segundo terminal, instale as dependências do frontend uma vez e inicie o Vite:

```powershell
cd front
npm install
npm run dev
```

Abra `http://127.0.0.1:5173`. O Vite encaminha as chamadas da API e as imagens ao backend em `http://127.0.0.1:5000`. Se o PowerShell bloquear `npm.ps1`, use `npm.cmd install` e `npm.cmd run dev` (ou execute `npm run dev` no Prompt de Comando).

O SQLite é criado em `backend\data\store.sqlite3`; cada personagem possui uma ilustração individual em `front\public\brainrots`.

O seed idempotente está disponível em `backend\services\seed.py`, na função `popular_banco()`. Também pode ser executado novamente pela rota `POST http://127.0.0.1:5000/popular-banco`. Reexecutar o seed não duplica personagens nem altera preços, estoques ou outros dados existentes.

## Contas e administração

Visitantes podem criar uma conta pela opção **Entrar → Criar conta**. A senha é armazenada com hash; para comprar e consultar os próprios pedidos é necessário estar conectado.

Na primeira inicialização, o backend cria o usuário `admin` com uma senha aleatória e a mostra uma única vez no terminal. Guarde essa senha. Opcionalmente, antes da execução, defina `ADMIN_USERNAME` e `ADMIN_PASSWORD` no ambiente para criar ou redefinir as credenciais administrativas (mínimo de 8 caracteres). A conta administrativa pode cadastrar Brainrots na opção **Admin**, com ou sem upload de imagem.

## Funcionalidades

- Catálogo pesquisável, detalhes do produto, raridade com cor e estoque.
- Carrinho salvo no navegador e finalização de compra simulada.
- Pedidos registrados no SQLite, com baixa de estoque transacional.
- Imagens dos personagens exibidas no catálogo, detalhes, carrinho e pedidos.

Para gerar os arquivos finais do frontend, execute `npm run build` dentro de `front`.
