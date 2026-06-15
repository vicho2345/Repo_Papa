import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Ofertas para Ronald',
  description: 'Agente de búsqueda de empleo personalizado',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  )
}
