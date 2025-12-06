# Setup do Repositório Git

## Inicializar e Fazer Push para GitHub

Se o repositório ainda não está inicializado:

```bash
cd /home/flavio/Documentos/PESSOAL/PROJETO_FINCANCAS/mamhedge

# Inicializar repositório Git
git init

# Adicionar arquivos
git add .

# Fazer commit inicial
git commit -m "Initial commit: Sistema MamHedge completo"

# Adicionar remote (substitua com sua URL se diferente)
git remote add origin https://github.com/flaviomamede/mamhedge.git

# Verificar remote
git remote -v

# Fazer push
git branch -M main
git push -u origin main
```

## Se o repositório já está inicializado

```bash
# Verificar status
git status

# Adicionar arquivos novos/modificados
git add .

# Fazer commit
git commit -m "Descrição das mudanças"

# Fazer push
git push origin main
```

## Arquivos que NÃO serão commitados (devido ao .gitignore)

- `__pycache__/` - Cache do Python
- `*.db` - Bancos de dados (incluindo `mamhedge_operations.db`)
- `radar.md` - Dados sensíveis do robô
- `venv/` ou `env/` - Ambientes virtuais
- Arquivos de IDE (`.vscode/`, `.idea/`)

## Nota Importante

O arquivo `radar.md` contém dados do robô e está no `.gitignore` por padrão.
Se você quiser versionar um exemplo (sem dados reais), pode criar um `radar.example.md`.

