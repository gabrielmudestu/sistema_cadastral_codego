# Publicação do Sistema Cadastral na VM da CODEGO

Guia para colocar o sistema no ar na máquina virtual Windows da CODEGO
(IP interno `192.168.0.245`), com https e domínio próprio.

## Como fica

```
Internet ──https──▶ 177.107.60.124 (IP público da CODEGO)
                          │  roteador/firewall encaminha 80 e 443
                          ▼
                    VM 192.168.0.245
                    └─ Caddy (portas 80/443) ── certificado https automático
                         ├─ /        → site (pasta frontend/)
                         └─ /api/... → backend (FastAPI) → MySQL
```

- Tudo roda em Docker, com `deploy/docker-compose.prod.yml`.
- O **Caddy** é a única porta de entrada. Ele serve o site, encaminha `/api`
  para o backend e, com um domínio configurado, obtém e renova o certificado
  https sozinho (Let's Encrypt, gratuito).
- O backend e o banco **não** ficam acessíveis de fora da VM.
- Site e API ficam no mesmo endereço, então o Netlify não é necessário.

Arquivos desta pasta:

| Arquivo | Para quê |
|---|---|
| `docker-compose.prod.yml` | Serviços de produção: banco, backend e Caddy |
| `Caddyfile` | Configuração do Caddy (site, `/api`, https) |
| `subir.ps1` | Sobe ou atualiza o sistema |
| `backup.ps1` | Backup do banco e dos arquivos |

---

## 1. Pedir ao TI

Texto pronto para enviar:

> Para publicar o Sistema Cadastral na VM **192.168.0.245**, precisamos:
>
> 1. Encaminhar as portas **80 e 443 (TCP)** do IP público **177.107.60.124**
>    para **192.168.0.245**, e liberar essas portas no firewall (da rede e do
>    Windows da VM).
> 2. Criar o subdomínio **`sistemacadastral.codego.com.br`** (registro DNS do
>    tipo A) apontando para **177.107.60.124**.
> 3. Deixar o IP da VM **fixo** em 192.168.0.245 (reserva no DHCP ou IP
>    estático), para o encaminhamento não quebrar.
>
> A porta 80 é necessária mesmo com https: o certificado (Let's Encrypt) é
> validado por ela, e ela também redireciona quem acessar por http.

Enquanto o TI não faz isso, dá para instalar e testar tudo **na rede interna**
(passo 4).

---

## 2. Preparar a VM (uma vez só)

1. **Git** — instalar de <https://git-scm.com/download/win>.
2. **WSL 2** — a VM já tem o WSL ativo. Conferir no PowerShell:
   ```powershell
   wsl --status
   ```
3. **Docker Desktop** — instalar de <https://www.docker.com/products/docker-desktop/>,
   usando o WSL 2 (padrão). Nas configurações do Docker Desktop, marcar
   **"Start Docker Desktop when you sign in"**.

   > **Licença:** o Docker Desktop é gratuito para empresas com menos de 250
   > funcionários **e** menos de US$ 10 milhões de faturamento anual. Se a
   > CODEGO passar de algum desses limites, precisa de uma assinatura paga
   > (Docker Pro/Team) — confirmar com o TI.

   > **O Docker Desktop só roda com um usuário logado.** Depois de reiniciar
   > a VM (ex.: Windows Update), o sistema só volta quando alguém fizer login.
   > Ao sair da Área de Trabalho Remota, **desconecte** (feche a janela) em vez
   > de **sair/fazer logoff**. Se a VM reiniciar com frequência, peça ao TI
   > para configurar o login automático desse usuário.

4. Conferir que está tudo instalado:
   ```powershell
   git --version; docker --version; docker compose version
   ```

---

## 3. Instalar o sistema

No PowerShell da VM:

```powershell
cd C:\
git clone https://github.com/gabrielmudestu/sistema_cadastral_codego.git
cd C:\sistema_cadastral_codego
copy .env.example .env
notepad .env
```

Preencha o `.env` com os valores de **produção**:

| Variável | Valor |
|---|---|
| `APP_ENV` | `production` |
| `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD`, `APP_SECRET_KEY` | senhas **novas e fortes** (não reutilizar as de desenvolvimento) — gerar com o comando abaixo |
| `DOMINIO` | **vazio** por enquanto (passo 4); depois `sistemacadastral.codego.com.br` (passo 5) |
| `CORS_ORIGINS` | `*` por enquanto; depois `https://sistemacadastral.codego.com.br` |
| `NOTIFICATION_EMAIL` | `atualizacaocadastral@codego.com.br` |
| `EMAIL_PROVIDER` | `smtp` |
| `SMTP_ENABLED` | `true` |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USE_TLS` | `smtp.gmail.com` / `587` / `true` |
| `SMTP_USER` e `SMTP_FROM_EMAIL` | `emailsendercodego@gmail.com` |
| `SMTP_PASSWORD` | a senha de app de 16 letras do Gmail |
| `RECAPTCHA_ENABLED` / `RECAPTCHA_SECRET_KEY` | ver passo 6 |

Para gerar uma senha forte (rodar uma vez para cada senha):

```powershell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object { [char]$_ })
```

> O `.env` tem senhas: nunca enviar para o GitHub (ele já está no
> `.gitignore`) nem por e-mail/WhatsApp.

Subir o sistema:

```powershell
.\deploy\subir.ps1
```

Na primeira vez demora alguns minutos (baixa as imagens e monta o backend).
No final aparecem os três serviços (`db`, `backend`, `caddy`) como `Up`.

> Se o PowerShell bloquear o script ("execução de scripts foi desabilitada"),
> rode antes, na mesma janela:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

---

## 4. Testar na rede interna (sem domínio)

Com `DOMINIO` vazio, o Caddy responde só por **http** na porta 80.

1. Na própria VM, abrir <http://localhost>.
2. De outro computador da CODEGO, abrir <http://192.168.0.245>.

Deve aparecer a tela inicial com os anexos. Para testar a API:
<http://192.168.0.245/api/processos/protocolo/REC-2026-00000> deve responder
`{"detail":"Protocolo não encontrado."}`.

> **Atenção:** o sistema já está com o e-mail de produção configurado. Um
> formulário preenchido nesse teste manda e-mail de verdade (protocolo para o
> endereço digitado e avisos para o `NOTIFICATION_EMAIL`).

> O reCAPTCHA pode mostrar erro de domínio nesse teste por IP e bloquear o
> envio dos formulários — ver passo 6.

---

## 5. Ativar o domínio e o https (depois do TI)

1. Confirmar que o DNS já responde com o IP público:
   ```powershell
   Resolve-DnsName sistemacadastral.codego.com.br
   ```
2. No `.env`:
   ```
   DOMINIO=sistemacadastral.codego.com.br
   CORS_ORIGINS=https://sistemacadastral.codego.com.br
   ```
3. Aplicar:
   ```powershell
   .\deploy\subir.ps1
   ```
4. Abrir <https://sistemacadastral.codego.com.br> — de preferência de fora da
   rede da CODEGO (ex.: celular no 4G).

O Caddy obtém o certificado sozinho no primeiro acesso (alguns segundos). Se
não funcionar, ver os logs dele (passo 9): o erro mais comum é a porta 80 ou
443 ainda não encaminhada, ou o DNS ainda não propagado.

---

## 6. reCAPTCHA

As páginas usam uma chave do Google reCAPTCHA (a `data-sitekey` nos HTML dos
formulários). Quem administra essa chave precisa, em
<https://www.google.com/recaptcha/admin>:

1. Adicionar o domínio **`sistemacadastral.codego.com.br`** à lista de
   domínios da chave.
2. Copiar a **chave secreta** para o `.env`:
   ```
   RECAPTCHA_ENABLED=true
   RECAPTCHA_SECRET_KEY=<chave secreta>
   ```
3. Rodar `.\deploy\subir.ps1`.

Se a chave for de uma conta pessoal, o ideal é criar uma nova numa conta da
CODEGO e trocar a `data-sitekey` nos formulários.

---

## 7. Atualizar o sistema

Quando houver mudanças no GitHub:

```powershell
cd C:\sistema_cadastral_codego
git pull
.\deploy\subir.ps1
```

- Mudanças no **site** (pasta `frontend/`) aparecem logo após o `git pull`.
- Mudanças no **backend** só valem depois do `subir.ps1` (ele remonta o backend).
- Mudanças que alteram tabelas do banco já existentes precisam ser aplicadas à
  mão (os scripts de `database/migrations/` só rodam automaticamente num banco
  novo). Tabelas **novas** são criadas sozinhas quando o backend inicia.
  **Faça um backup antes de atualizar.**

---

## 8. Backup

```powershell
.\deploy\backup.ps1
```

Cria `C:\backups\sistema-cadastral\<data>\` com:
- `banco.sql` — o banco inteiro;
- `arquivos.tgz` — PDFs gerados, assinados e documentos enviados.

Backups com mais de 30 dias são apagados (`-ManterDias` muda isso;
`-Destino` muda a pasta).

**Agendar todo dia às 2h** (PowerShell como administrador):

```powershell
$acao = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument '-NoProfile -ExecutionPolicy Bypass -File C:\sistema_cadastral_codego\deploy\backup.ps1'
$quando = New-ScheduledTaskTrigger -Daily -At 2am
Register-ScheduledTask -TaskName 'Backup Sistema Cadastral' -Action $acao -Trigger $quando -User $env:USERNAME -RunLevel Highest
```

> Backup na mesma VM não protege contra perda da VM. Peça ao TI uma pasta de
> rede ou outro servidor e use `-Destino \\servidor\pasta`, ou copie a pasta de
> backups para lá.

**Restaurar** (substitui os dados atuais):

```powershell
$compose = @('compose','-f','deploy\docker-compose.prod.yml','--env-file','.env')
$pasta = 'C:\backups\sistema-cadastral\<data>'
# banco
docker cp "$pasta\banco.sql" "$(docker @compose ps -q db):/tmp/banco.sql"
docker @compose exec -T db sh -c 'mysql -u root -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE" < /tmp/banco.sql'
# arquivos
docker cp "$pasta\arquivos.tgz" "$(docker @compose ps -q backend):/tmp/arquivos.tgz"
docker @compose exec -T backend tar xzf /tmp/arquivos.tgz -C /app
```

---

## 9. Comandos úteis

Na pasta `C:\sistema_cadastral_codego`:

```powershell
$compose = @('compose','-f','deploy\docker-compose.prod.yml','--env-file','.env')

docker @compose ps                    # situação dos serviços
docker @compose logs -f --tail 100 backend   # logs do backend (Ctrl+C sai)
docker @compose logs -f --tail 100 caddy     # logs do Caddy (https, acessos)
docker @compose restart backend       # reiniciar o backend
docker @compose down                  # parar tudo (os dados continuam salvos)
```

> Nunca use `down -v`: o `-v` **apaga** o banco e os arquivos.

---

## 10. Checklist de publicação

- [ ] TI: portas 80/443 encaminhadas, subdomínio criado, IP da VM fixo
- [ ] Docker Desktop instalado, iniciando com o login (licença verificada)
- [ ] `.env` de produção com senhas novas e `APP_ENV=production`
- [ ] Teste na rede interna (`http://192.168.0.245`)
- [ ] `DOMINIO` e `CORS_ORIGINS` preenchidos; https funcionando de fora da rede
- [ ] reCAPTCHA com o domínio adicionado e `RECAPTCHA_ENABLED=true`
- [ ] Ciclo completo testado: formulário → PDF → e-mail → envio do assinado → recibo → mensagem
- [ ] Backup agendado e copiado para fora da VM
- [ ] Restauração de um backup testada pelo menos uma vez
