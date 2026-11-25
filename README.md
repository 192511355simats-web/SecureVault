# SecureVault

SecureVault is a Flask app for creating, verifying, and restoring encrypted
backups.

## Deploy to Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/192511355simats-web/SecureVault)

The Render Blueprint in `render.yaml` installs the requirements, starts the
Flask app, generates its secret values, and provisions persistent storage for
the database, encryption keys, and backups. The persistent disk requires a
paid Render web service.

After deployment finishes, Render provides a `*.onrender.com` URL. Open that
URL in a browser to use SecureVault.

## Public access warning

The deployed app has no user sign-in. Anyone with the URL can use the same
backup workspace, including its uploaded files, backups, audit records, and
encryption-key operations. Do not upload sensitive data to an unrestricted
deployment.
