## Landing (Vercel)

Esta carpeta es una landing “linda” para compartir en LinkedIn.

### Medir clicks (gratis)

En lugar de eventos custom (que suelen requerir plan pago), el botón “Quiero probarlo” navega a `/intent`.
Con **Vercel Web Analytics** podés mirar cuántas pageviews tuvo esa ruta y usarlo como proxy de clicks.

### Correr local

```bash
npm install
npm run dev
```

### Deploy en Vercel

- Importar el repo en Vercel
- **Root Directory**: `landing`
- Build: `next build`
- Output: default
- (Opcional) Activar **Web Analytics** en el proyecto para contar pageviews.

