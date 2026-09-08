"""
Script de login único para autorizar o Sistema Cadastral CODEGO a enviar
e-mails em nome da sua conta Outlook/Hotmail, via Microsoft Graph API.

Rode este script UMA VEZ (ou sempre que precisar reautorizar):

    docker compose exec backend python scripts/setup_outlook_auth.py

Ele vai mostrar um código e um link. Abra o link em qualquer navegador,
digite o código e faça login com a conta Outlook que vai enviar os e-mails.
Depois disso, o token fica salvo em disco (OUTLOOK_TOKEN_CACHE_PATH) e o
backend passa a renovar automaticamente, sem precisar logar de novo.

Pré-requisito: ter cadastrado um app em portal.azure.com > Microsoft Entra ID
> Registros de aplicativo, com "Allow public client flows" = Yes e a permissão
delegada "Mail.Send" do Microsoft Graph, e ter OUTLOOK_CLIENT_ID configurado
no .env.
"""
import sys

import msal

sys.path.insert(0, "/app")

from app.config import settings  # noqa: E402
from app.services.outlook_auth import GRAPH_SCOPES, montar_app, salvar_cache  # noqa: E402


def main():
    if not settings.outlook_client_id:
        print("ERRO: OUTLOOK_CLIENT_ID não está configurado no .env.")
        print("Cadastre um app em portal.azure.com primeiro (veja instruções no README).")
        sys.exit(1)

    app = montar_app()

    contas = app.get_accounts()
    if contas:
        print(f"Já existe uma conta autorizada em cache: {contas[0].get('username')}")
        resposta = input("Quer reautorizar mesmo assim? [s/N]: ").strip().lower()
        if resposta != "s":
            print("Cancelado.")
            return

    flow = app.initiate_device_flow(scopes=GRAPH_SCOPES)
    if "user_code" not in flow:
        print("ERRO ao iniciar o device flow:", flow.get("error_description", flow))
        sys.exit(1)

    print()
    print("=" * 60)
    print(flow["message"])
    print("=" * 60)
    print()
    print("Aguardando você concluir o login no navegador...")

    resultado = app.acquire_token_by_device_flow(flow)  # bloqueia até concluir ou expirar

    salvar_cache(app.token_cache)

    if "access_token" in resultado:
        conta = app.get_accounts()[0]
        print()
        print(f"✓ Autorizado com sucesso como: {conta.get('username')}")
        print(f"✓ Token salvo em: {settings.outlook_token_cache_path}")
        print()
        print("Pronto! Configure no .env:")
        print("  EMAIL_PROVIDER=outlook_graph")
        print(f"  OUTLOOK_SENDER_EMAIL={conta.get('username')}")
        print("E reinicie o backend (docker compose restart backend).")
    else:
        print()
        print("ERRO ao obter o token:")
        print(resultado.get("error_description", resultado))
        sys.exit(1)


if __name__ == "__main__":
    main()
