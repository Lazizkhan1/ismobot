
# Add GitHub Actions Deployment Through Cloudflare SSH

  ## Summary

  - Add .github/workflows/deploy.yml.
  - Deploy on pushes to main.
  - Use cloudflare/wrangler-action@v4 with CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID.
  - Install cloudflared in the runner and configure SSH with:
    ProxyCommand /usr/local/bin/cloudflared access ssh --hostname %h

  - SSH into the local server using SSH_HOST, SSH_USERNAME, and SSH_PASSWORD.

  ## Workflow File

  Create .github/workflows/deploy.yml:

  name: Deploy Ismobot

  on:
    push:
      branches:
        - main
    workflow_dispatch:

  jobs:
    deploy:
      runs-on: ubuntu-latest
      timeout-minutes: 30

      env:
        CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
        CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
        SSH_HOST: ${{ secrets.SSH_HOST }}
        SSH_USERNAME: ${{ secrets.SSH_USERNAME }}
        SSH_PASSWORD: ${{ secrets.SSH_PASSWORD }}
        DEPLOY_DIR: /opt/ismobot
        SERVICE_NAME: ismobot

      steps:
        - name: Checkout
          uses: actions/checkout@v4

        - name: Authenticate Cloudflare Wrangler
          uses: cloudflare/wrangler-action@v4
          with:
            apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
            accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}

        - name: Install SSH tools
          run: |
            sudo apt-get update
            sudo apt-get install -y sshpass curl lsb-release

        - name: Install cloudflared
          run: |
            curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg \
              | sudo tee /usr/share/keyrings/cloudflare-archive-keyring.gpg >/dev/null
            echo "deb [signed-by=/usr/share/keyrings/cloudflare-archive-keyring.gpg]
            https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" \
              | sudo tee /etc/apt/sources.list.d/cloudflared.list
            sudo apt-get update
            sudo apt-get install -y cloudflared

        - name: Configure SSH over Cloudflare
          run: |
            mkdir -p ~/.ssh
            chmod 700 ~/.ssh
            cat > ~/.ssh/config <<EOF
            Host ${SSH_HOST}
              HostName ${SSH_HOST}
              User ${SSH_USERNAME}
              ProxyCommand /usr/local/bin/cloudflared access ssh --hostname %h
              StrictHostKeyChecking accept-new
            EOF
            chmod 600 ~/.ssh/config

        - name: Deploy on server
          run: |
            sshpass -p "${SSH_PASSWORD}" ssh "${SSH_USERNAME}@${SSH_HOST}" "
              cd '${DEPLOY_DIR}'

              git fetch origin main
              git checkout main
              git pull --ff-only origin main

              if [ ! -d venv ]; then
                python3 -m venv venv
              fi

              ./venv/bin/pip install --upgrade pip
              ./venv/bin/pip install -r requirements.txt

              if [ -f alembic.ini ]; then
                ./venv/bin/alembic upgrade head
              fi

              sudo systemctl restart '${SERVICE_NAME}'
              sudo systemctl is-active --quiet '${SERVICE_NAME}'
            "

  ## Server Requirements

  - The server already has /opt/ismobot as a Git checkout of this repository.
  - The deploy user can read/write /opt/ismobot.
  - The deploy user can run sudo systemctl restart ismobot without an interactive password
    prompt.

  - .env stays on the server and is not copied from GitHub.
  - Cloudflare SSH access works with cloudflared access ssh --hostname %h without interactive
    browser login in GitHub Actions.

  ## Integration With Main Refactor Plan

  - After the SQLAlchemy/Alembic migration is added, this workflow will automatically run alembic
    upgrade head during deploy.

  - Keep the existing shell scripts as local/server fallback, but GitHub Actions becomes the
    primary deploy path.