# sv

Everything you need to build a Svelte project, powered by [`sv`](https://github.com/sveltejs/cli).

## Creating a project

If you're seeing this, you've probably already done this step. Congrats!

```sh
# create a new project
npx sv create my-app
```

To recreate this project with the same configuration:

```sh
# recreate this project
npx sv@0.17.1 create --template minimal --types ts --add prettier eslint tailwindcss="plugins:none" vitest="usages:component,unit" --install npm .
```

## Developing

Once you've created a project and installed dependencies with `npm install` (or `pnpm install` or `yarn`), start a development server:

```sh
npm run dev

# or start the server and open the app in a new browser tab
npm run dev -- --open
```

## Building

To create a production version of your app:

```sh
npm run build
```

You can preview the production build with `npm run preview`.

> To deploy your app, you may need to install an [adapter](https://svelte.dev/docs/kit/adapters) for your target environment.


## Staging WebRTC / TURN (Fase 7C)

La configuración de TURN REST efímero para navegador y backend privado se describe
en [infra/ansible/README.md](infra/ansible/README.md#fase-7c-turn-rest), junto con
variables, puertos, orden Terraform → build/push → Ansible y pruebas locales.
El secreto compartido permanece en SSM SecureString y en el state remoto cifrado;
no hay output del secreto. HTTP sirve para demo con archivo; HTTPS es obligatorio
antes de usar cámara clínica real.
