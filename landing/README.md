## Landing (Vercel)

Esta carpeta es una landing “linda” para compartir en LinkedIn.

### Botón “Try it” + medir intención (sin eventos de pago)

El CTA apunta a **`/go`** en la misma web (Vercel). Esa página:

1. Carga un instante (Web Analytics registra **pageview en `/go`**).
2. Redirige al API en Render (`NEXT_PUBLIC_MVP_API_URL` o default).

En el dashboard de **Analytics**, filtrá por path **`/go`** ≈ cantidad de clics en “Try it” que siguieron al producto.

Para cambiar la URL del API, en Vercel → **Environment Variables**:

- `NEXT_PUBLIC_MVP_API_URL` = `https://tu-api.onrender.com`

### Analytics

- **Home** `/` — tráfico general.
- **`/go`** — intención de probar el producto (CTA).

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

