## Landing (Vercel)

Esta carpeta es una landing “linda” para compartir en LinkedIn.

### Botón “Try it”

Por defecto abre el **API en Render**: `https://tracker-gastos-api.onrender.com` (nueva pestaña).

Para cambiar la URL sin tocar código, en Vercel → Project → **Settings → Environment Variables**:

- `NEXT_PUBLIC_MVP_API_URL` = tu URL del API

### Analytics

Podés seguir usando **Web Analytics** para pageviews del home. La ruta `/intent` ya no es el destino del CTA principal (quedó como página opcional).

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

